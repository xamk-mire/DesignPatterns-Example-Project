import type { DeviceDto } from "../../services/api";

type Props = {
  devices: DeviceDto[];
  loading: boolean;
  error: string | null;
};

function roleBadge(role: string): string {
  return role === "actuator"
    ? "bg-amber-50 text-amber-800 ring-amber-200"
    : "bg-sky-50 text-sky-800 ring-sky-200";
}

function familyBadge(family: string): string {
  return family === "edge"
    ? "bg-violet-50 text-violet-800 ring-violet-200"
    : "bg-emerald-50 text-emerald-800 ring-emerald-200";
}

export function DeviceList({ devices, loading, error }: Props) {
  if (error) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>
    );
  }
  if (loading) {
    return <p className="text-sm text-slate-500">Loading devices…</p>;
  }
  if (devices.length === 0) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
        No devices in this family yet. Provision a kit to persist four matching devices.
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {devices.map((device) => (
        <li key={device.id} className="rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-slate-800">{device.display_name}</p>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${roleBadge(device.role)}`}>
              {device.role}
            </span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${familyBadge(device.device_family)}`}
            >
              {device.device_family}
            </span>
          </div>
          <p className="mt-1 text-slate-500">{device.device_type}</p>
        </li>
      ))}
    </ul>
  );
}
