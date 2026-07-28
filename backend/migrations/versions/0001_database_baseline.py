"""Create or adopt the initial WattsUp schema.

Revision ID: 0001_database_baseline
Revises:
"""

from alembic import op

from wattsup.database.base import Base
from wattsup.models import (  # noqa: F401
    Administrator,
    AutomationConfig,
    ManagedUps,
    NotificationChannel,
    NutServer,
    RemoteDevice,
    UpsReading,
)

revision = "0001_database_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create_all is intentional for this baseline: it creates a fresh database and safely
    # adopts development databases which predate Alembic without replacing their tables.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
