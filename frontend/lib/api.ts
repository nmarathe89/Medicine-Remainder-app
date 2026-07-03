// REST client for the FastAPI backend.
//
// Environment-aware base URL so the SAME code runs locally and on cloud:
//  - Client-side (browser): NEXT_PUBLIC_API_BASE_URL (e.g. http://localhost:8000)
//  - Server-side (SSR/Node): INTERNAL_API_BASE_URL (compose service name or
//    the Cloud Run backend URL), falling back to the public one.
export function apiBase(): string {
  if (typeof window === "undefined") {
    return (
      process.env.INTERNAL_API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
}

export interface ApiError {
  status: number;
  detail: string;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${apiBase()}${path}`, { ...options, headers });
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err: ApiError = {
      status: res.status,
      detail: (body && (body.detail || JSON.stringify(body))) || "Request failed",
    };
    throw err;
  }
  return body as T;
}

export const api = {
  register: (username: string, password: string) =>
    request("/api/auth/register", { method: "POST", body: JSON.stringify({ username, password }) }),
  login: (username: string, password: string) =>
    request<{ access_token: string; role: string; username: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  adminLogin: (username: string, password: string) =>
    request<{ access_token: string; role: string; username: string }>("/api/auth/admin/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: (token: string) => request("/api/auth/logout", { method: "POST" }, token),
  sessions: (token: string) => request<any[]>("/api/auth/sessions", {}, token),

  listMedicines: (token: string) => request<any[]>("/api/medicines", {}, token),
  createMedicine: (token: string, data: any) =>
    request("/api/medicines", { method: "POST", body: JSON.stringify(data) }, token),
  deleteMedicine: (token: string, id: number) =>
    request(`/api/medicines/${id}`, { method: "DELETE" }, token),

  dueAlerts: (token: string) => request<any[]>("/api/alerts/due", {}, token),
  upcomingAlerts: (token: string) => request<any[]>("/api/alerts/upcoming", {}, token),
  alertHistory: (token: string) => request<any[]>("/api/alerts/history", {}, token),
  ackAlert: (token: string, id: number, action: "taken" | "skipped") =>
    request(`/api/alerts/${id}/ack`, { method: "POST", body: JSON.stringify({ action }) }, token),

  submitFeedback: (token: string, sentiment: string, message: string) =>
    request("/api/feedback", { method: "POST", body: JSON.stringify({ sentiment, message }) }, token),

  adminUsers: (token: string) => request<any>("/api/admin/stats/users", {}, token),
  adminFeedback: (token: string) => request<any>("/api/admin/stats/feedback", {}, token),
  adminTrend: (token: string) => request<any[]>("/api/admin/stats/user-trend", {}, token),
  adminAlerts: (token: string) => request<any>("/api/admin/stats/alerts", {}, token),
};
