import { apiFetch } from "./client";

export interface BillingDay {
  date: string;
  energy_kwh: number;
  cost: number;
  currency: string;
  sample_count: number;
  max_power_watts: number | null;
}

export interface BillingMonth {
  month: string;
  energy_kwh: number;
  cost: number;
  currency: string;
  days: BillingDay[];
}

export interface BillingDayDetail {
  summary: BillingDay;
  raw_available: boolean;
  points: {
    recorded_at: string;
    power_watts: number | null;
    energy_kwh: number | null;
    cost: number | null;
  }[];
}

async function get<T>(path: string): Promise<T> {
  const response = await apiFetch(path);
  if (!response.ok) throw new Error("Could not load billing history");
  return response.json() as Promise<T>;
}

export const billingApi = {
  month: (ups: string, month: string) =>
    get<BillingMonth>(
      `/api/billing/month?ups=${encodeURIComponent(ups)}&month=${month}`,
    ),
  day: (ups: string, day: string) =>
    get<BillingDayDetail>(
      `/api/billing/day?ups=${encodeURIComponent(ups)}&day=${day}`,
    ),
};
