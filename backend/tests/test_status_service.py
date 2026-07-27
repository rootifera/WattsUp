from unittest.mock import AsyncMock

from wattsup.services.status import OPTIONAL_METRIC_RETRY_LIMIT, StatusService


async def test_hides_optional_metrics_after_consecutive_missing_values() -> None:
    client = AsyncMock()
    client.get_variables.return_value = {"ups.status": "OL"}
    service = StatusService(client, "ups")

    for _ in range(OPTIONAL_METRIC_RETRY_LIMIT - 1):
        status = await service.get_status()
        assert not status.hidden_metrics.output_voltage
        assert not status.hidden_metrics.input_frequency

    status = await service.get_status()

    assert status.hidden_metrics.output_voltage
    assert status.hidden_metrics.input_frequency


async def test_optional_metric_reappears_when_value_is_reported() -> None:
    client = AsyncMock()
    client.get_variables.return_value = {"ups.status": "OL"}
    service = StatusService(client, "ups")

    for _ in range(OPTIONAL_METRIC_RETRY_LIMIT):
        await service.get_status()

    client.get_variables.return_value = {
        "ups.status": "OL",
        "output.voltage": "230.0",
    }
    status = await service.get_status()

    assert not status.hidden_metrics.output_voltage
    assert status.output_voltage == 230.0
