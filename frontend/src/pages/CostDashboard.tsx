import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Area,
  AreaChart,
} from "recharts";
import { useState } from "react";

import { billingApi, type BillingDay } from "../api/billing";

const today = new Date().toISOString().slice(0, 10);
const money = (currency: string, value: number) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency }).format(
    value,
  );

export function CostDashboard({ ups }: { ups: string }) {
  const [month, setMonth] = useState(today.slice(0, 7));
  const [day, setDay] = useState(today);
  const [hoveredDay, setHoveredDay] = useState<BillingDay | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["billing-month", ups, month],
    queryFn: () => billingApi.month(ups, month),
    enabled: Boolean(ups),
  });
  const { data: detail } = useQuery({
    queryKey: ["billing-day", ups, day],
    queryFn: () => billingApi.day(ups, day),
    enabled: Boolean(ups),
  });
  return (
    <section className="space-y-5">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Cost &amp; usage</h2>
          <p className="mt-1 text-sm text-slate-500">
            Historical energy and cost for the selected UPS.
          </p>
        </div>
        <label className="text-xs text-slate-500">
          Billing month
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="mt-1 block rounded-lg border border-slate-800 bg-panel px-3 py-2 text-sm text-slate-200"
          />
        </label>
      </header>
      {isLoading ? (
        <p className="text-sm text-slate-500">Loading billing history…</p>
      ) : (
        data && (
          <>
            {(() => {
              const displayedDay =
                hoveredDay?.date.startsWith(month) === true
                  ? hoveredDay
                  : data.days.find((entry) => entry.date === day);

              return (
                <>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <Metric
                      label="Month cost"
                      value={money(data.currency, data.cost)}
                    />
                    <Metric
                      label="Month usage"
                      value={`${data.energy_kwh.toFixed(2)} kWh`}
                    />
                    <Metric
                      label="Daily average"
                      value={`${(data.energy_kwh / Math.max(1, data.days.filter((d) => d.sample_count).length)).toFixed(2)} kWh`}
                    />
                    <Metric
                      label="Recorded days"
                      value={String(
                        data.days.filter((d) => d.sample_count).length,
                      )}
                    />
                  </div>
                  <div className="rounded-2xl border border-slate-800 bg-panel p-4">
                    <h3 className="mb-4 text-sm font-medium">Daily cost</h3>
                    <div className="overflow-x-auto pb-2">
                      <div className="h-72 min-w-[620px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={data.days}>
                            <CartesianGrid stroke="#1e293b" vertical={false} />
                            <XAxis
                              dataKey="date"
                              tickFormatter={(v) => String(Number(v.slice(-2)))}
                              tick={{ fill: "#64748b", fontSize: 11 }}
                            />
                            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
                            <Bar
                              dataKey="cost"
                              fill="#67e8f9"
                              radius={[4, 4, 0, 0]}
                              onMouseEnter={(entry) =>
                                setHoveredDay(entry.payload as BillingDay)
                              }
                              onMouseLeave={() => setHoveredDay(null)}
                              onClick={(entry) => {
                                const selected = entry.payload as BillingDay;
                                setDay(selected.date);
                                setHoveredDay(selected);
                              }}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div className="mt-3 min-h-16 rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3">
                      {displayedDay ? (
                        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                          <div>
                            <p className="text-xs text-slate-500">Day</p>
                            <p className="text-sm font-medium text-slate-200">
                              {new Date(
                                `${displayedDay.date}T00:00:00`,
                              ).toLocaleDateString(undefined, {
                                weekday: "short",
                                day: "numeric",
                                month: "short",
                              })}
                            </p>
                          </div>
                          <ChartDetail
                            label="Cost"
                            value={money(data.currency, displayedDay.cost)}
                          />
                          <ChartDetail
                            label="Usage"
                            value={`${displayedDay.energy_kwh.toFixed(3)} kWh`}
                          />
                          <ChartDetail
                            label="Peak load"
                            value={
                              displayedDay.max_power_watts === null
                                ? "—"
                                : `${displayedDay.max_power_watts.toFixed(0)} W`
                            }
                          />
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500">
                          Hover over a day to see its cost and usage. Tap it to
                          open the power timeline.
                        </p>
                      )}
                    </div>
                  </div>
                </>
              );
            })()}
          </>
        )
      )}
      <div className="rounded-2xl border border-slate-800 bg-panel p-4">
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-sm font-medium">Day detail</h3>
            {detail && (
              <p className="mt-1 text-xs text-slate-500">
                {detail.summary.energy_kwh.toFixed(3)} kWh ·{" "}
                {money(detail.summary.currency, detail.summary.cost)}
              </p>
            )}
          </div>
          <input
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm"
          />
        </div>
        {detail?.raw_available ? (
          <div className="overflow-x-auto pb-2">
            <div className="h-64 min-w-[620px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={detail.points.map((p) => ({
                    ...p,
                    time: new Date(p.recorded_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    }),
                  }))}
                >
                  <XAxis
                    dataKey="time"
                    tick={{ fill: "#64748b", fontSize: 10 }}
                    minTickGap={35}
                  />
                  <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
                  <Tooltip formatter={(v) => `${Number(v).toFixed(0)} W`} />
                  <Area dataKey="power_watts" stroke="#67e8f9" fill="#164e63" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <p className="py-10 text-center text-sm text-slate-500">
            The daily total is retained, but raw readings for this day are
            unavailable.
          </p>
        )}
      </div>
    </section>
  );
}

function ChartDetail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-sm font-medium text-slate-200">{value}</p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-panel p-4">
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold">{value}</p>
    </div>
  );
}
