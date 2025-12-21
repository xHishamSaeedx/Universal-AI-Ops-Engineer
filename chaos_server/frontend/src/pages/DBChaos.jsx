import { useEffect, useMemo, useState } from "react";
import { API_BASE, chaosApi } from "../services/chaosApi";
import "./DBChaos.css";

function isTerminalAttackState(state) {
  return state === "completed" || state === "cancelled" || state === "failed";
}

function getAttackBadgeClass(state) {
  if (!state) return "warn";
  if (state === "completed") return "ok";
  if (state === "running" || state === "starting" || state === "cancelling")
    return "warn";
  return "err";
}

function DBChaos() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Pool exhaustion chaos controls
  const [targetBaseUrl, setTargetBaseUrl] = useState("http://127.0.0.1:8000");
  const [connections, setConnections] = useState(20);
  const [holdSeconds, setHoldSeconds] = useState(60);
  const [attackId, setAttackId] = useState(null);
  const [attack, setAttack] = useState(null);
  const [attackLoading, setAttackLoading] = useState(false);
  const [attackError, setAttackError] = useState(null);

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

  async function startDbPoolAttack() {
    setAttackLoading(true);
    setAttackError(null);
    setAttack(null);
    try {
      const res = await chaosApi.breakDbPool({
        targetBaseUrl,
        connections,
        holdSeconds,
      });
      setAttackId(res.attack_id);
    } catch (e) {
      setAttackId(null);
      setAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setAttackLoading(false);
    }
  }

  async function stopDbPoolAttack() {
    if (!attackId) return;
    setAttackLoading(true);
    setAttackError(null);
    try {
      await chaosApi.stopDbPoolAttack(attackId);
    } catch (e) {
      setAttackError(e instanceof Error ? e.message : String(e));
    } finally {
      setAttackLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  // Poll attack status while an attack_id is active
  useEffect(() => {
    if (!attackId) return;

    let cancelled = false;
    let timer = null;

    async function poll() {
      try {
        const data = await chaosApi.getDbPoolAttack(attackId);
        if (cancelled) return;
        setAttack(data);
        if (isTerminalAttackState(data?.state)) {
          if (timer) clearInterval(timer);
          timer = null;
        }
      } catch (e) {
        if (cancelled) return;
        setAttackError(e instanceof Error ? e.message : String(e));
      }
    }

    poll();
    timer = setInterval(poll, 1000);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [attackId]);

  return (
    <div className="db-chaos-page">
      <div className="page-header">
        <h1>Database Chaos Testing</h1>
        <p>
          Simulate database connection pool exhaustion and test your
          application's resilience
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
            <h2>DB Pool Exhaustion Attack</h2>
            <span className={`badge ${getAttackBadgeClass(attack?.state)}`}>
              {attack?.state || "idle"}
            </span>
          </div>

          <div className="attack-description">
            <p>
              This test simulates database connection pool exhaustion by
              creating multiple concurrent connections that hold database
              connections for a specified duration.
            </p>
          </div>

          <div className="formGrid">
            <label className="field">
              <div className="fieldLabel">Target base URL</div>
              <input
                className="input"
                value={targetBaseUrl}
                onChange={(e) => setTargetBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:8000"
              />
            </label>

            <label className="field">
              <div className="fieldLabel">Concurrent connections</div>
              <input
                className="input"
                type="number"
                min={1}
                max={500}
                value={connections}
                onChange={(e) => setConnections(Number(e.target.value))}
              />
            </label>

            <label className="field">
              <div className="fieldLabel">Hold seconds</div>
              <input
                className="input"
                type="number"
                min={1}
                max={600}
                value={holdSeconds}
                onChange={(e) => setHoldSeconds(Number(e.target.value))}
              />
            </label>
          </div>

          <div className="attack-controls">
            <div className="attack-info">
              {attackId ? (
                <div className="attack-id">
                  attack_id: <code>{attackId}</code>
                </div>
              ) : (
                <div className="no-attack">No attack running.</div>
              )}
            </div>
            <div className="btnRow">
              <button
                className="btn btn-primary"
                onClick={startDbPoolAttack}
                disabled={attackLoading}
              >
                {attackLoading ? "Starting…" : "Exhaust DB Pool"}
              </button>
              <button
                className="btn btnDanger"
                onClick={stopDbPoolAttack}
                disabled={!attackId || attackLoading}
              >
                Stop Attack
              </button>
            </div>
          </div>

          {attackError && <pre className="code errText">{attackError}</pre>}

          <div className="attack-status">
            <h3>Attack Status</h3>
            <pre className="code">
              {attack
                ? JSON.stringify(attack, null, 2)
                : "No attack status yet."}
            </pre>
          </div>

          <div className="hint">
            This calls <code>/api/v1/break/db_pool</code>, which triggers many{" "}
            <code>/api/v1/pool/hold</code> requests on the target server.
          </div>
        </section>
      </div>
    </div>
  );
}

export default DBChaos;
