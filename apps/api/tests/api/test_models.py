import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Appointment,
    AppointmentSource,
    Clinic,
    ClinicUser,
    Patient,
    PetParent,
    RecallJob,
    RecallTrigger,
    UserRole,
    VaccineEvent,
)


async def make_clinic(session) -> Clinic:
    clinic = Clinic(
        name="Shanti Vet Clinic",
        phone="+919876500001",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        address_street="100 Feet Road, Indiranagar",
        city="Bengaluru",
        state="Karnataka",
        pincode="560038",
    )
    session.add(clinic)
    await session.flush()
    return clinic


async def make_user(session, clinic, *, role: UserRole, vci: str | None = "KAR-12345") -> ClinicUser:
    user = ClinicUser(
        clinic_id=clinic.id,
        full_name="Clinic User",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        vci_registration_no=vci,
        role=role,
    )
    session.add(user)
    await session.flush()
    return user


async def make_patient(session, clinic, doctor) -> Patient:
    parent = PetParent(full_name="Priya", phone=f"+9198{uuid.uuid4().int % 10**8:08d}")
    session.add(parent)
    await session.flush()
    patient = Patient(
        parent_id=parent.id,
        primary_clinic_id=clinic.id,
        name="Bruno",
        species="Canine",
        breed="Golden Retriever",
        gender="Male",
        passport_slug=uuid.uuid4().hex[:10].replace("0", "2").replace("1", "3"),
    )
    session.add(patient)
    await session.flush()
    return patient


async def make_vaccine_event(session, clinic, doctor, patient) -> VaccineEvent:
    event = VaccineEvent(
        patient_id=patient.id,
        clinic_id=clinic.id,
        doctor_id=doctor.id,
        vaccine_name="Anti-Rabies (Annual)",
        brand_name="Nobivac Rabies",
        batch_number="B78942",
        administered_date=date(2027, 11, 19),
        next_due_date=date(2028, 11, 19),
    )
    session.add(event)
    await session.flush()
    return event


async def test_receptionist_is_allowed_without_a_vci_number(session):
    clinic = await make_clinic(session)
    user = await make_user(session, clinic, role=UserRole.RECEPTIONIST, vci=None)
    assert user.role is UserRole.RECEPTIONIST
    assert user.is_doctor is False


async def test_doctor_without_a_vci_number_is_rejected(session):
    clinic = await make_clinic(session)
    with pytest.raises(IntegrityError, match="ck_clinic_users_doctor_vci"):
        await make_user(session, clinic, role=UserRole.DOCTOR, vci=None)


async def test_recall_job_is_unique_per_event_and_trigger(session):
    clinic = await make_clinic(session)
    doctor = await make_user(session, clinic, role=UserRole.DOCTOR)
    patient = await make_patient(session, clinic, doctor)
    event = await make_vaccine_event(session, clinic, doctor, patient)

    session.add(RecallJob(vaccine_event_id=event.id, trigger=RecallTrigger.T7, template_name="recall_t7_v1"))
    await session.flush()

    with pytest.raises(IntegrityError, match="uq_recall_jobs_event_trigger"):
        session.add(
            RecallJob(
                vaccine_event_id=event.id,
                trigger=RecallTrigger.T7,
                template_name="recall_t7_v1",
            )
        )
        await session.flush()


async def test_appointment_is_unique_per_recall_job(session):
    clinic = await make_clinic(session)
    doctor = await make_user(session, clinic, role=UserRole.DOCTOR)
    patient = await make_patient(session, clinic, doctor)
    event = await make_vaccine_event(session, clinic, doctor, patient)
    job = RecallJob(vaccine_event_id=event.id, trigger=RecallTrigger.T7, template_name="recall_t7_v1")
    session.add(job)
    await session.flush()

    starts_at = datetime.now(UTC) + timedelta(days=7)
    session.add(
        Appointment(
            clinic_id=clinic.id,
            patient_id=patient.id,
            recall_job_id=job.id,
            starts_at=starts_at,
            source=AppointmentSource.RECALL,
        )
    )
    await session.flush()

    with pytest.raises(IntegrityError):
        session.add(
            Appointment(
                clinic_id=clinic.id,
                patient_id=patient.id,
                recall_job_id=job.id,
                starts_at=starts_at,
                source=AppointmentSource.RECALL,
            )
        )
        await session.flush()
