import { apiFetch } from "./client";

export interface EnergySummary {
  current_watts: number | null;
  power_source: "measured" | "estimated" | null;
  today_kwh: number;
  month_kwh: number;
  today_cost: number;
  month_cost: number;
  currency: string;
}

export interface EnergyPoint {
  recorded_at: string;
  power_watts: number | null;
}

export async function getEnergy(ups: string): Promise<EnergySummary> {
  const response = await apiFetch(`/api/energy?ups=${encodeURIComponent(ups)}`);
  if (!response.ok) throw new Error("Could not load energy totals");
  return response.json() as Promise<EnergySummary>;
}

export async function getEnergyHistory(ups: string): Promise<EnergyPoint[]> {
  const response = await apiFetch(
    `/api/history?ups=${encodeURIComponent(ups)}&hours=24`,
  );
  if (!response.ok) throw new Error("Could not load energy history");
  return response.json() as Promise<EnergyPoint[]>;
}
