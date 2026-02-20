import { api } from './apiClient';
import type { ClustersResponse } from './types';

const BASE = '/api/v1/exams';

export const clustersService = {
  get(examId: string): Promise<ClustersResponse> {
    return api.get<ClustersResponse>(`${BASE}/${examId}/clusters`);
  },
};
