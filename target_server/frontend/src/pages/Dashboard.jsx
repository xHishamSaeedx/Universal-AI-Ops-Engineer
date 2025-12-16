import { useState, useEffect } from "react";
import { Card, Text, Badge, Loader, Button, Group } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { healthAPI } from "../services/api";

const Dashboard = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const response = await healthAPI.getHealth();
      setHealthData(response.data);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error fetching health data:", error);
      notifications.show({
        title: "Error",
        message: "Failed to fetch health data from backend",
        color: "red",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case "healthy":
        return "green";
      case "warning":
        return "yellow";
      case "unhealthy":
        return "red";
      default:
        return "gray";
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case "healthy":
        return "✅";
      case "warning":
        return "⚠️";
      case "unhealthy":
        return "❌";
      default:
        return "❓";
    }
  };

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
          <h1>System Dashboard</h1>
          <p>Monitor your target server health and performance</p>
        </div>
        <Button
          onClick={fetchHealthData}
          loading={loading}
          variant="light"
          color="blue"
        >
          Refresh Data
        </Button>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "1rem",
        }}
      >
        {/* Overall Status Card */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Card.Section withBorder inheritPadding py="xs">
            <Text size="lg" weight={500}>
              System Status
            </Text>
          </Card.Section>

          <Group position="apart" mt="md" mb="xs">
            <Text size="sm">Overall Health</Text>
            {loading ? (
              <Loader size="sm" />
            ) : (
              <Badge
                color={getStatusColor(healthData?.status)}
                variant="light"
                size="lg"
              >
                {getStatusIcon(healthData?.status)}{" "}
                {healthData?.status || "Unknown"}
              </Badge>
            )}
          </Group>

          <Text size="sm" color="dimmed" mt="sm">
            Last updated: {lastUpdate || "Never"}
          </Text>
        </Card>

        {/* Database Status Card */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Card.Section withBorder inheritPadding py="xs">
            <Text size="lg" weight={500}>
              Database
            </Text>
          </Card.Section>

          <Group position="apart" mt="md" mb="xs">
            <Text size="sm">Connection Status</Text>
            {loading ? (
              <Loader size="sm" />
            ) : (
              <Badge
                color={getStatusColor(healthData?.services?.database?.status)}
                variant="light"
              >
                {getStatusIcon(healthData?.services?.database?.status)}{" "}
                {healthData?.services?.database?.status || "Unknown"}
              </Badge>
            )}
          </Group>

          {healthData?.services?.database?.error && (
            <Text size="sm" color="red" mt="sm">
              Error: {healthData.services.database.error}
            </Text>
          )}
        </Card>

        {/* System Metrics Card */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Card.Section withBorder inheritPadding py="xs">
            <Text size="lg" weight={500}>
              System Metrics
            </Text>
          </Card.Section>

          <div style={{ marginTop: "1rem" }}>
            {loading ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  padding: "2rem",
                }}
              >
                <Loader />
              </div>
            ) : healthData?.system ? (
              <div style={{ display: "grid", gap: "0.5rem" }}>
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <Text size="sm">CPU Usage:</Text>
                  <Text size="sm" weight={500}>
                    {healthData.system.cpu_percent?.toFixed(1)}%
                  </Text>
                </div>
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <Text size="sm">Memory Usage:</Text>
                  <Text size="sm" weight={500}>
                    {healthData.system.memory_percent?.toFixed(1)}%
                  </Text>
                </div>
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <Text size="sm">Disk Usage:</Text>
                  <Text size="sm" weight={500}>
                    {healthData.system.disk_percent?.toFixed(1)}%
                  </Text>
                </div>
              </div>
            ) : (
              <Text size="sm" color="dimmed">
                No system metrics available
              </Text>
            )}
          </div>
        </Card>

        {/* API Information Card */}
        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Card.Section withBorder inheritPadding py="xs">
            <Text size="lg" weight={500}>
              API Information
            </Text>
          </Card.Section>

          <div style={{ marginTop: "1rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <Text size="sm">Backend:</Text>
              <Text size="sm" weight={500}>
                FastAPI
              </Text>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <Text size="sm">Version:</Text>
              <Text size="sm" weight={500}>
                {healthData?.version || "Unknown"}
              </Text>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Text size="sm">Uptime:</Text>
              <Text size="sm" weight={500}>
                {healthData?.timestamp
                  ? new Date(healthData.timestamp * 1000).toLocaleString()
                  : "Unknown"}
              </Text>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
