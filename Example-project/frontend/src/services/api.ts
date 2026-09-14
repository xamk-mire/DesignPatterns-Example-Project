const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type HealthResponse = { status: string; db: "ok" | "fail" };

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return (await response.json()) as HealthResponse;
}

export type SensorDto = {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
};

export async function fetchSensors(): Promise<SensorDto[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`);
  if (!response.ok) {
    throw new Error(`Failed to list sensors (${response.status})`);
  }
  return (await response.json()) as SensorDto[];
}

export async function createSensor(type: string, displayName?: string | null): Promise<SensorDto> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, display_name: displayName ?? null }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Failed to create sensor (${response.status})`);
  }
  return (await response.json()) as SensorDto;
}
