import { Plus, Trash2, Zap } from "lucide-react";
import { useState, type FormEvent } from "react";

import { install, type Installation } from "../api/setup";

const emptyServer = () => ({
  name: "",
  host: "",
  port: 3493,
  username: "",
  password: "",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
});

export function Setup({ onComplete }: { onComplete: () => void }) {
  const [form, setForm] = useState<Installation>({
    setup_token: "",
    admin_username: "admin",
    admin_password: "",
    currency: "GBP",
    price_per_kwh: 0.25,
    servers: [emptyServer()],
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await install(form);
      onComplete();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Installation failed",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-ink px-3 py-5 text-slate-100 sm:px-5 sm:py-10">
      <form
        onSubmit={submit}
        className="mx-auto max-w-3xl space-y-6 rounded-2xl border border-slate-800 bg-panel p-4 sm:rounded-3xl sm:p-7"
      >
        <header>
          <div className="mb-4 flex items-center gap-3">
            <span className="rounded-xl bg-cyan-300 p-2 text-slate-950">
              <Zap className="h-5 w-5" fill="currentColor" />
            </span>
            <span className="font-semibold tracking-wide">WATTSUP</span>
          </div>
          <h1 className="text-2xl font-semibold">Set up WattsUp</h1>
          <p className="mt-1 text-sm text-slate-500">
            Create the administrator and connect your NUT servers.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-2">
          <Input
            label="Setup token from .env"
            type="password"
            value={form.setup_token}
            onChange={(value) => setForm({ ...form, setup_token: value })}
          />
          <Input
            label="Administrator username"
            value={form.admin_username}
            onChange={(value) => setForm({ ...form, admin_username: value })}
          />
          <Input
            label="Administrator password"
            type="password"
            value={form.admin_password}
            onChange={(value) => setForm({ ...form, admin_password: value })}
          />
          <Input
            label="Currency"
            value={form.currency}
            onChange={(value) =>
              setForm({ ...form, currency: value.toUpperCase().slice(0, 3) })
            }
          />
          <Input
            label="Default price per kWh"
            type="number"
            step="0.0001"
            value={String(form.price_per_kwh)}
            onChange={(value) =>
              setForm({ ...form, price_per_kwh: Number(value) })
            }
          />
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-medium">NUT servers</h2>
              <p className="text-xs text-slate-500">
                UPS units will be discovered automatically.
              </p>
            </div>
            <button
              type="button"
              onClick={() =>
                setForm({ ...form, servers: [...form.servers, emptyServer()] })
              }
              className="flex items-center gap-2 rounded-lg border border-cyan-900 px-3 py-2 text-xs text-cyan-300"
            >
              <Plus className="h-4 w-4" /> Add server
            </button>
          </div>
          {form.servers.map((server, index) => (
            <div
              key={index}
              className="grid gap-3 rounded-2xl border border-slate-800 p-4 md:grid-cols-2"
            >
              <Input
                label="Friendly name"
                value={server.name}
                onChange={(value) =>
                  updateServer(index, "name", value, form, setForm)
                }
              />
              <Input
                label="Host or IP"
                value={server.host}
                onChange={(value) =>
                  updateServer(index, "host", value, form, setForm)
                }
              />
              <Input
                label="Port"
                type="number"
                value={String(server.port)}
                onChange={(value) =>
                  updateServer(index, "port", Number(value), form, setForm)
                }
              />
              <Input
                label="NUT username (optional)"
                value={server.username || ""}
                onChange={(value) =>
                  updateServer(index, "username", value || null, form, setForm)
                }
              />
              <Input
                label="NUT password (optional)"
                type="password"
                value={server.password || ""}
                onChange={(value) =>
                  updateServer(index, "password", value || null, form, setForm)
                }
              />
              {form.servers.length > 1 && (
                <button
                  type="button"
                  onClick={() =>
                    setForm({
                      ...form,
                      servers: form.servers.filter((_, item) => item !== index),
                    })
                  }
                  className="self-end justify-self-start rounded-lg border border-rose-900 p-2 text-rose-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </section>
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button
          disabled={submitting}
          className="w-full rounded-xl bg-cyan-300 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50"
        >
          {submitting ? "Testing connections…" : "Install WattsUp"}
        </button>
      </form>
    </main>
  );
}

function Input({
  label,
  value,
  onChange,
  type = "text",
  step,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  step?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs text-slate-500">{label}</span>
      <input
        required={!label.includes("optional")}
        type={type}
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm outline-none focus:border-cyan-800"
      />
    </label>
  );
}

function updateServer(
  index: number,
  field: string,
  value: string | number | null,
  form: Installation,
  setForm: (form: Installation) => void,
) {
  setForm({
    ...form,
    servers: form.servers.map((server, item) =>
      item === index ? { ...server, [field]: value } : server,
    ),
  });
}
