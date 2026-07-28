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
  const [serverNotice, setServerNotice] = useState("");
  const [server, setServer] = useState({
    name: "",
    host: "",
    port: 3493,
    username: "",
    password: "",
    currency: "GBP",
    price_per_kwh: 0.25,
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
      <NotificationsPanel channels={channels} />
    </section>
  );
}
