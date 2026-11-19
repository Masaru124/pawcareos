"""Public vet search and slot booking.

Booking is unauthenticated on purpose: a pet parent is not expected to hold an
account before their first visit. Nothing here can write a prescription.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.deps import NotFoundError
from app.models import (
    Appointment,
    AppointmentSource,
    AppointmentStatus,
    Clinic,
    ClinicUser,
    ConsultMode,
    MessageOutbox,
    OutboxKind,
    Patient,
    PetParent,
    UserRole,
)
from app.schemas.directory import (
    AvailabilityOut,
    BookingIn,
    BookingOut,
    ClinicOut,
    DoctorOut,
    RoomOut,
    SlotOut,
)
from app.services.consult import passport_url
from app.services.outbox import enqueue

REMINDER_OFFSETS = (timedelta(hours=24), timedelta(hours=2))


async def _verified_doctor(session: AsyncSession, doctor_id: uuid.UUID) -> tuple[ClinicUser, Clinic]:
    row = (
        await session.execute(
            select(ClinicUser, Clinic)
            .join(Clinic, ClinicUser.clinic_id == Clinic.id)
            .where(
                ClinicUser.id == doctor_id,
                ClinicUser.role == UserRole.DOCTOR,
                ClinicUser.is_active.is_(True),
                ClinicUser.vci_registration_no.is_not(None),
            )
        )
    ).first()
    if row is None:
        raise NotFoundError("Verified doctor not found")
    return row[0], row[1]


def clinic_timezone(clinic: Clinic) -> ZoneInfo:
    try:
        return ZoneInfo(clinic.timezone)
    except Exception:  # noqa: BLE001 - a bad stored zone must not take booking down
        return ZoneInfo("Asia/Kolkata")


def slot_grid(clinic: Clinic, day: date, mode: ConsultMode = ConsultMode.IN_CLINIC) -> list[datetime]:
    """Clinic hours for a visit; the whole clock for an online consult."""
    zone = clinic_timezone(clinic)
    step = max(clinic.slot_minutes, 5)
    if mode is ConsultMode.ONLINE:
        first = datetime.combine(day, time(0, 0), tzinfo=zone)
        close = first + timedelta(days=1)
    else:
        first = datetime.combine(day, clinic.opens_at, tzinfo=zone)
        close = datetime.combine(day, clinic.closes_at, tzinfo=zone)
    cursor = first
    slots: list[datetime] = []
    while cursor < close:
        slots.append(cursor)
        cursor += timedelta(minutes=step)
    return slots


async def search_doctors(
    session: AsyncSession,
    *,
    query: str | None = None,
    city: str | None = None,
    limit: int = 20,
) -> list[DoctorOut]:
    statement = (
        select(ClinicUser, Clinic)
        .join(Clinic, ClinicUser.clinic_id == Clinic.id)
        .where(
            ClinicUser.role == UserRole.DOCTOR,
            ClinicUser.is_active.is_(True),
            ClinicUser.vci_registration_no.is_not(None),
        )
    )
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                ClinicUser.full_name.ilike(pattern),
                Clinic.name.ilike(pattern),
                Clinic.city.ilike(pattern),
            )
        )
    if city:
        statement = statement.where(Clinic.city.ilike(f"%{city.strip()}%"))

    rows = (await session.execute(statement.order_by(Clinic.name, ClinicUser.full_name).limit(limit))).all()
    return [
        DoctorOut(
            doctor_id=doctor.id,
            full_name=doctor.full_name,
            qualification=doctor.qualification,
            # A professional registration number is identifying: publish the tail only.
            vci_suffix=f"…{(doctor.vci_registration_no or '')[-4:]}",
            clinic=ClinicOut(
                id=clinic.id,
                name=clinic.name,
                city=clinic.city,
                address=clinic.address_street,
                phone=clinic.phone,
            ),
        )
        for doctor, clinic in rows
    ]


async def availability(
    session: AsyncSession,
    *,
    doctor_id: uuid.UUID,
    day: date | None = None,
    mode: str = "in_clinic",
) -> AvailabilityOut:
    consult_mode = _mode(mode)
    _, clinic = await _verified_doctor(session, doctor_id)
    zone = clinic_timezone(clinic)
    today = datetime.now(zone).date()
    target = day or today
    if target < today:
        return AvailabilityOut(day=target, timezone=str(zone), mode=consult_mode.value, slots=[])

    # A slot belongs to one vet: another doctor's booking must not hide it.
    booked = set(
        (
            await session.execute(
                select(Appointment.starts_at).where(
                    Appointment.clinic_id == clinic.id,
                    or_(
                        Appointment.doctor_id == doctor_id,
                        Appointment.doctor_id.is_(None),
                    ),
                    Appointment.status != AppointmentStatus.CANCELLED,
                    Appointment.starts_at >= datetime.combine(target, time(0, 0), tzinfo=zone),
                    Appointment.starts_at < datetime.combine(target + timedelta(days=1), time(0, 0), tzinfo=zone),
                )
            )
        ).scalars()
    )

    now = datetime.now(UTC)
    slots = [
        SlotOut(starts_at=slot, label=slot.strftime("%H:%M"))
        for slot in slot_grid(clinic, target, consult_mode)
        if slot > now and slot.astimezone(UTC) not in booked
    ]
    return AvailabilityOut(day=target, timezone=str(zone), mode=consult_mode.value, slots=slots)


def _mode(value: str) -> ConsultMode:
    try:
        return ConsultMode(value)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "mode must be in_clinic or online"
        ) from exc


def _on_grid(clinic: Clinic, starts_at: datetime, mode: ConsultMode) -> bool:
    zone = clinic_timezone(clinic)
    local = starts_at.astimezone(zone)
    return local in slot_grid(clinic, local.date(), mode)


async def book(session: AsyncSession, *, payload: BookingIn) -> BookingOut:
    doctor, clinic = await _verified_doctor(session, payload.doctor_id)
    zone = clinic_timezone(clinic)
    consult_mode = _mode(payload.mode)

    starts_at = payload.starts_at
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=zone)
    if starts_at <= datetime.now(UTC):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Pick a slot in the future")
    if not _on_grid(clinic, starts_at, consult_mode):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "That time is outside the clinic's booking grid",
        )

    taken = await session.scalar(
        select(Appointment.id).where(
            Appointment.clinic_id == clinic.id,
            Appointment.doctor_id == doctor.id,
            Appointment.starts_at == starts_at,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    if taken is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "That slot was just booked. Pick another.")

    parent = await session.scalar(
        select(PetParent).where(PetParent.phone == payload.parent.phone)
    )
    if parent is None:
        parent = PetParent(
            full_name=payload.parent.full_name,
            phone=payload.parent.phone,
            email=payload.parent.email,
        )
        session.add(parent)
        await session.flush()
    elif parent.email is None and payload.parent.email:
        parent.email = payload.parent.email

    patient = await session.scalar(
        select(Patient).where(
            Patient.parent_id == parent.id,
            Patient.is_active.is_(True),
            Patient.name.ilike(payload.patient.name.strip()),
        )
    )
    if patient is None:
        from app.services.patients import _unique_slug

        patient = Patient(
            parent_id=parent.id,
            primary_clinic_id=clinic.id,
            name=payload.patient.name.strip(),
            species=payload.patient.species,
            breed=payload.patient.breed,
            gender=payload.patient.gender,
            passport_slug=await _unique_slug(session),
        )
        session.add(patient)
        await session.flush()

    room_url = None
    if consult_mode is ConsultMode.ONLINE:
        room_url = (
            f"{get_settings().video_base_url.rstrip('/')}/pawcare-{uuid.uuid4().hex[:16]}"
        )

    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        starts_at=starts_at,
        status=AppointmentStatus.BOOKED,
        source=AppointmentSource.WEB,
        mode=consult_mode,
        room_url=room_url,
    )
    session.add(appointment)
    await session.flush()

    queued = 0
    if payload.consent:
        now = datetime.now(UTC)
        for offset in REMINDER_OFFSETS:
            dispatch_at = starts_at - offset
            if dispatch_at <= now:
                continue
            hours = int(offset.total_seconds() // 3600)
            queued += await enqueue(
                session,
                MessageOutbox(
                    clinic_id=clinic.id,
                    correlation_id=str(appointment.id),
                    kind=OutboxKind.APPOINTMENT_REMINDER,
                    to_phone=parent.phone,
                    template_name=f"appointment_reminder_t{hours}_v1",
                    payload={
                        "pet": patient.name,
                        "clinic": clinic.name,
                        "doctor": doctor.full_name,
                        "starts_at": starts_at.isoformat(),
                    },
                    idempotency_key=f"appt:{appointment.id}:reminder:t{hours}",
                    next_attempt_at=dispatch_at,
                ),
            )

    return BookingOut(
        appointment_id=appointment.id,
        starts_at=starts_at,
        clinic_name=clinic.name,
        doctor_name=doctor.full_name,
        passport_slug=patient.passport_slug,
        passport_url=passport_url(patient.passport_slug),
        reminders_queued=queued,
        mode=consult_mode.value,
        room_url=room_url,
    )


async def room(session: AsyncSession, *, appointment_id: uuid.UUID) -> RoomOut:
    row = (
        await session.execute(
            select(Appointment, Clinic, Patient)
            .join(Clinic, Appointment.clinic_id == Clinic.id)
            .join(Patient, Appointment.patient_id == Patient.id)
            .where(Appointment.id == appointment_id)
        )
    ).first()
    if row is None:
        raise NotFoundError("Appointment not found")
    appointment, clinic, patient = row
    return RoomOut(
        appointment_id=appointment.id,
        starts_at=appointment.starts_at,
        mode=appointment.mode.value,
        room_url=appointment.room_url,
        clinic_name=clinic.name,
        doctor_name="Care team",
        patient_name=patient.name,
    )
