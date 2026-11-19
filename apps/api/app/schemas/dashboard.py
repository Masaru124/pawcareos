import uuid

from pydantic import BaseModel


class DaySlotOut(BaseModel):
    """One appointment as a dashboard needs it: who, when, why, and what can happen next."""

    id: uuid.UUID
    starts_at: str
    patient_id: uuid.UUID
    patient_name: str
    species: str
    breed: str | None
    passport_slug: str
    parent_name: str | None
    parent_phone_suffix: str | None
    status: str
    source: str
    mode: str
    room_url: str | None
    doctor_name: str | None
    allergies: list[str]
    chronic_conditions: list[str]


class DayCountsOut(BaseModel):
    total: int
    waiting: int
    checked_in: int
    seen: int
    online: int
    cancelled: int


class DoctorDayOut(BaseModel):
    date: str
    timezone: str
    doctor_name: str
    counts: DayCountsOut
    appointments: list[DaySlotOut]
    next_up: DaySlotOut | None


class FrontDeskOut(BaseModel):
    date: str
    timezone: str
    clinic_name: str
    opens_at: str
    closes_at: str
    counts: DayCountsOut
    arriving: list[DaySlotOut]
    finished: list[DaySlotOut]
