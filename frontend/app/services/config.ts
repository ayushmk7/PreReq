const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '') ?? 'http://localhost:8000';

const INSTRUCTOR_USERNAME = import.meta.env.VITE_INSTRUCTOR_USERNAME ?? '';
const INSTRUCTOR_PASSWORD = import.meta.env.VITE_INSTRUCTOR_PASSWORD ?? '';

export const config = {
  apiBaseUrl: API_BASE_URL,
  instructorUsername: INSTRUCTOR_USERNAME,
  instructorPassword: INSTRUCTOR_PASSWORD,
} as const;
