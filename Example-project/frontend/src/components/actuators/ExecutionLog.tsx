import { useCallback, useEffect, useState } from "react";

import {
  applyActuator,
  fetchDevices,
  fetchExecutions,
  type DeviceDto,
  type ExecutionDto,
} from "../../services/api";

export function ExecutionLog() {
  const [actuators, setActuators] = useState<DeviceDto[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [command, setCommand] = useState("start_pump");
  const [rows, setRows] = useState<ExecutionDto[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [devices, executions] = await Promise.all([
      fetchDevices({ role: "actuator" }),
      fetchExecutions(),
    ]);
    setActuators(devices);
    setDeviceId((current) => current || devices[0]?.id || "");
    setRows(executions);
  }, []);

  useEffect(() => {
    void load().catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load executions");
    });
  }, [load]);

  async function onApply() {
    if (!deviceId || !command.trim()) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await applyActuator(deviceId, command.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply command");
    } finally {
      try {
        setRows(await fetchExecutions());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load executions");
      }
      setBusy(false);
    }
  }

  const names = Object.fromEntries(actuators.map((device) => [device.id, device.display_name]));

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <article className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <h4 className="font-medium text-slate-800">Successful apply</h4>
          <p className="mt-1">
            Apply sends the command through logging, then max-run-time, then the simulation adapter.
            The Policies column lists those wrapper names, not the command text.
          </p>
          <p className="mt-1 text-slate-600">
            Any command succeeds while the actuator has not been running for 30 minutes. The message
            stays empty. Example: command start_pump on an idle pump records success and logging.
          </p>
        </article>
        <article className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <h4 className="font-medium text-slate-800">Blocked apply</h4>
          <p className="mt-1">
            The same command fails after the device card has been running for 30 minutes. Max-run-time
            stops the call before the simulation adapter.
          </p>
          <p className="mt-1 text-slate-600">
            The result is failed, the message is Max run time exceeded, and the policies are maxRunTime,
            logging.
          </p>
        </article>
      </div>
      <div className="flex flex-wrap items-end gap-2">
        <label className="block min-w-48 flex-1 text-sm text-slate-700">
          Actuator
          <select
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            value={deviceId}
            onChange={(event) => setDeviceId(event.target.value)}
          >
            {actuators.length === 0 ? <option value="">No actuators</option> : null}
            {actuators.map((device) => (
              <option key={device.id} value={device.id}>
                {device.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="block min-w-40 text-sm text-slate-700">
          Command
          <input
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            value={command}
            onChange={(event) => setCommand(event.target.value)}
          />
        </label>
        <button
          type="button"
          className="rounded-md bg-emerald-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          disabled={busy || !deviceId}
          onClick={() => void onApply()}
        >
          Apply
        </button>
        <button
          type="button"
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 disabled:opacity-50"
          disabled={busy}
          onClick={() =>
            void load().catch((err: unknown) => {
              setError(err instanceof Error ? err.message : "Failed to load executions");
            })
          }
        >
          Refresh
        </button>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {rows.length === 0 ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">No executions yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="px-2 py-2 font-medium">Time</th>
                <th className="px-2 py-2 font-medium">Device</th>
                <th className="px-2 py-2 font-medium">Result</th>
                <th className="px-2 py-2 font-medium">Policies</th>
                <th className="px-2 py-2 font-medium">Message</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100">
                  <td className="px-2 py-2 whitespace-nowrap">{new Date(row.created_at).toLocaleString()}</td>
                  <td className="px-2 py-2">{names[row.device_id] ?? row.device_id}</td>
                  <td className="px-2 py-2">
                    <span
                      className={
                        row.success
                          ? "rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800 ring-1 ring-emerald-200"
                          : "rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-800 ring-1 ring-red-200"
                      }
                    >
                      {row.success ? "success" : "failed"}
                    </span>
                  </td>
                  <td className="px-2 py-2">{row.policy_applied.join(", ")}</td>
                  <td className="px-2 py-2">{row.message ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
