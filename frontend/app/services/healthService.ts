import { api } from './apiClient';
import type { HealthResponse } from './types';

export const healthService = {
  check(): Promise<HealthResponse> {
    return api.get<HealthResponse>('/health', { auth: false });
  },
};
