import { api } from './apiClient';
import type { CourseCreate, CourseResponse } from './types';

const BASE = '/api/v1/courses';

export const coursesService = {
  list(): Promise<CourseResponse[]> {
    return api.get<CourseResponse[]>(BASE, { auth: false });
  },

  get(courseId: string): Promise<CourseResponse> {
    return api.get<CourseResponse>(`${BASE}/${courseId}`, { auth: false });
  },

  create(data: CourseCreate): Promise<CourseResponse> {
    return api.post<CourseResponse>(BASE, data, { auth: false });
  },
};
