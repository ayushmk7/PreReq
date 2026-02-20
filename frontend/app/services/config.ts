const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '') ?? 'http://localhost:8000';

const INSTRUCTOR_USERNAME = import.meta.env.VITE_INSTRUCTOR_USERNAME ?? '';
const INSTRUCTOR_PASSWORD = import.meta.env.VITE_INSTRUCTOR_PASSWORD ?? '';
const INSTRUCTOR_NAME = import.meta.env.VITE_INSTRUCTOR_NAME ?? '';
const INSTRUCTOR_EMAIL = import.meta.env.VITE_INSTRUCTOR_EMAIL ?? '';
const INSTRUCTOR_PHONE = import.meta.env.VITE_INSTRUCTOR_PHONE ?? '';
const INSTRUCTOR_OFFICE = import.meta.env.VITE_INSTRUCTOR_OFFICE ?? '';
const INSTRUCTOR_HOURS = import.meta.env.VITE_INSTRUCTOR_HOURS ?? '';
const TA_NAME = import.meta.env.VITE_TA_NAME ?? '';
const TA_EMAIL = import.meta.env.VITE_TA_EMAIL ?? '';
const TA_PHONE = import.meta.env.VITE_TA_PHONE ?? '';
const TA_OFFICE = import.meta.env.VITE_TA_OFFICE ?? '';
const TA_HOURS = import.meta.env.VITE_TA_HOURS ?? '';

export const config = {
  apiBaseUrl: API_BASE_URL,
  instructorUsername: INSTRUCTOR_USERNAME,
  instructorPassword: INSTRUCTOR_PASSWORD,
  contacts: {
    instructor: {
      name: INSTRUCTOR_NAME,
      email: INSTRUCTOR_EMAIL,
      phone: INSTRUCTOR_PHONE,
      office: INSTRUCTOR_OFFICE,
      hours: INSTRUCTOR_HOURS,
    },
    ta: {
      name: TA_NAME,
      email: TA_EMAIL,
      phone: TA_PHONE,
      office: TA_OFFICE,
      hours: TA_HOURS,
    },
  },
} as const;
