import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ConsentSource

PHONE_PATTERN = r"^\+[1-9]\d{9,14}$"


class ParentIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(pattern=PHONE_PATTERN)

    @field_validator("phone")
    @classmethod
    def strip_spaces(cls, value: str) -> str:
        return value.replace(" ", "").replace("-", "")


class PatientIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    species: str = Field(min_length=2, max_length=50)
    breed: str | None = Field(default=None, max_length=100)
    gender: str = Field(min_length=1, max_length=30)
    dob: date | None = None
    dob_is_approximate: bool = False
    weight_kg: float | None = Field(default=None, ge=0, le=200)


class ConsentIn(BaseModel):
    granted: bool
    source: ConsentSource = ConsentSource.INTAKE_TAP


class IntakeIn(BaseModel):
    parent: ParentIn
    patient: PatientIn
    consent: ConsentIn | None = None


class IntakeOut(BaseModel):
    parent_id: uuid.UUID
    patient_id: uuid.UUID
    passport_slug: str


class PatientSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    species: str
    breed: str | None
    passport_slug: str
    parent_name: str | None = None
    parent_phone_suffix: str | None = None


class PatientListOut(BaseModel):
    items: list[PatientSummary]
