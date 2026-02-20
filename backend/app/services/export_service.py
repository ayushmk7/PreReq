"""Export artifact service for Canvas-ready download bundles.

Generates deterministic zip packages containing:
  - Knowledge graph (JSON + CSV)
  - Readiness results (student-level + class-level)
  - Intervention and cluster reports
  - Mapping and parameter snapshots
  - Run manifest with checksums
"""

import csv
import hashlib
import io
import json
import os
import zipfile
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.config import settings


def generate_export_bundle(
    exam_id: str,
    exam_name: str,
    graph_json: dict[str, Any],
    readiness_results: list[dict[str, Any]],
    class_aggregates: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    cluster_assignments: list[dict[str, Any]],
    interventions: list[dict[str, Any]],
    parameters: dict[str, Any],
    question_mapping: list[dict[str, Any]],
    compute_run_id: Optional[str] = None,
) -> tuple[str, str, dict[str, Any]]:
    """Generate a zip export bundle and write to disk.

    Returns (file_path, sha256_checksum, manifest_dict).
    """
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in exam_name)
    filename = f"conceptlens_{safe_name}_{timestamp}.zip"
    file_path = os.path.join(settings.EXPORT_DIR, filename)

    file_checksums: dict[str, str] = {}
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Knowledge graph
        graph_bytes = json.dumps(graph_json, indent=2).encode()
        zf.writestr("graph/graph.json", graph_bytes)
        file_checksums["graph/graph.json"] = _sha256(graph_bytes)

        nodes_csv = _dicts_to_csv(
            [{"id": n["id"], "label": n.get("label", n["id"])} for n in graph_json.get("nodes", [])],
            ["id", "label"],
        )
        zf.writestr("graph/graph_nodes.csv", nodes_csv)
        file_checksums["graph/graph_nodes.csv"] = _sha256(nodes_csv.encode())

        edges_csv = _dicts_to_csv(
            [{"source": e["source"], "target": e["target"], "weight": e.get("weight", 0.5)}
             for e in graph_json.get("edges", [])],
            ["source", "target", "weight"],
        )
        zf.writestr("graph/graph_edges.csv", edges_csv)
        file_checksums["graph/graph_edges.csv"] = _sha256(edges_csv.encode())

        # 2. Student-level readiness
        readiness_csv = _dicts_to_csv(
            readiness_results,
            ["student_id", "concept_id", "direct_readiness", "prerequisite_penalty",
             "downstream_boost", "final_readiness", "confidence"],
        )
        zf.writestr("readiness/student_readiness.csv", readiness_csv)
        file_checksums["readiness/student_readiness.csv"] = _sha256(readiness_csv.encode())

        readiness_json = json.dumps(readiness_results, indent=2).encode()
        zf.writestr("readiness/student_readiness.json", readiness_json)
        file_checksums["readiness/student_readiness.json"] = _sha256(readiness_json)

        # 3. Class-level aggregates
        agg_csv = _dicts_to_csv(
            class_aggregates,
            ["concept_id", "mean_readiness", "median_readiness", "std_readiness", "below_threshold_count"],
        )
        zf.writestr("readiness/class_aggregates.csv", agg_csv)
        file_checksums["readiness/class_aggregates.csv"] = _sha256(agg_csv.encode())

        # 4. Cluster reports
        clusters_json = json.dumps(clusters, indent=2).encode()
        zf.writestr("clusters/clusters.json", clusters_json)
        file_checksums["clusters/clusters.json"] = _sha256(clusters_json)

        assignments_csv = _dicts_to_csv(
            cluster_assignments,
            ["student_id", "cluster_label"],
        )
        zf.writestr("clusters/cluster_assignments.csv", assignments_csv)
        file_checksums["clusters/cluster_assignments.csv"] = _sha256(assignments_csv.encode())

        # 5. Intervention recommendations
        interventions_json = json.dumps(interventions, indent=2).encode()
        zf.writestr("interventions/interventions.json", interventions_json)
        file_checksums["interventions/interventions.json"] = _sha256(interventions_json)

        interventions_csv = _dicts_to_csv(
            interventions,
            ["concept_id", "students_affected", "downstream_concepts",
             "current_readiness", "impact", "rationale", "suggested_format"],
        )
        zf.writestr("interventions/interventions.csv", interventions_csv)
        file_checksums["interventions/interventions.csv"] = _sha256(interventions_csv.encode())

        # 6. Mapping snapshot
        mapping_csv = _dicts_to_csv(
            question_mapping,
            ["question_id", "concept_id", "weight"],
        )
        zf.writestr("mapping/question_concept_mapping.csv", mapping_csv)
        file_checksums["mapping/question_concept_mapping.csv"] = _sha256(mapping_csv.encode())

        # 7. Parameters snapshot
        params_json = json.dumps(parameters, indent=2).encode()
        zf.writestr("parameters.json", params_json)
        file_checksums["parameters.json"] = _sha256(params_json)

        # 8. Canvas upload instructions
        instructions = _canvas_upload_instructions(exam_name)
        zf.writestr("CANVAS_UPLOAD_INSTRUCTIONS.md", instructions)
        file_checksums["CANVAS_UPLOAD_INSTRUCTIONS.md"] = _sha256(instructions.encode())

        # 9. Manifest
        manifest = {
            "schema_version": "1.0",
            "export_timestamp": datetime.utcnow().isoformat(),
            "exam_id": exam_id,
            "exam_name": exam_name,
            "compute_run_id": compute_run_id,
            "files": file_checksums,
            "file_count": len(file_checksums),
            "students_count": len(set(r.get("student_id", "") for r in readiness_results)),
            "concepts_count": len(set(r.get("concept_id", "") for r in readiness_results)),
            "parameters": parameters,
        }
        manifest_bytes = json.dumps(manifest, indent=2).encode()
        zf.writestr("manifest.json", manifest_bytes)

    zip_bytes = buf.getvalue()
    bundle_checksum = _sha256(zip_bytes)

    with open(file_path, "wb") as f:
        f.write(zip_bytes)

    manifest["bundle_checksum"] = bundle_checksum
    return file_path, bundle_checksum, manifest


def validate_export_bundle(file_path: str, manifest: dict[str, Any]) -> list[str]:
    """Validate an export bundle against its manifest. Returns list of errors."""
    errors = []

    if not os.path.exists(file_path):
        return [f"Export file not found: {file_path}"]

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            expected_files = manifest.get("files", {})
            zip_names = set(zf.namelist())

            for fname, expected_hash in expected_files.items():
                if fname not in zip_names:
                    errors.append(f"Missing file: {fname}")
                    continue
                content = zf.read(fname)
                actual_hash = _sha256(content)
                if actual_hash != expected_hash:
                    errors.append(
                        f"Checksum mismatch for {fname}: "
                        f"expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
                    )
    except zipfile.BadZipFile:
        errors.append("Corrupt zip file")

    return errors


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dicts_to_csv(rows: list[dict[str, Any]], columns: list[str]) -> str:
    """Convert a list of dicts to CSV string with given column order."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in columns})
    return output.getvalue()


def _canvas_upload_instructions(exam_name: str) -> str:
    return f"""# Canvas Upload Instructions for "{exam_name}"

## Export Contents

This bundle contains the following artifacts ready for Canvas upload:

### 1. Knowledge Graph (`graph/`)
- `graph.json` — Full concept dependency graph (JSON format)
- `graph_nodes.csv` — Concept nodes list
- `graph_edges.csv` — Prerequisite edges with weights

### 2. Readiness Results (`readiness/`)
- `student_readiness.csv` — Per-student concept readiness scores
- `student_readiness.json` — Same data in JSON format
- `class_aggregates.csv` — Class-level statistics per concept

### 3. Cluster Reports (`clusters/`)
- `clusters.json` — Cluster definitions with centroids and weak concepts
- `cluster_assignments.csv` — Student-to-cluster assignments

### 4. Intervention Recommendations (`interventions/`)
- `interventions.json` — Ranked intervention suggestions
- `interventions.csv` — Same data in CSV format

### 5. Configuration
- `mapping/question_concept_mapping.csv` — Question-concept mapping used
- `parameters.json` — Computation parameters used

## Canvas Upload Steps

1. Navigate to your course in Canvas
2. Go to **Files** in the course navigation
3. Create a folder named `ConceptLens Exports` (or similar)
4. Upload the entire zip file, or extract and upload individual files
5. For gradebook integration:
   - Use `student_readiness.csv` for grade import
   - Ensure StudentID column matches Canvas student identifiers
6. For assignment feedback:
   - Reference `interventions.json` for per-concept recommendations
   - Use cluster reports for group-targeted interventions

## Data Integrity

- Each file has a SHA-256 checksum in `manifest.json`
- Verify the bundle checksum matches before uploading
- Re-export from the same compute run ID for identical results

## Privacy Notes

- Student data uses anonymized IDs only
- No names, emails, or demographic data included
- Suitable for institutional sharing per FERPA guidelines
"""
