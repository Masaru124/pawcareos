import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    species: str
    breed: str | None
    gender: str
    dob: date | None
    weight_kg: float | None
    passport_slug: str
