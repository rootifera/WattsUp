import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  detail?: string;
  progress?: {
    value: number | null;
    direction: "low-to-high" | "high-to-low";
  };
}

export function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
  progress,
}: MetricCardProps) {
  const progressValue =
    progress?.value === null || progress?.value === undefined
      ? null
      : Math.min(100, Math.max(0, progress.value));

  return (
    <article className="rounded-2xl border border-slate-800 bg-panel/80 p-5 shadow-xl shadow-black/10">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm font-medium text-slate-400">{label}</p>
        <Icon className="h-5 w-5 text-cyan-300" aria-hidden="true" />
      </div>
      <p className="text-3xl font-semibold tracking-tight text-white">
        {value}
      </p>
      {progress && (
        <div className="mt-4">
          <div
            className={`relative h-2.5 overflow-hidden rounded-full ${
              progress.direction === "low-to-high"
                ? "bg-gradient-to-r from-rose-500 via-amber-400 to-emerald-400"
                : "bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500"
            }`}
            role="progressbar"
            aria-label={label}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progressValue ?? undefined}
          >
            <div
              className="absolute inset-y-0 right-0 bg-slate-800 transition-[width] duration-500"
              style={{ width: `${100 - (progressValue ?? 0)}%` }}
            />
            {progressValue !== null && (
              <div
                className="absolute inset-y-0 w-0.5 -translate-x-1/2 bg-white shadow-[0_0_6px_white] transition-[left] duration-500"
                style={{ left: `${progressValue}%` }}
              />
            )}
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-slate-600">
            <span>0%</span>
            <span>100%</span>
          </div>
        </div>
      )}
      {detail && <p className="mt-2 text-xs text-slate-500">{detail}</p>}
    </article>
  );
}
