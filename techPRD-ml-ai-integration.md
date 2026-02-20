# PreReq -- Technical PRD (Part 1)

## ML and AI Integration

> Split from `techPRD.md`. Focused on data/graph modeling, readiness inference, confidence estimation, clustering, and AI-assisted roadmap items.

---

## 1. Data Models and Schemas (ML-Facing)

### 1.1 Concept Readiness Graph

The core data structure is a directed acyclic graph (DAG) where nodes represent concepts and directed edges represent prerequisite dependencies. One graph exists per course per exam, with version history. *(Source: PRD §5, §6.2)*

#### Node Properties

| Property              | Type                       | Description                                              |
| --------------------- | -------------------------- | -------------------------------------------------------- |
| `concept_id`          | `string`                   | Unique identifier for the concept                        |
| `label`               | `string`                   | Human-readable concept name                              |
| `readiness_score`     | `float [0, 1]`             | Final computed readiness after propagation                |
| `direct_readiness`    | `float [0, 1]`             | Weighted average of tagged question scores                |
| `confidence`          | `enum: high / medium / low`| Based on evidence coverage and variance                  |
| `evidence_breakdown`  | `object`                   | Direct contribution, upstream penalty, downstream boost  |
| `explanation_trace`   | `string[]`                 | Human-readable reasoning chain                           |

#### Edge Properties

| Property    | Type               | Description                                      |
| ----------- | ------------------ | ------------------------------------------------ |
| `source`    | `string`           | Prerequisite `concept_id`                        |
| `target`    | `string`           | Dependent `concept_id`                           |
| `weight`    | `float [0, 1]`     | Dependency strength (default `0.5`)              |
| `rationale` | `string` (optional)| Instructor-provided reason for the dependency    |

#### Graph Constraints

- Must be a DAG (no cycles). Validated via topological sort on every upload and edit.
- If a cycle is detected, reject the operation and return the cycle path in the error message.
- If no graph is uploaded, the system creates isolated nodes (one per concept) with no edges.

#### Graph Management Operations

| Operation          | Behavior                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| Add/remove nodes   | Instructor can add new concept nodes or remove unused ones               |
| Add/remove edges   | Create or delete prerequisite relationships; adjust weights              |
| Cycle detection    | Runs on every edit; blocks invalid additions with an explanatory error   |
| Version control    | Each save creates a new timestamped, annotated version; revert supported |
| Clone              | Clone a graph from a previous exam as the starting point for a new exam  |

---

### 1.2 Input File Formats and Validation

Three input files are accepted. All are validated on upload before any computation begins. *(Source: PRD §6.1)*

#### 1.2.1 Exam Scores File (Required)

- **Format:** CSV
- **Required fields:** `StudentID` (string), `QuestionID` (string), `Score` (numeric)
- **Optional field:** `MaxScore` (numeric, defaults to `1.0` if absent)
- **Limits:** 50 MB file size; 500,000 rows

**Validation rules:**

| Rule | Detail |
| ---- | ------ |
| Non-null IDs | All rows must have non-null `StudentID` and `QuestionID` |
| Score range | `Score` must be numeric and in `[0, MaxScore]` |
| No duplicates | No duplicate `(StudentID, QuestionID)` pairs |
| MaxScore positive | If `MaxScore` is provided, it must be `> 0` for all rows |

#### 1.2.2 Question-to-Concept Mapping File (Required)

- **Format:** CSV
- **Required fields:** `QuestionID` (string), `ConceptID` (string)
- **Optional field:** `Weight` (float, default `1.0`)
- A single question may map to multiple concepts (one row per association).

**Validation rules:**

- Every `QuestionID` in the scores file must appear in the mapping file.
- All `ConceptID` values must be consistent with the concept graph.

#### 1.2.3 Concept Dependency Graph (Optional)

**JSON format:**

```json
{
  "nodes": [{ "id": "C1", "label": "Derivatives" }],
  "edges": [{ "source": "C0", "target": "C1", "weight": 0.7 }]
}
```

**CSV format:** columns `source`, `target`, `weight` (optional, default `0.5`).

**Validation rules:**

- Graph must be a DAG (no cycles); validated via topological sort.
- All concept IDs referenced in edges must exist as nodes.
- Edge weights must be in `[0, 1]`.

---

### 1.3 In-Memory Structures (During Computation)

*(Source: PRD §7.3.2)*

```python
# Student-concept matrix: shape (num_students, num_concepts)
# Each cell = DirectReadiness(student, concept) or NaN if no evidence
readiness_matrix: np.ndarray

# Adjacency matrix: shape (num_concepts, num_concepts)
# adj[i][j] = edge weight from concept i to concept j, 0 if no edge
adjacency: np.ndarray

# Topological order: list of concept indices, leaves first
topo_order: list[int]
```

---

## 2. Algorithms and Computation

### 2.1 Readiness Inference Engine

Computes a readiness score for each `(student, concept)` pair in four stages. Processing order follows the topological sort of the DAG: leaves (no prerequisites) are processed first, progressing toward roots so all upstream values are available before any dependent concept. *(Source: PRD §6.3)*

#### Stage 1: Direct Readiness

For each concept `C` and student `S`:

```
DirectReadiness(S, C) = SUM(w_q * (score_q / maxscore_q)) / SUM(w_q)
```

- `w_q` = weight from the question-to-concept mapping
- Sum is over all questions `q` tagged to concept `C`
- If no questions are tagged to `C`, `DirectReadiness` is `null` and the concept is marked **"inferred only"**

#### Stage 2: Upstream Weakness Propagation (Prerequisite Penalty)

```
PrerequisitePenalty(S, C) = SUM over parents P of:
    edge_weight(P, C) * max(0, threshold - DirectReadiness(S, P))
```

- Only prerequisites below the `threshold` parameter contribute a penalty.
- This prevents strong prerequisites from generating noise.

#### Stage 3: Downstream Validation Boost

```
DownstreamBoost(S, P) = SUM over children D of:
    validation_weight * DirectReadiness(S, D)
```

- `validation_weight = edge_weight * 0.4`
- Boost is **capped at 0.2** to prevent advanced performance from fully overriding direct evidence of weakness.

#### Stage 4: Final Readiness

```
FinalReadiness(S, C) = clamp([0, 1],
    alpha * DirectReadiness(S, C)
    - beta * PrerequisitePenalty(S, C)
    + gamma * DownstreamBoost(S, C)
)
```

### 2.1.1 Tunable Parameters

All parameters are instructor-adjustable per exam via the dashboard settings panel.

| Parameter   | Default | Used In               | Description                                         |
| ----------- | ------- | --------------------- | --------------------------------------------------- |
| `alpha`     | `1.0`   | Stage 4 (final)       | Weight of direct readiness                          |
| `beta`      | `0.3`   | Stage 4 (final)       | Weight of prerequisite penalty                      |
| `gamma`     | `0.2`   | Stage 4 (final)       | Weight of downstream boost                          |
| `threshold` | `0.6`   | Stage 2 (penalty)     | Readiness below which a prerequisite is "weak"      |
| `k`         | `4`     | Clustering (§2.3)     | Number of clusters for k-means                      |

---

### 2.2 Confidence Estimation

Each readiness score is accompanied by a confidence level: **High**, **Medium**, or **Low**. Confidence is the **minimum** of three independent factors. *(Source: PRD §6.4)*

| Factor                           | High      | Medium    | Low       |
| -------------------------------- | --------- | --------- | --------- |
| Tagged questions for this concept| >= 3      | 2         | 0 or 1    |
| Total points coverage            | >= 10 pts | 5–9 pts   | < 5 pts   |
| Variance across related concepts | < 0.15    | 0.15–0.30 | > 0.30    |

Confidence is displayed alongside every readiness score to prevent overinterpretation of weak evidence.

---

### 2.3 Clustering and Intervention Ranking

#### Misconception Clustering *(Source: PRD §6.5.4)*

- **Algorithm:** k-means
- **Default k:** 4 (configurable)
- **Input features:** per-student concept readiness vectors (no demographic data)
- **Output per cluster:** cluster size, centroid readiness values, top 3 distinguishing weak concepts, suggested targeted interventions

#### Intervention Ranking *(Source: PRD §6.5.5)*

Generate a prioritized list of recommended interventions ranked by estimated impact:

```
Impact = (num_students_affected) * (num_downstream_concepts) * (1 - current_readiness)
```

Each recommendation includes: target concept, estimated student reach, rationale, and suggested format (review session, practice problems, office hours focus).

---

## 3. AI Integration Roadmap Items

*(Extracted from implementation roadmap in original PRD)*

- LMS integration (Canvas API for grade export/import)
- LLM-assisted concept tagging: given question text, suggest concept tags
- LLM-assisted graph generation: given a list of concepts, suggest prerequisite edges
- Misconception clustering with cluster-level intervention suggestions

---

## Appendix A: Example Inputs

### A.1 Exam Scores CSV

```csv
StudentID,QuestionID,Score,MaxScore
S001,Q1,8,10
S001,Q2,5,10
S001,Q3,9,10
S002,Q1,6,10
S002,Q2,3,10
S002,Q3,7,10
```

### A.2 Question-to-Concept Mapping CSV

```csv
QuestionID,ConceptID,Weight
Q1,C_derivatives,1.0
Q1,C_limits,0.5
Q2,C_integrals,1.0
Q3,C_chain_rule,1.0
Q3,C_derivatives,0.8
```

### A.3 Concept Dependency Graph JSON

```json
{
  "nodes": [
    { "id": "C_limits",     "label": "Limits" },
    { "id": "C_derivatives", "label": "Derivatives" },
    { "id": "C_chain_rule",  "label": "Chain Rule" },
    { "id": "C_integrals",   "label": "Integrals" }
  ],
  "edges": [
    { "source": "C_limits",      "target": "C_derivatives", "weight": 0.7 },
    { "source": "C_derivatives",  "target": "C_chain_rule",  "weight": 0.8 },
    { "source": "C_derivatives",  "target": "C_integrals",   "weight": 0.5 }
  ]
}
```
