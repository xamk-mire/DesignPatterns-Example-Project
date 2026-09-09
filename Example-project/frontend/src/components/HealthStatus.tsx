import { useEffect, useState } from "react";

import { fetchHealth, type HealthResponse } from "../services/api";

type BadgeState =
  | { kind: "loading" }
  | { kind: "ok"; health: HealthResponse }
  | { kind: "degraded"; health: HealthResponse }
  | { kind: "error" };

function ringClass(state: BadgeState): string {
  if (state.kind === "ok") {
    return "border-emerald-500 bg-emerald-50 text-emerald-800";
  }
  if (state.kind === "degraded") {
    return "border-amber-500 bg-amber-50 text-amber-800";
  }
  if (state.kind === "error") {
    return "border-red-500 bg-red-50 text-red-800";
  }
  return "border-slate-300 bg-slate-100 text-slate-600";
}

function label(state: BadgeState): string {
  if (state.kind === "loading") {
    return "Checking…";
  }
  if (state.kind === "error") {
    return "API: unreachable";
  }
  return `API: ${state.health.status} · DB: ${state.health.db}`;
}

export function HealthStatus() {
  const [state, setState] = useState<BadgeState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const health = await fetchHealth();
        if (cancelled) {
          return;
        }
        const ok = health.status === "ok" && health.db === "ok";
        setState({ kind: ok ? "ok" : "degraded", health });
      } catch {
        if (!cancelled) {
          setState({ kind: "error" });
        }
      }
    }

    void load();
    const interval = window.setInterval(() => {
      void load();
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${ringClass(state)}`}
    >
      {label(state)}
    </span>
  );
}
