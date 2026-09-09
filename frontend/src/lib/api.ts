const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
  }
}

/** Set by AuthContext on login/refresh/logout; read here so every request carries it. */
let accessToken: string | null = null;
export function setAccessToken(token: string | null) {
  accessToken = token;
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body.detail === "string" ? body.detail : res.statusText;
  } catch {
    return res.statusText;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init?.headers,
    },
  });

  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** For the one endpoint (jwt/login) that speaks OAuth2 form-encoding, not JSON. */
async function requestForm<T>(path: string, fields: Record<string, string>): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(fields),
  });

  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  postForm: <T>(path: string, fields: Record<string, string>) => requestForm<T>(path, fields),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
