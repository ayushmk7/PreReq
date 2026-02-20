import { api } from './apiClient';
import type {
  ApplySuggestionsRequest,
  ApplySuggestionsResponse,
  BulkReviewRequest,
  ConceptTagRequest,
  ConceptTagResponse,
  InterventionDraftRequest,
  InterventionDraftResponse,
  PrereqEdgeRequest,
  PrereqEdgeResponse,
  SuggestionListResponse,
  SuggestionReviewAction,
} from './types';

const BASE = '/api/v1/exams';

export const aiSuggestionsService = {
  suggestTags(examId: string, data: ConceptTagRequest): Promise<ConceptTagResponse> {
    return api.post<ConceptTagResponse>(`${BASE}/${examId}/ai/suggest-tags`, data);
  },

  suggestEdges(examId: string, data: PrereqEdgeRequest): Promise<PrereqEdgeResponse> {
    return api.post<PrereqEdgeResponse>(`${BASE}/${examId}/ai/suggest-edges`, data);
  },

  draftInterventions(examId: string, data: InterventionDraftRequest): Promise<InterventionDraftResponse> {
    return api.post<InterventionDraftResponse>(`${BASE}/${examId}/ai/draft-interventions`, data);
  },

  listSuggestions(
    examId: string,
    filters?: { suggestion_type?: string; status?: string },
  ): Promise<SuggestionListResponse> {
    return api.get<SuggestionListResponse>(`${BASE}/${examId}/ai/suggestions`, {
      params: filters,
    });
  },

  reviewSuggestion(
    examId: string,
    suggestionId: string,
    action: SuggestionReviewAction,
  ): Promise<{ status: string; suggestion_status: string }> {
    return api.post(`${BASE}/${examId}/ai/suggestions/${suggestionId}/review`, action);
  },

  bulkReview(
    examId: string,
    data: BulkReviewRequest,
  ): Promise<{ status: string; updated: number; total_requested: number }> {
    return api.post(`${BASE}/${examId}/ai/suggestions/bulk-review`, data);
  },

  apply(examId: string, data: ApplySuggestionsRequest): Promise<ApplySuggestionsResponse> {
    return api.post<ApplySuggestionsResponse>(`${BASE}/${examId}/ai/suggestions/apply`, data);
  },
};
