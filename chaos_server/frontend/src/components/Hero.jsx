import { Link } from "react-router-dom";
import Lightning from "./Lightning";
import "./Hero.css";

function Hero() {
  return (
    <section className="hero">
      <div className="hero-lightning-container">
        <Lightning hue={270} xOffset={0} speed={1} intensity={1} size={1} />
      </div>
      <div className="hero-overlay"></div>
      <div className="hero-container">
        <div className="hero-content">
          <h1 className="hero-title">Chaos Engineering Platform</h1>
          <p className="hero-tagline">
            Safely break things to build resilient systems. Train AI agents to
            autonomously detect, diagnose, and fix failures.
          </p>
          <div className="hero-buttons">
            <Link to="/db-chaos" className="hero-button primary">
              Start DB Chaos Testing
            </Link>
            <a href="#about" className="hero-button secondary">
              Learn More
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Hero;
