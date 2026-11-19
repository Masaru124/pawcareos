import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, enum_column
from app.models.enums import OutboxKind, OutboxStatus


class MessageOutbox(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "message_outbox"
    __table_args__ = (
        Index("ix_message_outbox_due", "status", "next_attempt_at"),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False
    )
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    kind: Mapped[OutboxKind] = mapped_column(enum_column(OutboxKind, "outbox_kind"), nullable=False)
    to_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        enum_column(OutboxStatus, "outbox_status"), default=OutboxStatus.QUEUED, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    provider_message_id: Mapped[str | None] = mapped_column(String(128))
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InboundEvent(Base, IdMixin):
    """One row per provider message id, so a Meta retry cannot act twice."""

    __tablename__ = "inbound_events"

    provider_message_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    from_phone: Mapped[str | None] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class JobRun(Base, IdMixin):
    __tablename__ = "job_runs"

    job_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enqueued: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)


class AuditLog(Base, IdMixin):
    __tablename__ = "audit_log"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinic_users.id")
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
