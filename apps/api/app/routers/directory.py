import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import SessionDep
from app.schemas.directory import (
    AvailabilityOut,
    BookingIn,
    BookingOut,
    DoctorOut,
    RoomOut,
)
from app.services import booking as booking_service

router = APIRouter(prefix="/directory", tags=["directory"])


@router.get("/doctors", response_model=list[DoctorOut])
async def list_doctors(
    session: SessionDep,
    q: Annotated[str | None, Query(min_length=2, max_length=60)] = None,
    city: Annotated[str | None, Query(min_length=2, max_length=60)] = None,
) -> list[DoctorOut]:
    """Public: verified vets only, no clinic-internal identifiers."""
    return await booking_service.search_doctors(session, query=q, city=city)


@router.get("/doctors/{doctor_id}/availability", response_model=AvailabilityOut)
async def doctor_availability(
    doctor_id: uuid.UUID,
    session: SessionDep,
    day: Annotated[date | None, Query(alias="date")] = None,
    mode: Annotated[str, Query()] = "in_clinic",
) -> AvailabilityOut:
    return await booking_service.availability(
        session, doctor_id=doctor_id, day=day, mode=mode
    )


@router.post("/bookings", response_model=BookingOut, status_code=201)
async def create_booking(payload: BookingIn, session: SessionDep) -> BookingOut:
    """Anyone can book; only a clinic user can prescribe."""
    return await booking_service.book(session, payload=payload)


@router.get("/rooms/{appointment_id}", response_model=RoomOut)
async def get_room(appointment_id: uuid.UUID, session: SessionDep) -> RoomOut:
    """The join page needs the room and who it is for. The id is unguessable."""
    return await booking_service.room(session, appointment_id=appointment_id)
