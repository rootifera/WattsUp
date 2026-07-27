import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ChevronDown,
  FlaskConical,
  Radio,
  Settings,
  Volume2,
} from "lucide-react";
import { useState, type ComponentType } from "react";

import { executeCommand, getCommands, type UpsCommand } from "../api/commands";

interface Category {
  id: string;
  title: string;
  description: string;
  icon: ComponentType<{ className?: string }>;
  collapsed?: boolean;
  dangerous?: boolean;
}

const categories: Category[] = [
  {
    id: "battery",
    title: "Battery tests",
    description: "Check battery health and runtime performance.",
    icon: FlaskConical,
  },
  {
    id: "beeper",
    title: "Beeper",
    description: "Control audible UPS alerts.",
    icon: Volume2,
  },
  {
    id: "panel",
    title: "Panel tests",
    description: "Test indicators and controls on the UPS.",
    icon: Radio,
  },
  {
    id: "driver",
    title: "Driver actions",
    description: "Advanced controls for the running NUT driver.",
    icon: Settings,
    collapsed: true,
  },
  {
    id: "dangerous",
    title: "Dangerous power actions",
    description: "These actions may immediately interrupt connected equipment.",
    icon: AlertTriangle,
    collapsed: true,
    dangerous: true,
  },
  {
    id: "other",
    title: "Other controls",
    description: "Additional commands reported by this UPS.",
    icon: Settings,
  },
];

const friendlyName = (name: string) =>
  name
    .replace("test.battery.start.deep", "Start deep battery test")
    .replace("test.battery.start.quick", "Start quick battery test")
    .replace("test.battery.stop", "Stop battery test")
    .replace("test.panel.start", "Start panel test")
    .replace("test.panel.stop", "Stop panel test")
    .replace("beeper.", "")
    .replace("driver.", "")
    .replaceAll(".", " ")
    .replace(/^\w/, (letter) => letter.toUpperCase());

function CommandButton({
  command,
  pending,
  onRun,
}: {
  command: UpsCommand;
  pending: boolean;
  onRun: (command: UpsCommand) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onRun(command)}
      disabled={pending}
      className={`rounded-xl border px-4 py-3 text-left transition disabled:opacity-50 ${
        command.dangerous
          ? "border-rose-900/80 bg-rose-950/20 hover:border-rose-700 hover:bg-rose-950/40"
          : "border-slate-800 bg-slate-950/30 hover:border-cyan-900 hover:bg-slate-900"
      }`}
    >
      <span className="block text-sm font-medium text-slate-100">
        {friendlyName(command.name)}
      </span>
      <span className="mt-1 block text-xs leading-relaxed text-slate-500">
        {command.description || command.name}
      </span>
    </button>
  );
}

export function CommandPanel({ ups }: { ups: string }) {
  const [message, setMessage] = useState("");
  const { data = [], isLoading } = useQuery({
    queryKey: ["commands", ups],
    queryFn: () => getCommands(ups),
  });
  const mutation = useMutation({
    mutationFn: ({
      command,
      confirmed,
    }: {
      command: UpsCommand;
      confirmed: boolean;
    }) => executeCommand(command.name, confirmed, ups),
    onSuccess: (_, { command }) =>
      setMessage(`${friendlyName(command.name)} accepted by NUT.`),
    onError: (error) =>
      setMessage(error instanceof Error ? error.message : "Command failed"),
  });

  const run = (command: UpsCommand) => {
    let confirmed = false;
    if (command.dangerous) {
      confirmed =
        window.prompt(
          `This may interrupt power. Type ${command.name} to continue.`,
        ) === command.name;
      if (!confirmed) return;
    } else if (!window.confirm(`Run “${friendlyName(command.name)}”?`)) {
      return;
    }
    mutation.mutate({ command, confirmed });
  };

  const visible = data.filter(
    (command) => command.name !== "beeper.on" && command.name !== "beeper.off",
  );

  return (
    <section>
      <div className="mb-6">
        <h2 className="text-xl font-semibold">UPS controls</h2>
        <p className="mt-1 text-sm text-slate-500">
          Commands available on this UPS, organized by purpose and risk.
        </p>
      </div>
      {message && (
        <p className="mb-5 rounded-xl border border-slate-700 bg-panel p-3 text-sm">
          {message}
        </p>
      )}
      {isLoading && <p className="text-slate-500">Discovering commands…</p>}

      <div className="space-y-4">
        {categories.map((category) => {
          const commands = visible.filter(
            (command) => command.category === category.id,
          );
          if (commands.length === 0) return null;
          const Icon = category.icon;
          const content = (
            <div className="grid gap-3 border-t border-slate-800 p-4 md:grid-cols-2">
              {commands.map((command) => (
                <CommandButton
                  key={command.name}
                  command={command}
                  pending={mutation.isPending}
                  onRun={run}
                />
              ))}
            </div>
          );

          if (category.collapsed) {
            return (
              <details
                key={category.id}
                className={`overflow-hidden rounded-2xl border bg-panel ${
                  category.dangerous ? "border-rose-900/70" : "border-slate-800"
                }`}
              >
                <summary className="flex cursor-pointer list-none items-center gap-4 p-5">
                  <Icon
                    className={`h-5 w-5 shrink-0 ${
                      category.dangerous ? "text-rose-400" : "text-amber-300"
                    }`}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium">{category.title}</span>
                    <span className="mt-0.5 block text-xs text-slate-500">
                      {category.description}
                    </span>
                  </span>
                  <span className="rounded-full bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                    {commands.length}
                  </span>
                  <ChevronDown className="h-4 w-4 text-slate-500" />
                </summary>
                {content}
              </details>
            );
          }

          return (
            <section
              key={category.id}
              className="overflow-hidden rounded-2xl border border-slate-800 bg-panel"
            >
              <header className="flex items-center gap-4 p-5">
                <div className="rounded-xl bg-cyan-300/10 p-2.5 text-cyan-300">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-medium">{category.title}</h3>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {category.description}
                  </p>
                </div>
              </header>
              {content}
            </section>
          );
        })}
      </div>
    </section>
  );
}
