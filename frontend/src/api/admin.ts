import { apiFetch } from "./client";

export interface NutServer {
  id: number;
  name: string;
  host: string;
  port: number;
  currency: string;
  price_per_kwh: number;
  units: { id: number; nut_name: string; display_name: string }[];
}

export interface NotificationChannel {
  id: number;
  name: string;
  kind: "smtp" | "gotify" | "pushover" | "webhook";
  enabled: boolean;
  configuration: Record<string, unknown>;
  events: string[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const adminApi = {
  servers: () => request<NutServer[]>("/api/admin/servers"),
  updateServer: (
    id: number,
    body: Pick<NutServer, "name" | "currency" | "price_per_kwh">,
  ) =>
    request(`/api/admin/servers/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  renameUps: (id: number, display_name: string) =>
    request(`/api/admin/ups/${id}`, {
      method: "PUT",
      body: JSON.stringify({ display_name }),
    }),
  addServer: (body: Record<string, unknown>) =>
    request("/api/admin/servers", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  channels: () => request<NotificationChannel[]>("/api/admin/notifications"),
  addChannel: (body: Record<string, unknown>) =>
    request<{ id: number }>("/api/admin/notifications", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  testChannel: (id: number) =>
    request<{ message: string }>(`/api/admin/notifications/${id}/test`, {
      method: "POST",
    }),
};
