import type { ChatHistoryResponse, ChatResponse, PlanResponse } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

/** Active demo profile; kept in sync by ProfileProvider. */
let activeUserId = "demo-veteran";

export function setApiUserId(userId: string) {
  activeUserId = userId.trim() || "demo-veteran";
}

export function getApiUserId() {
  return activeUserId;
}

export type ProfileSummary = {
  user_id: string;
  name: string;
  goal: string;
  onboarding_complete: boolean;
  is_ephemeral?: boolean;
  expires_at?: string | null;
  created_at?: string | null;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function userHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  headers.set("X-User-Id", activeUserId);
  return headers;
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(detail || `Request failed (${res.status})`, res.status);
  }
  return res.json() as Promise<T>;
}

export async function fetchProfiles(): Promise<ProfileSummary[]> {
  const res = await fetch(`${API_URL}/api/profiles`, { cache: "no-store" });
  const data = await parseJson<{ profiles: ProfileSummary[] }>(res);
  return data.profiles ?? [];
}

/** Public no-login guest session — no X-User-Id header. */
export async function createTryProfile(): Promise<{ user_id: string }> {
  const res = await fetch(`${API_URL}/api/profiles/try`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  return parseJson<{ user_id: string }>(res);
}

export async function sendChat(
  message: string,
  threadId?: string | null,
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: userHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ message, thread_id: threadId ?? undefined }),
  });
  return parseJson<ChatResponse>(res);
}

export async function sendApprove(
  threadId: string,
  decision: "accept" | "reject",
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/approve`, {
    method: "POST",
    headers: userHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ thread_id: threadId, decision }),
  });
  return parseJson<ChatResponse>(res);
}

export async function fetchChatHistory(
  threadId: string,
): Promise<ChatHistoryResponse> {
  const params = `?thread_id=${encodeURIComponent(threadId)}`;
  const res = await fetch(`${API_URL}/api/chat/history${params}`, {
    cache: "no-store",
    headers: userHeaders(),
  });
  return parseJson<ChatHistoryResponse>(res);
}

export async function fetchPlan(threadId?: string | null): Promise<PlanResponse> {
  const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : "";
  const res = await fetch(`${API_URL}/api/plan${params}`, {
    cache: "no-store",
    headers: userHeaders(),
  });
  return parseJson<PlanResponse>(res);
}

export type UploadResponse = {
  ingested_chunks: number;
};

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    headers: userHeaders(),
    body,
  });
  return parseJson<UploadResponse>(res);
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}
