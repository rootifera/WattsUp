import {
  BatteryCharging,
  Gauge,
  PlugZap,
  Timer,
  Waves,
  Zap,
} from "lucide-react";

interface PowerOverviewProps {
  batteryCharge: number | null;
  batteryVoltage: number | null;
  runtimeSeconds: number | null;
  loadPercent: number | null;
  inputVoltage: number | null;
  outputVoltage: number | null;
  inputFrequency: number | null;
  showOutputVoltage: boolean;
  showInputFrequency: boolean;
  status: string | undefined;
}

const number = (value: number | null, suffix: string, digits = 0) =>
  value === null ? "—" : `${value.toFixed(digits)}${suffix}`;

const runtime = (seconds: number | null) => {
  if (seconds === null) return "—";
  const minutes = Math.floor(seconds / 60);
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
};

function Meter({
  value,
  direction,
  label,
}: {
  value: number | null;
  direction: "low-to-high" | "high-to-low";
  label: string;
}) {
  const normalized = value === null ? 0 : Math.min(100, Math.max(0, value));
  return (
    <div
      className={`relative h-2.5 overflow-hidden rounded-full ${
        direction === "low-to-high"
          ? "bg-gradient-to-r from-rose-500 via-amber-400 to-emerald-400"
          : "bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500"
      }`}
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value ?? undefined}
    >
      <div
        className="absolute inset-y-0 right-0 bg-slate-800 transition-[width] duration-500"
        style={{ width: `${100 - normalized}%` }}
      />
      {value !== null && (
        <div
          className="absolute inset-y-0 w-0.5 -translate-x-1/2 bg-white shadow-[0_0_6px_white]"
          style={{ left: `${normalized}%` }}
        />
      )}
    </div>
  );
}

function SupportingMetric({
  icon: Icon,
  label,
  value,
  detail,
  meter,
}: {
  icon: typeof Timer;
  label: string;
  value: string;
  detail?: string;
  meter?: { value: number | null; direction: "low-to-high" | "high-to-low" };
}) {
  return (
    <div className="min-w-0 p-5 md:p-6">
      <div className="mb-4 flex items-center gap-2 text-slate-500">
        <Icon className="h-4 w-4 text-cyan-300" />
        <span className="text-xs font-semibold uppercase tracking-wider">
          {label}
        </span>
      </div>
      <p className="text-2xl font-semibold tracking-tight text-white">
        {value}
      </p>
      {meter && (
        <div className="mt-4">
          <Meter
            value={meter.value}
            direction={meter.direction}
            label={label}
          />
        </div>
      )}
      {detail && <p className="mt-2 text-xs text-slate-500">{detail}</p>}
    </div>
  );
}

export function PowerOverview(props: PowerOverviewProps) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-800 bg-panel shadow-2xl shadow-black/10">
      <header className="flex items-center justify-between border-b border-slate-800 px-5 py-4 md:px-7">
        <div>
          <h2 className="font-semibold text-white">Live power</h2>
          <p className="text-xs text-slate-500">
            Current UPS operating conditions
          </p>
        </div>
        {props.status && (
          <span className="rounded-full border border-emerald-900 bg-emerald-950/50 px-3 py-1.5 text-xs font-medium text-emerald-300">
            {props.status}
          </span>
        )}
      </header>

      <div className="grid lg:grid-cols-[1.35fr_2fr]">
        <div className="border-b border-slate-800 p-6 md:p-8 lg:border-r lg:border-b-0">
          <div className="mb-8 flex items-start justify-between">
            <div>
              <p className="mb-2 text-sm font-medium text-slate-400">
                Battery reserve
              </p>
              <p className="text-5xl font-semibold tracking-[-0.05em] text-white md:text-6xl">
                {number(props.batteryCharge, "%")}
              </p>
            </div>
            <div className="rounded-2xl bg-cyan-300/10 p-3 text-cyan-300">
              <BatteryCharging className="h-7 w-7" />
            </div>
          </div>
          <Meter
            value={props.batteryCharge}
            direction="low-to-high"
            label="Battery reserve"
          />
          <div className="mt-3 flex justify-between text-xs text-slate-500">
            <span>Empty</span>
            <span>{number(props.batteryVoltage, " V", 1)}</span>
            <span>Full</span>
          </div>
        </div>

        <div className="grid sm:grid-cols-2">
          <SupportingMetric
            icon={Timer}
            label="Runtime"
            value={runtime(props.runtimeSeconds)}
            detail="Estimated time remaining"
          />
          <div className="border-t border-slate-800 sm:border-t-0 sm:border-l">
            <SupportingMetric
              icon={Gauge}
              label="UPS load"
              value={number(props.loadPercent, "%")}
              meter={{ value: props.loadPercent, direction: "high-to-low" }}
            />
          </div>
          <div className="border-t border-slate-800">
            <SupportingMetric
              icon={PlugZap}
              label="Input voltage"
              value={number(props.inputVoltage, " V", 1)}
            />
          </div>
          {props.showOutputVoltage && (
            <div className="border-t border-slate-800 sm:border-l">
              <SupportingMetric
                icon={Zap}
                label="Output voltage"
                value={number(props.outputVoltage, " V", 1)}
              />
            </div>
          )}
          {props.showInputFrequency && (
            <div className="border-t border-slate-800 sm:border-l">
              <SupportingMetric
                icon={Waves}
                label="Frequency"
                value={number(props.inputFrequency, " Hz", 1)}
              />
            </div>
          )}
          {!props.showOutputVoltage && !props.showInputFrequency && (
            <div className="border-t border-slate-800 p-5 sm:border-l md:p-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                Connection
              </p>
              <p className="mt-4 text-sm text-slate-400">Monitoring via NUT</p>
              <p className="mt-1 text-xs text-slate-600">
                Updates every 5 seconds
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
