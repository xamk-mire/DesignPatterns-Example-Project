import { DeviceFamilyPanel } from '../components/devices/DeviceFamilyPanel';
import { SensorList } from '../features/sensors/SensorList';

const placeholders = [
  { id: 'configuration', title: 'Configuration', note: 'Phase 4 — Builder' },
  { id: 'automation', title: 'Automation', note: 'Phase 6 — Strategy' },
  { id: 'overview', title: 'Overview', note: 'Phase 7 — Facade' },
  { id: 'controls', title: 'Controls', note: 'Phase 10 — Command' },
  { id: 'events', title: 'Events', note: 'Phase 11 — Observer' },
] as const;

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-emerald-700">Dashboard</h2>
        <p className="mt-1 text-slate-600">
          Sensors use Factory Method. Device kits use Abstract Factory
          (simulation vs edge). Other sections stay placeholders.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <section
          id="sensors"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Sensors</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">
            Phase 2 — Factory Method
          </p>
          <SensorList />
        </section>
        <section
          id="devices"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Devices</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">
            Phase 3 — Abstract Factory
          </p>
          <DeviceFamilyPanel />
        </section>
        {placeholders.map((section) => (
          <section
            key={section.id}
            id={section.id}
            className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <h3 className="text-lg font-semibold text-slate-800">
              {section.title}
            </h3>
            <p className="mt-2 text-sm text-slate-500">{section.note}</p>
            <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-400">
              Coming in a later phase.
            </p>
          </section>
        ))}
      </div>
    </div>
  );
}
