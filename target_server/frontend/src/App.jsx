import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import Dashboard from "./pages/Dashboard";
import HealthMonitor from "./pages/HealthMonitor";
import Header from "./components/Header";
import "./App.css";

function App() {
  return (
    <MantineProvider withGlobalStyles withNormalizeCSS>
      <Notifications />
      <Router>
        <div className="App">
          <Header />
          <main>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/health" element={<HealthMonitor />} />
            </Routes>
          </main>
        </div>
      </Router>
    </MantineProvider>
  );
}

export default App;
