import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, FlaskConical, Radio, Volume2 } from "lucide-react";
import { useState } from "react";

import { executeCommand, getCommands, type UpsCommand } from "../api/commands";

const categoryIcon = {
  battery: FlaskConical,
  panel: Radio,
  beeper: Volume2,
  dangerous: AlertTriangle,
};

const friendlyName = (name: string) =>
  name
    .replace("test.battery.start.", "Start ")
    .replace("test.battery.stop", "Stop battery test")
    .replace("test.panel.start", "Start panel test")
    .replace("test.panel.stop", "Stop panel test")
    .replace("beeper.", "Beeper ")
    .replaceAll(".", " ")
    .replace(/^\w/, (letter) => letter.toUpperCase());

export function CommandPanel() {
  const [message, setMessage] = useState("");
  const { data = [], isLoading } = useQuery({
    queryKey: ["commands"],
    queryFn: getCommands,
  });
  const mutation = useMutation({
    mutationFn: ({
      command,
      confirmed,
    }: {
      command: UpsCommand;
      confirmed: boolean;
    }) => executeCommand(command.name, confirmed),
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
          `Type ${command.name} to execute this dangerous command.`,
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
      <div className="mb-4">
        <h2 className="text-xl font-semibold">UPS controls</h2>
        <p className="mt-1 text-sm text-slate-500">
          Commands are discovered directly from this UPS.
        </p>
      </div>
      {message && (
        <p className="mb-4 rounded-xl border border-slate-700 bg-panel p-3 text-sm">
          {message}
        </p>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        {isLoading && <p className="text-slate-500">Discovering commands…</p>}
        {visible.map((command) => {
          const Icon =
            categoryIcon[command.category as keyof typeof categoryIcon] ??
            AlertTriangle;
          return (
            <button
              key={command.name}
              type="button"
              onClick={() => run(command)}
              disabled={mutation.isPending}
              className={`flex items-start gap-4 rounded-2xl border p-4 text-left transition hover:-translate-y-0.5 disabled:opacity-50 ${
                command.dangerous
                  ? "border-rose-900 bg-rose-950/20 hover:border-rose-700"
                  : "border-slate-800 bg-panel hover:border-cyan-900"
              }`}
            >
              <Icon
                className={`mt-0.5 h-5 w-5 shrink-0 ${
                  command.dangerous ? "text-rose-400" : "text-cyan-300"
                }`}
              />
              <span>
                <span className="block font-medium">
                  {friendlyName(command.name)}
                </span>
                <span className="mt-1 block text-xs text-slate-500">
                  {command.description || command.name}
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
