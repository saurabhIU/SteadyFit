import type {
  ChatHistoryResponse,
  ChatResponse,
  PlanResponse,
  TodayFoodLogResponse,
} from "./types";

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
  image?: { base64: string; mime: string } | null,
  opts?: { userId?: string },
): Promise<ChatResponse> {
  const body: Record<string, unknown> = {
    message,
    thread_id: threadId ?? undefined,
  };
  if (image?.base64) {
    body.image_base64 = image.base64;
    body.image_mime = image.mime || "image/jpeg";
  }
  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  const uid = (opts?.userId || activeUserId || "").trim();
  if (!uid) {
    throw new ApiError("No active profile — refresh and try again", 400);
  }
  headers.set("X-User-Id", uid);
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  return parseJson<ChatResponse>(res);
}

export async function sendApprove(
  threadId: string,
  decision: "accept" | "reject",
  opts?: { userId?: string },
): Promise<ChatResponse> {
  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  const uid = (opts?.userId || activeUserId || "").trim();
  if (!uid) {
    throw new ApiError("No active profile — refresh and try again", 400);
  }
  headers.set("X-User-Id", uid);
  const res = await fetch(`${API_URL}/api/approve`, {
    method: "POST",
    headers,
    body: JSON.stringify({ thread_id: threadId, decision }),
  });
  return parseJson<ChatResponse>(res);
}

export type QuickWorkoutAction = "done" | "replace" | "extra";

export type QuickWorkoutResponse = ChatResponse & {
  logged?: boolean;
  awaiting_choice?: boolean;
  case?: string;
  action?: QuickWorkoutAction;
};

/** Structured Done / replace / extra — bypasses /api/chat entirely. */
export async function completeQuickWorkout(
  action: QuickWorkoutAction = "done",
  threadId?: string | null,
): Promise<QuickWorkoutResponse> {
  const res = await fetch(`${API_URL}/api/quick-workout/complete`, {
    method: "POST",
    headers: userHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      action,
      thread_id: threadId ?? undefined,
    }),
  });
  return parseJson<QuickWorkoutResponse>(res);
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

export async function fetchPlan(
  threadId?: string | null,
  opts?: { userId?: string },
): Promise<PlanResponse> {
  const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : "";
  const headers = new Headers();
  headers.set("X-User-Id", opts?.userId?.trim() || activeUserId);
  const res = await fetch(`${API_URL}/api/plan${params}`, {
    cache: "no-store",
    headers,
  });
  return parseJson<PlanResponse>(res);
}

export async function fetchTodayFoodLog(
  threadId?: string | null,
  opts?: { userId?: string },
): Promise<TodayFoodLogResponse> {
  const params = new URLSearchParams();
  if (threadId) params.set("thread_id", threadId);
  const qs = params.toString();
  const headers = new Headers();
  headers.set("X-User-Id", opts?.userId?.trim() || activeUserId);
  const res = await fetch(`${API_URL}/api/food_log/today${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
    headers,
  });
  return parseJson<TodayFoodLogResponse>(res);
}

export type UploadResponse = {
  ingested_chunks: number;
};

export async function uploadDocument(
  file: File,
  opts?: { userId?: string },
): Promise<UploadResponse> {
  const body = new FormData();
  body.append("file", file);
  const headers = new Headers();
  const uid = (opts?.userId || activeUserId || "").trim();
  if (!uid) {
    throw new ApiError("No active profile — refresh and try again", 400);
  }
  headers.set("X-User-Id", uid);
  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    headers,
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
