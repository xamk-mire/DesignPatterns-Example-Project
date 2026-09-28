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
