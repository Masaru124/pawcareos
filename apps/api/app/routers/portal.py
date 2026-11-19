import uuid
from datetime import UTC, date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, NotFoundError, ParentDep, SessionDep, require_permission
from app.models import (
    Appointment,
    AppointmentStatus,
    Clinic,
    ClinicUser,
    Consultation,
    Patient,
    PetParent,
    PetParentAccount,
    Prescription,
    PrescriptionItem,
    VaccineEvent,
    VaccineStatus,
)
from app.rbac import Action
from app.schemas.portal import (
    ParentInviteIn,
    ParentInviteOut,
    PetRecordsOut,
    PortalAppointmentOut,
    PortalMeOut,
    PortalPetOut,
    RecordItemOut,
    RecordPrescriptionOut,
    RecordVaccineOut,
)
from app.services.audit import record_audit

router = APIRouter(prefix="/portal", tags=["portal"])

CITY_TIMEZONE = ZoneInfo("Asia/Kolkata")


async def _next_due(session: SessionDep, patient_id, today: date) -> date | None:
    """The soonest booster still ahead, else the oldest one that has lapsed."""
    upcoming = await session.scalar(
        select(func.min(VaccineEvent.next_due_date)).where(
            VaccineEvent.patient_id == patient_id,
            VaccineEvent.status == VaccineStatus.ADMINISTERED,
            VaccineEvent.next_due_date >= today,
        )
    )
    if upcoming is not None:
        return upcoming
    return await session.scalar(
        select(func.min(VaccineEvent.next_due_date)).where(
            VaccineEvent.patient_id == patient_id,
            VaccineEvent.status == VaccineStatus.ADMINISTERED,
        )
    )


@router.get("/me", response_model=PortalMeOut)
async def me(identity: ParentDep, session: SessionDep) -> PortalMeOut:
    today = datetime.now(CITY_TIMEZONE).date()
    rows = (
        await session.execute(
            select(Patient, Clinic)
            .join(Clinic, Patient.primary_clinic_id == Clinic.id)
            .where(Patient.parent_id == identity.parent.id, Patient.is_active.is_(True))
            .order_by(Patient.name)
        )
    ).all()

    pets = [
        PortalPetOut(
            id=patient.id,
            name=patient.name,
            species=patient.species,
            breed=patient.breed,
            passport_slug=patient.passport_slug,
            clinic_name=clinic.name,
            next_due=await _next_due(session, patient.id, today),
        )
        for patient, clinic in rows
    ]
    return PortalMeOut(
        parent_name=identity.parent.full_name,
        phone_suffix=identity.parent.phone[-4:],
        pets=pets,
    )


@router.get("/appointments", response_model=list[PortalAppointmentOut])
async def upcoming_appointments(
    identity: ParentDep, session: SessionDep
) -> list[PortalAppointmentOut]:
    rows = (
        await session.execute(
            select(Appointment, Patient, Clinic)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(Clinic, Appointment.clinic_id == Clinic.id)
            .where(
                Patient.parent_id == identity.parent.id,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.starts_at >= datetime.now(UTC),
            )
            .order_by(Appointment.starts_at)
            .limit(20)
        )
    ).all()

    return [
        PortalAppointmentOut(
            id=appointment.id,
            starts_at=appointment.starts_at,
            patient_name=patient.name,
            clinic_name=clinic.name,
            status=appointment.status.value,
            mode=appointment.mode.value,
            room_url=appointment.room_url,
        )
        for appointment, patient, clinic in rows
    ]


@router.get("/pets/{patient_id}/records", response_model=PetRecordsOut)
async def pet_records(
    patient_id: uuid.UUID, identity: ParentDep, session: SessionDep
) -> PetRecordsOut:
    """The pet's whole record, readable only by the family that owns it."""
    row = (
        await session.execute(
            select(Patient, Clinic)
            .join(Clinic, Patient.primary_clinic_id == Clinic.id)
            .where(Patient.id == patient_id, Patient.parent_id == identity.parent.id)
        )
    ).first()
    if row is None:
        raise NotFoundError("Pet not found")
    patient, clinic = row

    vaccine_rows = (
        await session.execute(
            select(VaccineEvent, ClinicUser)
            .join(ClinicUser, VaccineEvent.doctor_id == ClinicUser.id)
            .where(VaccineEvent.patient_id == patient.id)
            .order_by(VaccineEvent.administered_date.desc())
        )
    ).all()

    prescription_rows = (
        await session.execute(
            select(Prescription, Consultation, ClinicUser)
            .join(Consultation, Prescription.consultation_id == Consultation.id)
            .join(ClinicUser, Consultation.doctor_id == ClinicUser.id)
            .where(Consultation.patient_id == patient.id)
            .order_by(Consultation.consult_date.desc())
            .limit(20)
        )
    ).all()

    items_by_prescription: dict[uuid.UUID, list[PrescriptionItem]] = {}
    prescription_ids = [prescription.id for prescription, _, _ in prescription_rows]
    if prescription_ids:
        for item in (
            await session.execute(
                select(PrescriptionItem).where(
                    PrescriptionItem.prescription_id.in_(prescription_ids)
                )
            )
        ).scalars():
            items_by_prescription.setdefault(item.prescription_id, []).append(item)

    return PetRecordsOut(
        pet_id=patient.id,
        name=patient.name,
        species=patient.species,
        breed=patient.breed,
        passport_slug=patient.passport_slug,
        clinic_name=clinic.name,
        vaccines=[
            RecordVaccineOut(
                vaccine_name=event.vaccine_name,
                brand_name=event.brand_name,
                batch_number=event.batch_number,
                administered_date=event.administered_date,
                next_due_date=event.next_due_date,
                status=event.status.value,
                doctor_name=doctor.full_name,
            )
            for event, doctor in vaccine_rows
        ],
        prescriptions=[
            RecordPrescriptionOut(
                rx_code=prescription.rx_code,
                date=consultation.consult_date.date(),
                doctor_name=doctor.full_name,
                diagnosis=consultation.provisional_diagnosis,
                items=[
                    RecordItemOut(
                        medication_name=item.medication_name,
                        dosage_form=item.dosage_form,
                        dosage_strength=item.dosage_strength,
                        frequency=item.frequency,
                        duration_days=item.duration_days,
                        route=item.route,
                        is_chronic=item.is_chronic,
                    )
                    for item in items_by_prescription.get(prescription.id, [])
                ],
            )
            for prescription, consultation, doctor in prescription_rows
        ],
    )


@router.post("/invites", response_model=ParentInviteOut, status_code=201)
async def invite_parent(
    payload: ParentInviteIn,
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.PATIENT_WRITE))],
) -> ParentInviteOut:
    """Staff attach an email to a family. That address is what claims the portal account."""
    parent = await session.scalar(
        select(PetParent)
        .join(Patient, Patient.parent_id == PetParent.id)
        .where(
            Patient.primary_clinic_id == user.clinic_id,
            PetParent.phone == payload.parent_phone,
        )
        .limit(1)
    )
    if parent is None:
        raise NotFoundError("No pet parent with that phone at this clinic")

    existing = await session.scalar(
        select(PetParentAccount).where(func.lower(PetParentAccount.email) == payload.email)
    )
    if existing is not None:
        if existing.pet_parent_id != parent.id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "That email already belongs to another family",
            )
        return ParentInviteOut(
            parent_name=parent.full_name,
            email=existing.email,
            already_claimed=existing.auth_user_id is not None,
        )

    account = PetParentAccount(pet_parent_id=parent.id, email=payload.email)
    session.add(account)
    if parent.email is None:
        parent.email = payload.email
    await session.flush()

    await record_audit(
        session,
        actor_id=user.id,
        clinic_id=user.clinic_id,
        action="parent.invited",
        subject_type="pet_parent_account",
        subject_id=account.id,
    )
    return ParentInviteOut(parent_name=parent.full_name, email=account.email, already_claimed=False)
