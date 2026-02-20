import { config } from './config';

export class ApiError extends Error {
  status: number;
  detail: string;
  validationErrors: Array<{ row?: number; field?: string; message: string }>;

  constructor(
    status: number,
    detail: string,
    validationErrors: Array<{ row?: number; field?: string; message: string }> = [],
  ) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.validationErrors = validationErrors;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    let validationErrors: Array<{ row?: number; field?: string; message: string }> = [];
    try {
      const body = await response.json();
      if (body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      if (body.errors) validationErrors = body.errors;
      if (body.message) detail = body.message;
    } catch {
      // response body was not JSON
    }
    throw new ApiError(response.status, detail, validationErrors);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function buildUrl(path: string, params?: Record<string, string | undefined>): string {
  const url = new URL(path, config.apiBaseUrl);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') url.searchParams.set(key, value);
    });
  }
  return url.toString();
}

function headers(auth: boolean): HeadersInit {
  void auth;
  const username = config.instructorUsername.trim();
  if (!username) return {};
  const password = config.instructorPassword ?? '';
  return {
    Authorization: `Basic ${btoa(`${username}:${password}`)}`,
  };
}

export const api = {
  async get<T>(path: string, opts?: { auth?: boolean; params?: Record<string, string | undefined> }): Promise<T> {
    const { auth = true, params } = opts ?? {};
    const res = await fetch(buildUrl(path, params), {
      method: 'GET',
      headers: headers(auth),
    });
    return handleResponse<T>(res);
  },

  async post<T>(path: string, body?: unknown, opts?: { auth?: boolean }): Promise<T> {
    const { auth = true } = opts ?? {};
    const h: Record<string, string> = { 'Content-Type': 'application/json', ...headers(auth) as Record<string, string> };
    const res = await fetch(buildUrl(path), {
      method: 'POST',
      headers: h,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },

  async put<T>(path: string, body?: unknown, opts?: { auth?: boolean }): Promise<T> {
    const { auth = true } = opts ?? {};
    const h: Record<string, string> = { 'Content-Type': 'application/json', ...headers(auth) as Record<string, string> };
    const res = await fetch(buildUrl(path), {
      method: 'PUT',
      headers: h,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },

  async patch<T>(path: string, body?: unknown, opts?: { auth?: boolean }): Promise<T> {
    const { auth = true } = opts ?? {};
    const h: Record<string, string> = { 'Content-Type': 'application/json', ...headers(auth) as Record<string, string> };
    const res = await fetch(buildUrl(path), {
      method: 'PATCH',
      headers: h,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },

  async delete<T>(path: string, opts?: { auth?: boolean }): Promise<T> {
    const { auth = true } = opts ?? {};
    const res = await fetch(buildUrl(path), {
      method: 'DELETE',
      headers: headers(auth),
    });
    return handleResponse<T>(res);
  },

  async upload<T>(path: string, file: File, opts?: { auth?: boolean; fieldName?: string }): Promise<T> {
    const { auth = true, fieldName = 'file' } = opts ?? {};
    const form = new FormData();
    form.append(fieldName, file);
    const res = await fetch(buildUrl(path), {
      method: 'POST',
      headers: headers(auth),
      body: form,
    });
    return handleResponse<T>(res);
  },

  async downloadBlob(path: string, opts?: { auth?: boolean }): Promise<Blob> {
    const { auth = true } = opts ?? {};
    const res = await fetch(buildUrl(path), {
      method: 'GET',
      headers: headers(auth),
    });
    if (!res.ok) {
      let detail = `Download failed (${res.status})`;
      try {
        const body = await res.json();
        if (body.detail) detail = body.detail;
      } catch { /* ignore */ }
      throw new ApiError(res.status, detail);
    }
    return res.blob();
  },
};
