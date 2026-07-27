import type { UpsStatus } from "../types/status";
import { apiFetch } from "./client";

export async function getStatus(): Promise<UpsStatus> {
  const response = await apiFetch("/api/status");
  if (!response.ok) {
    throw new Error(`Status request failed (${response.status})`);
  }
  return response.json() as Promise<UpsStatus>;
}
