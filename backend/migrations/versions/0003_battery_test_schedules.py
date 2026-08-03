"""Add periodic battery test schedules and result storage.

Revision ID: 0003_battery_test_schedules
Revises: 0002_billing_history
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_battery_test_schedules"
down_revision = "0002_billing_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    now = sa.text("CURRENT_TIMESTAMP")
    op.add_column(
        "managed_ups",
        sa.Column("quick_test_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "managed_ups",
        sa.Column("deep_test_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "managed_ups",
        sa.Column("last_quick_test_at", sa.DateTime(timezone=True), server_default=now),
    )
    op.add_column(
        "managed_ups",
        sa.Column("last_deep_test_at", sa.DateTime(timezone=True), server_default=now),
    )
    op.add_column("managed_ups", sa.Column("last_battery_test_result", sa.Text()))
    op.add_column(
        "managed_ups", sa.Column("last_battery_test_result_at", sa.DateTime(timezone=True))
    )


def downgrade() -> None:
    for name in (
        "last_battery_test_result_at",
        "last_battery_test_result",
        "last_deep_test_at",
        "last_quick_test_at",
        "deep_test_enabled",
        "quick_test_enabled",
    ):
        op.drop_column("managed_ups", name)
