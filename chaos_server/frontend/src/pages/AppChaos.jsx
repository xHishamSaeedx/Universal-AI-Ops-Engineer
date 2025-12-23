import { useEffect, useState, useMemo } from "react";
import { API_BASE, chaosApi } from "../services/chaosApi";
import "./AppChaos.css";

function isTerminalAttackState(state) {
  return (
    state === "completed" ||
    state === "cancelled" ||
    state === "failed" ||
    state === "rolled_back" ||
    state === "rollback_failed"
  );
}

function getAttackBadgeClass(state) {
  if (!state) return "warn";
  if (state === "completed" || state === "rolled_back" || state === "recovered") return "ok";
  if (state === "running" || state === "starting" || state === "cancelling")
    return "warn";
  if (state === "crashed" || state === "partially_recovered" || state === "failed_to_recover" || state === "recovery_failed")
    return "err";
  return "err";
}

function AppChaos() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Env vars chaos controls
  const [targetEnvFile, setTargetEnvFile] = useState("target_server/backend/.env");
  const [envVarName, setEnvVarName] = useState("EXTERNAL_API_KEY");
  const [failureType, setFailureType] = useState("missing");
  const [wrongValue, setWrongValue] = useState("INVALID_VALUE_12345");
  const [composeFile, setComposeFile] = useState("target_server/docker-compose.yml");
  const [durationSeconds, setDurationSeconds] = useState("");
  const [targetApiBaseUrl, setTargetApiBaseUrl] = useState("http://127.0.0.1:8000");
  const [envVarsAttackId, setEnvVarsAttackId] = useState(null);
  const [envVarsAttack, setEnvVarsAttack] = useState(null);
  const [envVarsAttackLoading, setEnvVarsAttackLoading] = useState(false);
  const [envVarsAttackError, setEnvVarsAttackError] = useState(null);

  // API crash chaos controls
  const [apiCrashTargetBaseUrl, setApiCrashTargetBaseUrl] = useState("http://127.0.0.1:8000");
  const [crashType, setCrashType] = useState("stop");
  const [apiCrashDurationSeconds, setApiCrashDurationSeconds] = useState("");
  const [containerName, setContainerName] = useState("");
  const [apiCrashAttackId, setApiCrashAttackId] = useState(null);
  const [apiCrashAttack, setApiCrashAttack] = useState(null);
  const [apiCrashAttackLoading, setApiCrashAttackLoading] = useState(false);
  const [apiCrashAttackError, setApiCrashAttackError] = useState(null);

  // Rate limit chaos controls
  const [rateLimitTargetBaseUrl, setRateLimitTargetBaseUrl] = useState("http://127.0.0.1:8000");
  const [maxRequests, setMaxRequests] = useState(10);
  const [windowSeconds, setWindowSeconds] = useState(60);
  const [floodRequests, setFloodRequests] = useState(30);
  const [floodRate, setFloodRate] = useState(5.0);
  const [targetEndpoint, setTargetEndpoint] = useState("/api/v1/health");
  const [rateLimitDurationSeconds, setRateLimitDurationSeconds] = useState("");
  const [rateLimitAttackId, setRateLimitAttackId] = useState(null);
  const [rateLimitAttack, setRateLimitAttack] = useState(null);
  const [rateLimitAttackLoading, setRateLimitAttackLoading] = useState(false);
  const [rateLimitAttackError, setRateLimitAttackError] = useState(null);

  const backendLabel = useMemo(() => {
    // If we're using the dev proxy, show the real backend too
    if (import.meta.env.DEV && API_BASE === "/api")
      return "http://127.0.0.1:8080 (via Vite proxy)";
    return API_BASE;
  }, []);

  let healthBadgeText = "unknown";
  let healthBadgeClass = "warn";
  if (health?.status) {
    healthBadgeText = health.status;
    healthBadgeClass = health.status === "ok" ? "ok" : "warn";
  } else if (error) {
    healthBadgeText = "error";
    healthBadgeClass = "err";
  }

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const data = await chaosApi.getHealth();
      setHealth(data);
    } catch (e) {
      setHealth(null);
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function startEnvVarsAttack() {
    setEnvVarsAttackLoading(true);
    setEnvVarsAttackError(null);
    setEnvVarsAttack(null);
    try {
      const res = await chaosApi.breakEnvVars({
        targetEnvFile: targetEnvFile || undefined,
        envVarName,
        failureType,
        wrongValue: failureType === "wrong" ? wrongValue : undefined,
        composeFile: composeFile || undefined,
        durationSeconds: durationSeconds ? Number(durationSeconds) : undefined,
        targetApiBaseUrl,
      });
      setEnvVarsAttackId(res.attack_id);
    } catch (e) {
      setEnvVarsAttackId(null);
      setEnvVarsAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setEnvVarsAttackLoading(false);
    }
  }

  async function stopEnvVarsAttack() {
    if (!envVarsAttackId) return;
    setEnvVarsAttackLoading(true);
    setEnvVarsAttackError(null);
    try {
      await chaosApi.stopEnvVarsAttack(envVarsAttackId);
    } catch (e) {
      setEnvVarsAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setEnvVarsAttackLoading(false);
    }
  }

  async function startApiCrashAttack() {
    setApiCrashAttackLoading(true);
    setApiCrashAttackError(null);
    setApiCrashAttack(null);
    try {
      const res = await chaosApi.breakApiCrash({
        targetBaseUrl: apiCrashTargetBaseUrl,
        crashType,
        durationSeconds: apiCrashDurationSeconds ? Number(apiCrashDurationSeconds) : undefined,
        containerName: containerName || undefined,
      });
      setApiCrashAttackId(res.attack_id);
    } catch (e) {
      setApiCrashAttackId(null);
      setApiCrashAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setApiCrashAttackLoading(false);
    }
  }

  async function stopApiCrashAttack() {
    if (!apiCrashAttackId) return;
    setApiCrashAttackLoading(true);
    setApiCrashAttackError(null);
    try {
      await chaosApi.stopApiCrashAttack(apiCrashAttackId);
    } catch (e) {
      setApiCrashAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setApiCrashAttackLoading(false);
    }
  }

  async function startRateLimitAttack() {
    setRateLimitAttackLoading(true);
    setRateLimitAttackError(null);
    setRateLimitAttack(null);
    try {
      const res = await chaosApi.breakRateLimit({
        targetBaseUrl: rateLimitTargetBaseUrl,
        maxRequests,
        windowSeconds,
        floodRequests,
        floodRate,
        targetEndpoint,
        durationSeconds: rateLimitDurationSeconds ? Number(rateLimitDurationSeconds) : undefined,
      });
      setRateLimitAttackId(res.attack_id);
    } catch (e) {
      setRateLimitAttackId(null);
      setRateLimitAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setRateLimitAttackLoading(false);
    }
  }

  async function stopRateLimitAttack() {
    if (!rateLimitAttackId) return;
    setRateLimitAttackLoading(true);
    setRateLimitAttackError(null);
    try {
      await chaosApi.stopRateLimitAttack(rateLimitAttackId);
    } catch (e) {
      setRateLimitAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setRateLimitAttackLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  // Poll env vars attack status while an attack_id is active
  useEffect(() => {
    if (!envVarsAttackId) return;

    let cancelled = false;
    let timer = null;

    async function poll() {
      try {
        const data = await chaosApi.getEnvVarsAttack(envVarsAttackId);
        if (cancelled) return;
        setEnvVarsAttack(data);
        if (isTerminalAttackState(data?.state)) {
          if (timer) clearInterval(timer);
          timer = null;
        }
      } catch (e) {
        if (cancelled) return;
        setEnvVarsAttackError(e instanceof Error ? e.message : String(e));
      }
    }

    poll();
    timer = setInterval(poll, 1000);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [envVarsAttackId]);

  // Poll API crash attack status while an attack_id is active
  useEffect(() => {
    if (!apiCrashAttackId) return;

    let cancelled = false;
    let timer = null;

    async function poll() {
      try {
        const data = await chaosApi.getApiCrashAttack(apiCrashAttackId);
        if (cancelled) return;
        setApiCrashAttack(data);
        if (isTerminalAttackState(data?.state) || data?.state === "crashed" || data?.state === "recovered") {
          if (timer) clearInterval(timer);
          timer = null;
        }
      } catch (e) {
        if (cancelled) return;
        setApiCrashAttackError(e instanceof Error ? e.message : String(e));
      }
    }

    poll();
    timer = setInterval(poll, 1000);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [apiCrashAttackId]);

  // Poll rate limit attack status while an attack_id is active
  useEffect(() => {
    if (!rateLimitAttackId) return;

    let cancelled = false;
    let timer = null;

    async function poll() {
      try {
        const data = await chaosApi.getRateLimitAttack(rateLimitAttackId);
        if (cancelled) return;
        setRateLimitAttack(data);
        if (isTerminalAttackState(data?.state) || data?.state === "completed" || data?.state === "recovered" || data?.state === "partially_recovered") {
          if (timer) clearInterval(timer);
          timer = null;
        }
      } catch (e) {
        if (cancelled) return;
        setRateLimitAttackError(e instanceof Error ? e.message : String(e));
      }
    }

    poll();
    timer = setInterval(poll, 1000);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [rateLimitAttackId]);

  return (
    <div className="app-chaos-page">
      <div className="page-header">
        <h1>Application / API Chaos Testing</h1>
        <p>
          Simulate application and API failures including API crashes, missing or incorrect
          environment variables to test your system's resilience
        </p>
      </div>

      <div className="chaos-container">
        <section className="chaos-panel health-panel">
          <div className="panel-header">
            <h2>Backend Health</h2>
            <button
              className="btn refresh-btn"
              onClick={refresh}
              disabled={loading}
            >
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
          <div className="subtle">Backend: {backendLabel}</div>

          {error ? (
            <pre className="code errText">{error}</pre>
          ) : (
            <pre className="code">
              {health ? JSON.stringify(health, null, 2) : "No data yet."}
            </pre>
          )}

          <div className="hint">
            Tip: start the backend with <code>python main.py</code> or{" "}
            <code>uvicorn main:app --reload --port 8080</code>.
          </div>
        </section>

        <section className="chaos-panel attack-panel">
          <div className="panel-header">
            <h2>Environment Variable Chaos Attack</h2>
            <span
              className={`badge ${getAttackBadgeClass(envVarsAttack?.state)}`}
            >
              {envVarsAttack?.state || "idle"}
            </span>
          </div>

          <div className="attack-description">
            <p>
              This test simulates configuration errors by modifying or removing
              environment variables in the target server's .env file. This causes
              the application to fail when it tries to use the missing or invalid
              environment variable.
            </p>
            <p>
              <strong>Failure Types:</strong>
            </p>
            <ul>
              <li>
                <strong>missing</strong>: Removes the environment variable from
                the .env file entirely. The application will fail when it tries to
                access this variable.
              </li>
              <li>
                <strong>wrong</strong>: Sets the environment variable to an
                invalid value (e.g., "INVALID_VALUE_12345"). The application will
                fail when it tries to validate or use this value.
              </li>
            </ul>
            <p>
              <strong>How it works:</strong> The chaos server backs up the .env
              file, modifies it, restarts the Docker container to pick up the
              changes, and then optionally auto-rollbacks after a specified
              duration. The target server's <code>/api/v1/test/env</code> endpoint
              will fail when the environment variable is broken.
            </p>
          </div>

          <div className="formGrid">
            <label className="field">
              <div className="fieldLabel">Target .env File Path</div>
              <input
                className="input"
                value={targetEnvFile}
                onChange={(e) => setTargetEnvFile(e.target.value)}
                placeholder="target_server/backend/.env"
              />
              <div className="field-hint">
                Path relative to workspace root or absolute path
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">Environment Variable Name</div>
              <input
                className="input"
                value={envVarName}
                onChange={(e) => setEnvVarName(e.target.value)}
                placeholder="EXTERNAL_API_KEY"
              />
            </label>

            <label className="field">
              <div className="fieldLabel">Failure Type</div>
              <select
                className="input"
                value={failureType}
                onChange={(e) => setFailureType(e.target.value)}
              >
                <option value="missing">Missing (Remove Variable)</option>
                <option value="wrong">Wrong (Invalid Value)</option>
              </select>
            </label>

            {failureType === "wrong" && (
              <label className="field">
                <div className="fieldLabel">Wrong Value</div>
                <input
                  className="input"
                  value={wrongValue}
                  onChange={(e) => setWrongValue(e.target.value)}
                  placeholder="INVALID_VALUE_12345"
                />
              </label>
            )}

            <label className="field">
              <div className="fieldLabel">Docker Compose File Path</div>
              <input
                className="input"
                value={composeFile}
                onChange={(e) => setComposeFile(e.target.value)}
                placeholder="target_server/docker-compose.yml"
              />
              <div className="field-hint">
                Path relative to workspace root or absolute path
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">
                Auto-rollback (seconds, optional)
              </div>
              <input
                className="input"
                type="number"
                min={1}
                max={3600}
                value={durationSeconds}
                onChange={(e) => setDurationSeconds(e.target.value)}
                placeholder="Leave empty for manual rollback"
              />
            </label>

            <label className="field">
              <div className="fieldLabel">Target API Base URL</div>
              <input
                className="input"
                value={targetApiBaseUrl}
                onChange={(e) => setTargetApiBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:8000"
              />
              <div className="field-hint">
                Used to verify the endpoint fails after the attack
              </div>
            </label>
          </div>

          <div className="attack-controls">
            <div className="attack-info">
              {envVarsAttackId ? (
                <div className="attack-id">
                  attack_id: <code>{envVarsAttackId}</code>
                  {envVarsAttack?.action && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      {envVarsAttack.action}
                    </span>
                  )}
                  {envVarsAttack?.original_value !== undefined && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      Original: {envVarsAttack.original_value || "(not set)"}
                    </span>
                  )}
                </div>
              ) : (
                <div className="no-attack">No attack running.</div>
              )}
            </div>
            <div className="btnRow">
              <button
                className="btn btn-primary"
                onClick={startEnvVarsAttack}
                disabled={envVarsAttackLoading}
              >
                {envVarsAttackLoading ? "Starting…" : "Break Environment Variable"}
              </button>
              <button
                className="btn btnDanger"
                onClick={stopEnvVarsAttack}
                disabled={!envVarsAttackId || envVarsAttackLoading}
              >
                Rollback Attack
              </button>
            </div>
          </div>

          {envVarsAttackError && (
            <pre className="code errText">{envVarsAttackError}</pre>
          )}

          <div className="attack-status">
            <h3>Attack Status</h3>
            <pre className="code">
              {envVarsAttack
                ? JSON.stringify(envVarsAttack, null, 2)
                : "No attack status yet."}
            </pre>
          </div>

          <div className="hint">
            This calls <code>/api/v1/break/env_vars</code>, which modifies the
            target server's .env file and restarts the container. The original
            .env file is backed up for safe rollback. Make sure the target server
            has a .env file with the environment variable you want to break (e.g.,
            <code>EXTERNAL_API_KEY=valid_api_key_12345</code>).
          </div>
        </section>

        <section className="chaos-panel attack-panel">
          <div className="panel-header">
            <h2>API Crash Chaos Attack</h2>
            <span
              className={`badge ${getAttackBadgeClass(apiCrashAttack?.state)}`}
            >
              {apiCrashAttack?.state || "idle"}
            </span>
          </div>

          <div className="attack-description">
            <p>
              This test simulates API crashes by stopping or restarting the target server's
              Docker container. This causes the API to become unavailable, simulating real-world
              scenarios like container crashes, OOM kills, system failures, or deployment issues.
            </p>
            <p>
              <strong>Crash Types:</strong>
            </p>
            <ul>
              <li>
                <strong>stop</strong>: Stops the Docker container, causing the API to go down.
                If auto-recovery is enabled, the container will be restarted after the specified
                duration. Otherwise, manual recovery is required.
              </li>
              <li>
                <strong>restart</strong>: Immediately restarts the Docker container, causing a
                brief downtime followed by automatic recovery. This simulates service restarts
                or deployment scenarios.
              </li>
            </ul>
            <p>
              <strong>How it works:</strong> The chaos server uses Docker commands to stop or
              restart the target server's API container. It verifies that the API is actually
              down/up and tracks the attack state. If auto-recovery is enabled, the container
              will be automatically restarted after the specified duration.
            </p>
          </div>

          <div className="formGrid">
            <label className="field">
              <div className="fieldLabel">Target API Base URL</div>
              <input
                className="input"
                value={apiCrashTargetBaseUrl}
                onChange={(e) => setApiCrashTargetBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:8000"
              />
              <div className="field-hint">
                Used to verify the API is down/up
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">Crash Type</div>
              <select
                className="input"
                value={crashType}
                onChange={(e) => setCrashType(e.target.value)}
              >
                <option value="stop">Stop (API goes down, requires recovery)</option>
                <option value="restart">Restart (brief downtime, then recovery)</option>
              </select>
            </label>

            <label className="field">
              <div className="fieldLabel">
                Auto-recovery (seconds, optional)
              </div>
              <input
                className="input"
                type="number"
                min={1}
                max={3600}
                value={apiCrashDurationSeconds}
                onChange={(e) => setApiCrashDurationSeconds(e.target.value)}
                placeholder="Leave empty for manual recovery"
              />
              <div className="field-hint">
                Only applies to "stop" type. Container will auto-restart after this duration.
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">Container Name (optional)</div>
              <input
                className="input"
                value={containerName}
                onChange={(e) => setContainerName(e.target.value)}
                placeholder="target_server_api (default)"
              />
              <div className="field-hint">
                Docker container name. Defaults to "target_server_api" if not specified.
              </div>
            </label>
          </div>

          <div className="attack-controls">
            <div className="attack-info">
              {apiCrashAttackId ? (
                <div className="attack-id">
                  attack_id: <code>{apiCrashAttackId}</code>
                  {apiCrashAttack?.container_name && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      Container: {apiCrashAttack.container_name}
                    </span>
                  )}
                  {apiCrashAttack?.crash_type && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      Type: {apiCrashAttack.crash_type}
                    </span>
                  )}
                  {apiCrashAttack?.api_verified_down !== undefined && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      API Down: {apiCrashAttack.api_verified_down ? "Yes" : "No"}
                    </span>
                  )}
                  {apiCrashAttack?.api_verified_up !== undefined && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      API Up: {apiCrashAttack.api_verified_up ? "Yes" : "No"}
                    </span>
                  )}
                </div>
              ) : (
                <div className="no-attack">No attack running.</div>
              )}
            </div>
            <div className="btnRow">
              <button
                className="btn btn-primary"
                onClick={startApiCrashAttack}
                disabled={apiCrashAttackLoading}
              >
                {apiCrashAttackLoading ? "Starting…" : "Crash API"}
              </button>
              <button
                className="btn btnDanger"
                onClick={stopApiCrashAttack}
                disabled={!apiCrashAttackId || apiCrashAttackLoading}
              >
                Recover API
              </button>
            </div>
          </div>

          {apiCrashAttackError && (
            <pre className="code errText">{apiCrashAttackError}</pre>
          )}

          <div className="attack-status">
            <h3>Attack Status</h3>
            <pre className="code">
              {apiCrashAttack
                ? JSON.stringify(apiCrashAttack, null, 2)
                : "No attack status yet."}
            </pre>
          </div>

          <div className="hint">
            This calls <code>/api/v1/break/api_crash</code>, which uses Docker commands to stop
            or restart the target server's API container. Make sure Docker is accessible from
            the chaos server and the container name matches your target server setup (default:
            <code>target_server_api</code>).
          </div>
        </section>

        <section className="chaos-panel attack-panel">
          <div className="panel-header">
            <h2>Rate Limit Chaos Attack</h2>
            <span
              className={`badge ${getAttackBadgeClass(rateLimitAttack?.state)}`}
            >
              {rateLimitAttack?.state || "idle"}
            </span>
          </div>

          <div className="attack-description">
            <p>
              This test simulates misconfigured rate limits by setting very restrictive limits
              and then flooding the target server with requests that exceed those limits. This
              causes 429 (Too Many Requests) errors to appear in the target server logs.
            </p>
            <p>
              <strong>How it works:</strong>
            </p>
            <ul>
              <li>
                Backs up the current rate limit configuration
              </li>
              <li>
                Sets restrictive limits (e.g., 10 requests per 60 seconds instead of 100)
              </li>
              <li>
                Sends a flood of requests at a specified rate that exceed the limit
              </li>
              <li>
                Tracks 429 responses and verifies they appear in target server logs
              </li>
              <li>
                Optionally auto-recovers by restoring original limits
              </li>
            </ul>
            <p>
              This simulates real-world SRE issues where rate limits are misconfigured,
              causing legitimate traffic to be blocked with 429 errors.
            </p>
          </div>

          <div className="formGrid">
            <label className="field">
              <div className="fieldLabel">Target API Base URL</div>
              <input
                className="input"
                value={rateLimitTargetBaseUrl}
                onChange={(e) => setRateLimitTargetBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:8000"
              />
            </label>

            <label className="field">
              <div className="fieldLabel">Max Requests (Restrictive Limit)</div>
              <input
                className="input"
                type="number"
                min={1}
                max={1000}
                value={maxRequests}
                onChange={(e) => setMaxRequests(Number(e.target.value))}
              />
              <div className="field-hint">
                Number of requests allowed per time window (e.g., 10)
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">Window Seconds</div>
              <input
                className="input"
                type="number"
                min={1}
                max={3600}
                value={windowSeconds}
                onChange={(e) => setWindowSeconds(Number(e.target.value))}
              />
              <div className="field-hint">
                Time window in seconds (e.g., 60 for 1 minute)
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">Flood Requests</div>
              <input
                className="input"
                type="number"
                min={1}
                max={10000}
                value={floodRequests}
                onChange={(e) => setFloodRequests(Number(e.target.value))}
              />
              <div className="field-hint">
                Total number of requests to send (should exceed max_requests)
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">Flood Rate (requests/second)</div>
              <input
                className="input"
                type="number"
                min={0.1}
                max={100}
                step={0.1}
                value={floodRate}
                onChange={(e) => setFloodRate(Number(e.target.value))}
              />
              <div className="field-hint">
                Rate at which to send requests (e.g., 5.0 = 5 requests per second)
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">Target Endpoint</div>
              <input
                className="input"
                value={targetEndpoint}
                onChange={(e) => setTargetEndpoint(e.target.value)}
                placeholder="/api/v1/health"
              />
              <div className="field-hint">
                Endpoint to hit with requests
              </div>
            </label>

            <label className="field">
              <div className="fieldLabel">
                Auto-recovery (seconds, optional)
              </div>
              <input
                className="input"
                type="number"
                min={1}
                max={3600}
                value={rateLimitDurationSeconds}
                onChange={(e) => setRateLimitDurationSeconds(e.target.value)}
                placeholder="Leave empty for manual recovery"
              />
              <div className="field-hint">
                Restore original limits after this duration
              </div>
            </label>
          </div>

          <div className="attack-controls">
            <div className="attack-info">
              {rateLimitAttackId ? (
                <div className="attack-id">
                  attack_id: <code>{rateLimitAttackId}</code>
                  {rateLimitAttack?.restrictive_config && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      Limit: {rateLimitAttack.restrictive_config.max_requests}/{rateLimitAttack.restrictive_config.window_seconds}s
                    </span>
                  )}
                  {rateLimitAttack?.flood_results && (
                    <span className="subtle" style={{ marginLeft: "1rem" }}>
                      {rateLimitAttack.flood_results.rate_limited} / {rateLimitAttack.flood_results.total_sent} rate limited
                    </span>
                  )}
                </div>
              ) : (
                <div className="no-attack">No attack running.</div>
              )}
            </div>
            <div className="btnRow">
              <button
                className="btn btn-primary"
                onClick={startRateLimitAttack}
                disabled={rateLimitAttackLoading}
              >
                {rateLimitAttackLoading ? "Starting…" : "Break Rate Limits"}
              </button>
              <button
                className="btn btnDanger"
                onClick={stopRateLimitAttack}
                disabled={!rateLimitAttackId || rateLimitAttackLoading}
              >
                Recover Rate Limits
              </button>
            </div>
          </div>

          {rateLimitAttackError && (
            <pre className="code errText">{rateLimitAttackError}</pre>
          )}

          {rateLimitAttack?.flood_results && (
            <div className="attack-status" style={{ marginTop: "1rem" }}>
              <h3>Flood Results</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem", marginBottom: "1rem" }}>
                <div>
                  <strong>Total Sent:</strong> {rateLimitAttack.flood_results.total_sent}
                </div>
                <div>
                  <strong>Successful (200):</strong> {rateLimitAttack.flood_results.successful}
                </div>
                <div>
                  <strong>Rate Limited (429):</strong> {rateLimitAttack.flood_results.rate_limited}
                </div>
                <div>
                  <strong>Errors:</strong> {rateLimitAttack.flood_results.errors}
                </div>
              </div>
              {rateLimitAttack?.verification && (
                <div style={{ marginTop: "1rem", padding: "0.5rem", backgroundColor: rateLimitAttack.verification.verified ? "#d4edda" : "#f8d7da", borderRadius: "4px" }}>
                  <strong>Verification:</strong>{" "}
                  {rateLimitAttack.verification.verified ? "✅" : "❌"}{" "}
                  Expected {rateLimitAttack.verification.expected_429s} 429s, got {rateLimitAttack.verification.actual_429s}
                </div>
              )}
            </div>
          )}

          <div className="attack-status">
            <h3>Attack Status</h3>
            <pre className="code">
              {rateLimitAttack
                ? JSON.stringify(rateLimitAttack, null, 2)
                : "No attack status yet."}
            </pre>
          </div>

          <div className="hint">
            This calls <code>/api/v1/break/rate_limit</code>, which sets restrictive rate limits
            on the target server and floods it with requests. Check the target server logs to see
            429 rate limit errors. The first N requests (within limit) will succeed, subsequent
            requests will get 429 responses.
          </div>
        </section>
      </div>
    </div>
  );
}

export default AppChaos;

