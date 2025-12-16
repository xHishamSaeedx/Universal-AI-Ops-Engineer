import { Link, useLocation } from "react-router-dom";
import "./Header.css";

const Header = () => {
  const location = useLocation();

  return (
    <header className="header">
      <nav className="nav">
        <div className="nav-brand">
          <h1>🎯 Target Server Monitor</h1>
          <p>Universal AI Ops Engineer</p>
        </div>
        <div className="nav-links">
          <Link to="/" className={location.pathname === "/" ? "active" : ""}>
            Dashboard
          </Link>
          <Link
            to="/health"
            className={location.pathname === "/health" ? "active" : ""}
          >
            Health Monitor
          </Link>
        </div>
      </nav>
    </header>
  );
};

export default Header;
