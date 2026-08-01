"""Create or adopt the initial WattsUp schema.

Revision ID: 0001_database_baseline
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_database_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing development installations already have these tables. Alembic is introduced
    # after them, so create only what is absent while keeping this baseline frozen in time.
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "administrators" not in existing:
        op.create_table(
            "administrators",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(100), nullable=False, unique=True),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "nut_servers" not in existing:
        op.create_table(
            "nut_servers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("host", sa.String(255), nullable=False),
            sa.Column("port", sa.Integer(), nullable=False),
            sa.Column("username_encrypted", sa.Text()),
            sa.Column("password_encrypted", sa.Text()),
            sa.Column("timeout_seconds", sa.Float(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("price_per_kwh", sa.Numeric(12, 6), nullable=False),
        )
    if "managed_ups" not in existing:
        op.create_table(
            "managed_ups",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "server_id",
                sa.Integer(),
                sa.ForeignKey("nut_servers.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("nut_name", sa.String(255), nullable=False),
            sa.Column("display_name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("enabled", sa.Boolean(), nullable=False),
        )
    if "notification_channels" not in existing:
        op.create_table(
            "notification_channels",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("kind", sa.String(20), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("configuration_encrypted", sa.Text(), nullable=False),
            sa.Column("events", sa.Text(), nullable=False),
        )
    if "ups_readings" not in existing:
        op.create_table(
            "ups_readings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ups_name", sa.String(255), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(64)),
            sa.Column("battery_charge", sa.Float()),
            sa.Column("battery_voltage", sa.Float()),
            sa.Column("runtime_seconds", sa.Float()),
            sa.Column("input_voltage", sa.Float()),
            sa.Column("output_voltage", sa.Float()),
            sa.Column("load_percent", sa.Float()),
            sa.Column("power_watts", sa.Float()),
            sa.Column("power_source", sa.String(20)),
        )
        op.create_index("ix_ups_readings_ups_name", "ups_readings", ["ups_name"])
        op.create_index("ix_ups_readings_recorded_at", "ups_readings", ["recorded_at"])
    if "remote_devices" not in existing:
        op.create_table(
            "remote_devices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ups_name", sa.String(255), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("host", sa.String(255), nullable=False),
            sa.Column("port", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(100), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("use_sudo", sa.Boolean(), nullable=False),
            sa.Column("mains_state", sa.String(20), nullable=False),
            sa.Column("battery_state", sa.String(20), nullable=False),
            sa.Column("battery_threshold", sa.Integer(), nullable=False),
            sa.Column("custom_command", sa.Text()),
            sa.Column("trusted_host_key", sa.Text()),
            sa.Column("host_key_fingerprint", sa.String(255)),
            sa.Column("last_test_at", sa.DateTime(timezone=True)),
            sa.Column("last_result", sa.Text()),
        )
        op.create_index("ix_remote_devices_ups_name", "remote_devices", ["ups_name"])
    if "automation_config" not in existing:
        op.create_table(
            "automation_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("dry_run", sa.Boolean(), nullable=False),
        )


def downgrade() -> None:
    for table in (
        "automation_config",
        "remote_devices",
        "ups_readings",
        "notification_channels",
        "managed_ups",
        "nut_servers",
        "administrators",
    ):
        op.drop_table(table)
