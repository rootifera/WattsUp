import { apiFetch } from "./client";

export interface Installation {
  setup_token: string;
  admin_username: string;
  admin_password: string;
  currency: string;
  price_per_kwh: number;
  servers: {
    name: string;
    host: string;
    port: number;
    username: string | null;
    password: string | null;
  }[];
}

export async function setupRequired(): Promise<boolean> {
  const response = await apiFetch("/api/setup/status");
  if (!response.ok) throw new Error("Could not determine installation status");
  return ((await response.json()) as { required: boolean }).required;
}

export async function install(body: Installation): Promise<void> {
  const response = await apiFetch("/api/setup", {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const result = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(result.detail || "Installation failed");
  }
}
