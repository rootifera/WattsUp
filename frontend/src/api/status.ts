import type { UpsStatus } from "../types/status";
import { apiFetch } from "./client";

export interface UpsUnit {
  name: string;
  description: string;
}

export async function getUpsUnits(): Promise<UpsUnit[]> {
  const response = await apiFetch("/api/ups");
  if (!response.ok) throw new Error("Could not discover UPS units");
  return response.json() as Promise<UpsUnit[]>;
}

export async function getStatus(ups: string): Promise<UpsStatus> {
  const response = await apiFetch(`/api/status?ups=${encodeURIComponent(ups)}`);
  if (!response.ok) {
    throw new Error(`Status request failed (${response.status})`);
  }
  return response.json() as Promise<UpsStatus>;
}
