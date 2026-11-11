import { useState } from 'react';

import { EventFeed } from '../components/alerts/EventFeed';
import { ExecutionLog } from '../components/actuators/ExecutionLog';
import { CommandPanel } from '../components/commands/CommandPanel';
import { StrategyPanel } from '../components/automation/StrategyPanel';
import { LocationConfigWizard } from '../components/config/LocationConfigWizard';
import { DeviceFamilyPanel } from '../components/devices/DeviceFamilyPanel';
import { OverviewPanel } from '../components/overview/OverviewPanel';
import { SensorList } from '../features/sensors/SensorList';

export function DashboardPage() {
  const [assignmentVersion, setAssignmentVersion] = useState(0);
  const [catalogVersion, setCatalogVersion] = useState(0);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-emerald-700">Dashboard</h2>
        <p className="mt-1 text-slate-600">
          Sensors use Factory Method. Device kits use Abstract Factory.
          Location configuration uses Builder. Irrigation uses Strategy.
          The location summary uses Facade. Actuator attempts use Decorator.
          Controls use Command. Alerts use Observer.
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
          <DeviceFamilyPanel
            catalogVersion={catalogVersion}
            onAssigned={() => setAssignmentVersion((version) => version + 1)}
          />
        </section>
        <section
          id="configuration"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Configuration</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">Phase 4 — Builder</p>
          <LocationConfigWizard
            assignmentVersion={assignmentVersion}
            onSaved={() => undefined}
            onLocationsChanged={() => setCatalogVersion((version) => version + 1)}
          />
        </section>
        <section
          id="automation"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Automation</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">Phase 6 — Strategy</p>
          <StrategyPanel />
        </section>
        <section
          id="overview"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Overview</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">Phase 7 — Facade</p>
          <OverviewPanel />
        </section>
        <section
          id="executions"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Executions</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">Phase 9 — Decorator</p>
          <ExecutionLog />
        </section>
        <section
          id="controls"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Controls</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">Phase 10 — Command</p>
          <CommandPanel />
        </section>
        <section
          id="events"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:col-span-3"
        >
          <h3 className="text-lg font-semibold text-slate-800">Events</h3>
          <p className="mt-1 mb-3 text-sm text-slate-500">Phase 11 — Observer</p>
          <EventFeed />
        </section>
      </div>
    </div>
  );
}
