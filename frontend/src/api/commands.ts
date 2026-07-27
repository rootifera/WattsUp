import { apiFetch } from "./client";

export interface UpsCommand {
  name: string;
  category: string;
  dangerous: boolean;
  description: string | null;
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
