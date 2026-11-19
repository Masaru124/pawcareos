"""Role dashboards.

Each role gets its own question answered: a doctor asks what is in front of them,
the front desk asks who is arriving, the owner asks how the clinic is doing. The
owner panel keeps its own endpoint; the day board here is shared machinery.
"""

import uuid
from datetime import date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser, SessionDep
from app.models import (
    Appointment,
    AppointmentStatus,
    Clinic,
    ClinicUser,
    Patient,
    PetParent,
    UserRole,
)
from app.schemas.dashboard import DayCountsOut, DaySlotOut, DoctorDayOut, FrontDeskOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _zone(clinic: Clinic | None) -> ZoneInfo:
    try:
        return ZoneInfo(clinic.timezone if clinic else "Asia/Kolkata")
    except Exception:  # noqa: BLE001 - a bad stored zone must not block a dashboard
        return ZoneInfo("Asia/Kolkata")


def require_roles(*roles: UserRole):
    """Narrow a shared clinic endpoint to the roles whose dashboard it is."""

    async def dependency(user: CurrentUser) -> ClinicUser:
        if user.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "This dashboard belongs to " + ", ".join(role.value for role in roles) + ".",
            )
        return user

    return dependency


def _slot(
    appointment: Appointment,
    patient: Patient,
    parent: PetParent | None,
    doctor: ClinicUser | None,
    zone: ZoneInfo,
) -> DaySlotOut:
    return DaySlotOut(
        id=appointment.id,
        starts_at=appointment.starts_at.astimezone(zone).strftime("%H:%M"),
        patient_id=patient.id,
        patient_name=patient.name,
        species=patient.species,
        breed=patient.breed,
        passport_slug=patient.passport_slug,
        parent_name=parent.full_name if parent else None,
        parent_phone_suffix=parent.phone[-4:] if parent else None,
        status=appointment.status.value,
        source=appointment.source.value,
        mode=appointment.mode.value,
        room_url=appointment.room_url,
        doctor_name=doctor.full_name if doctor else None,
        allergies=list(patient.allergies or []),
        chronic_conditions=list(patient.chronic_conditions or []),
    )


async def _day_rows(
    session: AsyncSession,
    clinic: Clinic,
    day: date,
    *,
    doctor_id: uuid.UUID | None = None,
) -> tuple[list[DaySlotOut], ZoneInfo]:
    zone = _zone(clinic)
    start = datetime.combine(day, time(0, 0), tzinfo=zone)
    end = start + timedelta(days=1)

    statement = (
        select(Appointment, Patient, PetParent, ClinicUser)
        .join(Patient, Appointment.patient_id == Patient.id)
        .outerjoin(PetParent, Patient.parent_id == PetParent.id)
        .outerjoin(ClinicUser, Appointment.doctor_id == ClinicUser.id)
        .where(
            Appointment.clinic_id == clinic.id,
            Appointment.starts_at >= start,
            Appointment.starts_at < end,
        )
        .order_by(Appointment.starts_at)
    )
    if doctor_id is not None:
        statement = statement.where(Appointment.doctor_id == doctor_id)

    rows = (await session.execute(statement)).all()
    return [_slot(*row, zone) for row in rows], zone


def _counts(slots: list[DaySlotOut]) -> DayCountsOut:
    def of(state: AppointmentStatus) -> int:
        return sum(1 for slot in slots if slot.status == state.value)

    return DayCountsOut(
        total=len(slots),
        waiting=of(AppointmentStatus.BOOKED),
        checked_in=of(AppointmentStatus.CONFIRMED),
        seen=of(AppointmentStatus.COMPLETED),
        online=sum(1 for slot in slots if slot.mode == "online"),
        cancelled=of(AppointmentStatus.CANCELLED),
    )


@router.get("/doctor", response_model=DoctorDayOut)
async def doctor_day(
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_roles(UserRole.DOCTOR))],
    on: Annotated[date | None, Query()] = None,
) -> DoctorDayOut:
    """A doctor's own list. Empty is a valid answer: it means nothing is booked with them."""
    clinic = await session.get(Clinic, user.clinic_id)
    if clinic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clinic not found")

    zone = _zone(clinic)
    day = on or datetime.now(zone).date()
    slots, zone = await _day_rows(session, clinic, day, doctor_id=user.id)

    live = [slot for slot in slots if slot.status not in {"completed", "cancelled"}]
    now_label = datetime.now(zone).strftime("%H:%M")
    next_up = next((slot for slot in live if slot.starts_at >= now_label), None)
    if next_up is None and live:
        next_up = live[0]

    return DoctorDayOut(
        date=day.isoformat(),
        timezone=str(zone),
        doctor_name=user.full_name,
        counts=_counts(slots),
        appointments=slots,
        next_up=next_up,
    )


@router.get("/frontdesk", response_model=FrontDeskOut)
async def front_desk(
    session: SessionDep,
    user: Annotated[
        CurrentUser, Depends(require_roles(UserRole.RECEPTIONIST, UserRole.OWNER))
    ],
    on: Annotated[date | None, Query()] = None,
) -> FrontDeskOut:
    """The desk's board: who is due, who has arrived, who has been seen."""
    clinic = await session.get(Clinic, user.clinic_id)
    if clinic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clinic not found")

    zone = _zone(clinic)
    day = on or datetime.now(zone).date()
    slots, zone = await _day_rows(session, clinic, day)

    arriving = [slot for slot in slots if slot.status not in {"completed", "cancelled"}]
    finished = [slot for slot in slots if slot.status == "completed"]

    return FrontDeskOut(
        date=day.isoformat(),
        timezone=str(zone),
        clinic_name=clinic.name,
        opens_at=clinic.opens_at.strftime("%H:%M"),
        closes_at=clinic.closes_at.strftime("%H:%M"),
        counts=_counts(slots),
        arriving=arriving,
        finished=finished,
    )
