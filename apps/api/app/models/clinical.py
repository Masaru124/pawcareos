import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, enum_column
from app.models.enums import ConsultStatus


class Consultation(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "consultations"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinic_users.id"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    consult_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    temperature_f: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    symptoms: Mapped[str | None] = mapped_column(Text)
    clinical_examination: Mapped[str | None] = mapped_column(Text)
    provisional_diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ConsultStatus] = mapped_column(
        enum_column(ConsultStatus, "consult_status"),
        default=ConsultStatus.COMPLETED,
        nullable=False,
    )
    consult_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("500.00"), nullable=False
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)


class Prescription(Base, IdMixin, CreatedAtMixin):
    """Issued prescriptions are immutable; a correction is a new version."""

    __tablename__ = "prescriptions"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )
    rx_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prescriptions.id")
    )
    dietary_advice: Mapped[str | None] = mapped_column(Text)
    special_instructions: Mapped[str | None] = mapped_column(Text)
    pdf_storage_url: Mapped[str | None] = mapped_column(Text)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PrescriptionItem(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "prescription_items"

    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    active_ingredient: Mapped[str | None] = mapped_column(String(255))
    dosage_form: Mapped[str] = mapped_column(String(50), nullable=False)
    dosage_strength: Mapped[str | None] = mapped_column(String(50))
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    route: Mapped[str] = mapped_column(String(50), default="Oral", nullable=False)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
