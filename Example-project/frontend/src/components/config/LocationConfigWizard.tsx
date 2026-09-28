import { useCallback, useEffect, useState } from "react";

import {
  addZone,
  createLocationConfig,
  deleteLocation,
  deleteZone,
  fetchLocationConfig,
  fetchLocations,
  fetchZoneDevices,
  updateZone,
  type DeviceDto,
  type LocationConfigDto,
  type LocationSummary,
  type ZoneDto,
} from "../../services/api";

type ZoneDraft = {
  name: string;
  low: string;
  high: string;
  watering: string;
};

function emptyZone(): ZoneDraft {
  return { name: "", low: "0.2", high: "0.45", watering: "08:00" };
}

function draftFromZone(zone: ZoneDto): ZoneDraft {
  const watering = zone.schedule.watering;
  return {
    name: zone.name,
    low: String(zone.moisture_threshold_low),
    high: String(zone.moisture_threshold_high),
    watering: typeof watering === "string" ? watering : "08:00",
  };
}

function validate(locationName: string, zones: ZoneDraft[]): string | null {
  if (!locationName.trim()) {
    return "Location name is required.";
  }
  if (zones.length === 0) {
    return "Add at least one zone.";
  }
  for (const [index, zone] of zones.entries()) {
    const message = validateZone(zone, `Zone ${index + 1}`);
    if (message) {
      return message;
    }
  }
  return null;
}

function validateZone(zone: ZoneDraft, label: string): string | null {
  if (!zone.name.trim()) {
    return `${label} needs a name.`;
  }
  const low = Number(zone.low);
  const high = Number(zone.high);
  if (!Number.isFinite(low) || !Number.isFinite(high)) {
    return `${label} thresholds must be numbers.`;
  }
  if (low < 0 || low > 1 || high < 0 || high > 1) {
    return `${label} thresholds must be between 0 and 1.`;
  }
  if (low >= high) {
    return `${label} low threshold must be strictly less than high.`;
  }
  return null;
}

function toZoneInput(zone: ZoneDraft) {
  return {
    name: zone.name.trim(),
    moisture_threshold_low: Number(zone.low),
    moisture_threshold_high: Number(zone.high),
    schedule: zone.watering ? { watering: zone.watering } : {},
  };
}

export function LocationConfigWizard({
  onSaved,
  onLocationsChanged,
  assignmentVersion,
}: {
  onSaved: (config: LocationConfigDto | null) => void;
  onLocationsChanged: () => void;
  assignmentVersion: number;
}) {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [saved, setSaved] = useState<LocationConfigDto | null>(null);
  const [zoneDrafts, setZoneDrafts] = useState<Record<string, ZoneDraft>>({});
  const [zoneDevices, setZoneDevices] = useState<Record<string, DeviceDto[]>>({});
  const [locationName, setLocationName] = useState("");
  const [zones, setZones] = useState<ZoneDraft[]>([emptyZone()]);
  const [newZone, setNewZone] = useState<ZoneDraft>(emptyZone());
  const [formError, setFormError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const applyConfig = useCallback(
    (config: LocationConfigDto | null) => {
      setSaved(config);
      setSelectedId(config?.location.id ?? null);
      setZoneDrafts(
        Object.fromEntries((config?.zones ?? []).map((zone) => [zone.id, draftFromZone(zone)])),
      );
      onSaved(config);
    },
    [onSaved],
  );

  const refreshList = useCallback(async () => {
    setLocations(await fetchLocations());
  }, []);

  useEffect(() => {
    void refreshList().catch((err: unknown) => {
      setApiError(err instanceof Error ? err.message : "Failed to list locations");
    });
  }, [refreshList]);

  useEffect(() => {
    if (!saved) {
      setZoneDevices({});
      return;
    }
    let cancelled = false;
    void Promise.all(
      saved.zones.map(async (zone) => {
        const devices = await fetchZoneDevices(saved.location.id, zone.id);
        return [zone.id, devices] as const;
      }),
    )
      .then((entries) => {
        if (!cancelled) {
          setZoneDevices(Object.fromEntries(entries));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setApiError("Failed to load devices for the saved zones");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [saved, assignmentVersion]);

  async function selectLocation(locationId: string) {
    setApiError(null);
    try {
      applyConfig(await fetchLocationConfig(locationId));
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Failed to load location");
    }
  }

  async function submit() {
    const message = validate(locationName, zones);
    setFormError(message);
    setApiError(null);
    if (message) {
      return;
    }
    setSaving(true);
    try {
      const result = await createLocationConfig({
        location_name: locationName.trim(),
        zones: zones.map(toZoneInput),
      });
      await refreshList();
      applyConfig(result);
      onLocationsChanged();
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Failed to save location config");
    } finally {
      setSaving(false);
    }
  }

  async function removeLocation(locationId: string) {
    const location = locations.find((item) => item.id === locationId);
    if (!window.confirm(`Delete ${location?.name ?? "this location"}? Its zones will be removed.`)) {
      return;
    }
    setApiError(null);
    try {
      await deleteLocation(locationId);
      await refreshList();
      if (selectedId === locationId) {
        applyConfig(null);
      }
      onLocationsChanged();
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Failed to delete location");
    }
  }

  async function createZone() {
    if (!saved) {
      return;
    }
    const message = validateZone(newZone, "New zone");
    setFormError(message);
    if (message) {
      return;
    }
    setApiError(null);
    try {
      await addZone(saved.location.id, toZoneInput(newZone));
      setNewZone(emptyZone());
      applyConfig(await fetchLocationConfig(saved.location.id));
      onLocationsChanged();
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Failed to add zone");
    }
  }

  async function saveZone(zoneId: string) {
    if (!saved) {
      return;
    }
    const draft = zoneDrafts[zoneId];
    if (!draft) {
      return;
    }
    const message = validateZone(draft, draft.name || "Zone");
    setFormError(message);
    if (message) {
      return;
    }
    setApiError(null);
    try {
      await updateZone(saved.location.id, zoneId, toZoneInput(draft));
      applyConfig(await fetchLocationConfig(saved.location.id));
      onLocationsChanged();
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Failed to update zone");
    }
  }

  async function removeZone(zoneId: string) {
    if (!saved) {
      return;
    }
    if (saved.zones.length <= 1) {
      setApiError("A location must keep at least one zone");
      return;
    }
    if (!window.confirm("Delete this zone? Devices in it will be unassigned.")) {
      return;
    }
    setApiError(null);
    try {
      await deleteZone(saved.location.id, zoneId);
      applyConfig(await fetchLocationConfig(saved.location.id));
      onLocationsChanged();
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Failed to delete zone");
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-sm font-medium text-slate-800">Saved locations</p>
        {locations.length === 0 ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">No locations yet.</p>
        ) : (
          <ul className="space-y-2">
            {locations.map((location) => (
              <li key={location.id} className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  className={
                    location.id === selectedId
                      ? "rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white"
                      : "rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  }
                  onClick={() => void selectLocation(location.id)}
                >
                  {location.name}
                </button>
                <button
                  type="button"
                  className="text-sm text-slate-500 hover:text-slate-800"
                  onClick={() => void removeLocation(location.id)}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <label className="block text-sm text-slate-700">
        New location name
        <input
          className="mt-1 w-full rounded-md border border-slate-200 px-3 py-1.5 text-sm"
          value={locationName}
          onChange={(event) => setLocationName(event.target.value)}
          placeholder="Lab Site A"
        />
      </label>

      <div className="space-y-3">
        {zones.map((zone, index) => (
          <div key={index} className="rounded-md border border-slate-100 bg-slate-50 p-3">
            <div className="mb-2 flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-slate-800">New zone {index + 1}</p>
              {zones.length > 1 ? (
                <button
                  type="button"
                  className="text-sm text-slate-500 hover:text-slate-800"
                  onClick={() => setZones((current) => current.filter((_, i) => i !== index))}
                >
                  Remove
                </button>
              ) : null}
            </div>
            <ZoneFields
              zone={zone}
              onChange={(patch) =>
                setZones((current) => current.map((item, i) => (i === index ? { ...item, ...patch } : item)))
              }
            />
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          onClick={() => setZones((current) => [...current, emptyZone()])}
        >
          Add zone
        </button>
        <button
          type="button"
          className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
          disabled={saving}
          onClick={() => void submit()}
        >
          {saving ? "Saving…" : "Save location"}
        </button>
      </div>

      {formError ? (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">{formError}</p>
      ) : null}
      {apiError ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{apiError}</p>
      ) : null}

      {saved ? (
        <div className="space-y-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-950">
          <p className="font-medium">Selected {saved.location.name}</p>
          <p className="text-emerald-900">Location id {saved.location.id}</p>
          <ul className="space-y-3">
            {saved.zones.map((zone) => {
              const draft = zoneDrafts[zone.id] ?? draftFromZone(zone);
              return (
                <li key={zone.id} className="rounded-md bg-white p-3 text-slate-800">
                  <ZoneFields
                    zone={draft}
                    onChange={(patch) =>
                      setZoneDrafts((current) => ({ ...current, [zone.id]: { ...draft, ...patch } }))
                    }
                  />
                  <p className="mt-2 text-xs text-slate-500">location_id {zone.location_id}</p>
                  <p className="mt-1 text-sm text-slate-600">
                    {(zoneDevices[zone.id] ?? []).length === 0
                      ? "No devices in this zone."
                      : (zoneDevices[zone.id] ?? []).map((device) => device.display_name).join(", ")}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-800"
                      onClick={() => void saveZone(zone.id)}
                    >
                      Save zone
                    </button>
                    <button
                      type="button"
                      className="text-sm text-slate-500 hover:text-slate-800 disabled:opacity-40"
                      disabled={saved.zones.length <= 1}
                      onClick={() => void removeZone(zone.id)}
                    >
                      Delete zone
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
          <div className="rounded-md bg-white p-3 text-slate-800">
            <p className="mb-2 text-sm font-medium">Add a zone</p>
            <ZoneFields zone={newZone} onChange={(patch) => setNewZone((current) => ({ ...current, ...patch }))} />
            <button
              type="button"
              className="mt-2 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              onClick={() => void createZone()}
            >
              Add zone to {saved.location.name}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ZoneFields({
  zone,
  onChange,
}: {
  zone: ZoneDraft;
  onChange: (patch: Partial<ZoneDraft>) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      <label className="block text-sm text-slate-700 sm:col-span-2">
        Name
        <input
          className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm"
          value={zone.name}
          onChange={(event) => onChange({ name: event.target.value })}
          placeholder="Bench 1"
        />
      </label>
      <label className="block text-sm text-slate-700">
        Moisture low (0–1)
        <input
          className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm"
          inputMode="decimal"
          value={zone.low}
          onChange={(event) => onChange({ low: event.target.value })}
        />
      </label>
      <label className="block text-sm text-slate-700">
        Moisture high (0–1)
        <input
          className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm"
          inputMode="decimal"
          value={zone.high}
          onChange={(event) => onChange({ high: event.target.value })}
        />
      </label>
      <label className="block text-sm text-slate-700 sm:col-span-2">
        Watering time
        <input
          type="time"
          className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm"
          value={zone.watering}
          onChange={(event) => onChange({ watering: event.target.value })}
        />
      </label>
    </div>
  );
}
