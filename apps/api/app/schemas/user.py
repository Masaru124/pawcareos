import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    role: UserRole
    full_name: str
