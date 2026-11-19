import uuid
from datetime import date, timedelta

from sqlalchemy import select

from app.models import Appointment, MessageOutbox, RecallJob, VaccineEvent
from app.models.enums import VaccineStatus

CRON = {"X-Cron-Secret": "dev-cron-secret"}


class Recorder:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, message: MessageOutbox) -> str:
        self.sent.append(message.template_name)
        return f"demo.{len(self.sent)}"


async def test_the_full_demo_loop(client, seeded, make_patient, session):
    """Intake to booked appointment, with WhatsApp kept inside the process."""
    intake = await client.post(
        "/api/v1/patients",
        json={
            "parent": {"full_name": "Priya Sharma", "phone": "+919900011122"},
            "patient": {"name": "Bruno", "species": "Canine", "gender": "Male"},
            "consent": {"granted": True, "source": "intake_tap"},
        },
        headers=seeded.headers(seeded.receptionist),
    )
    assert intake.status_code == 201
    patient_id = intake.json()["patient_id"]
    slug = intake.json()["passport_slug"]

    consult = await client.post(
        "/api/v1/consults",
        json={
            "patient_id": patient_id,
            "provisional_diagnosis": "Acute gastroenteritis",
            "medications": [
                {"name": "Metronidazole", "dosage": "250 mg", "frequency": "BD", "duration_days": 5}
            ],
        },
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert consult.status_code == 201
    rx_code = consult.json()["rx_code"]
    assert consult.json()["whatsapp_status"] == "queued"

    pdf = await client.get(
        f"/api/v1/prescriptions/{rx_code}/pdf", headers=seeded.headers(seeded.doctor)
    )
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")

    passport = await client.get(f"/p/{slug}")
    assert passport.status_code == 200
    assert passport.json()["pet"]["name"] == "Bruno"

    drain = await client.post("/api/v1/ops/outbox/drain", headers=CRON)
    assert drain.status_code == 200
    assert drain.json()["sent"] >= 1

    demo_sends = await client.get("/api/v1/ops/demo-sends", headers=CRON)
    assert any(send["template"] == "rx_delivery_v1" for send in demo_sends.json())

    # A booster that is exactly seven days out is what the nightly job acts on.
    session.add(
        VaccineEvent(
            patient_id=uuid.UUID(patient_id),
            clinic_id=seeded.clinic_a.id,
            doctor_id=seeded.doctor.id,
            vaccine_name="Rabies",
            batch_number="RAB-DEMO",
            administered_date=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=7),
            status=VaccineStatus.ADMINISTERED,
        )
    )
    await session.flush()

    recall = await client.post("/api/v1/ops/recalls/run", headers=CRON)
    assert recall.status_code == 200
    assert recall.json()["created"] == 1

    job = await session.scalar(
        select(RecallJob).order_by(RecallJob.created_at.desc()).limit(1)
    )
    tap = await client.post(
        "/api/v1/ops/simulate-tap",
        json={"recall_job_id": str(job.id), "action": "confirm"},
        headers=CRON,
    )
    assert tap.status_code == 200
    assert tap.json()["handled"] is True

    appointment = await session.scalar(select(Appointment).where(Appointment.recall_job_id == job.id))
    assert appointment is not None
    day = appointment.starts_at.date().isoformat()

    queue = await client.get(
        f"/api/v1/appointments?on={day}", headers=seeded.headers(seeded.receptionist)
    )
    assert queue.status_code == 200
    assert any(row["patient_id"] == patient_id for row in queue.json())

    assert appointment.status.value == "booked"
