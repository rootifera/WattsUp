"""Add durable billing history and retention controls.

Revision ID: 0002_billing_history
Revises: 0001_database_baseline
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_billing_history"
down_revision = "0001_database_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("nut_servers", sa.Column("timezone", sa.String(64), nullable=True))
    op.execute("UPDATE nut_servers SET timezone = 'UTC' WHERE timezone IS NULL")
    op.alter_column("nut_servers", "timezone", nullable=False)
    op.add_column("ups_readings", sa.Column("energy_kwh", sa.Float(), nullable=True))
    op.add_column("ups_readings", sa.Column("cost", sa.Float(), nullable=True))
    op.add_column("ups_readings", sa.Column("currency", sa.String(3), nullable=True))
    op.add_column("ups_readings", sa.Column("local_date", sa.Date(), nullable=True))
    op.create_index("ix_ups_readings_local_date", "ups_readings", ["local_date"])
    op.create_table(
        "tariff_rates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("nut_servers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(12, 6), nullable=False),
    )
    op.create_index("ix_tariff_rates_server_id", "tariff_rates", ["server_id"])
    op.create_index("ix_tariff_rates_effective_from", "tariff_rates", ["effective_from"])
    op.create_table(
        "daily_energy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "ups_id",
            sa.Integer(),
            sa.ForeignKey("managed_ups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("energy_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_power_watts", sa.Float(), nullable=True),
        sa.UniqueConstraint("ups_id", "local_date"),
    )
    op.create_index("ix_daily_energy_ups_id", "daily_energy", ["ups_id"])
    op.create_index("ix_daily_energy_local_date", "daily_energy", ["local_date"])
    op.create_table(
        "retention_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_days", sa.Integer(), nullable=True),
    )
    op.execute("INSERT INTO retention_settings (id, raw_days) VALUES (1, NULL)")
    op.execute(
        """
        INSERT INTO tariff_rates (server_id, effective_from, currency, price_per_kwh)
        SELECT id, TIMESTAMPTZ '1970-01-01 00:00:00+00', currency, price_per_kwh
        FROM nut_servers
    """
    )
    op.execute(
        """
        UPDATE ups_readings r SET
          energy_kwh = COALESCE(r.power_watts, 0) * 30 / 3600000.0,
          currency = s.currency,
          cost = COALESCE(r.power_watts, 0) * 30 / 3600000.0 * s.price_per_kwh,
          local_date = (r.recorded_at AT TIME ZONE s.timezone)::date
        FROM managed_ups u JOIN nut_servers s ON s.id = u.server_id
        WHERE r.ups_name = u.id::text
    """
    )
    op.execute(
        """
        INSERT INTO daily_energy
          (ups_id, local_date, energy_kwh, cost, currency, sample_count, max_power_watts)
        SELECT u.id, r.local_date, COALESCE(SUM(r.energy_kwh), 0), COALESCE(SUM(r.cost), 0),
               MAX(r.currency), COUNT(*), MAX(r.power_watts)
        FROM ups_readings r JOIN managed_ups u ON r.ups_name = u.id::text
        WHERE r.local_date IS NOT NULL GROUP BY u.id, r.local_date
    """
    )


def downgrade() -> None:
    op.drop_table("retention_settings")
    op.drop_table("daily_energy")
    op.drop_table("tariff_rates")
    op.drop_index("ix_ups_readings_local_date", table_name="ups_readings")
    for name in ("local_date", "currency", "cost", "energy_kwh"):
        op.drop_column("ups_readings", name)
    op.drop_column("nut_servers", "timezone")
