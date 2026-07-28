export interface UpsStatus {
  connected: boolean;
  ups_name: string;
  last_poll_at: string;
  error: string | null;
  status: string | null;
  battery_charge: number | null;
  battery_voltage: number | null;
  runtime_seconds: number | null;
  load_percent: number | null;
  input_voltage: number | null;
  output_voltage: number | null;
  input_frequency: number | null;
  power_watts: number | null;
  power_source: "measured" | "estimated" | null;
  battery_date: string | null;
  battery_test_result: string | null;
  model: string | null;
  manufacturer: string | null;
  driver: string | null;
  power_restored: boolean;
  hidden_metrics: {
    output_voltage: boolean;
    input_frequency: boolean;
  };
}
