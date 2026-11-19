"""consult idempotency and inbound event ledger

Revision ID: 0002_demo_seams
Revises: f92089b61760
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_demo_seams"
down_revision: str | None = "f92089b61760"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("consultations", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_unique_constraint(
        "uq_consultations_idempotency_key", "consultations", ["idempotency_key"]
    )
    op.create_table(
        "inbound_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("provider_message_id", sa.String(128), nullable=False, unique=True),
        sa.Column("from_phone", sa.String(20), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("inbound_events")
    op.drop_constraint("uq_consultations_idempotency_key", "consultations", type_="unique")
    op.drop_column("consultations", "idempotency_key")
