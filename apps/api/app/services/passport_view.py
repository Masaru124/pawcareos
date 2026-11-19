from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clinic, ClinicUser, Consultation, Patient, Prescription, VaccineEvent
from app.schemas.passport import (
    BadgeOut,
    ClinicRefOut,
    PassportView,
    PetOut,
    PrescriptionRefOut,
)

DUE_SOON_DAYS = 30


def _age_label(dob: date | None, today: date) -> str:
    if dob is None:
        return "Age not recorded"
    months = (today.year - dob.year) * 12 + (today.month - dob.month)
    if today.day < dob.day:
        months -= 1
    months = max(months, 0)
    years, remainder = divmod(months, 12)
    if years and remainder:
        return f"{years} yr {remainder} mo"
    if years:
        return f"{years} yr"
    return f"{remainder} mo"


def _sex_label(gender: str) -> str:
    lookup = {"male": "Male", "female": "Female", "m": "Male", "f": "Female"}
    return lookup.get(gender.strip().lower(), gender.strip().title())


def _mask(microchip: str | None) -> str | None:
    if not microchip:
        return None
    return f"{'•' * max(len(microchip) - 4, 4)}{microchip[-4:]}"


def _status_for(badges: list[BadgeOut], today: date) -> str:
    if any(badge.state == "overdue" for badge in badges):
        return "overdue"
    if any(badge.state == "due_soon" for badge in badges):
        return "due_soon"
    if not badges:
        return "no_records"
    return "fully_vaccinated"


async def build_passport_view(session: AsyncSession, *, slug: str) -> PassportView | None:
    patient = await session.scalar(
        select(Patient).where(Patient.passport_slug == slug, Patient.is_active.is_(True))
    )
    if patient is None:
        return None

    clinic = await session.get(Clinic, patient.primary_clinic_id)
    if clinic is None:
        return None

    today = datetime.now(ZoneInfo(clinic.timezone or "Asia/Kolkata")).date()

    events = (
        await session.execute(
            select(VaccineEvent)
            .where(VaccineEvent.patient_id == patient.id)
            .order_by(VaccineEvent.administered_date.desc())
        )
    ).scalars().all()

    latest: dict[str, VaccineEvent] = {}
    for event in events:
        latest.setdefault(event.vaccine_name, event)

    doctor_ids = {event.doctor_id for event in latest.values()}
    doctors = {
        user.id: user
        for user in (
            await session.execute(select(ClinicUser).where(ClinicUser.id.in_(doctor_ids)))
        ).scalars()
    }

    badges: list[BadgeOut] = []
    for event in latest.values():
        remaining = (event.next_due_date - today).days
        state = "overdue" if remaining < 0 else "due_soon" if remaining <= DUE_SOON_DAYS else "valid"
        doctor = doctors.get(event.doctor_id)
        badges.append(
            BadgeOut(
                label=event.vaccine_name,
                valid_until=event.next_due_date.isoformat(),
                state=state,
                doctor_name=doctor.full_name if doctor else "",
            )
        )

    history = (
        await session.execute(
            select(Prescription, Consultation, ClinicUser)
            .join(Consultation, Prescription.consultation_id == Consultation.id)
            .join(ClinicUser, Consultation.doctor_id == ClinicUser.id)
            .where(Consultation.patient_id == patient.id)
            .order_by(Consultation.consult_date.desc())
            .limit(5)
        )
    ).all()

    return PassportView(
        pet=PetOut(
            name=patient.name,
            species=patient.species,
            breed=patient.breed,
            age_label=_age_label(patient.dob, today),
            sex_label=_sex_label(patient.gender),
            microchip_masked=_mask(patient.microchip_number),
            passport_slug=patient.passport_slug,
        ),
        status=_status_for(badges, today),
        badges=badges,
        prescriptions=[
            PrescriptionRefOut(
                date=consultation.consult_date.date().isoformat(),
                doctor_name=doctor.full_name,
                rx_code=prescription.rx_code,
            )
            for prescription, consultation, doctor in history
        ],
        clinic=ClinicRefOut(
            name=clinic.name,
            address=f"{clinic.address_street}, {clinic.city}",
            phone=clinic.phone,
        ),
    )
