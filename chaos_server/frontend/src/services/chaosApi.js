const DEFAULT_BACKEND_API_BASE = "http://127.0.0.1:8080/api";

// In dev, prefer Vite proxy (/api -> http://127.0.0.1:8080)
export const API_BASE = import.meta.env.DEV
  ? "/api"
  : import.meta.env.VITE_API_BASE_URL || DEFAULT_BACKEND_API_BASE;

async function fetchJson(path, init) {
  const res = await fetch(path, {
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  const contentType = res.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await res.json()
    : await res.text();

  if (!res.ok) {
    const msg = typeof body === "string" ? body : JSON.stringify(body);
    throw new Error(`Request failed (${res.status}): ${msg}`);
  }

  return body;
}

export const chaosApi = {
  getHealth: () => fetchJson(`${API_BASE}/v1/health`),
  getHealthz: () => fetchJson(`${API_BASE}/v1/healthz`),
};
