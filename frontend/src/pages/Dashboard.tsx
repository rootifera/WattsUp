import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  LogOut,
  Power,
  SlidersHorizontal,
  Zap,
} from "lucide-react";
import { useState } from "react";

import { getStatus } from "../api/status";
import { CommandPanel } from "../components/CommandPanel";
import { PowerOverview } from "../components/PowerOverview";
import { UpsDetails } from "../components/UpsDetails";
import { ShutdownAutomation } from "./ShutdownAutomation";

const NUT_STATUS_LABELS: Record<string, string> = {
  OL: "Online",
  OB: "On battery",
  LB: "Low battery",
  RB: "Replace battery",
  CHRG: "Charging",
  DISCHRG: "Discharging",
  BYPASS: "Bypass active",
  CAL: "Calibrating",
  OFF: "Output off",
  OVER: "Overloaded",
  TRIM: "Trimming high input voltage",
  BOOST: "Boosting low input voltage",
  FSD: "Forced shutdown",
};

const HEADLINES = {
  online: [
    "Keeping the lights on.",
    "Everything's under control.",
    "All systems powered.",
    "Just keep charging.",
    "Power is good.",
  ],
  onBattery: [
    "I've got a bad feeling about this…",
    "This is where the fun begins.",
    "Stay calm.",
    "Running on borrowed time.",
    "Battery mode engaged.",
  ],
  critical: [
    "Houston, we've had a problem.",
    "Hold on to your butts.",
    "Brace for impact.",
    "Initiating Plan B.",
    "Time to say goodnight.",
  ],
  restored: [
    "I'll be back.",
    "Crisis averted.",
    "We live to serve another outage.",
    "Normal service has resumed.",
  ],
};

const headlineFor = (
  status: string | null | undefined,
  batteryCharge: number | null | undefined,
  powerRestored: boolean,
) => {
  const codes = new Set((status || "").split(/\s+/));
  let choices = HEADLINES.online;
  if (codes.has("LB") || (codes.has("OB") && (batteryCharge ?? 100) <= 10)) {
    choices = HEADLINES.critical;
  } else if (codes.has("OB")) {
    choices = HEADLINES.onBattery;
  } else if (powerRestored) {
    choices = HEADLINES.restored;
  }
  return choices[Math.floor(batteryCharge ?? 0) % choices.length];
};

const friendlyStatus = (
  status: string | null | undefined,
  batteryCharge: number | null | undefined,
) => {
  if (!status) return undefined;
  const codes = status.split(/\s+/);
  const labels = codes.map((code) => NUT_STATUS_LABELS[code] ?? code);
  if (
    codes.includes("OL") &&
    !codes.includes("CHRG") &&
    !codes.includes("DISCHRG") &&
    batteryCharge !== null &&
    batteryCharge !== undefined &&
    batteryCharge >= 100
  ) {
    labels.push("Battery full");
  }
  return labels.join(" · ");
};

interface DashboardProps {
  onLogout: () => void;
}

export function Dashboard({ onLogout }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<
    "dashboard" | "controls" | "shutdown"
  >("dashboard");
  const { data, isLoading, isError } = useQuery({
    queryKey: ["status"],
    queryFn: getStatus,
    refetchInterval: 5_000,
  });

  const connected = data?.connected ?? false;
  const showOutputVoltage = !data?.hidden_metrics.output_voltage;
  const showInputFrequency = !data?.hidden_metrics.input_frequency;
  const statusLabel = friendlyStatus(data?.status, data?.battery_charge);
  const headline = headlineFor(
    data?.status,
    data?.battery_charge,
    data?.power_restored ?? false,
  );

  return (
    <main className="min-h-screen bg-ink px-5 py-8 text-slate-100 md:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-10 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <div className="mb-3 flex items-center gap-3">
              <div className="rounded-xl bg-cyan-300 p-2 text-slate-950">
                <Zap className="h-5 w-5" fill="currentColor" />
              </div>
              <span className="font-semibold tracking-wide">WATTSUP</span>
            </div>
            <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
              {headline}
            </h1>
            <p className="mt-2 text-slate-400">
              {data?.manufacturer || "Network UPS Tools"}{" "}
              {data?.model || "monitor"}
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-full border border-slate-800 bg-panel px-4 py-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                connected
                  ? "bg-emerald-400 shadow-[0_0_12px_#34d399]"
                  : "bg-rose-400"
              }`}
            />
            <span className="text-sm text-slate-300">
              {isLoading
                ? "Connecting…"
                : connected
                  ? "NUT connected"
                  : "NUT unavailable"}
            </span>
            <button
              type="button"
              onClick={onLogout}
              className="ml-2 border-l border-slate-700 pl-3 text-slate-500 hover:text-white"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        {isError && (
          <div className="mb-6 rounded-xl border border-rose-900 bg-rose-950/40 p-4 text-rose-200">
            The WattsUp API could not be reached.
          </div>
        )}
        {data?.error && (
          <div className="mb-6 rounded-xl border border-amber-900 bg-amber-950/30 p-4 text-amber-100">
            {data.error}. Check your NUT connection settings.
          </div>
        )}

        <nav
          className="mb-6 flex gap-2 border-b border-slate-800"
          aria-label="Main navigation"
        >
          {[
            {
              id: "dashboard" as const,
              label: "Dashboard",
              icon: LayoutDashboard,
            },
            {
              id: "controls" as const,
              label: "UPS controls",
              icon: SlidersHorizontal,
            },
            {
              id: "shutdown" as const,
              label: "Shutdown automation",
              icon: Power,
            },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition ${
                activeTab === id
                  ? "border-cyan-300 text-cyan-200"
                  : "border-transparent text-slate-500 hover:text-slate-200"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>

        {activeTab === "dashboard" ? (
          <>
            <PowerOverview
              batteryCharge={data?.battery_charge ?? null}
              batteryVoltage={data?.battery_voltage ?? null}
              runtimeSeconds={data?.runtime_seconds ?? null}
              loadPercent={data?.load_percent ?? null}
              inputVoltage={data?.input_voltage ?? null}
              outputVoltage={data?.output_voltage ?? null}
              inputFrequency={data?.input_frequency ?? null}
              showOutputVoltage={showOutputVoltage}
              showInputFrequency={showInputFrequency}
              status={statusLabel}
            />
            <UpsDetails />
          </>
        ) : activeTab === "controls" ? (
          <CommandPanel />
        ) : (
          <ShutdownAutomation />
        )}

        <footer className="mt-8 text-xs text-slate-600">
          {data
            ? `Last poll ${new Date(data.last_poll_at).toLocaleString()}`
            : "Awaiting first poll"}
        </footer>
      </div>
    </main>
  );
}
