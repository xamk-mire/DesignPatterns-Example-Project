import { useCallback, useEffect, useState } from "react";

import { createSensor, fetchSensors, type SensorDto } from "../../services/api";

export function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSensors(await fetchSensors());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sensors");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function add(type: "moisture" | "light") {
    setCreating(type);
    setError(null);
    try {
      await createSensor(type);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create sensor");
    } finally {
      setCreating(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
          disabled={creating !== null}
          onClick={() => void add("moisture")}
        >
          {creating === "moisture" ? "Adding…" : "Add moisture"}
        </button>
        <button
          type="button"
          className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
          disabled={creating !== null}
          onClick={() => void add("light")}
        >
          {creating === "light" ? "Adding…" : "Add light"}
        </button>
      </div>

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>
      ) : null}

      {loading ? (
        <p className="text-sm text-slate-500">Loading sensors…</p>
      ) : sensors.length === 0 ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
          No sensors yet. Add a moisture or light sensor to persist one in PostgreSQL.
        </p>
      ) : (
        <ul className="space-y-2">
          {sensors.map((sensor) => (
            <li key={sensor.id} className="rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
              <p className="font-medium text-slate-800">{sensor.display_name}</p>
              <p className="text-slate-500">{sensor.device_type}</p>
              <pre className="mt-1 overflow-x-auto text-xs text-slate-600">
                {JSON.stringify(sensor.default_config)}
              </pre>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
