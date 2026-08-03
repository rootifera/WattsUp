from datetime import UTC, datetime, timedelta

from wattsup.services.battery_tests import BatteryTestScheduler


def test_weekly_schedule_becomes_due_after_seven_days() -> None:
    now = datetime.now(UTC)

    assert BatteryTestScheduler._due(now - timedelta(days=7), now, 7)
    assert not BatteryTestScheduler._due(now - timedelta(days=6), now, 7)


def test_new_schedule_is_not_immediately_due() -> None:
    assert not BatteryTestScheduler._due(None, datetime.now(UTC), 7)
