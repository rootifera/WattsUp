import {
  Bell,
  ChevronDown,
  Mail,
  Radio,
  Send,
  Trash2,
  Webhook,
} from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";

import { adminApi, type NotificationChannel } from "../api/admin";

const field =
  "w-full rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm outline-none placeholder:text-slate-600 focus:border-cyan-800";

const events = [
  {
    id: "on_battery",
    label: "Running on battery",
    detail: "Mains power is lost and the UPS switches to battery.",
  },
  {
    id: "power_restored",
    label: "Power restored",
    detail: "Mains power returns after a battery event.",
  },
  {
    id: "low_battery",
    label: "Low battery",
    detail: "NUT reports the critical low-battery state.",
  },
  {
    id: "unreachable",
    label: "UPS unreachable",
    detail: "WattsUp loses its connection to the UPS or NUT server.",
  },
  {
    id: "reconnected",
    label: "Connection restored",
    detail: "An unreachable UPS becomes available again.",
  },
];

const kinds = {
  smtp: {
    label: "Email",
    detail: "Send mail through an authenticated SMTP server.",
    icon: Mail,
  },
  gotify: {
    label: "Gotify",
    detail: "Push notifications to your self-hosted Gotify server.",
    icon: Radio,
  },
  pushover: {
    label: "Pushover",
    detail: "Send alerts through the Pushover mobile service.",
    icon: Send,
  },
  webhook: {
    label: "Webhook",
    detail: "POST a JSON payload to an automation endpoint.",
    icon: Webhook,
  },
} as const;

type Kind = keyof typeof kinds;

const initialForm = {
  name: "",
  kind: "smtp" as Kind,
  enabled: true,
  events: events.map((event) => event.id),
  host: "",
  port: 587,
  security: "starttls",
  username: "",
  password: "",
  from: "",
  to: "",
  url: "",
  token: "",
  user: "",
};

export function NotificationsPanel({
  channels,
  act,
}: {
  channels: NotificationChannel[];
  act: (operation: () => Promise<unknown>, success?: string) => Promise<void>;
}) {
  const [form, setForm] = useState(initialForm);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const configuration =
      form.kind === "smtp"
        ? {
            host: form.host,
            port: form.port,
            security: form.security,
            username: form.username,
            password: form.password,
            from: form.from,
            to: form.to,
          }
        : form.kind === "pushover"
          ? { token: form.token, user: form.user }
          : form.kind === "gotify"
            ? { url: form.url, token: form.token }
            : { url: form.url };
    void act(async () => {
      await adminApi.addChannel({
        name: form.name,
        kind: form.kind,
        enabled: form.enabled,
        configuration,
        events: form.events,
      });
      setForm(initialForm);
    }, "Notification channel added.");
  };

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-800 bg-panel">
      <header className="flex items-start gap-3 border-b border-slate-800 p-5">
        <span className="rounded-xl bg-cyan-300/10 p-2 text-cyan-300">
          <Bell className="h-5 w-5" />
        </span>
        <div>
          <h3 className="font-medium">Notifications</h3>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            Choose where alerts are delivered and exactly which UPS state
            changes should trigger them. Repeated polls do not produce repeated
            notifications.
          </p>
        </div>
      </header>

      <div className="space-y-3 p-5">
        {channels.length === 0 && (
          <p className="rounded-xl border border-dashed border-slate-800 p-5 text-center text-sm text-slate-500">
            No notification channels configured yet.
          </p>
        )}
        {channels.map((channel) => (
          <ChannelCard key={channel.id} channel={channel} act={act} />
        ))}

        <details className="overflow-hidden rounded-xl border border-slate-800">
          <summary className="flex cursor-pointer list-none items-center justify-between p-4 text-sm font-medium text-cyan-300">
            Add notification channel
            <ChevronDown className="h-4 w-4 text-slate-500" />
          </summary>
          <form
            onSubmit={submit}
            className="space-y-5 border-t border-slate-800 p-4"
          >
            <div className="grid gap-4 md:grid-cols-2">
              <Labeled label="Friendly name">
                <input
                  required
                  placeholder="Outage alerts"
                  value={form.name}
                  onChange={(event) =>
                    setForm({ ...form, name: event.target.value })
                  }
                  className={field}
                />
              </Labeled>
              <Labeled label="Delivery method">
                <select
                  value={form.kind}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      kind: event.target.value as Kind,
                    })
                  }
                  className={field}
                >
                  {Object.entries(kinds).map(([id, kind]) => (
                    <option key={id} value={id}>
                      {kind.label}
                    </option>
                  ))}
                </select>
              </Labeled>
            </div>

            <p className="text-xs text-slate-500">{kinds[form.kind].detail}</p>
            <ChannelFields form={form} setForm={setForm} />

            <div>
              <p className="mb-2 text-xs font-medium text-slate-400">
                Notify me when
              </p>
              <div className="grid gap-2 md:grid-cols-2">
                {events.map((item) => (
                  <label
                    key={item.id}
                    className="flex cursor-pointer gap-3 rounded-xl border border-slate-800 p-3"
                  >
                    <input
                      type="checkbox"
                      checked={form.events.includes(item.id)}
                      onChange={() =>
                        setForm({
                          ...form,
                          events: toggle(form.events, item.id),
                        })
                      }
                      className="mt-0.5 accent-cyan-300"
                    />
                    <span>
                      <span className="block text-sm text-slate-200">
                        {item.label}
                      </span>
                      <span className="mt-0.5 block text-xs text-slate-600">
                        {item.detail}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-slate-800 pt-4">
              <label className="flex items-center gap-2 text-sm text-slate-400">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(event) =>
                    setForm({ ...form, enabled: event.target.checked })
                  }
                  className="accent-cyan-300"
                />
                Enable immediately
              </label>
              <button className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-medium text-slate-950">
                Add channel
              </button>
            </div>
          </form>
        </details>
      </div>
    </section>
  );
}

function ChannelCard({
  channel,
  act,
}: {
  channel: NotificationChannel;
  act: (operation: () => Promise<unknown>, success?: string) => Promise<void>;
}) {
  const meta = kinds[channel.kind];
  const Icon = meta.icon;
  const update = (changes: Partial<NotificationChannel>) =>
    act(
      () =>
        adminApi.updateChannel(channel.id, {
          name: channel.name,
          kind: channel.kind,
          enabled: channel.enabled,
          configuration: channel.configuration,
          events: channel.events,
          ...changes,
        }),
      "Notification preferences updated.",
    );

  return (
    <article className="rounded-xl border border-slate-800 bg-slate-950/20 p-4">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div className="flex gap-3">
          <span className="rounded-lg bg-slate-900 p-2 text-cyan-300">
            <Icon className="h-4 w-4" />
          </span>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="font-medium">{channel.name}</h4>
              <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-400">
                {meta.label}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] ${
                  channel.enabled
                    ? "bg-emerald-950 text-emerald-300"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                {channel.enabled ? "Enabled" : "Paused"}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-600">
              {channel.events.length
                ? channel.events
                    .map(
                      (id) =>
                        events.find((event) => event.id === id)?.label ?? id,
                    )
                    .join(" · ")
                : "No events selected"}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void update({ enabled: !channel.enabled })}
            className="rounded-lg border border-slate-700 px-3 py-2 text-xs"
          >
            {channel.enabled ? "Pause" : "Enable"}
          </button>
          <button
            type="button"
            onClick={() =>
              void act(
                () => adminApi.testChannel(channel.id),
                "Test notification sent.",
              )
            }
            className="rounded-lg border border-cyan-900 px-3 py-2 text-xs text-cyan-300"
          >
            Send test
          </button>
          <button
            type="button"
            aria-label={`Remove ${channel.name}`}
            onClick={() => {
              if (window.confirm(`Remove ${channel.name}?`)) {
                void act(
                  () => adminApi.removeChannel(channel.id),
                  "Notification channel removed.",
                );
              }
            }}
            className="rounded-lg border border-rose-900 p-2 text-rose-400"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <details className="mt-3 border-t border-slate-800 pt-3">
        <summary className="cursor-pointer text-xs text-slate-500">
          Change notification events
        </summary>
        <div className="mt-3 flex flex-wrap gap-2">
          {events.map((item) => (
            <label
              key={item.id}
              className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-800 px-3 py-2 text-xs"
              title={item.detail}
            >
              <input
                type="checkbox"
                checked={channel.events.includes(item.id)}
                onChange={() =>
                  void update({
                    events: toggle(channel.events, item.id),
                  })
                }
                className="accent-cyan-300"
              />
              {item.label}
            </label>
          ))}
        </div>
      </details>
    </article>
  );
}

function ChannelFields({
  form,
  setForm,
}: {
  form: typeof initialForm;
  setForm: (value: typeof initialForm) => void;
}) {
  if (form.kind === "smtp") {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Labeled label="SMTP server">
          <input
            required
            placeholder="smtp.example.com"
            value={form.host}
            onChange={(event) => setForm({ ...form, host: event.target.value })}
            className={field}
          />
        </Labeled>
        <Labeled label="Port">
          <input
            required
            type="number"
            value={form.port}
            onChange={(event) =>
              setForm({ ...form, port: Number(event.target.value) })
            }
            className={field}
          />
        </Labeled>
        <Labeled label="Connection security">
          <select
            value={form.security}
            onChange={(event) =>
              setForm({ ...form, security: event.target.value })
            }
            className={field}
          >
            <option value="starttls">STARTTLS (usually port 587)</option>
            <option value="ssl">SSL/TLS (usually port 465)</option>
            <option value="none">None</option>
          </select>
        </Labeled>
        <Labeled label="Username">
          <input
            required
            autoComplete="username"
            value={form.username}
            onChange={(event) =>
              setForm({ ...form, username: event.target.value })
            }
            className={field}
          />
        </Labeled>
        <Labeled label="Password or app password">
          <input
            required
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={(event) =>
              setForm({ ...form, password: event.target.value })
            }
            className={field}
          />
        </Labeled>
        <Labeled label="From address">
          <input
            required
            type="email"
            value={form.from}
            onChange={(event) => setForm({ ...form, from: event.target.value })}
            className={field}
          />
        </Labeled>
        <Labeled label="Recipient address">
          <input
            required
            type="email"
            value={form.to}
            onChange={(event) => setForm({ ...form, to: event.target.value })}
            className={field}
          />
        </Labeled>
      </div>
    );
  }
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {form.kind !== "pushover" && (
        <Labeled
          label={form.kind === "gotify" ? "Gotify server URL" : "Webhook URL"}
        >
          <input
            required
            type="url"
            placeholder="https://…"
            value={form.url}
            onChange={(event) => setForm({ ...form, url: event.target.value })}
            className={field}
          />
        </Labeled>
      )}
      {(form.kind === "gotify" || form.kind === "pushover") && (
        <Labeled
          label={form.kind === "gotify" ? "Application token" : "API token"}
        >
          <input
            required
            type="password"
            value={form.token}
            onChange={(event) =>
              setForm({ ...form, token: event.target.value })
            }
            className={field}
          />
        </Labeled>
      )}
      {form.kind === "pushover" && (
        <Labeled label="User or group key">
          <input
            required
            value={form.user}
            onChange={(event) => setForm({ ...form, user: event.target.value })}
            className={field}
          />
        </Labeled>
      )}
    </div>
  );
}

function Labeled({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs text-slate-500">{label}</span>
      {children}
    </label>
  );
}

const toggle = (values: string[], value: string) =>
  values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
