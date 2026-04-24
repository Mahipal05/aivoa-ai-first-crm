import type { ChatResponse, InteractionListResponse, SessionResponse } from "../types";

const DEFAULT_API_BASE_URL = "/api";
const CONFIGURED_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
const FALLBACK_API_BASE_URLS = [
  CONFIGURED_API_BASE_URL,
  DEFAULT_API_BASE_URL,
  "http://127.0.0.1:8000/api",
  "http://localhost:8000/api",
];

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const candidates = [...new Set(FALLBACK_API_BASE_URLS)];
  let lastError: Error | null = null;

  for (const baseUrl of candidates) {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...(init?.headers ?? {}),
        },
        ...init,
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || `Request failed against ${baseUrl}`);
      }

      return response.json() as Promise<T>;
    } catch (error) {
      const reason = error instanceof Error ? error.message : "Request failed";
      lastError = new Error(`${reason} (attempted ${baseUrl}${path})`);
    }
  }

  const detail = lastError?.message ?? `Request failed for ${path}`;
  throw new Error(`Backend is not reachable. Start it with 'npm start' or 'npm run app'. ${detail}`);
}

export function bootstrapSession(sessionId?: string | null) {
  return request<SessionResponse>("/bootstrap", {
    method: "POST",
    body: JSON.stringify(sessionId ? { session_id: sessionId } : {}),
  });
}

export function fetchSession(sessionId: string) {
  return request<SessionResponse>(`/sessions/${sessionId}`);
}

export function sendChatMessage(sessionId: string, message: string) {
  return request<ChatResponse>(`/sessions/${sessionId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function fetchInteractions() {
  return request<InteractionListResponse>("/interactions");
}
