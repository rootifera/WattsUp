import { apiFetch } from "./client";

export interface UpsVariable {
  name: string;
  value: string;
  group: string;
}

export async function getVariables(): Promise<UpsVariable[]> {
  const response = await apiFetch("/api/variables");
  if (!response.ok) throw new Error("Could not load UPS details");
  return response.json() as Promise<UpsVariable[]>;
}
