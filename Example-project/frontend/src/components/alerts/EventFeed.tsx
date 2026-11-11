import { useEffect, useState } from "react";

import {
  fetchAlerts,
  fetchLocationConfig,
  fetchLocations,
  type AlertDto,
  type LocationSummary,
  type ZoneDto,
} from "../../services/api";

const POLL_MS = 5000;

export function EventFeed() {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [zones, setZones] = useState<ZoneDto[]>([]);
  const [locationId, setLocationId] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [alerts, setAlerts] = useState<AlertDto[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLocations()
      .then(setLocations)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Could not load locations");
      });
  }, []);

  useEffect(() => {
    if (!locationId) {
      setZones([]);
      setZoneId("");
      return;
    }
    fetchLocationConfig(locationId)
      .then((config) => setZones(config.zones))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Could not load zones");
      });
  }, [locationId]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const rows = await fetchAlerts({
          locationId: locationId || undefined,
          zoneId: zoneId || undefined,
        });
        if (!cancelled) {
          setAlerts(rows);
          setError(null);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load alerts");
        }
      }
    }

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [locationId, zoneId]);

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">
        Active alerts refresh every 5 seconds. Choose a location and a zone to narrow the feed.
      </p>
      <div className="flex flex-wrap gap-3">
        <label className="text-sm text-slate-600">
          Location
          <select
            value={locationId}
            onChange={(event) => {
              setLocationId(event.target.value);
              setZoneId("");
            }}
            className="ml-2 rounded border border-slate-300 px-2 py-1"
          >
            <option value="">All locations</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-600">
          Zone
          <select
            value={zoneId}
            onChange={(event) => setZoneId(event.target.value)}
            className="ml-2 rounded border border-slate-300 px-2 py-1"
          >
            <option value="">All zones</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      {alerts.length === 0 ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">No active alerts.</p>
      ) : (
        <ul className="space-y-2">
          {alerts.map((alert) => (
            <li key={alert.id} className="rounded-lg border border-slate-200 px-3 py-2">
              <p className="text-sm font-medium text-slate-800">{alert.message}</p>
              <p className="text-xs text-slate-500">
                <span
                  className={
                    alert.severity === "critical"
                      ? "text-red-700"
                      : alert.severity === "warning"
                        ? "text-amber-700"
                        : "text-slate-600"
                  }
                >
                  {alert.severity}
                </span>
                {" · "}
                {alert.event_type}
                {" · "}
                {new Date(alert.created_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
