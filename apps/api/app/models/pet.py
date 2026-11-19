import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, UpdatedAtMixin


class PetParent(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "pet_parents"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)


class Patient(Base, IdMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "patients"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pet_parents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    primary_clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str] = mapped_column(String(50), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(30), nullable=False)
    dob: Mapped[date | None] = mapped_column(Date)
    dob_is_approximate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    color: Mapped[str | None] = mapped_column(String(100))
    microchip_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    chronic_conditions: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    allergies: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(Text)
    passport_slug: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
