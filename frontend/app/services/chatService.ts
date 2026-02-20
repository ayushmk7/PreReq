import { api } from './apiClient';
import type {
  ChatMessageResponse,
  ChatSendRequest,
  ChatSendResponse,
  ChatSessionCreate,
  ChatSessionResponse,
} from './types';

const BASE = '/chat';

export const chatService = {
  createSession(data?: ChatSessionCreate): Promise<ChatSessionResponse> {
    return api.post<ChatSessionResponse>(`${BASE}/sessions`, data ?? {}, { auth: false });
  },

  listSessions(examId?: string): Promise<ChatSessionResponse[]> {
    return api.get<ChatSessionResponse[]>(`${BASE}/sessions`, {
      auth: false,
      params: { exam_id: examId },
    });
  },

  getSession(sessionId: string): Promise<ChatSessionResponse> {
    return api.get<ChatSessionResponse>(`${BASE}/sessions/${sessionId}`, { auth: false });
  },

  getMessages(sessionId: string): Promise<ChatMessageResponse[]> {
    return api.get<ChatMessageResponse[]>(`${BASE}/sessions/${sessionId}/messages`, { auth: false });
  },

  sendMessage(sessionId: string, data: ChatSendRequest): Promise<ChatSendResponse> {
    return api.post<ChatSendResponse>(`${BASE}/sessions/${sessionId}/messages`, data, { auth: false });
  },

  quickMessage(data: ChatSendRequest): Promise<ChatSendResponse> {
    return api.post<ChatSendResponse>(`${BASE}/quick`, data, { auth: false });
  },

  deleteSession(sessionId: string): Promise<{ status: string }> {
    return api.delete<{ status: string }>(`${BASE}/sessions/${sessionId}`, { auth: false });
  },
};
