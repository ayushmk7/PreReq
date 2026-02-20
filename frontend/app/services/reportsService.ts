import { ApiError, api } from './apiClient';
import type { StudentReportResponse, StudentTokenListResponse } from './types';

export interface StudentListItem {
  student_id: string;
}

export interface StudentListResponse {
  students: StudentListItem[];
}

export const reportsService = {
  getByToken(token: string): Promise<StudentReportResponse> {
    return api.get<StudentReportResponse>(`/api/v1/reports/${token}`, { auth: false });
  },

  listTokens(examId: string): Promise<StudentTokenListResponse> {
    return api.get<StudentTokenListResponse>(`/api/v1/exams/${examId}/reports/tokens`);
  },

  /** List all students who have computed results for an exam (instructor, no tokens needed) */
  async listStudents(examId: string): Promise<StudentListResponse> {
    try {
      return await api.get<StudentListResponse>(`/api/v1/exams/${examId}/students`);
    } catch (err) {
      // Backward-compatible fallback for older backend versions that only expose token listing.
      if (err instanceof ApiError && err.status === 404) {
        const tokenResponse = await api.get<StudentTokenListResponse>(`/api/v1/exams/${examId}/reports/tokens`);
        return {
          students: tokenResponse.tokens.map((t) => ({ student_id: t.student_id })),
        };
      }
      throw err;
    }
  },

  /** Fetch a student report directly by student ID (instructor, no token needed) */
  async getByStudentId(examId: string, studentId: string): Promise<StudentReportResponse> {
    try {
      return await api.get<StudentReportResponse>(`/api/v1/exams/${examId}/students/${studentId}/report`);
    } catch (err) {
      // Backward-compatible fallback for older backend versions with token-only report endpoint.
      if (err instanceof ApiError && err.status === 404) {
        const tokenResponse = await api.get<StudentTokenListResponse>(`/api/v1/exams/${examId}/reports/tokens`);
        const tokenItem = tokenResponse.tokens.find((t) => t.student_id === studentId);
        if (!tokenItem) {
          throw new ApiError(404, `No report token found for student '${studentId}'`);
        }
        return api.get<StudentReportResponse>(`/api/v1/reports/${tokenItem.token}`, { auth: false });
      }
      throw err;
    }
  },
};
