import { useCallback, useEffect, useState } from "react";

import {
  assignDeviceZone,
  fetchDevices,
  fetchLocationConfig,
  fetchLocations,
  fetchZoneDevices,
  provisionDeviceFamily,
  type DeviceDto,
  type DeviceFamily,
} from "../../services/api";
import { DeviceFamilySwitcher } from "./DeviceFamilySwitcher";
import { DeviceList, type ZoneGroup } from "./DeviceList";

type Props = {
  catalogVersion: number;
  onAssigned: () => void;
};

const FAMILIES = [
  {
    key: "simulation" as const,
    title: "Simulation",
    summary:
      "Provision adds one matching kit: Sim soil moisture sensor, Sim grow light sensor, Sim irrigation pump, and Sim grow light. The sensors use the simulation protocol.",
    example:
      "After one click the list shows those four devices. Read now on Sim soil moisture sensor stores a vwc reading. The pump and the grow light are actuators.",
  },
  {
    key: "edge" as const,
    title: "Edge",
    summary:
      "Provision adds the same four roles with Edge names and the mqtt protocol: Edge soil moisture sensor, Edge grow light sensor, Edge irrigation pump, and Edge grow light.",
    example:
      "Those sensors stay out of automatic sampling. Read now is refused until an MQTT payload is translated.",
  },
];

export function DeviceFamilyPanel({ catalogVersion, onAssigned }: Props) {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [zoneGroups, setZoneGroups] = useState<ZoneGroup[]>([]);
  const [zoneByDeviceId, setZoneByDeviceId] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assignError, setAssignError] = useState<string | null>(null);
  const [provisioning, setProvisioning] = useState(false);
  const [assigningId, setAssigningId] = useState<string | null>(null);

  const load = useCallback(async (selected: DeviceFamily) => {
    setLoading(true);
    setError(null);
    try {
      setDevices(await fetchDevices({ family: selected }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load devices");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadCatalog = useCallback(async () => {
    const summaries = await fetchLocations();
    const configs = await Promise.all(summaries.map((item) => fetchLocationConfig(item.id)));
    const groups: ZoneGroup[] = configs.map((config) => ({
      locationId: config.location.id,
      locationName: config.location.name,
      zones: config.zones.map((zone) => ({
        id: zone.id,
        name: zone.name,
        locationName: config.location.name,
      })),
    }));
    setZoneGroups(groups);
    const entries = await Promise.all(
      groups.flatMap((group) =>
        group.zones.map(async (zone) => {
          const assigned = await fetchZoneDevices(group.locationId, zone.id);
          return assigned.map((device) => [device.id, zone.id] as const);
        }),
      ),
    );
    setZoneByDeviceId(Object.fromEntries(entries.flat()));
  }, []);

  useEffect(() => {
    void load(family);
  }, [family, load]);

  useEffect(() => {
    void loadCatalog().catch((err: unknown) => {
      setAssignError(err instanceof Error ? err.message : "Failed to load zone assignments");
    });
  }, [catalogVersion, loadCatalog]);

  async function provision() {
    setProvisioning(true);
    setError(null);
    try {
      await provisionDeviceFamily(family);
      await load(family);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to provision kit");
    } finally {
      setProvisioning(false);
    }
  }

  async function assign(deviceId: string, zoneId: string | null) {
    setAssigningId(deviceId);
    setAssignError(null);
    try {
      await assignDeviceZone(deviceId, zoneId);
      await loadCatalog();
      onAssigned();
    } catch (err) {
      setAssignError(err instanceof Error ? err.message : "Failed to assign zone");
    } finally {
      setAssigningId(null);
    }
  }

  return (
    <div className="space-y-3">
      <DeviceFamilySwitcher family={family} onChange={setFamily} />
      <div className="grid gap-3 sm:grid-cols-2">
        {FAMILIES.map((item) => {
          const selected = item.key === family;
          return (
            <article
              key={item.key}
              className={
                selected
                  ? "rounded-md border border-emerald-600 bg-emerald-50 px-3 py-2 text-sm text-slate-700"
                  : "rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
              }
            >
              <h4 className="font-medium text-slate-800">{item.title}</h4>
              <p className="mt-1">{item.summary}</p>
              <p className="mt-1 text-slate-600">{item.example}</p>
            </article>
          );
        })}
      </div>
      <p className="text-sm text-slate-600">
        Each Provision adds another kit of four and leaves earlier kits in place. The switcher only changes
        which family is listed. Save a location in Configuration before assigning a zone. Each option is the
        location name and the zone name. Unassigned removes the device from every zone.
      </p>
      <button
        type="button"
        className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
        disabled={provisioning}
        onClick={() => void provision()}
      >
        {provisioning ? "Provisioning…" : `Provision ${family} kit`}
      </button>
      {zoneGroups.length > 0 ? (
        <p className="text-sm text-slate-500">
          Each option shows the location and the zone. Unassigned devices stay out of every zone list.
        </p>
      ) : (
        <p className="text-sm text-slate-500">Save a location in Configuration to assign devices to a zone.</p>
      )}
      {assignError ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{assignError}</p>
      ) : null}
      <DeviceList
        devices={devices}
        loading={loading}
        error={error}
        zoneGroups={zoneGroups.length > 0 ? zoneGroups : undefined}
        zoneByDeviceId={zoneByDeviceId}
        assigningId={assigningId}
        onAssign={zoneGroups.length > 0 ? (deviceId, zoneId) => void assign(deviceId, zoneId) : undefined}
      />
    </div>
  );
}
