"""appointment mode and video room url

Revision ID: 0004_online_consults
Revises: 0003_platform_expansion
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_online_consults"
down_revision: str | None = "0003_platform_expansion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE consult_mode AS ENUM ('in_clinic', 'online')")
    op.add_column(
        "appointments",
        sa.Column(
            "mode",
            sa.Enum("in_clinic", "online", name="consult_mode"),
            nullable=False,
            server_default="in_clinic",
        ),
    )
    op.add_column("appointments", sa.Column("room_url", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "room_url")
    op.drop_column("appointments", "mode")
    op.execute("DROP TYPE consult_mode")
