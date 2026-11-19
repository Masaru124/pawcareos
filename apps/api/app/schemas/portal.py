import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

PHONE_PATTERN = r"^\+[1-9]\d{9,14}$"


class PortalPetOut(BaseModel):
    id: uuid.UUID
    name: str
    species: str
    breed: str | None
    passport_slug: str
    clinic_name: str
    next_due: date | None


class PortalMeOut(BaseModel):
    parent_name: str
    phone_suffix: str
    pets: list[PortalPetOut]


class PortalAppointmentOut(BaseModel):
    id: uuid.UUID
    starts_at: datetime
    patient_name: str
    clinic_name: str
    status: str
    mode: str = "in_clinic"
    room_url: str | None = None


class RecordVaccineOut(BaseModel):
    vaccine_name: str
    brand_name: str | None
    batch_number: str
    administered_date: date
    next_due_date: date
    status: str
    doctor_name: str


class RecordItemOut(BaseModel):
    medication_name: str
    dosage_form: str
    dosage_strength: str | None
    frequency: str
    duration_days: int
    route: str
    is_chronic: bool


class RecordPrescriptionOut(BaseModel):
    rx_code: str
    date: date
    doctor_name: str
    diagnosis: str
    items: list[RecordItemOut]


class PetRecordsOut(BaseModel):
    pet_id: uuid.UUID
    name: str
    species: str
    breed: str | None
    passport_slug: str
    clinic_name: str
    vaccines: list[RecordVaccineOut]
    prescriptions: list[RecordPrescriptionOut]


class ParentInviteIn(BaseModel):
    parent_phone: str = Field(pattern=PHONE_PATTERN)
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def looks_like_email(cls, value: str) -> str:
        email = value.strip().lower()
        local, _, domain = email.partition("@")
        if not local or "." not in domain:
            raise ValueError("Enter a valid email address")
        return email


class ParentInviteOut(BaseModel):
    parent_name: str
    email: str
    already_claimed: bool
