import { NavLink, Outlet } from "react-router-dom";

import { HealthStatus } from "./HealthStatus";

const navClass = ({ isActive }: { isActive: boolean }) =>
  [
    "rounded-md px-3 py-1.5 text-sm font-medium",
    isActive ? "bg-emerald-700 text-white" : "text-emerald-50 hover:bg-emerald-800",
  ].join(" ");

export function AppLayout() {
  return (
    <div className="min-h-screen">
      <header className="bg-emerald-900 text-white shadow">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <h1 className="text-xl font-semibold tracking-tight">Smart Greenhouse</h1>
          <nav className="flex items-center gap-2">
            <NavLink to="/" className={navClass} end>
              Home
            </NavLink>
            <NavLink to="/dashboard" className={navClass}>
              Dashboard
            </NavLink>
          </nav>
          <HealthStatus />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
