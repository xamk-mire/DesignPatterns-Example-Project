import { useCallback, useEffect, useState } from "react";

import {
  fetchDevices,
  provisionDeviceFamily,
  type DeviceDto,
  type DeviceFamily,
} from "../../services/api";
import { DeviceFamilySwitcher } from "./DeviceFamilySwitcher";
import { DeviceList } from "./DeviceList";

export function DeviceFamilyPanel() {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [provisioning, setProvisioning] = useState(false);

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

  useEffect(() => {
    void load(family);
  }, [family, load]);

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
      <DeviceList devices={devices} loading={loading} error={error} />
    </div>
  );
}
