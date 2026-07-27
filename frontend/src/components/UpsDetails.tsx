import { useQuery } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";

import { getVariables, type UpsVariable } from "../api/variables";

const friendlyName = (name: string) => {
  const words = name.replaceAll(".", " ").replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
};

export function UpsDetails({ ups }: { ups: string }) {
  const { data = [] } = useQuery({
    queryKey: ["variables", ups],
    queryFn: () => getVariables(ups),
    refetchInterval: 30_000,
  });

  const groups = data.reduce<Record<string, UpsVariable[]>>(
    (result, variable) => {
      (result[variable.group] ??= []).push(variable);
      return result;
    },
    {},
  );

  return (
    <details className="mt-10 rounded-2xl border border-slate-800 bg-panel">
      <summary className="flex cursor-pointer list-none items-center justify-between p-5">
        <span>
          <span className="block text-lg font-semibold">UPS details</span>
          <span className="text-sm text-slate-500">
            {data.length} variables reported by NUT
          </span>
        </span>
        <ChevronDown className="h-5 w-5 text-slate-500" />
      </summary>
      <div className="grid gap-6 border-t border-slate-800 p-5 md:grid-cols-2">
        {Object.entries(groups).map(([group, variables]) => (
          <section key={group}>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-cyan-400">
              {friendlyName(group)}
            </h3>
            <dl className="divide-y divide-slate-800">
              {variables?.map((variable) => (
                <div
                  key={variable.name}
                  className="flex justify-between gap-4 py-2 text-sm"
                >
                  <dt className="text-slate-500" title={variable.name}>
                    {friendlyName(variable.name)}
                  </dt>
                  <dd className="break-all text-right text-slate-200">
                    {variable.value}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </details>
  );
}
