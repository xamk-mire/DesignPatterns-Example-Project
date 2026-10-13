import { useEffect, useState } from "react";

import {
  evaluateStrategy,
  fetchLocations,
  saveStrategy,
  type EvaluationDto,
  type LocationSummary,
} from "../../services/api";

const STRATEGIES = [
  {
    key: "conservative",
    summary:
      "Irrigates a zone only when the latest moisture is strictly below that zone’s low threshold.",
    example:
      "For a zone with low 0.20 and high 0.45, moisture 0.30 waits because 0.30 is above 0.20. Moisture 0.15 irrigates.",
  },
  {
    key: "aggressive",
    summary:
      "Irrigates when the latest moisture is below the midpoint of the zone’s low and high thresholds.",
    example:
      "For the same zone the midpoint is 0.33, so moisture 0.30 irrigates. Moisture 0.40 waits.",
  },
] as const;

type StrategyKey = (typeof STRATEGIES)[number]["key"];

export function StrategyPanel() {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [locationId, setLocationId] = useState("");
  const [strategyKey, setStrategyKey] = useState<StrategyKey>("conservative");
  const [result, setResult] = useState<EvaluationDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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

  async function onSave() {
    if (!locationId) {
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await saveStrategy(locationId, strategyKey);
      setNotice(`Saved ${strategyKey}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save strategy");
    } finally {
      setBusy(false);
    }
  }

  async function onEvaluate() {
    if (!locationId) {
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    setResult(null);
    try {
      setResult(await evaluateStrategy(locationId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to evaluate");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm text-slate-700">
        Location
        <select
          className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          value={locationId}
          onChange={(event) => {
            setLocationId(event.target.value);
            setResult(null);
            setNotice(null);
          }}
        >
          {locations.length === 0 ? <option value="">No locations</option> : null}
          {locations.map((location) => (
            <option key={location.id} value={location.id}>
              {location.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm text-slate-700">
        Strategy
        <select
          className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          value={strategyKey}
          onChange={(event) =>
            setStrategyKey(event.target.value as StrategyKey)
          }
        >
          {STRATEGIES.map((strategy) => (
            <option key={strategy.key} value={strategy.key}>
              {strategy.key}
            </option>
          ))}
        </select>
      </label>
      <div className="grid gap-3 sm:grid-cols-2">
        {STRATEGIES.map((strategy) => {
          const selected = strategy.key === strategyKey;
          return (
            <article
              key={strategy.key}
              className={
                selected
                  ? "rounded-md border border-emerald-600 bg-emerald-50 px-3 py-2 text-sm text-slate-700"
                  : "rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
              }
            >
              <h4 className="font-medium text-slate-800">{strategy.key}</h4>
              <p className="mt-1">{strategy.summary}</p>
              <p className="mt-1 text-slate-600">{strategy.example}</p>
            </article>
          );
        })}
      </div>
      <p className="text-sm text-slate-600">
        Both strategies wait, with the reason “no moisture sensor in this zone”, when the zone has
        no assigned moisture sensor.
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded-md bg-emerald-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          disabled={busy || !locationId}
          onClick={() => void onSave()}
        >
          Save
        </button>
        <button
          type="button"
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 disabled:opacity-50"
          disabled={busy || !locationId}
          onClick={() => void onEvaluate()}
        >
          Evaluate
        </button>
      </div>
      {error ? (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : null}
      {notice ? (
        <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{notice}</p>
      ) : null}
      {result ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <span className="font-medium">{result.action}</span>
          {" — "}
          {result.reason}
          <span className="mt-1 block text-slate-500">Strategy: {result.strategy_key}</span>
        </p>
      ) : null}
    </div>
  );
}
