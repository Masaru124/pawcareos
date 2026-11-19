import uuid
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.passport import make_passport_slug
from app.models import ConsentEvent, Patient, PetParent
from app.models.enums import ConsentChannel
from app.schemas.intake import IntakeIn, IntakeOut, PatientSummary
from app.services.audit import record_audit


async def _unique_slug(session: AsyncSession) -> str:
    for _ in range(5):
        slug = make_passport_slug()
        exists = await session.scalar(select(Patient.id).where(Patient.passport_slug == slug))
        if exists is None:
            return slug
    raise RuntimeError("Could not allocate a unique passport slug")


async def create_intake(
    session: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    actor_id: uuid.UUID,
    payload: IntakeIn,
) -> IntakeOut:
    parent = await session.scalar(select(PetParent).where(PetParent.phone == payload.parent.phone))
    if parent is None:
        parent = PetParent(full_name=payload.parent.full_name, phone=payload.parent.phone)
        session.add(parent)
        await session.flush()

    patient = Patient(
        parent_id=parent.id,
        primary_clinic_id=clinic_id,
        name=payload.patient.name,
        species=payload.patient.species,
        breed=payload.patient.breed,
        gender=payload.patient.gender,
        dob=payload.patient.dob,
        dob_is_approximate=payload.patient.dob_is_approximate,
        weight_kg=Decimal(str(payload.patient.weight_kg)) if payload.patient.weight_kg else None,
        passport_slug=await _unique_slug(session),
    )
    session.add(patient)
    await session.flush()

    if payload.consent is not None:
        session.add(
            ConsentEvent(
                pet_parent_id=parent.id,
                channel=ConsentChannel.WHATSAPP,
                granted=payload.consent.granted,
                source=payload.consent.source,
                created_by=actor_id,
            )
        )

    await record_audit(
        session,
        actor_id=actor_id,
        clinic_id=clinic_id,
        action="patient.created",
        subject_type="patient",
        subject_id=patient.id,
    )
    return IntakeOut(parent_id=parent.id, patient_id=patient.id, passport_slug=patient.passport_slug)


async def search_patients(
    session: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    query: str | None,
    limit: int = 20,
) -> list[PatientSummary]:
    """With a query, match name/phone suffix/microchip. Without one, list the clinic's newest."""
    statement = (
        select(Patient, PetParent)
        .join(PetParent, Patient.parent_id == PetParent.id)
        .where(Patient.primary_clinic_id == clinic_id, Patient.is_active.is_(True))
    )
    if not query:
        rows = (
            await session.execute(statement.order_by(Patient.created_at.desc()).limit(limit))
        ).all()
        return [_summary(patient, parent) for patient, parent in rows]

    digits = "".join(character for character in query if character.isdigit())
    if digits:
        statement = statement.where(
            or_(
                Patient.name.ilike(f"%{query}%"),
                PetParent.phone.endswith(digits),
                Patient.microchip_number.ilike(f"%{query}%"),
            )
        )
    else:
        statement = statement.where(
            or_(
                Patient.name.ilike(f"%{query}%"),
                Patient.microchip_number.ilike(f"%{query}%"),
            )
        )

    rows = (await session.execute(statement.order_by(Patient.name).limit(limit))).all()
    return [_summary(patient, parent) for patient, parent in rows]


def _summary(patient: Patient, parent: PetParent) -> PatientSummary:
    return PatientSummary(
        id=patient.id,
        name=patient.name,
        species=patient.species,
        breed=patient.breed,
        passport_slug=patient.passport_slug,
        parent_name=parent.full_name,
        parent_phone_suffix=parent.phone[-4:],
    )
