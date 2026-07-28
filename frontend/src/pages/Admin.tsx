import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Plus, Server } from "lucide-react";
import { useState, type FormEvent } from "react";

import { adminApi } from "../api/admin";

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
  const [notice, setNotice] = useState("");
  const [server, setServer] = useState({
    name: "",
    host: "",
    port: 3493,
    username: "",
    password: "",
    currency: "GBP",
    price_per_kwh: 0.25,
  });
  const [channel, setChannel] = useState({
    name: "",
    kind: "gotify",
    url: "",
    token: "",
    user: "",
    to: "",
    from: "",
    host: "",
    port: 587,
  });

  const act = async (operation: () => Promise<unknown>) => {
    try {
      await operation();
      setNotice("Saved.");
      await client.invalidateQueries();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Action failed");
    }
  };
  const addServer = (event: FormEvent) => {
    event.preventDefault();
    void act(() => adminApi.addServer(server));
  };
  const addChannel = (event: FormEvent) => {
    event.preventDefault();
    const configuration =
      channel.kind === "smtp"
        ? {
            host: channel.host,
            port: channel.port,
            from: channel.from,
            to: channel.to,
            username: channel.user,
            password: channel.token,
            starttls: true,
          }
        : channel.kind === "pushover"
          ? { token: channel.token, user: channel.user }
          : { url: channel.url, token: channel.token };
    void act(() =>
      adminApi.addChannel({
        name: channel.name,
        kind: channel.kind,
        enabled: true,
        configuration,
        events: [
          "on_battery",
          "power_restored",
          "low_battery",
          "unreachable",
          "reconnected",
          "test_result",
          "shutdown_result",
        ],
      }),
    );
  };

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold">Administration</h2>
        <p className="mt-1 text-sm text-slate-500">
          NUT servers, UPS names, tariffs and notifications.
        </p>
      </header>
      {notice && (
        <p className="rounded-xl border border-slate-800 bg-panel p-3 text-sm">
          {notice}
        </p>
      )}
      <section className="rounded-2xl border border-slate-800 bg-panel p-5">
        <h3 className="flex items-center gap-2 font-medium">
          <Server className="h-4 w-4 text-cyan-300" /> NUT servers
        </h3>
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
                      currency: String(form.get("currency")),
                      price_per_kwh: Number(form.get("price")),
                    }),
                  );
                }}
                className="flex flex-wrap gap-2"
              >
                <input name="name" defaultValue={item.name} className={field} />
                <input
                  name="currency"
                  defaultValue={item.currency}
                  maxLength={3}
                  className={`${field} w-20`}
                />
                <input
                  name="price"
                  type="number"
                  step="0.0001"
                  defaultValue={item.price_per_kwh}
                  className={`${field} w-32`}
                />
                <button className="rounded-lg border border-cyan-900 px-3 text-xs text-cyan-300">
                  Save tariff
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
        <h3 className="flex items-center gap-2 font-medium">
          <Bell className="h-4 w-4 text-cyan-300" /> Notifications
        </h3>
        <div className="mt-3 space-y-2">
          {channels.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between rounded-xl border border-slate-800 p-3"
            >
              <span>
                <span className="font-medium">{item.name}</span>
                <span className="ml-2 text-xs uppercase text-slate-500">
                  {item.kind}
                </span>
              </span>
              <button
                onClick={() => void act(() => adminApi.testChannel(item.id))}
                className="rounded-lg border border-cyan-900 px-3 py-2 text-xs text-cyan-300"
              >
                Send test
              </button>
            </div>
          ))}
        </div>
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-cyan-300">
            Add notification channel
          </summary>
          <form
            onSubmit={addChannel}
            className="mt-3 grid gap-2 md:grid-cols-3"
          >
            <input
              required
              placeholder="Friendly name"
              value={channel.name}
              onChange={(e) => setChannel({ ...channel, name: e.target.value })}
              className={field}
            />
            <select
              value={channel.kind}
              onChange={(e) => setChannel({ ...channel, kind: e.target.value })}
              className={field}
            >
              <option value="smtp">SMTP email</option>
              <option value="gotify">Gotify</option>
              <option value="pushover">Pushover</option>
              <option value="webhook">Webhook</option>
            </select>
            {channel.kind === "smtp" ? (
              <>
                <input
                  placeholder="SMTP host"
                  value={channel.host}
                  onChange={(e) =>
                    setChannel({ ...channel, host: e.target.value })
                  }
                  className={field}
                />
                <input
                  placeholder="From address"
                  value={channel.from}
                  onChange={(e) =>
                    setChannel({ ...channel, from: e.target.value })
                  }
                  className={field}
                />
                <input
                  placeholder="To address"
                  value={channel.to}
                  onChange={(e) =>
                    setChannel({ ...channel, to: e.target.value })
                  }
                  className={field}
                />
              </>
            ) : (
              channel.kind !== "pushover" && (
                <input
                  placeholder="URL"
                  value={channel.url}
                  onChange={(e) =>
                    setChannel({ ...channel, url: e.target.value })
                  }
                  className={field}
                />
              )
            )}
            {(channel.kind === "gotify" || channel.kind === "pushover") && (
              <input
                placeholder="API token"
                type="password"
                value={channel.token}
                onChange={(e) =>
                  setChannel({ ...channel, token: e.target.value })
                }
                className={field}
              />
            )}
            {channel.kind === "pushover" && (
              <input
                placeholder="User key"
                value={channel.user}
                onChange={(e) =>
                  setChannel({ ...channel, user: e.target.value })
                }
                className={field}
              />
            )}
            <button className="rounded-lg bg-cyan-300 px-3 py-2 text-sm font-medium text-slate-950">
              Add channel
            </button>
          </form>
        </details>
      </section>
    </section>
  );
}
