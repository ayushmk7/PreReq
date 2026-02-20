/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_INSTRUCTOR_USERNAME?: string;
  readonly VITE_INSTRUCTOR_PASSWORD?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
