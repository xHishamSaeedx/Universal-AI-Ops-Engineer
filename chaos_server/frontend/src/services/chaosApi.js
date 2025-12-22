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
  breakDbPool: ({ targetBaseUrl, connections, holdSeconds } = {}) => {
    const params = new URLSearchParams();
    if (targetBaseUrl) params.set("target_base_url", targetBaseUrl);
    if (typeof connections === "number")
      params.set("connections", String(connections));
    if (typeof holdSeconds === "number")
      params.set("hold_seconds", String(holdSeconds));
    const qs = params.toString();
    const url = `${API_BASE}/v1/break/db_pool` + (qs ? "?" + qs : "");
    return fetchJson(url, {
      method: "POST",
    });
  },
  getDbPoolAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/db_pool/${attackId}`),
  stopDbPoolAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/db_pool/${attackId}/stop`, {
      method: "POST",
    }),
  breakMigrations: ({
    targetDatabaseUrl,
    failureType,
    durationSeconds,
  } = {}) => {
    const params = new URLSearchParams();
    if (targetDatabaseUrl) params.set("target_database_url", targetDatabaseUrl);
    if (failureType) params.set("failure_type", failureType);
    if (typeof durationSeconds === "number")
      params.set("duration_seconds", String(durationSeconds));
    const qs = params.toString();
    const url = `${API_BASE}/v1/break/migrations` + (qs ? "?" + qs : "");
    return fetchJson(url, {
      method: "POST",
    });
  },
  getMigrationsAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/migrations/${attackId}`),
  stopMigrationsAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/migrations/${attackId}/stop`, {
      method: "POST",
    }),
  breakLongTransactions: ({
    targetDatabaseUrl,
    lockType,
    durationSeconds,
    targetTable,
    lockCount,
    advisoryLockId,
  } = {}) => {
    const params = new URLSearchParams();
    if (targetDatabaseUrl) params.set("target_database_url", targetDatabaseUrl);
    if (lockType) params.set("lock_type", lockType);
    if (typeof durationSeconds === "number")
      params.set("duration_seconds", String(durationSeconds));
    if (targetTable) params.set("target_table", targetTable);
    if (typeof lockCount === "number")
      params.set("lock_count", String(lockCount));
    if (typeof advisoryLockId === "number")
      params.set("advisory_lock_id", String(advisoryLockId));
    const qs = params.toString();
    const url = `${API_BASE}/v1/break/long_transactions` + (qs ? "?" + qs : "");
    return fetchJson(url, {
      method: "POST",
    });
  },
  getLongTransactionsAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/long_transactions/${attackId}`),
  stopLongTransactionsAttack: (attackId, forceKill = false) => {
    const params = new URLSearchParams();
    if (forceKill) params.set("force_kill", "true");
    const qs = params.toString();
    const url =
      `${API_BASE}/v1/break/long_transactions/${attackId}/stop` +
      (qs ? "?" + qs : "");
    return fetchJson(url, {
      method: "POST",
    });
  },
};
