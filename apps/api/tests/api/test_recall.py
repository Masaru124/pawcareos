from datetime import date, timedelta

from sqlalchemy import func, select

from app.models import MessageOutbox, RecallJob, VaccineEvent
from app.models.enums import VaccineStatus
from app.services.recall import generate_recall_jobs


async def seed_event(session, patient, *, doctor_id, due_in: int) -> VaccineEvent:
    event = VaccineEvent(
        patient_id=patient.id,
        clinic_id=patient.primary_clinic_id,
        doctor_id=doctor_id,
        vaccine_name="Rabies",
        batch_number="RAB-1",
        administered_date=date.today() - timedelta(days=358),
        next_due_date=date.today() + timedelta(days=due_in),
        status=VaccineStatus.ADMINISTERED,
    )
    session.add(event)
    await session.flush()
    return event


async def test_one_reminder_per_due_date_and_only_once(session, seeded, make_patient):
    first = await make_patient(seeded.clinic_a, name="Bruno")
    second = await make_patient(seeded.clinic_a, name="Simba")
    await seed_event(session, first.patient, doctor_id=seeded.doctor.id, due_in=7)
    await seed_event(session, second.patient, doctor_id=seeded.doctor.id, due_in=2)

    first_run = await generate_recall_jobs(session)
    second_run = await generate_recall_jobs(session)

    assert first_run.created == 2
    assert first_run.enqueued == 2
    assert second_run.created == 0
    assert second_run.enqueued == 0
    assert await session.scalar(select(func.count()).select_from(RecallJob)) == 2
    assert await session.scalar(select(func.count()).select_from(MessageOutbox)) == 2


async def test_without_consent_nothing_is_queued(session, seeded, make_patient):
    created = await make_patient(seeded.clinic_a, consent=False)
    await seed_event(session, created.patient, doctor_id=seeded.doctor.id, due_in=7)

    result = await generate_recall_jobs(session)

    assert result.suppressed == 1
    assert result.created == 0
    assert await session.scalar(select(func.count()).select_from(MessageOutbox)) == 0


async def test_overdue_events_get_an_overdue_reminder(session, seeded, make_patient):
    created = await make_patient(seeded.clinic_a)
    await seed_event(session, created.patient, doctor_id=seeded.doctor.id, due_in=-3)

    result = await generate_recall_jobs(session)

    assert result.created == 1
    trigger = await session.scalar(select(RecallJob.trigger))
    assert trigger is not None
    assert trigger.value == "OVERDUE"


async def test_a_distant_due_date_is_ignored(session, seeded, make_patient):
    created = await make_patient(seeded.clinic_a)
    await seed_event(session, created.patient, doctor_id=seeded.doctor.id, due_in=120)

    result = await generate_recall_jobs(session)

    assert result.created == 0
    assert result.enqueued == 0
