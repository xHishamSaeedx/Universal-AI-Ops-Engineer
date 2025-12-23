import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          Chaos Server
        </Link>
        <ul className="navbar-menu">
          <li>
            <Link
              to="/"
              className={`navbar-link ${
                location.pathname === "/" ? "active" : ""
              }`}
            >
              Home
            </Link>
          </li>
          <li>
            <Link
              to="/db-chaos"
              className={`navbar-link ${
                location.pathname === "/db-chaos" ? "active" : ""
              }`}
            >
              DB Chaos
            </Link>
          </li>
          <li>
            <Link
              to="/app-chaos"
              className={`navbar-link ${
                location.pathname === "/app-chaos" ? "active" : ""
              }`}
            >
              Application / API Chaos
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
