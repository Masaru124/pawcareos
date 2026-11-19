"""appointment doctor assignment

Booking already asks which vet the parent chose and then threw that away, so a
slot was blocked clinic-wide and no doctor could see their own day. This adds the
column and backfills history with the clinic's longest-serving doctor.

Revision ID: 0005_appointment_doctor
Revises: 0004_online_consults
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_appointment_doctor"
down_revision: str | None = "0004_online_consults"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_appointments_doctor_id",
        "appointments",
        "clinic_users",
        ["doctor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])

    # Existing rows predate the column; attribute them to the clinic's first doctor.
    op.execute(
        """
        UPDATE appointments AS a
        SET doctor_id = (
            SELECT u.id
            FROM clinic_users AS u
            WHERE u.clinic_id = a.clinic_id AND u.role = 'doctor'
            ORDER BY u.created_at, u.id
            LIMIT 1
        )
        WHERE a.doctor_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_constraint("fk_appointments_doctor_id", "appointments", type_="foreignkey")
    op.drop_column("appointments", "doctor_id")
