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
    def __init__(self, client: NutClient, ups_name: str) -> None:
        self.client = client
        self.ups_name = ups_name
        self._missing_optional_metrics = {
            "output_voltage": 0,
            "input_frequency": 0,
        }
        self._was_on_battery: bool | None = None
        self._power_restored_at: datetime | None = None

    async def get_status(self) -> UpsStatus:
        polled_at = datetime.now(UTC)
        try:
            variables = await self.client.get_variables(self.ups_name)
        except NutError as error:
            return UpsStatus(
                connected=False,
                ups_name=self.ups_name,
                last_poll_at=polled_at,
                error=str(error),
            )

        output_voltage = _number(variables, "output.voltage")
        input_frequency = _number(variables, "input.frequency")
        status_codes = set(variables.get("ups.status", "").split())
        on_battery = "OB" in status_codes
        if self._was_on_battery is True and not on_battery:
            self._power_restored_at = polled_at
        self._was_on_battery = on_battery
        power_restored = (
            self._power_restored_at is not None
            and polled_at - self._power_restored_at < timedelta(minutes=5)
        )
        self._record_optional_metric("output_voltage", output_voltage)
        self._record_optional_metric("input_frequency", input_frequency)

        return UpsStatus(
            connected=True,
            ups_name=self.ups_name,
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
                output_voltage=(
                    self._missing_optional_metrics["output_voltage"] >= OPTIONAL_METRIC_RETRY_LIMIT
                ),
                input_frequency=(
                    self._missing_optional_metrics["input_frequency"] >= OPTIONAL_METRIC_RETRY_LIMIT
                ),
            ),
        )

    def _record_optional_metric(self, name: str, value: float | None) -> None:
        self._missing_optional_metrics[name] = (
            self._missing_optional_metrics[name] + 1 if value is None else 0
        )
