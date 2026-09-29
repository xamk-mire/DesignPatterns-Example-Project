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
  sampling_interval_seconds: number;
  tracking_enabled: boolean;
  zone_name: string | null;
};

export type ReadingDto = {
  device_id: string;
  value: number;
  unit: string;
  source: string;
  recorded_at: string;
};

export async function fetchSensors(): Promise<SensorDto[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`);
  if (!response.ok) {
    throw new Error(`Failed to list sensors (${response.status})`);
  }
  return (await response.json()) as SensorDto[];
}

export async function readSensor(sensorId: string): Promise<ReadingDto> {
  const response = await fetch(`${API_BASE_URL}/api/sensors/${sensorId}/read`, { method: "POST" });
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to read sensor (${response.status})`));
  }
  return (await response.json()) as ReadingDto;
}

export async function fetchSensorReadings(sensorId: string, limit = 1): Promise<ReadingDto[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors/${sensorId}/readings?limit=${limit}`);
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to load readings (${response.status})`));
  }
  return (await response.json()) as ReadingDto[];
}

export async function updateSampling(
  deviceId: string,
  samplingIntervalSeconds: number,
  trackingEnabled: boolean,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/sampling`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sampling_interval_seconds: samplingIntervalSeconds,
      tracking_enabled: trackingEnabled,
    }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to update sampling (${response.status})`));
  }
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

export type ZoneInput = {
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule?: Record<string, unknown>;
};

export type BuildLocationConfigRequest = {
  location_name: string;
  zones: ZoneInput[];
};

export type LocationSummary = { id: string; name: string };

export type ZoneDto = {
  id: string;
  location_id: string;
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule: Record<string, unknown>;
};

export type LocationConfigDto = {
  location: LocationSummary;
  zones: ZoneDto[];
};

export async function createLocationConfig(
  body: BuildLocationConfigRequest,
): Promise<LocationConfigDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let message = `Failed to save location config (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      /* keep the status message */
    }
    throw new Error(message);
  }
  return (await response.json()) as LocationConfigDto;
}

async function errorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    /* keep the fallback */
  }
  return fallback;
}

export async function fetchLocations(): Promise<LocationSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/locations`);
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to list locations (${response.status})`));
  }
  return (await response.json()) as LocationSummary[];
}

export async function fetchLocationConfig(locationId: string): Promise<LocationConfigDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/config`);
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to load location (${response.status})`));
  }
  return (await response.json()) as LocationConfigDto;
}

export async function deleteLocation(locationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to delete location (${response.status})`));
  }
}

export async function addZone(locationId: string, zone: ZoneInput): Promise<ZoneDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/zones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(zone),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to add zone (${response.status})`));
  }
  return (await response.json()) as ZoneDto;
}

export async function updateZone(locationId: string, zoneId: string, zone: ZoneInput): Promise<ZoneDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(zone),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to update zone (${response.status})`));
  }
  return (await response.json()) as ZoneDto;
}

export async function deleteZone(locationId: string, zoneId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Failed to delete zone (${response.status})`));
  }
}

export async function fetchZoneDevices(locationId: string, zoneId: string): Promise<DeviceDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}/devices`,
  );
  if (!response.ok) {
    throw new Error(`Failed to list zone devices (${response.status})`);
  }
  return (await response.json()) as DeviceDto[];
}

export async function assignDeviceZone(deviceId: string, zoneId: string | null): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/zone`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ zone_id: zoneId }),
  });
  if (!response.ok) {
    let message = `Failed to assign zone (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      /* keep the status message */
    }
    throw new Error(message);
  }
}
