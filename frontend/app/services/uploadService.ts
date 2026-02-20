import { api } from './apiClient';
import type {
  GraphUploadRequest,
  GraphUploadResponse,
  MappingUploadResponse,
  ScoresUploadResponse,
} from './types';

const BASE = '/api/v1/exams';

export const uploadService = {
  uploadScores(examId: string, file: File): Promise<ScoresUploadResponse> {
    return api.upload<ScoresUploadResponse>(`${BASE}/${examId}/scores`, file);
  },

  uploadMapping(examId: string, file: File): Promise<MappingUploadResponse> {
    return api.upload<MappingUploadResponse>(`${BASE}/${examId}/mapping`, file);
  },

  uploadGraph(examId: string, data: GraphUploadRequest): Promise<GraphUploadResponse> {
    return api.post<GraphUploadResponse>(`${BASE}/${examId}/graph`, data);
  },
};
