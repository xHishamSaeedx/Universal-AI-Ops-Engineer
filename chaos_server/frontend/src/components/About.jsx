import "./About.css";

function About() {
  return (
    <section id="about" className="about">
      <div className="about-container">
        <div className="about-header">
          <h2 className="about-title">What is Chaos Engineering?</h2>
          <p className="about-subtitle">
            Deliberately introducing failures to build resilient systems
          </p>
        </div>

        <div className="about-grid">
          <div className="about-card">
            <div className="card-icon">🎯</div>
            <h3>Controlled Testing</h3>
            <p>
              Simulate real-world failures in a controlled environment to
              identify weaknesses before they impact your users.
            </p>
          </div>

          <div className="about-card">
            <div className="card-icon">🛡️</div>
            <h3>Build Resilience</h3>
            <p>
              Learn how your systems behave under stress and implement proper
              safeguards to handle unexpected failures gracefully.
            </p>
          </div>

          <div className="about-card">
            <div className="card-icon">📊</div>
            <h3>Data-Driven Insights</h3>
            <p>
              Gather metrics and observability data during chaos experiments to
              make informed decisions about system improvements.
            </p>
          </div>

          <div className="about-card">
            <div className="card-icon">⚡</div>
            <h3>Database Chaos</h3>
            <p>
              Test database connection pool exhaustion, simulate slow queries,
              and verify your application's behavior under database stress.
            </p>
          </div>

          <div className="about-card">
            <div className="card-icon">🔄</div>
            <h3>Continuous Improvement</h3>
            <p>
              Integrate chaos engineering into your development pipeline to
              continuously validate system reliability.
            </p>
          </div>

          <div className="about-card">
            <div className="card-icon">🚀</div>
            <h3>Production Ready</h3>
            <p>
              Deploy with confidence knowing your systems can handle failures
              and recover automatically when issues occur.
            </p>
          </div>
        </div>

        <div className="about-cta">
          <h3>Ready to test your system's resilience?</h3>
          <p>
            Start with our database chaos experiments to see how your
            application handles connection pool exhaustion and other
            database-related failures.
          </p>
        </div>
      </div>
    </section>
  );
}

export default About;
