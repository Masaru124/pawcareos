"""legacy record vault

Phase 1 of the v3 spec lets a family digitise the paper vaccine cards and lab
reports they had before the clinic went digital. Those uploads are parent-authored
and unverified, so they live in their own table rather than in the
clinic-generated record tables.

Revision ID: 0006_legacy_records
Revises: 0005_appointment_doctor
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_legacy_records"
down_revision: str | None = "0005_appointment_doctor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "legacy_records",
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("record_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["pet_parent_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_legacy_records_patient_id", "legacy_records", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_legacy_records_patient_id", table_name="legacy_records")
    op.drop_table("legacy_records")
