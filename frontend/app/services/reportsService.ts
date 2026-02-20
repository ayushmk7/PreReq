import { api } from './apiClient';
import type { StudentReportResponse, StudentTokenListResponse } from './types';

export const reportsService = {
  getByToken(token: string): Promise<StudentReportResponse> {
    return api.get<StudentReportResponse>(`/api/v1/reports/${token}`, { auth: false });
  },

  listTokens(examId: string): Promise<StudentTokenListResponse> {
    return api.get<StudentTokenListResponse>(`/api/v1/exams/${examId}/reports/tokens`);
  },
};
