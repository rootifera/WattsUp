import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChevronDown,
  Copy,
  KeyRound,
  Plus,
  Server,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { useState, type FormEvent } from "react";

import { shutdownApi, type DeviceInput } from "../api/shutdown";

const initialDevice: DeviceInput = {
  name: "",
  host: "",
  port: 22,
  username: "wattsup",
  enabled: false,
  use_sudo: true,
  mains_state: "on_battery",
  battery_state: "discharging",
  battery_threshold: 30,
  custom_command: null,
};

const inputClass =
  "rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-300 outline-none placeholder:text-slate-600 focus:border-cyan-900";
const sudoersRule =
  "wattsup ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff, /usr/sbin/shutdown, /usr/sbin/poweroff";

const buildSetupScript = (publicKey: string) => `#!/usr/bin/env bash
set -euo pipefail

if [[ "\${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash setup-wattsup.sh" >&2
  exit 1
fi

WATTSUP_USER="wattsup"
PUBLIC_KEY='${publicKey}'
AUTHORIZED_KEYS="/home/\${WATTSUP_USER}/.ssh/authorized_keys"

if ! id "\${WATTSUP_USER}" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "\${WATTSUP_USER}"
fi

install -d -m 700 -o "\${WATTSUP_USER}" -g "\${WATTSUP_USER}" "/home/\${WATTSUP_USER}/.ssh"
touch "\${AUTHORIZED_KEYS}"
grep -qxF "\${PUBLIC_KEY}" "\${AUTHORIZED_KEYS}" || printf '%s\\n' "\${PUBLIC_KEY}" >> "\${AUTHORIZED_KEYS}"
chown "\${WATTSUP_USER}:\${WATTSUP_USER}" "\${AUTHORIZED_KEYS}"
chmod 600 "\${AUTHORIZED_KEYS}"

TEMP_SUDOERS="$(mktemp)"
trap 'rm -f "\${TEMP_SUDOERS}"' EXIT
printf '%s\\n' '${sudoersRule}' > "\${TEMP_SUDOERS}"
chmod 440 "\${TEMP_SUDOERS}"
visudo -cf "\${TEMP_SUDOERS}"
install -m 440 "\${TEMP_SUDOERS}" /etc/sudoers.d/wattsup

echo "WattsUp SSH access configured successfully."
`;

export function ShutdownAutomation() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(initialDevice);
  const [notice, setNotice] = useState("");
  const [deviceNotices, setDeviceNotices] = useState<Record<number, string>>(
    {},
  );
  const [results, setResults] = useState<
    { device_id: number; name: string; matches: boolean; reason: string }[]
  >([]);
  const [simulation, setSimulation] = useState({
    mains: "on_battery",
    battery: "discharging",
    percentage: 30,
  });
  const { data: devices = [] } = useQuery({
    queryKey: ["shutdown-devices"],
    queryFn: shutdownApi.devices,
  });
  const { data: key } = useQuery({
    queryKey: ["shutdown-key"],
    queryFn: shutdownApi.publicKey,
  });
  const { data: settings } = useQuery({
    queryKey: ["shutdown-settings"],
    queryFn: shutdownApi.settings,
  });
  const setupScript = key ? buildSetupScript(key.public_key) : "";
  const setupUrl = `${window.location.origin}/adduser.sh`;
  const curlCommand = `curl -fsSL ${setupUrl} | sudo bash`;

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["shutdown-devices"] });
    await queryClient.invalidateQueries({ queryKey: ["shutdown-settings"] });
  };
  const act = async (operation: () => Promise<unknown>, success: string) => {
    try {
      const response = await operation();
      setNotice(
        response && typeof response === "object" && "message" in response
          ? String(response.message)
          : success,
      );
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Action failed");
    }
  };
  const deviceAct = async (
    deviceId: number,
    operation: () => Promise<unknown>,
    success: string,
  ) => {
    try {
      const response = await operation();
      const message =
        response && typeof response === "object" && "message" in response
          ? String(response.message)
          : success;
      setDeviceNotices((current) => ({ ...current, [deviceId]: message }));
      await refresh();
    } catch (error) {
      setDeviceNotices((current) => ({
        ...current,
        [deviceId]: error instanceof Error ? error.message : "Action failed",
      }));
    }
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    void act(async () => {
      await shutdownApi.create(form);
      setForm(initialDevice);
    }, "Device added. Trust its host key before testing.");
  };

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold">Shutdown automation</h2>
        <p className="mt-1 text-sm text-slate-500">
          Power down Linux devices when their UPS conditions match.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-2">
        <details className="self-start overflow-hidden rounded-2xl border border-slate-800 bg-panel">
          <summary className="flex cursor-pointer list-none items-center gap-3 p-4">
            <ShieldAlert className="h-5 w-5 text-cyan-300" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium">Global safety</span>
              <span className="text-xs text-slate-500">
                Automation and dry-run controls
              </span>
            </span>
            <span className="rounded-full bg-slate-800 px-2.5 py-1 text-[11px] text-slate-400">
              {settings?.enabled ? "Enabled" : "Disabled"}
            </span>
            {settings?.dry_run && (
              <span className="rounded-full bg-amber-950 px-2.5 py-1 text-[11px] text-amber-300">
                Dry run
              </span>
            )}
            <ChevronDown className="h-4 w-4 text-slate-500" />
          </summary>
          <div className="border-t border-slate-800 p-4">
            {[
              [
                "Automation enabled",
                "Allows matching devices to run",
                "enabled",
              ],
              ["Dry-run mode", "Evaluate without shutting down", "dry_run"],
            ].map(([label, detail, field]) => (
              <label
                key={field}
                className="mb-3 flex items-center justify-between rounded-xl bg-slate-950/40 p-3"
              >
                <span>
                  <span className="block text-sm">{label}</span>
                  <span className="text-xs text-slate-500">{detail}</span>
                </span>
                <input
                  type="checkbox"
                  checked={
                    field === "enabled" ? settings?.enabled : settings?.dry_run
                  }
                  onChange={(event) =>
                    void act(
                      () =>
                        shutdownApi.updateSettings(
                          field === "enabled"
                            ? event.target.checked
                            : (settings?.enabled ?? false),
                          field === "dry_run"
                            ? event.target.checked
                            : (settings?.dry_run ?? true),
                        ),
                      "Safety settings updated",
                    )
                  }
                  className="h-5 w-5 accent-cyan-300"
                />
              </label>
            ))}
          </div>
        </details>

        <details className="self-start overflow-hidden rounded-2xl border border-slate-800 bg-panel">
          <summary className="flex cursor-pointer list-none items-center gap-3 p-4">
            <KeyRound className="h-5 w-5 text-cyan-300" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium">
                Remote device setup
              </span>
              <span className="text-xs text-slate-500">
                Public key and setup script
              </span>
            </span>
            <span className="rounded-full bg-emerald-950 px-2.5 py-1 text-[11px] text-emerald-300">
              {key ? "Key ready" : "Generating"}
            </span>
            <ChevronDown className="h-4 w-4 text-slate-500" />
          </summary>
          <div className="border-t border-slate-800 p-4">
            <p className="mb-3 text-xs text-slate-500">
              Add this line to the device user’s ~/.ssh/authorized_keys.
            </p>
            <pre className="max-h-24 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-400">
              {key?.public_key || "Generating…"}
            </pre>
            <button
              onClick={() => {
                if (key) void navigator.clipboard.writeText(key.public_key);
                setNotice("Public key copied.");
              }}
              className="mt-3 flex items-center gap-2 text-sm text-cyan-300"
            >
              <Copy className="h-4 w-4" /> Copy key
            </button>
            <div className="mt-5 border-t border-slate-800 pt-4">
              <p className="text-sm font-medium text-slate-300">
                Remote device setup script
              </p>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">
                Run this command on the remote Linux device. It downloads the
                setup script directly from this WattsUp instance.
              </p>
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-slate-950 p-3">
                <code className="min-w-0 flex-1 overflow-auto whitespace-nowrap text-xs text-cyan-200">
                  {curlCommand}
                </code>
                <button
                  type="button"
                  onClick={() => {
                    void navigator.clipboard.writeText(curlCommand);
                    setNotice("Setup command copied.");
                  }}
                  className="shrink-0 text-cyan-300"
                  aria-label="Copy setup command"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
              <p className="mt-4 text-xs text-slate-600">Script preview</p>
              <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-950 p-3 text-xs leading-relaxed text-slate-400">
                {setupScript || "Generating setup script…"}
              </pre>
              <button
                type="button"
                onClick={() => {
                  if (setupScript)
                    void navigator.clipboard.writeText(setupScript);
                  setNotice("Remote setup script copied.");
                }}
                className="mt-3 flex items-center gap-2 text-sm text-cyan-300"
              >
                <Copy className="h-4 w-4" /> Copy setup script
              </button>
            </div>
          </div>
        </details>
      </div>

      {notice && (
        <p className="rounded-xl border border-slate-700 bg-panel p-3 text-sm">
          {notice}
        </p>
      )}

      <section className="rounded-2xl border border-slate-800 bg-panel p-5">
        <h3 className="mb-4 font-medium">Add Linux device</h3>
        <form
          onSubmit={submit}
          className="grid gap-2.5 md:grid-cols-2 lg:grid-cols-4"
        >
          <input
            required
            placeholder="Friendly name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className={inputClass}
          />
          <input
            required
            placeholder="Hostname or IP"
            value={form.host}
            onChange={(e) => setForm({ ...form, host: e.target.value })}
            className={inputClass}
          />
          <input
            required
            placeholder="SSH username"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            className={inputClass}
          />
          <input
            type="number"
            aria-label="SSH port"
            value={form.port}
            onChange={(e) => setForm({ ...form, port: Number(e.target.value) })}
            className={inputClass}
          />
          <select
            value={form.mains_state}
            onChange={(e) =>
              setForm({
                ...form,
                mains_state: e.target.value as DeviceInput["mains_state"],
              })
            }
            className={inputClass}
          >
            <option value="on_battery">Mains: On battery</option>
            <option value="online">Mains: Online</option>
            <option value="any">Mains: Any</option>
          </select>
          <select
            value={form.battery_state}
            onChange={(e) =>
              setForm({
                ...form,
                battery_state: e.target.value as DeviceInput["battery_state"],
              })
            }
            className={inputClass}
          >
            <option value="discharging">Battery: Discharging</option>
            <option value="charging">Battery: Charging</option>
            <option value="full">Battery: Full</option>
            <option value="any">Battery: Any</option>
          </select>
          <label className={`${inputClass} flex items-center gap-2 text-sm`}>
            Battery ≤
            <input
              type="number"
              min="0"
              max="100"
              value={form.battery_threshold}
              onChange={(e) =>
                setForm({ ...form, battery_threshold: Number(e.target.value) })
              }
              className="w-14 bg-transparent"
            />
            %
          </label>
          <label className={`${inputClass} flex items-center gap-2 text-sm`}>
            <input
              type="checkbox"
              checked={form.use_sudo}
              onChange={(e) => setForm({ ...form, use_sudo: e.target.checked })}
            />
            Passwordless sudo
          </label>
          <label className={`${inputClass} flex items-center gap-2 text-sm`}>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            Enable this rule
          </label>
          <button className="flex items-center justify-center gap-2 rounded-lg bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200">
            <Plus className="h-4 w-4" /> Add device
          </button>
        </form>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Configured devices</h3>
          {devices.length > 0 && (
            <button
              onClick={() =>
                void Promise.all(
                  devices.map((device) =>
                    deviceAct(
                      device.id,
                      () => shutdownApi.test(device.id),
                      "Readiness test complete",
                    ),
                  ),
                )
              }
              className="rounded-lg border border-cyan-900 px-3 py-2 text-xs text-cyan-300"
            >
              Test all devices
            </button>
          )}
        </div>
        {devices.length === 0 && (
          <p className="text-sm text-slate-500">No devices configured.</p>
        )}
        {devices.map((device) => (
          <article
            key={device.id}
            className="rounded-2xl border border-slate-800 bg-panel p-5"
          >
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div className="flex gap-3">
                <Server className="mt-1 h-5 w-5 text-cyan-300" />
                <div>
                  <h4 className="font-medium">{device.name}</h4>
                  <p className="text-sm text-slate-500">
                    {device.username}@{device.host}:{device.port}
                  </p>
                  <p className="mt-1 text-xs text-slate-600">
                    {device.mains_state} · {device.battery_state} · ≤{" "}
                    {device.battery_threshold}%
                  </p>
                  {device.host_key_fingerprint && (
                    <p className="mt-1 text-xs text-emerald-400">
                      Trusted: {device.host_key_fingerprint}
                    </p>
                  )}
                  {(deviceNotices[device.id] || device.last_result) && (
                    <p className="mt-2 rounded-lg bg-slate-950/60 px-3 py-2 text-xs text-slate-300">
                      {deviceNotices[device.id] || device.last_result}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() =>
                    void deviceAct(
                      device.id,
                      async () => {
                        const keyInfo = await shutdownApi.inspectKey(device.id);
                        if (
                          !window.confirm(
                            `Trust ${keyInfo.algorithm} key?\n\n${keyInfo.fingerprint}`,
                          )
                        )
                          return { message: "Host key was not changed." };
                        await shutdownApi.trustKey(device.id);
                        return { message: "SSH host key trusted." };
                      },
                      "SSH host key trusted.",
                    )
                  }
                  className="rounded-lg border border-slate-700 px-3 py-2 text-xs"
                >
                  Inspect / trust key
                </button>
                <button
                  onClick={() =>
                    void deviceAct(
                      device.id,
                      () => shutdownApi.test(device.id),
                      "Readiness test complete",
                    )
                  }
                  className="rounded-lg border border-cyan-900 px-3 py-2 text-xs text-cyan-300"
                >
                  Test readiness
                </button>
                <button
                  onClick={() => {
                    if (window.confirm(`Remove ${device.name}?`))
                      void act(
                        () => shutdownApi.remove(device.id),
                        "Device removed",
                      );
                  }}
                  className="rounded-lg border border-rose-900 px-3 py-2 text-rose-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="rounded-2xl border border-slate-800 bg-panel p-5">
        <h3 className="font-medium">Simulate conditions</h3>
        <p className="mt-1 text-xs text-slate-500">
          Shows what would happen without running SSH commands.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={simulation.mains}
            onChange={(e) =>
              setSimulation({ ...simulation, mains: e.target.value })
            }
            className={inputClass}
          >
            <option value="on_battery">On battery</option>
            <option value="online">Online</option>
          </select>
          <select
            value={simulation.battery}
            onChange={(e) =>
              setSimulation({ ...simulation, battery: e.target.value })
            }
            className={inputClass}
          >
            <option value="discharging">Discharging</option>
            <option value="charging">Charging</option>
            <option value="full">Full</option>
          </select>
          <input
            type="number"
            min="0"
            max="100"
            value={simulation.percentage}
            onChange={(e) =>
              setSimulation({
                ...simulation,
                percentage: Number(e.target.value),
              })
            }
            className={`${inputClass} w-24`}
          />
          <button
            onClick={async () =>
              setResults(
                await shutdownApi.simulate(
                  simulation.mains,
                  simulation.battery,
                  simulation.percentage,
                ),
              )
            }
            className="rounded-lg bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200"
          >
            Run simulation
          </button>
        </div>
        <div className="mt-4 space-y-2">
          {results.map((result) => (
            <p
              key={result.device_id}
              className={`rounded-lg p-3 text-sm ${
                result.matches
                  ? "bg-amber-950/40 text-amber-200"
                  : "bg-slate-950 text-slate-400"
              }`}
            >
              <strong>{result.name}:</strong>{" "}
              {result.matches ? "Would shut down" : "Stays up"} —{" "}
              {result.reason}
            </p>
          ))}
        </div>
      </section>
    </section>
  );
}
