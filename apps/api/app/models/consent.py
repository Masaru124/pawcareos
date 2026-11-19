import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, enum_column
from app.models.enums import ConsentChannel, ConsentSource


class ConsentEvent(Base, IdMixin, CreatedAtMixin):
    """Append-only: the latest row per parent and channel is the consent state."""

    __tablename__ = "consent_events"

    pet_parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pet_parents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[ConsentChannel] = mapped_column(
        enum_column(ConsentChannel, "consent_channel"), nullable=False
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source: Mapped[ConsentSource] = mapped_column(
        enum_column(ConsentSource, "consent_source"), nullable=False
    )
    policy_version: Mapped[str] = mapped_column(String(32), default="2023-08", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinic_users.id")
    )
