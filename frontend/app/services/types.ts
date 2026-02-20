// Shared TypeScript types mirroring backend Pydantic schemas

// ---- Course ----
export interface CourseResponse {
  id: string;
  name: string;
  created_at: string;
}
export interface CourseCreate {
  name: string;
}

// ---- Exam ----
export interface ExamResponse {
  id: string;
  course_id: string;
  name: string;
  created_at: string;
}
export interface ExamCreate {
  name: string;
}

// ---- Upload ----
export interface ValidationError {
  row?: number;
  field?: string;
  message: string;
}
export interface ScoresUploadResponse {
  status: string;
  row_count: number;
  errors: ValidationError[];
}
export interface MappingUploadResponse {
  status: string;
  concept_count: number;
  errors: ValidationError[];
}

// ---- Graph ----
export interface GraphNode {
  id: string;
  label: string;
}
export interface GraphEdge {
  source: string;
  target: string;
  weight?: number;
}
export interface GraphUploadRequest {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
export interface GraphUploadResponse {
  status: string;
  node_count: number;
  edge_count: number;
  is_dag: boolean;
  errors: ValidationError[];
}
export interface GraphPatchRequest {
  add_nodes?: GraphNode[];
  remove_nodes?: string[];
  add_edges?: GraphEdge[];
  remove_edges?: GraphEdge[];
}
export interface GraphPatchResponse {
  status: string;
  is_dag: boolean;
  cycle_path?: string[];
}

// ---- Compute ----
export interface ComputeRequest {
  alpha?: number;
  beta?: number;
  gamma?: number;
  threshold?: number;
  k?: number;
}
export interface ComputeResponse {
  status: string;
  run_id?: string;
  students_processed: number;
  concepts_processed: number;
  time_ms: number;
}
export interface ComputeRunResponse {
  id: string;
  run_id: string;
  exam_id: string;
  status: string;
  students_processed?: number;
  concepts_processed?: number;
  parameters?: Record<string, unknown>;
  graph_version?: number;
  duration_ms?: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

// ---- Dashboard ----
export interface HeatmapCell {
  concept_id: string;
  concept_label: string;
  bucket: string;
  count: number;
  percentage: number;
}
export interface AlertItem {
  concept_id: string;
  concept_label: string;
  class_average_readiness: number;
  students_below_threshold: number;
  downstream_concepts: string[];
  impact: number;
  recommended_action: string;
}
export interface AggregateItem {
  concept_id: string;
  concept_label: string;
  mean_readiness: number;
  median_readiness: number;
  std_readiness: number;
  below_threshold_count: number;
}
export interface DashboardResponse {
  heatmap: HeatmapCell[];
  alerts: AlertItem[];
  aggregates: AggregateItem[];
}

// ---- Trace ----
export interface UpstreamContribution {
  concept_id: string;
  concept_label: string;
  readiness: number;
  contribution_weight: number;
  penalty_contribution: number;
}
export interface DownstreamContribution {
  concept_id: string;
  concept_label: string;
  readiness: number;
  boost_contribution: number;
}
export interface WaterfallStep {
  label: string;
  value: number;
  cumulative: number;
}
export interface TraceResponse {
  concept_id: string;
  concept_label: string;
  direct_readiness: number | null;
  upstream: UpstreamContribution[];
  downstream: DownstreamContribution[];
  waterfall: WaterfallStep[];
  students_affected: number;
}

// ---- Clusters ----
export interface ClusterItem {
  id: string;
  cluster_label: string;
  student_count: number;
  centroid: Record<string, number>;
  top_weak_concepts: string[];
  suggested_interventions: string[];
}
export interface ClusterAssignmentSummary {
  student_id: string;
  cluster_label: string;
}
export interface ClustersResponse {
  clusters: ClusterItem[];
  assignments_summary: ClusterAssignmentSummary[];
}

// ---- Student Report ----
export interface StudentConceptReadiness {
  concept_id: string;
  concept_label: string;
  direct_readiness: number | null;
  final_readiness: number;
  confidence: string;
}
export interface WeakConceptItem {
  concept_id: string;
  concept_label: string;
  readiness: number;
  confidence: string;
}
export interface StudyPlanItem {
  concept_id: string;
  concept_label: string;
  readiness: number;
  confidence: string;
  reason: string;
  explanation: string;
}
export interface StudentReportResponse {
  student_id: string;
  exam_id: string;
  concept_graph: Record<string, unknown>;
  readiness: StudentConceptReadiness[];
  top_weak_concepts: WeakConceptItem[];
  study_plan: StudyPlanItem[];
}

// ---- Report Tokens (new endpoint) ----
export interface StudentTokenItem {
  student_id: string;
  token: string;
  created_at: string;
  expires_at: string;
}
export interface StudentTokenListResponse {
  tokens: StudentTokenItem[];
}

// ---- Parameters ----
export interface ParametersSchema {
  alpha: number;
  beta: number;
  gamma: number;
  threshold: number;
  k: number;
}
export interface ParametersResponse {
  status: string;
  alpha: number;
  beta: number;
  gamma: number;
  threshold: number;
  k: number;
}

// ---- Interventions ----
export interface InterventionItem {
  concept_id: string;
  students_affected: number;
  downstream_concepts: number;
  current_readiness: number;
  impact: number;
  rationale: string;
  suggested_format: string;
}
export interface InterventionsResponse {
  interventions: InterventionItem[];
}

// ---- AI Suggestions ----
export interface ConceptTagRequest {
  question_text: string;
  concept_catalog?: string[];
}
export interface ConceptTagResponse {
  request_id: string;
  suggestion_id: string;
  suggestions: Array<{ concept_id: string; confidence: number; rationale: string }>;
  model: string;
  prompt_version: string;
}
export interface PrereqEdgeRequest {
  concepts: string[];
  context?: string;
}
export interface PrereqEdgeResponse {
  request_id: string;
  suggestion_id: string;
  suggestions: Array<{ source: string; target: string; weight: number; rationale: string }>;
  model: string;
  prompt_version: string;
}
export interface InterventionDraftRequest {
  cluster_centroid: Record<string, number>;
  weak_concepts: string[];
  student_count?: number;
}
export interface InterventionDraftResponse {
  request_id: string;
  suggestion_id: string;
  drafts: Array<{ concept_id: string; intervention_type: string; description: string; rationale: string }>;
  model: string;
  prompt_version: string;
}
export interface SuggestionListItem {
  id: string;
  suggestion_type: string;
  status: string;
  output_payload: Record<string, unknown>;
  validation_errors?: Array<Record<string, unknown>>;
  model?: string;
  prompt_version?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_note?: string;
  created_at: string;
}
export interface SuggestionListResponse {
  suggestions: SuggestionListItem[];
  total: number;
  pending: number;
  accepted: number;
  rejected: number;
  applied: number;
}
export interface SuggestionReviewAction {
  action: 'accept' | 'reject';
  note?: string;
}
export interface BulkReviewRequest {
  suggestion_ids: string[];
  action: 'accept' | 'reject';
  note?: string;
}
export interface ApplySuggestionsRequest {
  suggestion_ids: string[];
}
export interface ApplySuggestionsResponse {
  status: string;
  applied_count: number;
  errors: string[];
}

// ---- Export ----
export interface ExportRequest {
  compute_run_id?: string;
}
export interface ExportStatusResponse {
  id: string;
  exam_id: string;
  status: string;
  file_checksum?: string;
  manifest?: Record<string, unknown>;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}
export interface ExportListResponse {
  exports: ExportStatusResponse[];
}

// ---- Chat ----
export interface ChatSessionCreate {
  exam_id?: string;
  title?: string;
}
export interface ChatSessionResponse {
  id: string;
  exam_id?: string;
  title?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}
export interface ChatMessageResponse {
  id: string;
  role: string;
  content?: string;
  tool_calls?: Array<Record<string, unknown>>;
  tool_name?: string;
  created_at: string;
}
export interface ChatSendRequest {
  message: string;
  exam_id?: string;
}
export interface ChatSendResponse {
  session_id: string;
  assistant_message: string;
  tool_calls_made: string[];
}

// ---- Health ----
export interface HealthResponse {
  status: string;
  service: string;
  database: string;
  openai: string;
}
