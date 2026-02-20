import { api } from './apiClient';
import type { ParametersResponse, ParametersSchema } from './types';

const BASE = '/api/v1/exams';

export const parametersService = {
  get(examId: string): Promise<ParametersResponse> {
    return api.get<ParametersResponse>(`${BASE}/${examId}/parameters`, { auth: false });
  },

  update(examId: string, data: ParametersSchema): Promise<ParametersResponse> {
    return api.put<ParametersResponse>(`${BASE}/${examId}/parameters`, data, { auth: false });
  },
};
