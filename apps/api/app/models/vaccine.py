import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, enum_column
from app.models.enums import (
    AppointmentSource,
    AppointmentStatus,
    ConsultMode,
    RecallStatus,
    RecallTrigger,
    ResponseAction,
    VaccineStatus,
)


class VaccineEvent(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "vaccine_events"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinic_users.id"), nullable=False
    )
    vaccine_name: Mapped[str] = mapped_column(String(100), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(100))
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    administered_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[VaccineStatus] = mapped_column(
        enum_column(VaccineStatus, "vaccine_status"),
        default=VaccineStatus.ADMINISTERED,
        nullable=False,
    )


class RecallJob(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "recall_jobs"
    __table_args__ = (
        UniqueConstraint("vaccine_event_id", "trigger", name="uq_recall_jobs_event_trigger"),
    )

    vaccine_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaccine_events.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_dispatch_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    trigger: Mapped[RecallTrigger] = mapped_column(
        enum_column(RecallTrigger, "recall_trigger"), nullable=False
    )
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[RecallStatus] = mapped_column(
        enum_column(RecallStatus, "recall_status"),
        default=RecallStatus.QUEUED,
        nullable=False,
    )
    response_action: Mapped[ResponseAction | None] = mapped_column(
        enum_column(ResponseAction, "response_action")
    )


class Appointment(Base, IdMixin, CreatedAtMixin):
    """A booking. One recall job can produce at most one appointment."""

    __tablename__ = "appointments"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    # Nullable for rows that predate doctor assignment; new bookings always set it.
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinic_users.id", ondelete="SET NULL"), index=True
    )
    recall_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recall_jobs.id"), unique=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        enum_column(AppointmentStatus, "appointment_status"),
        default=AppointmentStatus.BOOKED,
        nullable=False,
    )
    source: Mapped[AppointmentSource] = mapped_column(
        enum_column(AppointmentSource, "appointment_source"),
        default=AppointmentSource.WALK_IN,
        nullable=False,
    )
    mode: Mapped[ConsultMode] = mapped_column(
        enum_column(ConsultMode, "consult_mode"),
        default=ConsultMode.IN_CLINIC,
        nullable=False,
    )
    room_url: Mapped[str | None] = mapped_column(String(255))
