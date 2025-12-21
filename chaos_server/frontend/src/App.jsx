import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import About from "./components/About";
import DBChaos from "./pages/DBChaos";
import "./App.css";

function HomePage() {
  return (
    <div className="home-page">
      <Hero />
      <About />
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/db-chaos" element={<DBChaos />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
