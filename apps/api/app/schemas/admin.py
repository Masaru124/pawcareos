import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole


class ClinicAdminOut(BaseModel):
    name: str
    city: str
    address: str
    phone: str
    timezone: str
    opens_at: str
    closes_at: str


class AdminCountsOut(BaseModel):
    patients: int
    appointments_today: int
    online_today: int
    upcoming_week: int
    overdue_vaccines: int
    doctors: int
    staff: int


class StaffOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: str
    claimed: bool
    is_active: bool
    vci_suffix: str | None


class ActivityOut(BaseModel):
    action: str
    subject_type: str
    created_at: datetime
    actor_name: str | None


class AdminOverviewOut(BaseModel):
    clinic: ClinicAdminOut
    counts: AdminCountsOut
    staff: list[StaffOut]
    activity: list[ActivityOut]


class StaffInviteIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    role: UserRole = UserRole.RECEPTIONIST
    vci_registration_no: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def normalise(cls, value: str) -> str:
        email = value.strip().lower()
        local, _, domain = email.partition("@")
        if not local or "." not in domain:
            raise ValueError("Enter a valid email address")
        return email
