import uuid
from datetime import date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep, require_permission
from app.models import Appointment, AppointmentStatus, Clinic, Patient
from app.rbac import Action
from app.services.audit import record_audit

router = APIRouter(prefix="/appointments", tags=["appointments"])

# The desk moves a booking forward: due -> arrived -> seen, or off the board.
TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.BOOKED: {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED},
    AppointmentStatus.CONFIRMED: {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED},
}

STATUS_LABEL = {
    AppointmentStatus.CONFIRMED: "checked in",
    AppointmentStatus.COMPLETED: "marked as seen",
    AppointmentStatus.CANCELLED: "cancelled",
}


class AppointmentOut(BaseModel):
    id: uuid.UUID
    starts_at: str
    patient_id: uuid.UUID
    patient_name: str
    passport_slug: str
    status: str
    source: str
    mode: str
    room_url: str | None


class AppointmentStatusIn(BaseModel):
    status: AppointmentStatus


def _clinic_zone(clinic: Clinic | None) -> ZoneInfo:
    try:
        return ZoneInfo(clinic.timezone if clinic else "Asia/Kolkata")
    except Exception:  # noqa: BLE001 - a bad stored zone must not block the board
        return ZoneInfo("Asia/Kolkata")


def _out(appointment: Appointment, patient: Patient, zone: ZoneInfo) -> AppointmentOut:
    return AppointmentOut(
        id=appointment.id,
        starts_at=appointment.starts_at.astimezone(zone).strftime("%H:%M"),
        patient_id=patient.id,
        patient_name=patient.name,
        passport_slug=patient.passport_slug,
        status=appointment.status.value,
        source=appointment.source.value,
        mode=appointment.mode.value,
        room_url=appointment.room_url,
    )


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.PATIENT_READ))],
    on: Annotated[date | None, Query()] = None,
) -> list[AppointmentOut]:
    clinic = await session.get(Clinic, user.clinic_id)
    timezone = _clinic_zone(clinic)
    day = on or datetime.now(timezone).date()
    start = datetime.combine(day, time(0, 0), tzinfo=timezone)
    end = start + timedelta(days=1)

    rows = (
        await session.execute(
            select(Appointment, Patient)
            .join(Patient, Appointment.patient_id == Patient.id)
            .where(
                Appointment.clinic_id == user.clinic_id,
                Appointment.starts_at >= start,
                Appointment.starts_at < end,
            )
            .order_by(Appointment.starts_at)
        )
    ).all()

    return [_out(appointment, patient, timezone) for appointment, patient in rows]


@router.post("/{appointment_id}/status", response_model=AppointmentOut)
async def set_appointment_status(
    appointment_id: uuid.UUID,
    payload: AppointmentStatusIn,
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.PATIENT_WRITE))],
) -> AppointmentOut:
    """Check a patient in, mark them seen, or take the booking off the board."""
    row = (
        await session.execute(
            select(Appointment, Patient)
            .join(Patient, Appointment.patient_id == Patient.id)
            .where(
                Appointment.id == appointment_id,
                Appointment.clinic_id == user.clinic_id,
            )
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")

    appointment, patient = row
    if payload.status is appointment.status:
        return _out(appointment, patient, _clinic_zone(await session.get(Clinic, user.clinic_id)))

    if payload.status not in TRANSITIONS.get(appointment.status, set()):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{appointment.status.value} cannot become {payload.status.value}",
        )

    appointment.status = payload.status
    await session.flush()
    await record_audit(
        session,
        clinic_id=user.clinic_id,
        actor_id=user.id,
        action=f"appointment.{payload.status.value}",
        subject_type="appointment",
        subject_id=appointment.id,
    )
    return _out(appointment, patient, _clinic_zone(await session.get(Clinic, user.clinic_id)))
