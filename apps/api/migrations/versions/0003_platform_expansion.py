"""pet parent accounts, clinic hours, web bookings and appointment reminders

Revision ID: 0003_platform_expansion
Revises: 0002_demo_seams
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_platform_expansion"
down_revision: str | None = "0002_demo_seams"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("opens_at", sa.Time(), nullable=False, server_default=sa.text("'09:00'")),
    )
    op.add_column(
        "clinics",
        sa.Column("closes_at", sa.Time(), nullable=False, server_default=sa.text("'18:00'")),
    )
    op.add_column(
        "clinics",
        sa.Column("slot_minutes", sa.Integer(), nullable=False, server_default=sa.text("30")),
    )

    # New enum labels are declared before any row can use them.
    op.execute("ALTER TYPE appointment_source ADD VALUE IF NOT EXISTS 'web'")
    op.execute("ALTER TYPE outbox_kind ADD VALUE IF NOT EXISTS 'appointment_reminder'")

    op.create_table(
        "pet_parent_accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "pet_parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pet_parents.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("auth_user_id", postgresql.UUID(as_uuid=True), nullable=True, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_pet_parent_accounts_pet_parent_id", "pet_parent_accounts", ["pet_parent_id"]
    )
    op.create_index(
        "ix_pet_parent_accounts_auth_user_id", "pet_parent_accounts", ["auth_user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_pet_parent_accounts_auth_user_id", table_name="pet_parent_accounts")
    op.drop_index("ix_pet_parent_accounts_pet_parent_id", table_name="pet_parent_accounts")
    op.drop_table("pet_parent_accounts")
    op.drop_column("clinics", "slot_minutes")
    op.drop_column("clinics", "closes_at")
    op.drop_column("clinics", "opens_at")
