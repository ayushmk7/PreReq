# PreReq Product Requirements Document

## 1. Document Purpose

This document is the canonical product and system specification for **PreReq**, an AI-assisted concept readiness platform for instructors and students. It is intended to be detailed enough that:

- an engineer can implement features without re-deriving the architecture,
- a product owner can scope roadmap work without reading the entire codebase,
- and another LLM can generate future PRDs or feature specs by extending this document rather than rewriting assumptions from scratch.

This PRD reflects both:

- the **current implemented system** present in this repository, and
- the **intended product direction** implied by the existing code, technical docs, and user flows.

When future features are added, this document should be updated first or in the same change set as implementation.

## 2. Product Summary

PreReq helps instructors understand whether students are ready for downstream course concepts by combining:

- exam score uploads,
- question-to-concept mappings,
- a concept prerequisite graph,
- a deterministic readiness computation engine,
- instructor-facing analytics,
- student-facing individualized reports,
- and AI-assisted authoring and analysis workflows.

The system is designed around the idea that raw question scores are not enough. A student may appear weak on an advanced concept because of a missing prerequisite, or appear stronger on a foundational concept because downstream success provides evidence of understanding. PreReq models those relationships explicitly with a directed acyclic graph (DAG) and produces explainable readiness outputs.

## 3. Product Goals

### 3.1 Primary goals

1. Give instructors a reliable, explainable view of class readiness by concept.
2. Help instructors identify foundational gaps and high-impact interventions.
3. Give students a non-punitive, actionable report that explains what to study next.
4. Reduce manual setup work with AI-assisted concept tagging, graph suggestion, graph expansion, and intervention drafting.
5. Keep the core readiness pipeline deterministic, auditable, and testable.

### 3.2 Non-goals

PreReq is not intended to:

- replace instructor grading systems,
- generate final grades,
- rank students against each other in student-facing views,
- use demographic or sensitive protected-class data,
- or allow the LLM to silently mutate instructional data without review.

## 4. Primary Users

### 4.1 Instructor

The instructor creates courses and exams, uploads score files and mappings, tunes parameters, runs computation, reviews dashboard outputs, inspects traces, reviews AI suggestions, chats with the AI assistant, and exports results for external systems.

### 4.2 Student

The student receives an individualized report, either via tokenized public report access or instructor-selected internal view, showing concept readiness, weak concepts, and a study plan ordered by prerequisites.

### 4.3 Internal builder or future LLM

A future builder or LLM should treat this document as the source of truth for terminology, workflows, domain rules, extension patterns, and system constraints.

## 5. Core Product Concepts

### 5.1 Course

A top-level container for instructional content. A course has many exams.

### 5.2 Exam

An assessment instance within a course. Most uploaded data, graph versions, parameters, compute runs, suggestions, exports, and reports are scoped to an exam.

### 5.3 Concept graph

A directed acyclic graph where nodes are concepts and directed edges represent prerequisite dependencies. Source -> target means source should be understood before target.

### 5.4 Readiness

A normalized value in `[0, 1]` representing estimated concept mastery after combining direct evidence, prerequisite weakness propagation, and downstream validation.

### 5.5 Confidence

A categorical label (`high`, `medium`, `low`) indicating how much evidence supports a readiness estimate.

### 5.6 Intervention

A ranked recommendation for instructor action, based on weak concepts, student impact, and downstream dependency effects.

## 6. End-to-End Product Workflow

### 6.1 Instructor workflow

1. Create or select a course.
2. Create or select an exam.
3. Upload scores CSV.
4. Upload concept mapping CSV.
5. Upload or generate a concept graph.
6. Configure analysis parameters.
7. Run compute.
8. Review dashboard outputs, alerts, interventions, clusters, and traces.
9. Generate student reports or export bundles.
10. Optionally use AI assistance to improve mappings, graph structure, and intervention messaging.

### 6.2 Student workflow

1. Access report via token or selected student view.
2. Review overall concept map.
3. Inspect top weak concepts.
4. Follow study plan in prerequisite order.
5. Use instructor/TA contact details if support is needed.

### 6.3 AI-assisted workflow

1. Instructor requests AI concept tag suggestions, prerequisite edge suggestions, graph expansion, intervention drafts, or chat analysis.
2. System calls OpenAI with structured prompts and response schemas.
3. Suggestions are stored with metadata, review status, and prompt version.
4. Instructor reviews, accepts, rejects, or applies suggestions.
5. Accepted changes can update graph or workflow state; rejected changes remain auditable.

## 7. Current Product Surfaces

The current repository implements the following primary frontend surfaces:

- `LandingPage`: entry point for instructors.
- `UploadWizard`: course/exam selection, file upload, parameter setup, and compute trigger.
- `InstructorDashboard`: readiness matrix, alerts, graph, interventions, parameter visualization.
- `RootCauseTrace`: detailed drill-down on one concept.
- `StudentReport`: student selector, concept graph, readiness breakdown, study plan, and contact details.
- `Chatbot`: persistent AI assistant surface for instructor questions and actions.

The current frontend is a **React + Vite + TypeScript** application, not Next.js. Future documentation must preserve that unless the implementation actually changes.

## 8. Backend Product Responsibilities

The backend must provide:

- authenticated instructor APIs,
- public or tokenized report access for students,
- data validation on uploads,
- graph validation and versioning,
- deterministic compute execution,
- cluster and intervention generation,
- AI suggestion orchestration,
- chat-session tooling,
- export generation,
- observability and health status,
- and durable persistence of all product-critical entities.

The current backend is **FastAPI + SQLAlchemy + Alembic**, with PostgreSQL-oriented models and optional async compute infrastructure.

## 9. Detailed Functional Requirements

### 9.1 Course and exam management

- Instructors must be able to create courses.
- Instructors must be able to list courses.
- Instructors must be able to create exams within a course.
- Instructors must be able to list exams for a course.
- Every downstream artifact must be scoped to an exam.

### 9.2 Scores upload

- The system must accept a scores CSV per exam.
- Each row must include a student identifier, question identifier, and numeric score.
- The system should support `MaxScore` when present and default to `1.0` when absent.
- Validation must reject malformed rows, out-of-range scores, missing identifiers, duplicate `(student, question)` records, and invalid score normalization inputs.
- The upload response must include row count, structured errors, and student-detection summary when available.

### 9.3 Mapping upload

- The system must accept a question-to-concept mapping CSV per exam.
- A question may map to multiple concepts.
- Mapping rows may include weights.
- Validation must ensure every scored question is represented in the mapping.
- Validation must reject invalid concept references and malformed weights.

### 9.4 Graph upload and editing

- The system must accept graph uploads in structured form.
- The graph must be validated as a DAG.
- Graph version history must be preserved.
- The system must support patch-style graph editing: add nodes, remove nodes, add edges, remove edges.
- Invalid graph edits must return the cycle path or validation issue.
- The system must support graph expansion suggestions from AI.

### 9.5 Parameter management

- Parameters are exam-scoped.
- Current supported parameters are:
  - `alpha`: weight on direct readiness
  - `beta`: weight on prerequisite penalty
  - `gamma`: weight on downstream boost
  - `threshold`: prerequisite weakness cutoff
  - `k`: cluster count
- Instructors must be able to fetch and update parameters.
- Parameter updates do not inherently imply persistence of new results; compute must be rerun.

### 9.6 Compute execution

- The system must calculate direct readiness, prerequisite penalty, downstream boost, final readiness, confidence, class aggregates, clusters, and interventions.
- Compute outputs must be deterministic for the same inputs and parameter set.
- Results must be stored in persistent tables tied to the exam and optionally a run identifier.
- The API must expose compute initiation and compute run history.
- The platform should support both synchronous and async compute modes.

### 9.7 Instructor analytics

- Dashboard must expose heatmap-style readiness distribution by concept.
- Dashboard must expose aggregate metrics per concept.
- Dashboard must surface alerts for foundational weak concepts.
- Root-cause trace must show direct readiness, upstream contributors, downstream evidence, waterfall-style composition, and affected-student count.
- Cluster views must summarize misconception groups.
- Intervention views must rank recommended instructional actions.

### 9.8 Student reports

- The system must generate a per-student concept readiness report for an exam.
- The student report must include:
  - student identifier,
  - exam identifier,
  - concept graph,
  - readiness by concept,
  - top weak concepts,
  - study plan ordered by prerequisites.
- Student reports must exclude peer ranking, percentile comparisons, and unnecessary comparative performance data.
- Student reports should emphasize actionability over judgment.

### 9.9 AI suggestions

- The system must support AI concept tag suggestions from question text.
- The system must support AI prerequisite edge suggestions from a concept list.
- The system must support AI intervention drafts from cluster and weak-concept data.
- The system must support AI graph expansion around a selected concept.
- Every AI suggestion must carry request metadata, model name, prompt version, and review status.
- AI suggestions must be reviewable, rejectable, and auditable before application.

### 9.10 AI chat assistant

- The instructor chat assistant must be able to answer questions using real product data, not fabricated summaries.
- The assistant must support tool-backed actions such as listing courses, listing exams, retrieving students, reading readiness data, checking parameters, updating parameters, triggering compute, generating exports, and surfacing intervention insights.
- If the assistant lacks exam context, it must request or infer it from session state rather than guessing.

### 9.11 Exports

- The system must support export generation per exam.
- Exports should be associated with compute runs where appropriate.
- Export status must be queryable.
- Download endpoints must expose completed export bundles.
- Export artifacts must be checksum-able and auditable.

## 10. Frontend Specifications

### 10.1 Frontend architecture

Current stack:

- React
- TypeScript
- Vite
- Tailwind CSS
- custom service layer for typed API access
- motion library for transitions

Required frontend principles:

- typed API contracts must mirror backend schemas,
- views must fail gracefully when data is missing,
- loading and empty states must be explicit,
- parameter changes must be understandable to instructors,
- student-facing UI must remain understandable to non-technical users,
- and frontend mock behavior must not be confused with production truth.

### 10.2 View requirements

#### Landing page

- Must orient instructors to the product.
- Must provide the entry point into upload/setup.

#### Upload wizard

- Must support course and exam creation or selection.
- Must support score upload.
- Must support mapping upload.
- Must expose parameter configuration.
- Must trigger compute.
- Must clearly surface upload validation errors.

#### Instructor dashboard

- Must support course and exam switching.
- Must render readiness matrix and aggregate summaries.
- Must expose intervention and alert views.
- Must provide access into root-cause trace.
- Must visually explain alpha/beta/gamma/threshold values.

#### Root-cause trace

- Must explain why a concept is weak or strong.
- Must visualize direct evidence, prerequisite penalty, downstream boost, and final result.

#### Student report

- Must support selecting a student for a chosen exam in the internal instructor-facing experience.
- Must support tokenized report retrieval for public report access.
- Must render concept graph, weak concepts, study plan, and contact information.

#### Chat assistant

- Must be visible to instructors across relevant workflows.
- Must preserve conversation session context when possible.

### 10.3 Frontend service-layer requirements

- Every backend endpoint should have a typed service wrapper.
- Shared types should be defined in a single `types.ts` contract layer.
- API errors should map to user-readable messages.
- Authentication failure should produce actionable UI guidance.

### 10.4 Known current frontend issue

As noted in `notes.txt`, the students page currently has a known issue where the student dropdown may not show available students even when expected. Future feature work must preserve a section for active product issues like this so the PRD remains operational, not idealized.

## 11. Backend Specifications

### 11.1 Backend architecture

Current stack:

- FastAPI for HTTP API layer
- SQLAlchemy ORM
- Alembic migrations
- PostgreSQL-oriented schema design using UUID and JSONB
- service-layer business logic
- router-layer endpoint definitions
- optional async worker and queue support

Architectural rules:

- routers own HTTP concerns,
- services own business logic,
- schemas own request and response contracts,
- models own persistence definitions,
- compute logic must remain deterministic and testable,
- and AI wrappers must remain isolated from core compute correctness.

### 11.2 Current API domains

The backend currently exposes these route groups:

- `/api/v1/courses`
- `/api/v1/courses/{course_id}/exams`
- `/api/v1/exams/{exam_id}`
- `/api/v1/exams/{exam_id}/scores`
- `/api/v1/exams/{exam_id}/mapping`
- `/api/v1/exams/{exam_id}/graph`
- `/api/v1/exams/{exam_id}/graph/expand`
- `/api/v1/exams/{exam_id}/compute`
- `/api/v1/exams/{exam_id}/compute/runs`
- `/api/v1/exams/{exam_id}/dashboard`
- `/api/v1/exams/{exam_id}/clusters`
- `/api/v1/exams/{exam_id}/parameters`
- `/api/v1/exams/{exam_id}/interventions`
- `/api/v1/exams/{exam_id}/reports/tokens`
- `/api/v1/exams/{exam_id}/students`
- `/api/v1/exams/{exam_id}/students/{student_id}/report`
- `/api/v1/reports/{token}`
- `/api/v1/exams/{exam_id}/ai/suggest-tags`
- `/api/v1/exams/{exam_id}/ai/suggest-edges`
- `/api/v1/exams/{exam_id}/ai/draft-interventions`
- `/api/v1/exams/{exam_id}/ai/suggestions`
- `/api/v1/exams/{exam_id}/export`
- `/chat/*`
- `/health`

Future features should extend existing domains before adding parallel, inconsistent API hierarchies.

### 11.3 Persistence model

The current schema includes, at minimum, these entities:

- `Course`
- `Exam`
- `ConceptGraph`
- `Question`
- `QuestionConceptMap`
- `Score`
- `ReadinessResult`
- `ClassAggregate`
- `Cluster`
- `ClusterAssignment`
- `StudentToken`
- `Parameter`
- `ComputeRun`
- `AISuggestion`
- `InterventionResult`
- `ExportRun`
- chat-session related entities

Persistence rules:

- most entities are exam-scoped,
- external student identifiers are stored instead of full student profiles,
- graph, trace, centroid, and export metadata may be stored as JSONB,
- and unique constraints must prevent duplicate score and readiness records.

### 11.4 Configuration requirements

Current backend configuration includes:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_TIMEOUT_SECONDS`
- `OPENAI_MAX_RETRIES`
- `INSTRUCTOR_USERNAME`
- `INSTRUCTOR_PASSWORD`
- `STUDENT_TOKEN_EXPIRY_DAYS`
- `EXPORT_DIR`
- `APP_ENV`
- `CORS_ALLOWED_ORIGINS`
- async compute settings
- optional OCI object storage settings

All new backend features must declare:

- required env vars,
- fallback defaults,
- security implications,
- and local-development behavior.

## 12. AI Specifications

### 12.1 AI role in the system

AI is an assistive layer, not the source of truth for readiness computation. The deterministic analytics engine owns numeric correctness. The AI layer helps with:

- interpreting content,
- suggesting structure,
- drafting narratives,
- and navigating data through a chat experience.

### 12.2 AI capabilities currently in scope

- concept tag suggestions from question text,
- prerequisite edge suggestions from concept lists,
- graph expansion around a concept,
- intervention draft generation,
- chat-based instructor assistant with tool calling.

### 12.3 AI design requirements

- AI outputs should be structured JSON whenever feasible.
- Prompts must be versioned.
- Returned metadata must include model, request id, latency, and token usage when available.
- AI failures must degrade gracefully and never corrupt core data.
- All applied suggestions must be reviewable after the fact.
- AI must never silently bypass graph validity constraints or compute validation rules.

### 12.4 AI governance requirements

- Human review is required for suggestion application.
- Suggestion records must preserve acceptance, rejection, application, reviewer identity when available, and optional review notes.
- AI-generated graph edits must still pass DAG validation.
- Chat actions that mutate state must map to explicit tools and real side effects, not free-form text claims.

### 12.5 AI prompt and output conventions

Every new AI feature spec must define:

- system prompt responsibility,
- user prompt inputs,
- exact output schema,
- failure modes,
- validation logic,
- reviewer workflow,
- audit fields,
- and whether outputs are advisory or automatically executable.

## 13. Readiness Computation Specifications

### 13.1 Inputs

The readiness engine depends on:

- normalized scores,
- question max scores,
- question-to-concept mappings with weights,
- concept graph adjacency,
- parameter values,
- and stable ordering of students and concepts.

### 13.2 Algorithm stages

#### Stage 1: Direct readiness

For each student and concept, compute weighted normalized performance across mapped questions.

#### Stage 2: Prerequisite penalty

For each concept, accumulate penalty from prerequisite concepts whose direct readiness falls below the threshold.

#### Stage 3: Downstream boost

Use evidence from downstream concept performance to provide bounded positive support for prerequisite understanding.

#### Stage 4: Final readiness

Combine direct readiness, prerequisite penalty, and downstream boost using `alpha`, `beta`, and `gamma`, then clamp to `[0, 1]`.

### 13.3 Confidence estimation

Confidence is derived from:

- count of tagged questions,
- total point coverage,
- and variance across related concepts.

The final confidence label is conservative and should prevent overinterpretation of weak evidence.

### 13.4 Determinism requirements

- same inputs must produce same outputs,
- NaN and infinite values must be sanitized before persistence,
- sorted traversal should be used where order affects output,
- and clustering randomness must be controlled by stable seeds or equivalent deterministic configuration.

## 14. Dashboard and Analytics Specifications

### 14.1 Heatmap

The dashboard heatmap should present readiness distribution buckets by concept. It is the primary class-level entry point for instructors.

### 14.2 Alerts

Alerts should identify weak foundational concepts with meaningful downstream impact. Alert priority should reflect both number of affected students and downstream dependency reach.

### 14.3 Root-cause trace

Trace views should answer:

- what is the direct evidence for this concept,
- which prerequisites are dragging it down,
- which downstream outcomes support it,
- how many students are affected,
- and what the final readiness composition looks like.

### 14.4 Clusters

Cluster analysis groups students with similar readiness profiles and should be used for instructional planning, not student labeling.

### 14.5 Interventions

Interventions should be ranked by estimated impact using number of affected students, downstream breadth, and current weakness severity.

## 15. Student Experience Specifications

### 15.1 Tone and framing

Student-facing outputs must be supportive, specific, and non-comparative.

### 15.2 Required content

- visual concept map,
- readiness per concept,
- top weak concepts,
- confidence cues,
- sequenced study plan,
- concise explanations,
- contact path to instructional support.

### 15.3 Prohibited content

- class rank,
- percentiles,
- comparisons against peers,
- predictive risk labels framed as identity judgments,
- demographic inference.

## 16. Workflow Specifications

### 16.1 Product workflow states

An exam typically progresses through these internal states:

1. Created
2. Scores uploaded
3. Mapping uploaded
4. Graph uploaded or generated
5. Parameters configured
6. Compute run initiated
7. Results available
8. Reports and exports available
9. AI suggestions reviewed and optionally applied

Future features may formalize these states in persistence, but the workflow model should remain consistent.

### 16.2 Error workflow

- Upload validation errors must be row-aware when possible.
- Graph errors must explain invalid edges or cycle paths.
- Compute failures must persist error details in run history.
- AI failures must surface as recoverable operational issues, not silent missing output.
- Auth failures must produce a clear next step for the user.

### 16.3 Review workflow for AI suggestions

1. Generate suggestion.
2. Store suggestion output and metadata.
3. Present suggestion to instructor.
4. Accept or reject.
5. Apply only accepted suggestions.
6. Revalidate system invariants after application.
7. Log review and application result.

### 16.4 Export workflow

1. Instructor requests export.
2. System creates export run.
3. Export artifacts are generated from current or chosen compute outputs.
4. Status becomes downloadable when complete.
5. Manifest and checksum are recorded.

### 16.5 Compute workflow

1. Validate required exam inputs exist.
2. Load scores, mapping, graph, and parameters.
3. Compute readiness and analytics.
4. Persist results transactionally.
5. Mark compute run completed or failed.
6. Expose outputs through dashboard and reports.

## 17. Non-Functional Requirements

### 17.1 Performance

Target expectations:

- compute should complete fast enough for iterative instructor use on normal class sizes,
- dashboard load should feel near-interactive after results exist,
- graph edits should validate quickly,
- student report access should be low-latency.

### 17.2 Reliability

- health endpoint must reflect database and AI-key status,
- compute history must preserve failures,
- exports and AI runs must be auditable,
- and the app must degrade gracefully when AI is unavailable.

### 17.3 Security

- instructor operations require authentication,
- student reports must use controlled access,
- secrets must stay in environment configuration or secret stores,
- and CORS must be configurable per deployment environment.

### 17.4 Privacy

- store minimal student data,
- prefer external student identifiers over profile data,
- avoid demographic data entirely unless a future privacy-reviewed feature explicitly requires it,
- and ensure exports do not leak unauthorized student information.

### 17.5 Observability

- structured logging is required,
- middleware should preserve correlation-friendly request observability,
- compute, AI, and export operations should record status and timing,
- and health reporting must remain machine-readable.

## 18. Testing Requirements

Every meaningful feature addition should include:

- unit tests for domain logic,
- integration tests for workflow behavior,
- schema-contract coverage where API contracts change,
- and regression coverage for known invariants.

Critical test domains:

- CSV validation,
- graph cycle detection,
- topological ordering,
- readiness computation,
- confidence computation,
- cluster generation,
- student report assembly,
- export generation,
- AI suggestion review and apply flows.

## 19. Deployment and Environment Specifications

The repository already includes OCI-oriented deployment docs and infrastructure. The product should remain deployable in:

- local developer mode,
- containerized backend/frontend mode,
- OCI-managed deployment flows with object storage, queue, worker, and managed database.

Any feature that changes storage, queues, async jobs, secrets, or runtime dependencies must document:

- local setup,
- cloud setup,
- migration requirements,
- rollback considerations,
- and cost implications if the feature affects managed services.

## 20. Roadmap Themes

Current and near-term themes implied by the codebase:

- harden student report reliability and student listing workflows,
- improve graph authoring and AI-assisted graph evolution,
- deepen export integrations,
- mature async compute and worker deployment,
- improve AI suggestion review UX,
- and make chat a reliable operational assistant for instructors.

## 21. Rules for Future PRD Extensions

When adding a new feature, the next PRD or PRD update must answer all of the following:

1. What user problem does the feature solve?
2. Which user type is affected?
3. Is the feature instructor-facing, student-facing, backend-only, AI-only, or cross-cutting?
4. What existing workflow state does it attach to?
5. What new data entities or fields are required?
6. What API endpoints or schema changes are required?
7. What frontend surfaces change?
8. What AI prompts, outputs, or review rules are required?
9. What invariants must remain true?
10. What tests prove the feature works and does not regress current behavior?

## 22. Required Template for New Feature Specs

Any future LLM generating a follow-on PRD should use this structure:

### Feature name

One-sentence summary.

### User problem

What is broken, slow, missing, or unclear today?

### Product behavior

What should the user be able to do after this feature ships?

### Backend changes

- models
- migrations
- services
- routes
- schemas
- validation

### Frontend changes

- pages
- components
- service layer
- loading/error states

### AI changes

- prompt
- output schema
- review flow
- safety constraints

### Workflow impact

What upstream and downstream flows change?

### Risks

What can break or become misleading?

### Tests

What unit, integration, and regression coverage is required?

## 23. Source-of-Truth Guidance for Future LLMs

If another LLM is asked to create a new PRD for this project, it should follow this order of precedence:

1. `prd.md`
2. current code in `backend/app/*` and `frontend/app/*`
3. backend/frontend shared types and schemas
4. existing technical PRDs in `techPRD*.md`
5. README and deployment docs
6. ad hoc notes such as `notes.txt`, `todo.txt`, and `ideas.md`

If there is a conflict between older docs and current code, prefer current code and update the PRD accordingly.

## 24. Acceptance Criteria for This Document

This document is successful if:

- a new engineer can understand the product without opening every file,
- a future LLM can draft a feature PRD without inventing basic architecture,
- current implementation details are distinguishable from aspirational roadmap items,
- and core system rules around readiness, graph validity, AI review, and student-safe outputs remain explicit.
