import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";

import { getEnergy, getEnergyHistory } from "../api/energy";

const currency = (code: string, value: number) =>
  new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: code,
  }).format(value);

export function EnergyPanel({ ups }: { ups: string }) {
  const { data } = useQuery({
    queryKey: ["energy", ups],
    queryFn: () => getEnergy(ups),
    refetchInterval: 30_000,
  });
  const { data: history = [] } = useQuery({
    queryKey: ["energy-history", ups],
    queryFn: () => getEnergyHistory(ups),
    refetchInterval: 30_000,
  });
  if (!data?.current_watts && history.length === 0) return null;
  const points = history.map((point) => ({
    time: new Date(point.recorded_at).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
    watts: point.power_watts,
  }));
  return (
    <section className="mt-6 overflow-hidden rounded-2xl border border-slate-800 bg-panel">
      <div className="grid divide-y divide-slate-800 md:grid-cols-4 md:divide-x md:divide-y-0">
        <Metric
          label={`${data?.power_source === "measured" ? "Current" : "Estimated"} demand`}
          value={`${(data?.current_watts ?? 0).toFixed(0)} W`}
        />
        <Metric
          label="Energy today"
          value={`${(data?.today_kwh ?? 0).toFixed(2)} kWh`}
        />
        <Metric
          label="Cost today"
          value={currency(data?.currency ?? "GBP", data?.today_cost ?? 0)}
        />
        <Metric
          label="Cost this month"
          value={currency(data?.currency ?? "GBP", data?.month_cost ?? 0)}
          detail={`${(data?.month_kwh ?? 0).toFixed(2)} kWh`}
        />
      </div>
      {points.length > 1 && (
        <div className="h-52 border-t border-slate-800 px-3 pt-5">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points}>
              <defs>
                <linearGradient id="power-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#67e8f9" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#67e8f9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                tick={{ fill: "#64748b", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                minTickGap={40}
              />
              <Tooltip
                contentStyle={{
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: 10,
                }}
                formatter={(value) => [
                  `${Number(value).toFixed(0)} W`,
                  "Power",
                ]}
              />
              <Area
                type="monotone"
                dataKey="watts"
                stroke="#67e8f9"
                fill="url(#power-fill)"
                strokeWidth={2}
                connectNulls
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}

function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <div className="p-5">
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold">{value}</p>
      {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
    </div>
  );
}
