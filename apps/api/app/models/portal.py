import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin


class PetParentAccount(Base, IdMixin, CreatedAtMixin):
    """A pet parent's own login. Deliberately separate from clinic_users."""

    __tablename__ = "pet_parent_accounts"

    pet_parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pet_parents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    auth_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), unique=True, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
