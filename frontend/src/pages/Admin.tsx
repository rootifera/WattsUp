import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Server } from "lucide-react";
import { useState, type FormEvent } from "react";

import { adminApi } from "../api/admin";
import { NotificationsPanel } from "../components/NotificationsPanel";

const field =
  "rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm outline-none focus:border-cyan-800";

export function Admin() {
  const client = useQueryClient();
  const { data: servers = [] } = useQuery({
    queryKey: ["admin-servers"],
    queryFn: adminApi.servers,
  });
  const { data: channels = [] } = useQuery({
    queryKey: ["notification-channels"],
    queryFn: adminApi.channels,
  });
  const { data: retention } = useQuery({
    queryKey: ["retention"],
    queryFn: adminApi.retention,
  });
  const [serverNotice, setServerNotice] = useState("");
  const [retentionNotice, setRetentionNotice] = useState("");
  const [server, setServer] = useState({
    name: "",
    host: "",
    port: 3493,
    username: "",
    password: "",
    currency: "GBP",
    price_per_kwh: 0.25,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
  });

  const act = async (operation: () => Promise<unknown>, success = "Saved.") => {
    try {
      await operation();
      setServerNotice(success);
      await client.invalidateQueries();
    } catch (error) {
      setServerNotice(error instanceof Error ? error.message : "Action failed");
    }
  };
  const addServer = (event: FormEvent) => {
    event.preventDefault();
    void act(() => adminApi.addServer(server));
  };

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold">Administration</h2>
        <p className="mt-1 text-sm text-slate-500">
          NUT servers, UPS names, tariffs and notifications.
        </p>
      </header>
      <section className="rounded-2xl border border-slate-800 bg-panel p-5">
        <h3 className="flex items-center gap-2 font-medium">
          <Server className="h-4 w-4 text-cyan-300" /> NUT servers
        </h3>
        {serverNotice && (
          <p className="mt-4 rounded-lg bg-slate-950/60 px-3 py-2 text-xs text-slate-300">
            {serverNotice}
          </p>
        )}
        <div className="mt-4 space-y-4">
          {servers.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-slate-800 p-4"
            >
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  const form = new FormData(event.currentTarget);
                  void act(() =>
                    adminApi.updateServer(item.id, {
                      name: String(form.get("name")),
                      host: String(form.get("host")),
                      port: Number(form.get("port")),
                      username: String(form.get("username") || ""),
                      password: String(form.get("password") || ""),
                      clear_credentials: form.get("clear_credentials") === "on",
                      currency: String(form.get("currency")),
                      price_per_kwh: Number(form.get("price")),
                      timezone: String(form.get("timezone")),
                      tariff_effective_date: String(form.get("effective_date")),
                    }),
                  );
                }}
                className="grid gap-3 md:grid-cols-2 lg:grid-cols-4"
              >
                <ServerField
                  label="Friendly name"
                  name="name"
                  value={item.name}
                />
                <ServerField label="Host or IP" name="host" value={item.host} />
                <ServerField
                  label="Port"
                  name="port"
                  value={item.port}
                  type="number"
                />
                <ServerField
                  label="NUT username"
                  name="username"
                  placeholder={
                    item.has_credentials
                      ? "Leave blank to keep current"
                      : "Optional"
                  }
                />
                <ServerField
                  label="NUT password"
                  name="password"
                  type="password"
                  placeholder={
                    item.has_credentials
                      ? "Leave blank to keep current"
                      : "Optional"
                  }
                />
                <ServerField
                  label="Currency"
                  name="currency"
                  value={item.currency}
                  maxLength={3}
                />
                <ServerField
                  label="Price per kWh"
                  name="price"
                  value={item.price_per_kwh}
                  type="number"
                  step="0.0001"
                />
                <ServerField
                  label="Timezone"
                  name="timezone"
                  value={item.timezone}
                />
                <ServerField
                  label="Tariff effective date"
                  name="effective_date"
                  value={new Date().toISOString().slice(0, 10)}
                  type="date"
                />
                {item.has_credentials && (
                  <label className="flex items-end gap-2 pb-2 text-xs text-slate-400">
                    <input name="clear_credentials" type="checkbox" />
                    Remove saved credentials
                  </label>
                )}
                <button className="self-end rounded-lg border border-cyan-900 px-3 py-2 text-xs text-cyan-300">
                  Save and test connection
                </button>
              </form>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {item.units.map((unit) => (
                  <form
                    key={unit.id}
                    onSubmit={(event) => {
                      event.preventDefault();
                      void act(() =>
                        adminApi.renameUps(
                          unit.id,
                          String(new FormData(event.currentTarget).get("name")),
                        ),
                      );
                    }}
                    className="flex gap-2"
                  >
                    <input
                      name="name"
                      defaultValue={unit.display_name}
                      className={`${field} min-w-0 flex-1`}
                    />
                    <button className="rounded-lg border border-slate-700 px-3 text-xs">
                      Rename
                    </button>
                  </form>
                ))}
              </div>
            </div>
          ))}
        </div>
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-cyan-300">
            Add another NUT server
          </summary>
          <form onSubmit={addServer} className="mt-3 grid gap-2 md:grid-cols-4">
            {(["name", "host", "username", "password"] as const).map((key) => (
              <input
                key={key}
                type={key === "password" ? "password" : "text"}
                placeholder={key}
                value={server[key]}
                onChange={(e) =>
                  setServer({ ...server, [key]: e.target.value })
                }
                className={field}
              />
            ))}
            <input
              type="number"
              value={server.port}
              onChange={(e) =>
                setServer({ ...server, port: Number(e.target.value) })
              }
              className={field}
            />
            <input
              value={server.timezone}
              onChange={(e) =>
                setServer({ ...server, timezone: e.target.value })
              }
              placeholder="Timezone"
              className={field}
            />
            <input
              value={server.currency}
              onChange={(e) =>
                setServer({ ...server, currency: e.target.value })
              }
              className={field}
            />
            <input
              type="number"
              step="0.0001"
              value={server.price_per_kwh}
              onChange={(e) =>
                setServer({ ...server, price_per_kwh: Number(e.target.value) })
              }
              className={field}
            />
            <button className="flex items-center justify-center gap-2 rounded-lg bg-cyan-300 px-3 py-2 text-sm font-medium text-slate-950">
              <Plus className="h-4 w-4" /> Add
            </button>
          </form>
        </details>
      </section>
      <section className="rounded-2xl border border-slate-800 bg-panel p-5">
        <h3 className="font-medium">Data retention</h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">
          Daily energy and cost totals are kept permanently. Choose how long
          detailed raw readings remain available for power timelines.
        </p>
        {retentionNotice && (
          <p className="mt-3 rounded-lg bg-slate-950/60 px-3 py-2 text-xs text-slate-300">
            {retentionNotice}
          </p>
        )}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const value = String(
              new FormData(event.currentTarget).get("raw_days") ?? "",
            );
            void adminApi
              .updateRetention(value === "unlimited" ? null : Number(value))
              .then(async () => {
                setRetentionNotice("Retention updated.");
                await client.invalidateQueries({ queryKey: ["retention"] });
              })
              .catch((error: unknown) =>
                setRetentionNotice(
                  error instanceof Error ? error.message : "Update failed",
                ),
              );
          }}
          className="mt-4 flex flex-col gap-2 sm:flex-row"
        >
          <select
            name="raw_days"
            defaultValue={retention?.raw_days ?? "unlimited"}
            key={String(retention?.raw_days)}
            className={`${field} sm:w-56`}
          >
            <option value="30">30 days</option>
            <option value="90">90 days</option>
            <option value="180">180 days</option>
            <option value="365">1 year</option>
            <option value="730">2 years</option>
            <option value="unlimited">Unlimited</option>
          </select>
          <button className="rounded-lg border border-cyan-900 px-4 py-2 text-sm text-cyan-300">
            Save retention
          </button>
        </form>
      </section>
      <NotificationsPanel channels={channels} />
    </section>
  );
}

function ServerField({
  label,
  name,
  value,
  type = "text",
  placeholder,
  step,
  maxLength,
}: {
  label: string;
  name: string;
  value?: string | number;
  type?: string;
  placeholder?: string;
  step?: string;
  maxLength?: number;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-slate-500">{label}</span>
      <input
        name={name}
        type={type}
        defaultValue={value}
        placeholder={placeholder}
        step={step}
        maxLength={maxLength}
        required={[
          "name",
          "host",
          "port",
          "currency",
          "price",
          "timezone",
        ].includes(name)}
        className={`${field} w-full`}
      />
    </label>
  );
}
