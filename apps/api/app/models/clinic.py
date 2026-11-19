import uuid
from datetime import time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin, UpdatedAtMixin, enum_column
from app.models.enums import UserRole


class Clinic(Base, IdMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "clinics"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_entity_name: Mapped[str | None] = mapped_column(String(255))
    gstin: Mapped[str | None] = mapped_column(String(15))
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    address_street: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    upi_vpa: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    opens_at: Mapped[time] = mapped_column(Time, default=time(9, 0), nullable=False)
    closes_at: Mapped[time] = mapped_column(Time, default=time(18, 0), nullable=False)
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="pro", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)


class ClinicUser(Base, IdMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "clinic_users"
    __table_args__ = (
        CheckConstraint(
            "role <> 'doctor' OR vci_registration_no IS NOT NULL",
            name="ck_clinic_users_doctor_vci",
        ),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    auth_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    vci_registration_no: Mapped[str | None] = mapped_column(String(100))
    qualification: Mapped[str | None] = mapped_column(String(255), default="B.V.Sc & A.H.")
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole, "user_role"), default=UserRole.DOCTOR, nullable=False
    )
    signature_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def is_doctor(self) -> bool:
        return self.role is UserRole.DOCTOR


class ClinicalCounter(Base):
    """Sequence per clinic per year for the rx_code suffix."""

    __tablename__ = "clinical_counters"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), primary_key=True
    )
    year: Mapped[int] = mapped_column(primary_key=True)
    next_seq: Mapped[int] = mapped_column(default=1, nullable=False)
