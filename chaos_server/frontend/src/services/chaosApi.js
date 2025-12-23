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
  breakEnvVars: ({
    targetEnvFile,
    envVarName,
    failureType,
    wrongValue,
    composeFile,
    durationSeconds,
    targetApiBaseUrl,
  } = {}) => {
    const params = new URLSearchParams();
    if (targetEnvFile) params.set("target_env_file", targetEnvFile);
    if (envVarName) params.set("env_var_name", envVarName);
    if (failureType) params.set("failure_type", failureType);
    if (wrongValue) params.set("wrong_value", wrongValue);
    if (composeFile) params.set("compose_file", composeFile);
    if (typeof durationSeconds === "number")
      params.set("duration_seconds", String(durationSeconds));
    if (targetApiBaseUrl) params.set("target_api_base_url", targetApiBaseUrl);
    const qs = params.toString();
    const url = `${API_BASE}/v1/break/env_vars` + (qs ? "?" + qs : "");
    return fetchJson(url, {
      method: "POST",
    });
  },
  getEnvVarsAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/env_vars/${attackId}`),
  stopEnvVarsAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/env_vars/${attackId}/stop`, {
      method: "POST",
    }),
  breakApiCrash: ({
    targetBaseUrl,
    crashType,
    durationSeconds,
    containerName,
  } = {}) => {
    const params = new URLSearchParams();
    if (targetBaseUrl) params.set("target_base_url", targetBaseUrl);
    if (crashType) params.set("crash_type", crashType);
    if (typeof durationSeconds === "number")
      params.set("duration_seconds", String(durationSeconds));
    if (containerName) params.set("container_name", containerName);
    const qs = params.toString();
    const url = `${API_BASE}/v1/break/api_crash` + (qs ? "?" + qs : "");
    return fetchJson(url, {
      method: "POST",
    });
  },
  getApiCrashAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/api_crash/${attackId}`),
  stopApiCrashAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/api_crash/${attackId}/stop`, {
      method: "POST",
    }),
  breakRateLimit: ({
    targetBaseUrl,
    maxRequests,
    windowSeconds,
    floodRequests,
    floodRate,
    targetEndpoint,
    durationSeconds,
  } = {}) => {
    const params = new URLSearchParams();
    if (targetBaseUrl) params.set("target_base_url", targetBaseUrl);
    if (typeof maxRequests === "number")
      params.set("max_requests", String(maxRequests));
    if (typeof windowSeconds === "number")
      params.set("window_seconds", String(windowSeconds));
    if (typeof floodRequests === "number")
      params.set("flood_requests", String(floodRequests));
    if (typeof floodRate === "number")
      params.set("flood_rate", String(floodRate));
    if (targetEndpoint) params.set("target_endpoint", targetEndpoint);
    if (typeof durationSeconds === "number")
      params.set("duration_seconds", String(durationSeconds));
    const qs = params.toString();
    const url = `${API_BASE}/v1/break/rate_limit` + (qs ? "?" + qs : "");
    return fetchJson(url, {
      method: "POST",
    });
  },
  getRateLimitAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/rate_limit/${attackId}`),
  stopRateLimitAttack: (attackId) =>
    fetchJson(`${API_BASE}/v1/break/rate_limit/${attackId}/stop`, {
      method: "POST",
    }),
};
