import { useCallback, useEffect, useState } from "react";

import {
  createSensor,
  fetchSensorReadings,
  fetchSensors,
  readSensor,
  updateSampling,
  type ReadingDto,
  type SensorDto,
} from "../../services/api";

// Phase 12 replaces this poll with a WebSocket push of reading.created.
const READING_POLL_MS = 5000;

export function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [readings, setReadings] = useState<Record<string, ReadingDto | null>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<string | null>(null);
  const [readingId, setReadingId] = useState<string | null>(null);

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

  const loadReadings = useCallback(async (items: SensorDto[]) => {
    const entries = await Promise.all(
      items.map(async (sensor) => {
        const latest = await fetchSensorReadings(sensor.id, 1);
        return [sensor.id, latest[0] ?? null] as const;
      }),
    );
    setReadings(Object.fromEntries(entries));
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (sensors.length === 0) {
      setReadings({});
      return;
    }
    void loadReadings(sensors).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load readings");
    });
    const timer = window.setInterval(() => {
      void loadReadings(sensors).catch(() => {
        /* keep the last stored value on a failed poll */
      });
    }, READING_POLL_MS);
    return () => window.clearInterval(timer);
  }, [sensors, loadReadings]);

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

  async function readNow(sensorId: string) {
    setReadingId(sensorId);
    setError(null);
    try {
      const reading = await readSensor(sensorId);
      setReadings((current) => ({ ...current, [sensorId]: reading }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to read sensor");
    } finally {
      setReadingId(null);
    }
  }

  async function saveSampling(sensor: SensorDto, interval: number, tracking: boolean) {
    setError(null);
    try {
      await updateSampling(sensor.id, interval, tracking);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update sampling");
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
            <SensorCard
              key={sensor.id}
              sensor={sensor}
              reading={readings[sensor.id] ?? null}
              readingNow={readingId === sensor.id}
              onRead={() => void readNow(sensor.id)}
              onSaveSampling={(interval, tracking) => void saveSampling(sensor, interval, tracking)}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function SensorCard({
  sensor,
  reading,
  readingNow,
  onRead,
  onSaveSampling,
}: {
  sensor: SensorDto;
  reading: ReadingDto | null;
  readingNow: boolean;
  onRead: () => void;
  onSaveSampling: (interval: number, tracking: boolean) => void;
}) {
  const [interval, setIntervalSeconds] = useState(String(sensor.sampling_interval_seconds));
  const [tracking, setTracking] = useState(sensor.tracking_enabled);

  useEffect(() => {
    setIntervalSeconds(String(sensor.sampling_interval_seconds));
    setTracking(sensor.tracking_enabled);
  }, [sensor.sampling_interval_seconds, sensor.tracking_enabled]);

  return (
    <li className="rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium text-slate-800">{sensor.display_name}</p>
        {reading ? (
          <span className="rounded-full bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-800 ring-1 ring-sky-200">
            {reading.source}
          </span>
        ) : null}
      </div>
      <p className="text-slate-500">{sensor.device_type}</p>
      {sensor.zone_name ? <p className="text-slate-600">Zone {sensor.zone_name}</p> : null}
      <p className="mt-1 text-slate-800">
        {reading ? `${reading.value} ${reading.unit}` : "No stored reading yet."}
      </p>
      <button
        type="button"
        className="mt-2 rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
        disabled={readingNow}
        onClick={onRead}
      >
        {readingNow ? "Reading…" : "Read now"}
      </button>
      <div className="mt-2 flex flex-wrap items-end gap-3">
        <label className="block text-xs text-slate-600">
          Interval (seconds)
          <input
            className="mt-1 w-24 rounded-md border border-slate-200 bg-white px-2 py-1 text-sm text-slate-800"
            inputMode="numeric"
            value={interval}
            onChange={(event) => setIntervalSeconds(event.target.value)}
          />
        </label>
        <label className="flex items-center gap-2 text-xs text-slate-600">
          <input
            type="checkbox"
            checked={tracking}
            onChange={(event) => setTracking(event.target.checked)}
          />
          Tracking
        </label>
        <button
          type="button"
          className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          onClick={() => onSaveSampling(Number(interval), tracking)}
        >
          Save sampling
        </button>
      </div>
    </li>
  );
}
