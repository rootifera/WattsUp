from datetime import UTC, datetime, timedelta

from wattsup.nut.exceptions import NutError
from wattsup.nut.protocol import NutClient
from wattsup.schemas.status import HiddenMetrics, UpsStatus

OPTIONAL_METRIC_RETRY_LIMIT = 10


def _number(variables: dict[str, str], name: str) -> float | None:
    value = variables.get(name)
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


class StatusService:
    def __init__(self, client: NutClient, default_ups_name: str) -> None:
        self.client = client
        self.default_ups_name = default_ups_name
        self._missing_optional_metrics: dict[str, dict[str, int]] = {}
        self._was_on_battery: dict[str, bool] = {}
        self._power_restored_at: dict[str, datetime] = {}

    async def get_status(self, ups_name: str | None = None) -> UpsStatus:
        ups_name = ups_name or self.default_ups_name
        polled_at = datetime.now(UTC)
        try:
            variables = await self.client.get_variables(ups_name)
        except NutError as error:
            return UpsStatus(
                connected=False,
                ups_name=ups_name,
                last_poll_at=polled_at,
                error=str(error),
            )

        output_voltage = _number(variables, "output.voltage")
        input_frequency = _number(variables, "input.frequency")
        status_codes = set(variables.get("ups.status", "").split())
        on_battery = "OB" in status_codes
        if self._was_on_battery.get(ups_name) is True and not on_battery:
            self._power_restored_at[ups_name] = polled_at
        self._was_on_battery[ups_name] = on_battery
        power_restored = (
            ups_name in self._power_restored_at
            and polled_at - self._power_restored_at[ups_name] < timedelta(minutes=5)
        )
        self._record_optional_metric(ups_name, "output_voltage", output_voltage)
        self._record_optional_metric(ups_name, "input_frequency", input_frequency)
        missing = self._missing_optional_metrics[ups_name]

        return UpsStatus(
            connected=True,
            ups_name=ups_name,
            last_poll_at=polled_at,
            status=variables.get("ups.status"),
            battery_charge=_number(variables, "battery.charge"),
            battery_voltage=_number(variables, "battery.voltage"),
            runtime_seconds=_number(variables, "battery.runtime"),
            load_percent=_number(variables, "ups.load"),
            input_voltage=_number(variables, "input.voltage"),
            output_voltage=output_voltage,
            input_frequency=input_frequency,
            battery_date=variables.get("battery.date") or variables.get("battery.mfr.date"),
            battery_test_result=variables.get("ups.test.result"),
            model=variables.get("ups.model"),
            manufacturer=variables.get("ups.mfr"),
            driver=variables.get("driver.name"),
            power_restored=power_restored,
            hidden_metrics=HiddenMetrics(
                output_voltage=(missing["output_voltage"] >= OPTIONAL_METRIC_RETRY_LIMIT),
                input_frequency=(missing["input_frequency"] >= OPTIONAL_METRIC_RETRY_LIMIT),
            ),
        )

    def _record_optional_metric(self, ups_name: str, name: str, value: float | None) -> None:
        counters = self._missing_optional_metrics.setdefault(
            ups_name, {"output_voltage": 0, "input_frequency": 0}
        )
        counters[name] = counters[name] + 1 if value is None else 0
