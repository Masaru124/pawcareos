from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.recall import QUICK_REPLY_TITLES, encode_button_id, recall_triggers_for
from app.models import JobRun, MessageOutbox, Patient, PetParent, RecallJob, VaccineEvent
from app.models.enums import OutboxKind, RecallStatus, RecallTrigger, VaccineStatus
from app.services.consult import latest_consent
from app.services.outbox import enqueue

CITY_TIMEZONE = ZoneInfo("Asia/Kolkata")

TEMPLATES: dict[RecallTrigger, str] = {
    RecallTrigger.T7: "recall_t7_v1",
    RecallTrigger.T2: "recall_t2_v1",
    RecallTrigger.OVERDUE: "recall_overdue_v1",
}


@dataclass(frozen=True)
class RecallRunResult:
    created: int
    enqueued: int
    suppressed: int


async def _parent_of(session: AsyncSession, patient_id) -> PetParent | None:
    patient = await session.get(Patient, patient_id)
    if patient is None:
        return None
    return await session.get(PetParent, patient.parent_id)


async def generate_recall_jobs(
    session: AsyncSession,
    *,
    today: date | None = None,
) -> RecallRunResult:
    run = JobRun(job_name="recall")
    session.add(run)
    await session.flush()

    reference = today or datetime.now(CITY_TIMEZONE).date()
    windows = [reference + timedelta(days=7), reference + timedelta(days=2)]

    events = (
        await session.execute(
            select(VaccineEvent).where(
                VaccineEvent.status == VaccineStatus.ADMINISTERED,
                or_(
                    VaccineEvent.next_due_date.in_(windows),
                    VaccineEvent.next_due_date < reference,
                ),
            )
        )
    ).scalars().all()

    created = enqueued = suppressed = 0
    for event in events:
        triggers = recall_triggers_for(event.next_due_date, reference)
        if not triggers:
            continue
        parent = await _parent_of(session, event.patient_id)
        if parent is None or not await latest_consent(session, parent.id):
            suppressed += 1
            continue

        patient = await session.get(Patient, event.patient_id)
        for trigger in triggers:
            new_id = await session.scalar(
                pg_insert(RecallJob)
                .values(
                    vaccine_event_id=event.id,
                    scheduled_dispatch_time=datetime.combine(
                        reference, time(9, 0), tzinfo=CITY_TIMEZONE
                    ),
                    trigger=trigger,
                    template_name=TEMPLATES[trigger],
                    status=RecallStatus.QUEUED,
                )
                .on_conflict_do_nothing(constraint="uq_recall_jobs_event_trigger")
                .returning(RecallJob.id)
            )
            if new_id is not None:
                created += 1

            job = await session.scalar(
                select(RecallJob).where(
                    RecallJob.vaccine_event_id == event.id,
                    RecallJob.trigger == trigger,
                )
            )
            if job is None or job.status != RecallStatus.QUEUED:
                continue

            queued = await enqueue(
                session,
                MessageOutbox(
                    clinic_id=event.clinic_id,
                    correlation_id=str(job.id),
                    kind=OutboxKind.RECALL,
                    to_phone=parent.phone,
                    template_name=TEMPLATES[trigger],
                    template_version=1,
                    payload={
                        "pet_name": patient.name if patient else "your pet",
                        "due_on": event.next_due_date.isoformat(),
                        "buttons": [
                            {
                                "title": title,
                                "id": encode_button_id(kind, job.id),
                            }
                            for title, kind in zip(
                                QUICK_REPLY_TITLES,
                                ("confirm", "reschedule", "optout"),
                                strict=True,
                            )
                        ],
                    },
                    idempotency_key=f"recall:{job.id}",
                ),
            )
            if queued:
                enqueued += 1

    run.scanned = len(events)
    run.enqueued = enqueued
    run.finished_at = datetime.now(UTC)
    await session.flush()
    return RecallRunResult(created=created, enqueued=enqueued, suppressed=suppressed)
