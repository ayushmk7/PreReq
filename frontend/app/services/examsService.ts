import { api } from './apiClient';
import type { ExamCreate, ExamResponse } from './types';

const BASE = '/api/v1/courses';

export const examsService = {
  list(courseId: string): Promise<ExamResponse[]> {
    return api.get<ExamResponse[]>(`${BASE}/${courseId}/exams`);
  },

  get(examId: string): Promise<ExamResponse> {
    return api.get<ExamResponse>(`/api/v1/exams/${examId}`);
  },

  create(courseId: string, data: ExamCreate): Promise<ExamResponse> {
    return api.post<ExamResponse>(`${BASE}/${courseId}/exams`, data);
  },
};
