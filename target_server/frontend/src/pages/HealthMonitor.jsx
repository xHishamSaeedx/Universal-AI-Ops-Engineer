import { useState, useEffect } from "react";
import { Card, Text, Button, Loader, JsonInput, Group } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { healthAPI } from "../services/api";

const HealthMonitor = () => {
  const [healthData, setHealthData] = useState(null);
  const [simpleHealth, setSimpleHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealthData = async () => {
    try {
      setLoading(true);

      // Fetch both detailed and simple health data
      const [detailedResponse, simpleResponse] = await Promise.all([
        healthAPI.getHealth(),
        healthAPI.getHealthz(),
      ]);

      setHealthData(detailedResponse.data);
      setSimpleHealth(simpleResponse.data);
    } catch (error) {
      console.error("Error fetching health data:", error);
      notifications.show({
        title: "Connection Error",
        message:
          "Cannot connect to FastAPI backend. Make sure the backend server is running.",
        color: "red",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();

    // Auto-refresh every 10 seconds if enabled
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchHealthData, 10000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
        }}
      >
        <div>
          <h1>Health Monitor</h1>
          <p>Detailed health checks and API responses</p>
        </div>
        <Group>
          <Button
            onClick={fetchHealthData}
            loading={loading}
            variant="light"
            color="blue"
          >
            Manual Refresh
          </Button>
          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            variant={autoRefresh ? "filled" : "light"}
            color="green"
          >
            {autoRefresh ? "Disable" : "Enable"} Auto Refresh
          </Button>
        </Group>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
          gap: "1rem",
        }}
      >
        {/* Simple Health Check */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Card.Section withBorder inheritPadding py="xs">
            <Text size="lg" weight={500}>
              Simple Health Check (GET /healthz)
            </Text>
          </Card.Section>

          <div style={{ marginTop: "1rem" }}>
            {loading ? (
              <Loader />
            ) : simpleHealth ? (
              <div>
                <Text size="sm" mb="xs">
                  Response:
                </Text>
                <JsonInput
                  value={JSON.stringify(simpleHealth, null, 2)}
                  readOnly
                  autosize
                  minRows={3}
                />
              </div>
            ) : (
              <Text size="sm" color="red">
                No data received
              </Text>
            )}
          </div>
        </Card>

        {/* Detailed Health Check */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Card.Section withBorder inheritPadding py="xs">
            <Text size="lg" weight={500}>
              Detailed Health Check (GET /api/v1/health)
            </Text>
          </Card.Section>

          <div style={{ marginTop: "1rem" }}>
            {loading ? (
              <Loader />
            ) : healthData ? (
              <div>
                <Text size="sm" mb="xs">
                  Response:
                </Text>
                <JsonInput
                  value={JSON.stringify(healthData, null, 2)}
                  readOnly
                  autosize
                  minRows={15}
                />
              </div>
            ) : (
              <Text size="sm" color="red">
                No data received
              </Text>
            )}
          </div>
        </Card>
      </div>

      {/* Connection Status */}
      <Card
        shadow="sm"
        padding="lg"
        radius="md"
        withBorder
        style={{ marginTop: "2rem" }}
      >
        <Card.Section withBorder inheritPadding py="xs">
          <Text size="lg" weight={500}>
            Connection Status
          </Text>
        </Card.Section>

        <div style={{ marginTop: "1rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <Text size="sm">Backend API:</Text>
              <Text size="sm" color="dimmed">
                http://localhost:8000
              </Text>
            </div>
            <div style={{ textAlign: "right" }}>
              <Text size="sm">Frontend:</Text>
              <Text size="sm" color="dimmed">
                http://localhost:3000
              </Text>
            </div>
          </div>

          <div
            style={{
              marginTop: "1rem",
              padding: "1rem",
              backgroundColor: "#1a1a1a",
              borderRadius: "4px",
            }}
          >
            <Text size="sm" mb="xs">
              API Endpoints:
            </Text>
            <div
              style={{
                fontFamily: "monospace",
                fontSize: "0.8rem",
                color: "#9ca3af",
              }}
            >
              <div>GET /healthz - Simple health check</div>
              <div>GET /api/v1/health - Detailed health with metrics</div>
              <div>Frontend proxy: /api/v1/health → backend</div>
            </div>
          </div>

          {autoRefresh && (
            <Text size="sm" color="green" mt="sm">
              🔄 Auto-refresh enabled (every 10 seconds)
            </Text>
          )}
        </div>
      </Card>
    </div>
  );
};

export default HealthMonitor;
