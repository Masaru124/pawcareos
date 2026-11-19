import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.deps import NotFoundError
from app.domain.rx_code import make_rx_code
from app.domain.vaccination import next_due_date
from app.models import (
    Clinic,
    ClinicalCounter,
    ClinicUser,
    ConsentEvent,
    Consultation,
    MessageOutbox,
    Patient,
    PetParent,
    Prescription,
    PrescriptionItem,
    RecallJob,
    VaccineEvent,
)
from app.models.enums import (
    ConsultStatus,
    OutboxKind,
    RecallStatus,
    RecallTrigger,
    VaccineStatus,
)
from app.schemas.consult import ConsultIn, ConsultOut
from app.services.audit import record_audit
from app.services.outbox import enqueue

DEFAULT_TEMPLATE = "rx_delivery_v1"


def passport_url(slug: str) -> str:
    base = get_settings().public_base_url.rstrip("/")
    return f"{base}/p/{slug}"


async def latest_consent(session: AsyncSession, parent_id: uuid.UUID) -> bool:
    row = await session.scalar(
        select(ConsentEvent)
        .where(ConsentEvent.pet_parent_id == parent_id)
        .order_by(ConsentEvent.created_at.desc())
        .limit(1)
    )
    return bool(row and row.granted)


async def _next_sequence(session: AsyncSession, clinic_id: uuid.UUID, year: int) -> int:
    await session.execute(
        pg_insert(ClinicalCounter)
        .values(clinic_id=clinic_id, year=year, next_seq=1)
        .on_conflict_do_nothing(index_elements=["clinic_id", "year"])
    )
    counter = await session.scalar(
        select(ClinicalCounter)
        .where(ClinicalCounter.clinic_id == clinic_id, ClinicalCounter.year == year)
        .with_for_update()
    )
    if counter is None:
        raise RuntimeError("Could not lock the prescription counter")
    sequence = counter.next_seq
    counter.next_seq = sequence + 1
    return sequence


async def complete_consult(
    session: AsyncSession,
    *,
    user: ClinicUser,
    payload: ConsultIn,
    idempotency_key: str,
) -> ConsultOut:
    patient = await session.scalar(
        select(Patient).where(
            Patient.id == payload.patient_id,
            Patient.primary_clinic_id == user.clinic_id,
        )
    )
    if patient is None:
        raise NotFoundError("Patient not found")

    existing = await session.scalar(
        select(Consultation).where(Consultation.idempotency_key == idempotency_key)
    )
    if existing is not None:
        prescription = await session.scalar(
            select(Prescription).where(Prescription.consultation_id == existing.id)
        )
        already_queued = await session.scalar(
            select(MessageOutbox.id).where(
                MessageOutbox.idempotency_key == f"rx:{existing.id}"
            )
        )
        return ConsultOut(
            consultation_id=existing.id,
            rx_code=prescription.rx_code if prescription else "",
            passport_url=passport_url(patient.passport_slug),
            whatsapp_status="queued" if already_queued else "suppressed",
        )

    clinic = await session.get(Clinic, user.clinic_id)
    clinic_timezone = ZoneInfo(clinic.timezone if clinic else "Asia/Kolkata")
    today = datetime.now(clinic_timezone).date()

    sequence = await _next_sequence(session, user.clinic_id, today.year)
    rx_code = make_rx_code(clinic.city if clinic else "IND", today.year, sequence)

    consultation = Consultation(
        clinic_id=user.clinic_id,
        doctor_id=user.id,
        patient_id=patient.id,
        temperature_f=Decimal(str(payload.temperature_f)) if payload.temperature_f else None,
        weight_kg=Decimal(str(payload.weight_kg)) if payload.weight_kg else None,
        symptoms=payload.symptoms,
        provisional_diagnosis=payload.provisional_diagnosis,
        status=ConsultStatus.COMPLETED,
        idempotency_key=idempotency_key,
    )
    session.add(consultation)
    await session.flush()

    prescription = Prescription(
        consultation_id=consultation.id,
        rx_code=rx_code,
        dietary_advice=payload.dietary_advice,
        special_instructions=payload.special_instructions,
    )
    session.add(prescription)
    await session.flush()

    for medication in payload.medications:
        session.add(
            PrescriptionItem(
                prescription_id=prescription.id,
                medication_name=medication.name,
                dosage_form=medication.route,
                dosage_strength=medication.dosage,
                frequency=medication.frequency,
                duration_days=medication.duration_days,
                route=medication.route,
                is_chronic=medication.is_chronic,
            )
        )

    for vaccination in payload.vaccinations:
        due_on = next_due_date(vaccination.kind, today)
        event = VaccineEvent(
            patient_id=patient.id,
            clinic_id=user.clinic_id,
            doctor_id=user.id,
            vaccine_name=vaccination.vaccine_name,
            brand_name=vaccination.brand_name,
            batch_number=vaccination.batch_number,
            administered_date=today,
            next_due_date=due_on,
            status=VaccineStatus.ADMINISTERED,
        )
        session.add(event)
        await session.flush()
        session.add(
            RecallJob(
                vaccine_event_id=event.id,
                scheduled_dispatch_time=datetime.combine(
                    due_on - timedelta(days=7), time(9, 0), tzinfo=clinic_timezone
                ),
                trigger=RecallTrigger.T7,
                template_name="recall_t7_v1",
                status=RecallStatus.QUEUED,
            )
        )

    parent = await session.get(PetParent, patient.parent_id)
    granted = await latest_consent(session, patient.parent_id)
    queued = False
    if parent is not None and granted:
        queued = await enqueue(
            session,
            MessageOutbox(
                clinic_id=user.clinic_id,
                correlation_id=str(consultation.id),
                kind=OutboxKind.RX_DELIVERY,
                to_phone=parent.phone,
                template_name=DEFAULT_TEMPLATE,
                template_version=1,
                payload={
                    "pet_name": patient.name,
                    "rx_code": rx_code,
                    "passport_url": passport_url(patient.passport_slug),
                },
                idempotency_key=f"rx:{consultation.id}",
            ),
        )

    await record_audit(
        session,
        actor_id=user.id,
        clinic_id=user.clinic_id,
        action="consult.completed",
        subject_type="prescription",
        subject_id=prescription.id,
    )

    return ConsultOut(
        consultation_id=consultation.id,
        rx_code=rx_code,
        passport_url=passport_url(patient.passport_slug),
        whatsapp_status="queued" if queued else "suppressed",
    )


def scheduled_for(due_on: date, clinic_timezone: ZoneInfo) -> datetime:
    return datetime.combine(due_on - timedelta(days=7), time(9, 0), tzinfo=clinic_timezone)
