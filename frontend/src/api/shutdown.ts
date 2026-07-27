import { apiFetch } from "./client";

export interface RemoteDevice {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string;
  enabled: boolean;
  use_sudo: boolean;
  mains_state: "online" | "on_battery" | "any";
  battery_state: "charging" | "discharging" | "full" | "any";
  battery_threshold: number;
  custom_command: string | null;
  host_key_fingerprint: string | null;
  last_test_at: string | null;
  last_result: string | null;
}

export type DeviceInput = Omit<
  RemoteDevice,
  "id" | "host_key_fingerprint" | "last_test_at" | "last_result"
>;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}

export const shutdownApi = {
  devices: () => request<RemoteDevice[]>("/api/shutdown/devices"),
  create: (body: DeviceInput) =>
    request<RemoteDevice>("/api/shutdown/devices", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  remove: (id: number) =>
    request<void>(`/api/shutdown/devices/${id}`, { method: "DELETE" }),
  publicKey: () => request<{ public_key: string }>("/api/shutdown/public-key"),
  inspectKey: (id: number) =>
    request<{ fingerprint: string; algorithm: string }>(
      `/api/shutdown/devices/${id}/host-key`,
    ),
  trustKey: (id: number) =>
    request<{ fingerprint: string }>(
      `/api/shutdown/devices/${id}/trust-host-key`,
      {
        method: "POST",
      },
    ),
  test: (id: number) =>
    request<{ success: boolean; message: string }>(
      `/api/shutdown/devices/${id}/test`,
      {
        method: "POST",
      },
    ),
  settings: () =>
    request<{ enabled: boolean; dry_run: boolean }>("/api/shutdown/settings"),
  updateSettings: (enabled: boolean, dry_run: boolean) =>
    request<{ enabled: boolean; dry_run: boolean }>("/api/shutdown/settings", {
      method: "PUT",
      body: JSON.stringify({ enabled, dry_run }),
    }),
  simulate: (
    mains_state: string,
    battery_state: string,
    battery_percentage: number,
  ) =>
    request<
      { device_id: number; name: string; matches: boolean; reason: string }[]
    >("/api/shutdown/simulate", {
      method: "POST",
      body: JSON.stringify({ mains_state, battery_state, battery_percentage }),
    }),
};
