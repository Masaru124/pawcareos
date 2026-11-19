import uuid
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.recall import decode_button_id
from app.models import (
    Appointment,
    ConsentEvent,
    InboundEvent,
    MessageOutbox,
    Patient,
    PetParent,
    RecallJob,
    VaccineEvent,
)
from app.models.enums import (
    AppointmentSource,
    AppointmentStatus,
    ConsentChannel,
    ConsentSource,
    OutboxKind,
    RecallStatus,
    ResponseAction,
)
from app.services.outbox import enqueue

CITY_TIMEZONE = ZoneInfo("Asia/Kolkata")


def next_saturday_morning(now: datetime | None = None) -> datetime:
    reference = (now or datetime.now(CITY_TIMEZONE)).astimezone(CITY_TIMEZONE)
    days_ahead = (5 - reference.weekday()) % 7 or 7
    target = (reference + timedelta(days=days_ahead)).date()
    return datetime.combine(target, time(11, 0), tzinfo=CITY_TIMEZONE)


async def _remember(session: AsyncSession, provider_message_id: str | None, from_phone: str | None, payload: dict) -> bool:
    """False when this provider message id was already processed."""
    if not provider_message_id:
        return True
    try:
        async with session.begin_nested():
            session.add(
                InboundEvent(
                    provider_message_id=provider_message_id,
                    from_phone=from_phone,
                    payload=payload,
                )
            )
            await session.flush()
    except IntegrityError:
        return False
    return True


async def handle_button_reply(
    session: AsyncSession,
    *,
    provider_message_id: str | None,
    from_phone: str | None,
    button_id: str,
) -> bool:
    if not await _remember(session, provider_message_id, from_phone, {"button_id": button_id}):
        return False

    decoded = decode_button_id(button_id)
    if decoded is None:
        return False
    kind, job_id = decoded

    job = await session.get(RecallJob, job_id)
    if job is None:
        return False
    event = await session.get(VaccineEvent, job.vaccine_event_id)
    if event is None:
        return False
    patient = await session.get(Patient, event.patient_id)
    if patient is None:
        return False
    parent = await session.get(PetParent, patient.parent_id)
    if parent is None:
        return False

    if kind == "confirm":
        await session.execute(
            pg_insert(Appointment)
            .values(
                clinic_id=event.clinic_id,
                patient_id=event.patient_id,
                recall_job_id=job.id,
                starts_at=next_saturday_morning(),
                status=AppointmentStatus.BOOKED,
                source=AppointmentSource.RECALL,
            )
            .on_conflict_do_nothing(index_elements=["recall_job_id"])
        )
        job.status = RecallStatus.RESPONDED
        job.response_action = ResponseAction.BOOKED
        await enqueue(
            session,
            MessageOutbox(
                clinic_id=event.clinic_id,
                correlation_id=str(job.id),
                kind=OutboxKind.CONFIRMATION,
                to_phone=parent.phone,
                template_name="booking_confirmation_v1",
                template_version=1,
                payload={
                    "pet_name": patient.name,
                    "when": next_saturday_morning().strftime("%a %d %b, 11:00 am"),
                },
                idempotency_key=f"confirm:{job.id}",
            ),
        )
    elif kind == "reschedule":
        job.status = RecallStatus.RESPONDED
        job.response_action = ResponseAction.POSTPONED
    else:
        job.status = RecallStatus.SUPPRESSED
        job.response_action = ResponseAction.OPTED_OUT
        session.add(
            ConsentEvent(
                pet_parent_id=parent.id,
                channel=ConsentChannel.WHATSAPP,
                granted=False,
                source=ConsentSource.WHATSAPP_REPLY,
            )
        )
        other_jobs = (
            select(RecallJob.id)
            .join(VaccineEvent, RecallJob.vaccine_event_id == VaccineEvent.id)
            .where(VaccineEvent.patient_id == patient.id, RecallJob.status == RecallStatus.QUEUED)
        )
        await session.execute(
            update(RecallJob)
            .where(RecallJob.id.in_(other_jobs))
            .values(status=RecallStatus.SUPPRESSED)
        )

    await session.flush()
    return True


async def job_for_patient(session: AsyncSession, patient_id: uuid.UUID) -> RecallJob | None:
    return await session.scalar(
        select(RecallJob)
        .join(VaccineEvent, RecallJob.vaccine_event_id == VaccineEvent.id)
        .where(VaccineEvent.patient_id == patient_id)
        .limit(1)
    )
