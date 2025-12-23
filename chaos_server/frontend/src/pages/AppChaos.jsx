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
  if (state === "completed" || state === "rolled_back") return "ok";
  if (state === "running" || state === "starting" || state === "cancelling")
    return "warn";
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

  return (
    <div className="app-chaos-page">
      <div className="page-header">
        <h1>Application / API Chaos Testing</h1>
        <p>
          Simulate application and API failures including missing or incorrect
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
      </div>
    </div>
  );
}

export default AppChaos;

