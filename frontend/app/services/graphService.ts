import { api } from './apiClient';
import type { GraphPatchRequest, GraphPatchResponse } from './types';

const BASE = '/api/v1/exams';

export const graphService = {
  patch(examId: string, data: GraphPatchRequest): Promise<GraphPatchResponse> {
    return api.patch<GraphPatchResponse>(`${BASE}/${examId}/graph`, data);
  },
};
