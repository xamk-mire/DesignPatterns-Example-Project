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

export type DeviceFamily = "simulation" | "edge";

export type DeviceDto = {
  id: string;
  device_type: string;
  role: "sensor" | "actuator" | string;
  device_family: string;
  display_name: string;
  default_config: Record<string, unknown>;
};

export async function fetchDevices(filters?: {
  family?: string;
  role?: string;
}): Promise<DeviceDto[]> {
  const params = new URLSearchParams();
  if (filters?.family) {
    params.set("family", filters.family);
  }
  if (filters?.role) {
    params.set("role", filters.role);
  }
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/api/devices${query ? `?${query}` : ""}`);
  if (!response.ok) {
    throw new Error(`Failed to list devices (${response.status})`);
  }
  return (await response.json()) as DeviceDto[];
}

export async function provisionDeviceFamily(family: DeviceFamily): Promise<DeviceDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/provision?family=${encodeURIComponent(family)}`,
    { method: "POST" },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Failed to provision family (${response.status})`);
  }
  return (await response.json()) as DeviceDto[];
}
