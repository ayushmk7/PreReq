import { api } from './apiClient';
import type { DashboardResponse, TraceResponse } from './types';

const BASE = '/api/v1/exams';

export const dashboardService = {
  getDashboard(examId: string, conceptId?: string): Promise<DashboardResponse> {
    return api.get<DashboardResponse>(`${BASE}/${examId}/dashboard`, {
      params: { concept_id: conceptId },
    });
  },

  getTrace(examId: string, conceptId: string): Promise<TraceResponse> {
    return api.get<TraceResponse>(`${BASE}/${examId}/dashboard/trace/${conceptId}`);
  },
};
