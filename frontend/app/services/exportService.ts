import { api } from './apiClient';
import type { ExportListResponse, ExportRequest, ExportStatusResponse } from './types';

const BASE = '/api/v1/exams';

export const exportService = {
  create(examId: string, data?: ExportRequest): Promise<ExportStatusResponse> {
    return api.post<ExportStatusResponse>(`${BASE}/${examId}/export`, data ?? {});
  },

  list(examId: string): Promise<ExportListResponse> {
    return api.get<ExportListResponse>(`${BASE}/${examId}/export`);
  },

  download(examId: string, exportId: string): Promise<Blob> {
    return api.downloadBlob(`${BASE}/${examId}/export/${exportId}/download`);
  },
};
