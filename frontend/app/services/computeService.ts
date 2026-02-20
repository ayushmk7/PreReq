import { api } from './apiClient';
import type {
  ComputeRequest,
  ComputeResponse,
  ComputeRunResponse,
  InterventionsResponse,
} from './types';

const BASE = '/api/v1/exams';

export const computeService = {
  run(examId: string, params?: ComputeRequest): Promise<ComputeResponse> {
    return api.post<ComputeResponse>(`${BASE}/${examId}/compute`, params ?? {});
  },

  listRuns(examId: string): Promise<ComputeRunResponse[]> {
    return api.get<ComputeRunResponse[]>(`${BASE}/${examId}/compute/runs`);
  },

  getInterventions(examId: string): Promise<InterventionsResponse> {
    return api.get<InterventionsResponse>(`${BASE}/${examId}/interventions`);
  },
};
