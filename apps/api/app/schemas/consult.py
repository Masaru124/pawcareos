import uuid

from pydantic import BaseModel, Field, model_validator

from app.domain.vaccination import VaccineKind


class MedicationIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=2, max_length=50)
    duration_days: int = Field(ge=1, le=365)
    route: str = Field(default="Oral", max_length=50)
    is_chronic: bool = False


class VaccinationIn(BaseModel):
    kind: VaccineKind
    vaccine_name: str = Field(min_length=2, max_length=100)
    brand_name: str | None = Field(default=None, max_length=100)
    batch_number: str = Field(min_length=1, max_length=100)


class ConsultIn(BaseModel):
    patient_id: uuid.UUID
    weight_kg: float | None = Field(default=None, ge=0, le=200)
    temperature_f: float | None = Field(default=None, ge=90, le=115)
    symptoms: str | None = None
    provisional_diagnosis: str = Field(min_length=3, max_length=500)
    medications: list[MedicationIn] = Field(default_factory=list)
    vaccinations: list[VaccinationIn] = Field(default_factory=list)
    dietary_advice: str | None = None
    special_instructions: str | None = None

    @model_validator(mode="after")
    def require_content(self) -> "ConsultIn":
        if not self.medications and not self.vaccinations:
            raise ValueError("Add at least one medication or vaccine")
        return self


class ConsultOut(BaseModel):
    consultation_id: uuid.UUID
    rx_code: str
    passport_url: str
    whatsapp_status: str
