import { useCallback, useEffect, useState } from "react";

import {
  fetchLocations,
  fetchOverview,
  type LocationOverview,
  type LocationSummary,
} from "../../services/api";

export function OverviewPanel() {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [locationId, setLocationId] = useState("");
  const [overview, setOverview] = useState<LocationOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchLocations()
      .then((items) => {
        if (cancelled) {
          return;
        }
        setLocations(items);
        setLocationId((current) => current || items[0]?.id || "");
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load locations");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadOverview = useCallback(async (id: string) => {
    if (!id) {
      setOverview(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setOverview(await fetchOverview(id));
    } catch (err) {
      setOverview(null);
      setError(err instanceof Error ? err.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadOverview(locationId);
  }, [locationId, loadOverview]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-2">
        <label className="block min-w-48 flex-1 text-sm text-slate-700">
          Location
          <select
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            value={locationId}
            onChange={(event) => setLocationId(event.target.value)}
          >
            {locations.length === 0 ? <option value="">No locations</option> : null}
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 disabled:opacity-50"
          disabled={loading || !locationId}
          onClick={() => void loadOverview(locationId)}
        >
          Refresh
        </button>
      </div>
      {error ? (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : null}
      {overview ? (
        <div className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <span className="font-medium text-slate-800">Assigned devices</span>
              <span className="mt-1 block">
                {overview.device_counts.sensor} sensors, {overview.device_counts.actuator} actuators
              </span>
            </p>
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <span className="font-medium text-slate-800">Strategy</span>
              <span className="mt-1 block">{overview.strategy_key ?? "No strategy saved"}</span>
              {overview.last_recommendation ? (
                <span className="mt-1 block text-slate-600">
                  {overview.last_recommendation.action} — {overview.last_recommendation.reason}
                </span>
              ) : (
                <span className="mt-1 block text-slate-500">No recommendation yet</span>
              )}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {overview.zones.map((zone) => (
              <article
                key={zone.id}
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
              >
                <h4 className="font-medium text-slate-800">{zone.name}</h4>
                <p className="mt-1 text-slate-500">
                  Moisture {zone.moisture_threshold_low}–{zone.moisture_threshold_high}
                </p>
                {zone.devices.length === 0 ? (
                  <p className="mt-2 text-slate-500">No assigned devices</p>
                ) : (
                  <ul className="mt-2 space-y-2">
                    {zone.devices.map((device) => {
                      const reading = zone.latest_readings.find(
                        (item) => item.device_id === device.id,
                      );
                      return (
                        <li key={device.id}>
                          <span className="font-medium">{device.display_name}</span>
                          <span className="text-slate-500">
                            {" "}
                            · {device.role} · {device.device_type}
                          </span>
                          {reading ? (
                            <span className="mt-1 block text-slate-600">
                              {reading.value} {reading.unit}
                              {reading.tracking_enabled ? "" : " · tracking off"}
                              {" · "}
                              every {reading.sampling_interval_seconds}s
                            </span>
                          ) : (
                            <span className="mt-1 block text-slate-500">No reading yet</span>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
