import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

PHONE_PATTERN = r"^\+[1-9]\d{9,14}$"


class ClinicOut(BaseModel):
    id: uuid.UUID
    name: str
    city: str
    address: str
    phone: str


class DoctorOut(BaseModel):
    doctor_id: uuid.UUID
    full_name: str
    qualification: str | None
    vci_suffix: str
    clinic: ClinicOut


class SlotOut(BaseModel):
    starts_at: datetime
    label: str


class AvailabilityOut(BaseModel):
    day: date
    timezone: str
    mode: str = "in_clinic"
    slots: list[SlotOut]


class BookingParentIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(pattern=PHONE_PATTERN)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("phone")
    @classmethod
    def strip_spaces(cls, value: str) -> str:
        return value.replace(" ", "").replace("-", "")


class BookingPatientIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    species: str = Field(default="Canine", min_length=2, max_length=50)
    breed: str | None = Field(default=None, max_length=100)
    gender: str = Field(default="Unknown", min_length=1, max_length=30)


class BookingIn(BaseModel):
    doctor_id: uuid.UUID
    starts_at: datetime
    parent: BookingParentIn
    patient: BookingPatientIn
    consent: bool = True
    mode: str = "in_clinic"


class BookingOut(BaseModel):
    appointment_id: uuid.UUID
    starts_at: datetime
    clinic_name: str
    doctor_name: str
    passport_slug: str
    passport_url: str
    reminders_queued: int
    mode: str
    room_url: str | None


class RoomOut(BaseModel):
    appointment_id: uuid.UUID
    starts_at: datetime
    mode: str
    room_url: str | None
    clinic_name: str
    doctor_name: str
    patient_name: str
