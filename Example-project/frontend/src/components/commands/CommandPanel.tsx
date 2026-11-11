import { type FormEvent, useEffect, useState } from "react";

import {
  errorText,
  fetchCommands,
  fetchDevices,
  submitCommand,
  type CommandLogDto,
  type DeviceDto,
} from "../../services/api";

const ACTIONS = ["start_pump", "stop_pump", "set_light_level"] as const;

export function CommandPanel() {
  const [actuators, setActuators] = useState<DeviceDto[]>([]);
  const [history, setHistory] = useState<CommandLogDto[]>([]);
  const [levels, setLevels] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  async function reload() {
    const [devices, rows] = await Promise.all([
      fetchDevices({ role: "actuator" }),
      fetchCommands(),
    ]);
    setActuators(devices);
    setHistory(rows);
  }

  useEffect(() => {
    reload().catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Could not load controls");
    });
  }, []);

  async function onCommand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const deviceId = String(new FormData(form).get("device_id") ?? "");
    const commandType = String(new FormData(form).get("command_type") ?? "");
    const level = Number(levels[deviceId] ?? "1");
    const payload = commandType === "set_light_level" ? { level: Number.isFinite(level) ? level : 1 } : {};
    setPending(`${deviceId}:${commandType}`);
    setError(null);
    try {
      await submitCommand({ command_type: commandType, device_id: deviceId, payload });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Command failed");
    } finally {
      setPending(null);
      try {
        await reload();
      } catch (err: unknown) {
        setError(errorText(err));
      }
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        A button is available when that command is legal for the actuator&apos;s saved state.
        Changing the light level sends the number in the field. The history lists every accepted,
        failed, and rejected command.
      </p>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <ul className="space-y-3">
        {actuators.map((device) => {
          const allowed = new Set(device.allowed_commands ?? []);
          return (
            <li key={device.id} className="rounded-lg border border-slate-200 p-3">
              <p className="font-medium text-slate-800">{device.display_name}</p>
              <p className="text-sm text-slate-500">
                {device.device_type} · {device.state ?? "unknown"}
              </p>
              {device.device_type === "grow_light" ? (
                <label className="mt-2 block text-sm text-slate-600">
                  Level
                  <input
                    type="number"
                    value={levels[device.id] ?? "1"}
                    onChange={(event) =>
                      setLevels((current) => ({ ...current, [device.id]: event.target.value }))
                    }
                    className="ml-2 w-20 rounded border border-slate-300 px-2 py-1"
                  />
                </label>
              ) : null}
              <div className="mt-2 flex flex-wrap gap-2">
                {ACTIONS.map((action) => (
                  <form key={action} onSubmit={onCommand}>
                    <input type="hidden" name="device_id" value={device.id} />
                    <input type="hidden" name="command_type" value={action} />
                    <button
                      type="submit"
                      disabled={!allowed.has(action) || pending !== null}
                      className="rounded bg-emerald-700 px-3 py-1 text-sm text-white disabled:bg-slate-300"
                    >
                      {pending === `${device.id}:${action}` ? "Sending…" : action}
                    </button>
                  </form>
                ))}
              </div>
            </li>
          );
        })}
      </ul>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="text-slate-500">
            <th className="py-1 pr-2">When</th>
            <th className="py-1 pr-2">Command</th>
            <th className="py-1 pr-2">Status</th>
            <th className="py-1">Message</th>
          </tr>
        </thead>
        <tbody>
          {history.map((row) => (
            <tr key={row.id} className="border-t border-slate-100">
              <td className="py-1 pr-2">{new Date(row.created_at).toLocaleString()}</td>
              <td className="py-1 pr-2">{row.command_type}</td>
              <td className="py-1 pr-2">{row.status}</td>
              <td className="py-1">{row.error_message ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
