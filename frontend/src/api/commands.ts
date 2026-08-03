import { apiFetch } from "./client";

export interface UpsCommand {
  name: string;
  category: string;
  dangerous: boolean;
  description: string | null;
}

export interface BatteryTestSchedule {
  quick_enabled: boolean;
  deep_enabled: boolean;
  last_quick_test_at: string | null;
  last_deep_test_at: string | null;
  last_result: string | null;
  last_result_at: string | null;
}

export async function getCommands(ups: string): Promise<UpsCommand[]> {
  const response = await apiFetch(
    `/api/commands?ups=${encodeURIComponent(ups)}`,
  );
  if (!response.ok) throw new Error("Could not load UPS commands");
  return response.json() as Promise<UpsCommand[]>;
}

export async function executeCommand(
  name: string,
  confirmed: boolean,
  ups: string,
): Promise<void> {
  const response = await apiFetch(
    `/api/command/${encodeURIComponent(name)}?ups=${encodeURIComponent(ups)}`,
    {
      method: "POST",
      body: JSON.stringify({ confirmed }),
    },
  );
  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new Error(body.detail || "Command failed");
  }
}

export async function getBatteryTestSchedule(
  ups: string,
): Promise<BatteryTestSchedule> {
  const response = await apiFetch(
    `/api/battery-test-schedule?ups=${encodeURIComponent(ups)}`,
  );
  if (!response.ok) throw new Error("Could not load battery test schedule");
  return response.json() as Promise<BatteryTestSchedule>;
}

export async function updateBatteryTestSchedule(
  ups: string,
  quickEnabled: boolean,
  deepEnabled: boolean,
): Promise<BatteryTestSchedule> {
  const response = await apiFetch(
    `/api/battery-test-schedule?ups=${encodeURIComponent(ups)}`,
    {
      method: "PUT",
      body: JSON.stringify({
        quick_enabled: quickEnabled,
        deep_enabled: deepEnabled,
      }),
    },
  );
  if (!response.ok) throw new Error("Could not update battery test schedule");
  return response.json() as Promise<BatteryTestSchedule>;
}
