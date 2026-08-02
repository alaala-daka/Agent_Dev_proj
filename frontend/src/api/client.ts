// fetch wrapper for REST API
const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const apiClient = {
  // ── Sessions ──
  listSessions: () => request<{ sessions: import('../types/session').Session[] }>('/sessions'),
  createSession: (name: string) =>
    request<{ session_id: string }>('/sessions', { method: 'POST', body: JSON.stringify({ name }) }),
  getSession: (id: string) => request<import('../types/session').Session>(`/sessions/${id}`),
  deleteSession: (id: string) =>
    request<{ deleted: string }>(`/sessions/${id}`, { method: 'DELETE' }),
  getMessages: (id: string, offset = 0, limit = 50) =>
    request<{ messages: unknown[]; total: number }>(`/sessions/${id}/messages?offset=${offset}&limit=${limit}`),

  // ── Config ──
  getConfig: (name: string) => request<{ config: string; values: Record<string, unknown> }>(`/config/${name}`),
  updateConfig: (name: string, values: Record<string, unknown>) =>
    request<{ config: string; updated: string[] }>(`/config/${name}`, {
      method: 'PUT',
      body: JSON.stringify({ values }),
    }),

  // ── Files / RAG ──
  listRagFiles: () => request<{ files: unknown[]; total: number }>('/files/rag-files'),
  getRagStatus: () => request<{ file_count: number; total_chunks: number; vector_count: number }>('/files/rag-status'),
  deleteRagFile: (name: string) =>
    request<{ deleted: string }>(`/files/rag-files/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  // ── Tools ──
  listTools: () => request<{ tools: unknown[] }>('/tools'),
  getTodos: () => request<{ todos: unknown[]; counter: number }>('/tools/todos'),
  searchReflections: (q: string) =>
    request<{ query: string; results: string }>(`/tools/reflections/search?q=${encodeURIComponent(q)}`),

  // ── Health ──
  health: () => request<{ status: string }>('/health'),
};
