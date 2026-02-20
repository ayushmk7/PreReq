# PreReq -- Technical PRD (Part 2)

## Backend System and Actual System Design

> Split from `techPRD.md`. Focused on backend architecture, APIs, frontend system surfaces, non-functional requirements, and delivery roadmap.

---

## 1. Backend Data Layer

### 1.1 Database Schema

*(Source: PRD §7.3.1)*

```
courses(id, name, created_at)

exams(id, course_id, name, created_at)

concept_graphs(id, exam_id, version, graph_json, created_at)

questions(id, exam_id, question_id_external, max_score)

question_concept_map(id, question_id, concept_id, weight)

scores(id, exam_id, student_id_external, question_id, score)

readiness_results(
    id, exam_id, student_id_external, concept_id,
    direct_readiness, prerequisite_penalty, downstream_boost,
    final_readiness, confidence, explanation_trace_json
)

class_aggregates(
    id, exam_id, concept_id,
    mean_readiness, median_readiness, std_readiness,
    below_threshold_count
)

clusters(id, exam_id, cluster_label, centroid_json, student_count)

cluster_assignments(id, exam_id, student_id_external, cluster_id)

student_tokens(id, exam_id, student_id_external, token, created_at)

parameters(id, exam_id, alpha, beta, gamma, threshold)
```

**MVP database:** SQLite (zero-config, single-instance).  
**Scale database:** PostgreSQL (JSONB for graph storage, concurrent access, full-text search).

---

## 2. Technology Stack and System Flow

### 2.1 Stack

*(Source: PRD §7.1)*

| Layer               | Technology                        | Justification                                                                       |
| ------------------- | --------------------------------- | ----------------------------------------------------------------------------------- |
| Frontend            | Next.js 14 (App Router)           | Server components for fast initial load; React for interactive dashboard            |
| Graph Visualization | D3.js (force-directed) or Visx    | Mature, flexible graph rendering with zoom/pan and custom node styling               |
| Backend API         | FastAPI (Python 3.11+)            | Async support, automatic OpenAPI docs, type validation via Pydantic                 |
| Graph Engine        | NetworkX                          | Topological sort, cycle detection, path analysis, DAG validation                    |
| Data Processing     | pandas + numpy                    | Vectorized readiness computation across all students                                |
| Clustering          | scikit-learn (KMeans)             | Standard, well-tested clustering with easy parameter tuning                         |
| Database (MVP)      | SQLite                            | Zero config, sufficient for single-instance MVP                                     |
| Database (Scale)    | PostgreSQL                        | JSONB for graph storage, concurrent access, full-text search                        |
| File Storage        | Local filesystem (MVP)            | Uploaded CSVs and computed results stored as files                                  |
| Auth (MVP)          | Token-based (unique URL per report)| No login required for students; instructor uses basic auth                          |

### 2.2 Processing Pipeline

*(Source: PRD §7.2)*

```
Step 1 (Upload)
  Input:  Exam scores CSV + question-to-concept mapping CSV
  Action: Validate schema, types, ranges, duplicates
  Output: Validated data or structured errors with row numbers

Step 2 (Graph)
  Input:  Concept dependency graph JSON/CSV (or edits via visual editor)
  Action: Validate DAG structure via topological sort
  Output: Validated graph or cycle-detection error with offending edges highlighted

Step 3 (Compute)
  Input:  Validated scores, mapping, graph, parameters
  Action: For each student: compute DirectReadiness per concept,
          iterate in topological order to apply upstream penalties
          and downstream boosts. Compute class aggregates in parallel.
          Vectorize with numpy where possible.
  Output: Per-student readiness vectors, class aggregates, confidence levels,
          explanation traces, cluster assignments

Step 4 (Store)
  Input:  Computation results
  Action: Write to database tables (readiness_results, class_aggregates,
          clusters, cluster_assignments)
  Output: Persisted results

Step 5 (Render)
  Input:  Stored results
  Action: Dashboard queries results and renders heatmap, alerts, tracing.
          Student reports generated on-demand via unique tokens.
  Output: Instructor dashboard views, student report pages
```

---

## 3. API Specification

*(Source: PRD §7.4)*

| ID     | Method | Endpoint                                        | Request Body / Params              | Response                                                |
| ------ | ------ | ----------------------------------------------- | ---------------------------------- | ------------------------------------------------------- |
| API-01 | POST   | `/api/v1/exams/{exam_id}/scores`                | Multipart CSV upload               | `{ status, row_count, errors[] }`                       |
| API-02 | POST   | `/api/v1/exams/{exam_id}/mapping`               | Multipart CSV upload               | `{ status, concept_count, errors[] }`                   |
| API-03 | POST   | `/api/v1/exams/{exam_id}/graph`                 | JSON body or CSV upload            | `{ status, node_count, edge_count, is_dag }`            |
| API-04 | PATCH  | `/api/v1/exams/{exam_id}/graph`                 | `{ add_edges, remove_edges, add_nodes, remove_nodes }` | `{ status, is_dag, cycle_path? }`          |
| API-05 | POST   | `/api/v1/exams/{exam_id}/compute`               | `{ alpha, beta, gamma, threshold }`| `{ status, students_processed, time_ms }`               |
| API-06 | GET    | `/api/v1/exams/{exam_id}/dashboard`             | Query: `concept_id?`              | `{ heatmap, alerts[], aggregates[] }`                   |
| API-07 | GET    | `/api/v1/exams/{exam_id}/dashboard/trace/{concept_id}` | None                        | `{ direct, upstream[], downstream[], waterfall }`       |
| API-08 | GET    | `/api/v1/exams/{exam_id}/clusters`              | None                               | `{ clusters[], assignments_summary }`                   |
| API-09 | GET    | `/api/v1/reports/{token}`                       | None                               | `{ student report JSON }`                               |
| API-10 | GET    | `/api/v1/exams/{exam_id}/parameters`            | None                               | `{ alpha, beta, gamma, threshold }`                     |
| API-11 | PUT    | `/api/v1/exams/{exam_id}/parameters`            | `{ alpha, beta, gamma, threshold }`| `{ status }`                                            |

**Auth:** All endpoints require authentication **except** API-09 (student report), which uses token-based access.

---

## 4. Frontend System Surfaces

### 4.1 Routes and Pages

*(Source: PRD §8.1)*

| Route                                       | Page               | Description                                                    |
| ------------------------------------------- | ------------------ | -------------------------------------------------------------- |
| `/`                                         | Landing / Login    | Instructor login, course selection                             |
| `/courses/{id}/exams`                       | Exam List          | List of exams for a course; upload new exam                    |
| `/exams/{id}/upload`                        | Upload Wizard      | Step-by-step upload: scores, mapping, graph                    |
| `/exams/{id}/graph`                         | Graph Editor       | Visual DAG editor with drag-and-drop nodes and edges           |
| `/exams/{id}/dashboard`                     | Instructor Dashboard| Heatmap, alerts, tracing, clusters                            |
| `/exams/{id}/dashboard/trace/{concept}`     | Root-Cause Trace   | Detailed waterfall for one concept                             |
| `/exams/{id}/settings`                      | Exam Settings      | Parameter tuning (alpha, beta, gamma, threshold)               |
| `/report/{token}`                           | Student Report     | Public page (no login); personal concept graph and study plan  |

### 4.2 Key Components

*(Source: PRD §8.2)*

#### ConceptHeatmap
- **Library:** D3.js or custom React grid
- **Data input:** class aggregates from API-06
- **Behavior:** Primary entry point for instructor analysis. Rows = concepts sorted by topological depth. Columns = readiness buckets (0–20, 20–40, 40–60, 60–80, 80–100). Each cell shows count and percentage of students in that bucket. Color intensity maps to the student count in each cell (not the readiness value). Cells are clickable to open the trace view (API-07).

#### Foundational Gap Alerts
- **Trigger:** A foundational concept (one with multiple dependents) has class-average readiness below a configurable threshold (default `0.5`).
- **Sorting:** Alerts sorted by impact, defined as: `impact = (num_downstream_concepts_affected) * (num_students_below_threshold)`
- **Alert content per item:** concept name, class average readiness, number of students below threshold, list of downstream concepts that may be affected, and a recommended action (review session, supplementary material, etc.).

#### Root-Cause Trace Panel
When an instructor clicks on any weak concept in the heatmap, the system displays: direct performance on the selected concept, contributing prerequisite weaknesses (with their readiness scores), the contribution weight of each prerequisite to the penalty, the number of affected students, and a waterfall-style visualization showing how direct readiness was modified by upstream penalties and downstream boosts to arrive at the final score.

#### ConceptDAGViewer
- **Library:** D3.js (force-directed layout) or Visx
- **Data input:** concept graph + class aggregates
- **Behavior:** Nodes sized by student count below threshold. Nodes colored by class-average readiness. Edges drawn as arrows with thickness proportional to weight. Supports zoom, pan, and click-to-select.

#### WaterfallChart
- **Library:** Recharts or D3.js
- **Data input:** trace data from API-07
- **Behavior:** Stacked bar chart showing how DirectReadiness is modified by prerequisite penalty and downstream boost to produce FinalReadiness.

#### StudentConceptGraph
- **Library:** D3.js (force-directed layout) or Visx
- **Data input:** per-student readiness data from API-09
- **Behavior:** Interactive personal DAG. Nodes colored by individual readiness: **green** (> 0.7), **yellow** (0.4–0.7), **red** (< 0.4). Supports zoom, pan, click-to-select.

#### TopWeakConcepts
- **Library:** React component
- **Data input:** student report from API-09
- **Behavior:** Ordered list of the **5 weakest concepts** for the student, each showing readiness score and confidence level.

#### StudyPlanList
- **Library:** React component
- **Data input:** student report from API-09
- **Behavior:** Sequential list of concepts to review, ordered by topological sort so prerequisites come first. Each item shows concept name, readiness score (color-coded: green > 0.7, yellow 0.4–0.7, red < 0.4), confidence badge, why it was flagged, and a brief explanation.

#### Student Report Exclusions
Students must **NOT** see: peer comparisons, rankings, percentile positions, predictive risk labels, or any demographic-correlated analysis.

#### GraphEditor
- **Library:** D3.js or custom React + SVG
- **Data input:** concept graph from API-03 / API-04
- **Behavior:** Nodes are draggable. Edges are created by drawing from one node to another. Weight is set via a slider on the edge. Cycle detection runs on every edit and blocks invalid additions with an inline error.

---

## 5. Non-Functional Requirements

### 5.1 Performance

*(Source: PRD §9.1)*

| Operation                        | Target      |
| -------------------------------- | ----------- |
| Full readiness computation (1,200 students x 30 concepts x 50 questions) | < 10 seconds |
| Dashboard page load (after computation) | < 2 seconds |
| Graph editor interactions (add node, add edge, cycle check) | < 200 ms |
| Student report generation        | < 1 second  |

### 5.2 Reliability and Testing

*(Source: PRD §9.2)*

**Determinism:** Same inputs must always produce the same outputs.

**Error handling:** All upload and compute endpoints return structured error objects with field-level detail.

**Required unit test coverage:**
- Topological sort correctness
- Cycle detection (positive and negative cases)
- Readiness formula: all four stages including edge cases (null direct readiness, single-concept graph, disconnected nodes, zero-edge-weight)
- Confidence computation (all threshold boundaries)
- CSV validation (reject malformed files with correct error messages)

**Required integration test coverage:**
- Full upload → compute → dashboard pipeline end-to-end
- Parameter changes trigger recomputation and produce updated results
- Graph edits trigger DAG validation; invalid edits are rejected

### 5.3 Security and Privacy

*(Source: PRD §9.3)*

- **Minimal PII:** only `StudentID` (may be anonymized). No names, emails, or demographics stored.
- **Role-based access:** instructors see all students; students see only their own report.
- **Student report tokens:** 128-bit random UUIDs, non-guessable, expire after a configurable period (default 30 days).
- **Auth:** all API endpoints require authentication except the student report endpoint (token-based access).
- **HTTPS:** required in production.

---

## 6. Technical Success Metrics

*(Source: PRD §10.1)*

| Metric                            | Target                                           | Measurement Method                                |
| --------------------------------- | ------------------------------------------------ | ------------------------------------------------- |
| Computation time (1,200 students) | < 10 seconds                                     | Server-side timer on `/compute` endpoint          |
| Dashboard load time               | < 2 seconds                                      | Lighthouse or browser performance API             |
| Graph rendering stability          | No crashes on graphs up to 50 nodes / 100 edges | Automated browser test                            |
| Readiness output validity          | All values in `[0, 1]`; no `NaN` in final output| Unit test assertions                              |
| CSV validation accuracy            | 100% of malformed files rejected with correct error | Test suite with 20+ malformed CSV variants     |

---

## 7. Technical Implementation Roadmap

*(Source: PRD §15)*

### Phase 1: MVP (Weeks 1–6)

- CSV upload with full validation (scores, mapping, graph)
- Manual concept graph creation and editing via visual editor
- Readiness inference engine (all 4 stages)
- Instructor dashboard: heatmap, alerts, root-cause tracing
- Student report: concept graph, study plan, confidence indicators
- SQLite database
- Basic auth for instructors; token-based student access

### Phase 2: Integration (Weeks 7–12)

- LMS integration (Canvas API for grade export/import)
- LLM-assisted concept tagging: given question text, suggest concept tags
- LLM-assisted graph generation: given a list of concepts, suggest prerequisite edges
- Misconception clustering with cluster-level intervention suggestions
- PostgreSQL migration

### Phase 3: Longitudinal (Months 4–6)

- Multi-exam tracking: readiness trends over time per student and per class
- Curriculum diagnostics: identify consistently weak concepts across semesters
- Exportable reports (PDF, CSV) for institutional review

### Phase 4: Institutional (Months 6–12)

- Multi-department analytics dashboard
- SSO integration (SAML / OAuth)
- SLA-backed deployment options
- API for third-party integrations
