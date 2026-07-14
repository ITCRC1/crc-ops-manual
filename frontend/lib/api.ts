// Cliente HTTP contra el backend FastAPI. Adjunta el Bearer, y ante un 401 intenta
// una única rotación con el refresh token (single-flight) antes de reintentar.

import { clearTokens, getAccess, getRefresh, setTokens } from "./tokens";
import type { Tokens } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

let refreshing: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
  const rt = getRefresh();
  if (!rt) return false;
  try {
    const res = await fetch(`${BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const data = (await res.json()) as Tokens;
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

function refreshOnce(): Promise<boolean> {
  if (!refreshing) {
    refreshing = doRefresh().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
}

interface Options {
  method?: string;
  body?: unknown;
  auth?: boolean;
  retry?: boolean;
}

export async function api<T>(path: string, opts: Options = {}): Promise<T> {
  const { method = "GET", body, auth = true, retry = true } = opts;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && retry) {
    const ok = await refreshOnce();
    if (ok) return api<T>(path, { ...opts, retry: false });
    clearTokens();
  }

  if (!res.ok) {
    let detail: string = res.statusText;
    try {
      const j = await res.json();
      if (j && typeof j.detail === "string") detail = j.detail;
      else if (j && j.detail) detail = JSON.stringify(j.detail);
    } catch {
      // respuesta sin cuerpo JSON
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  return (ct.includes("application/json") ? await res.json() : await res.text()) as T;
}

// Descarga autenticada de un binario (p.ej. el PDF del documento controlado).
export async function apiDownload(path: string): Promise<{ blob: Blob; filename: string }> {
  const pedir = async (): Promise<Response> => {
    const headers: Record<string, string> = {};
    const token = getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return fetch(`${BASE}${path}`, { headers });
  };
  let res = await pedir();
  if (res.status === 401) {
    const ok = await refreshOnce();
    if (ok) res = await pedir();
    else clearTokens();
  }
  if (!res.ok) throw new ApiError(res.status, res.statusText);
  const cd = res.headers.get("content-disposition") ?? "";
  const m = /filename="?([^"]+)"?/.exec(cd);
  return { blob: await res.blob(), filename: m ? m[1] : "documento.pdf" };
}

// Subida autenticada de un archivo (multipart). No fija Content-Type: el browser pone
// el boundary. Reintenta una vez ante 401 (igual que `api`).
export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const pedir = async (): Promise<Response> => {
    const headers: Record<string, string> = {};
    const token = getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return fetch(`${BASE}${path}`, { method: "POST", headers, body: form });
  };
  let res = await pedir();
  if (res.status === 401) {
    const ok = await refreshOnce();
    if (ok) res = await pedir();
    else clearTokens();
  }
  if (!res.ok) {
    let detail: string = res.statusText;
    try {
      const j = await res.json();
      if (j && typeof j.detail === "string") detail = j.detail;
      else if (j && j.detail) detail = JSON.stringify(j.detail);
    } catch {
      // sin cuerpo JSON
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export function guardarBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// Serializa parámetros de query, descartando null/undefined/"".
export function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}
