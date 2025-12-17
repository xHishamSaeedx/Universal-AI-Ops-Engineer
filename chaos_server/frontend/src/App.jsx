import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { API_BASE, chaosApi } from "./services/chaosApi";

function App() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const backendLabel = useMemo(() => {
    // If we're using the dev proxy, show the real backend too
    if (import.meta.env.DEV && API_BASE === "/api")
      return "http://127.0.0.1:8080 (via Vite proxy)";
    return API_BASE;
  }, []);

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

  useEffect(() => {
    refresh();
  }, []);

  return (
    <>
      <div className="container">
        <header className="header">
          <div>
            <h1>Chaos Server</h1>
            <div className="subtle">Backend: {backendLabel}</div>
          </div>
          <button className="btn" onClick={refresh} disabled={loading}>
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </header>

        <section className="panel">
          <div className="row">
            <div className="label">Health</div>
            {health?.status ? (
              <span
                className={`badge ${health.status === "ok" ? "ok" : "warn"}`}
              >
                {health.status}
              </span>
            ) : error ? (
              <span className="badge err">error</span>
            ) : (
              <span className="badge warn">unknown</span>
            )}
          </div>

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
      </div>
    </>
  );
}

export default App;
