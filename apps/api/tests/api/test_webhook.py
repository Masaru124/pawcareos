import hashlib
import hmac
from datetime import date, timedelta
from types import SimpleNamespace

from sqlalchemy import func, select

from app.domain.recall import encode_button_id
from app.models import Appointment, ConsentEvent, InboundEvent, RecallJob, VaccineEvent
from app.models.enums import RecallStatus, ResponseAction, VaccineStatus
from app.services.inbound import handle_button_reply


def meta_payload(message_id: str, button_id: str, sender: str = "919900011122") -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": message_id,
                                    "from": sender,
                                    "type": "button",
                                    "button": {"payload": button_id},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


async def make_event(session, patient, *, doctor_id, due_in: int = 7) -> VaccineEvent:
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


async def make_job(session, event) -> RecallJob:
    from datetime import UTC, datetime

    job = RecallJob(
        vaccine_event_id=event.id,
        scheduled_dispatch_time=datetime.now(UTC),
        trigger="T-7",
        template_name="recall_t7_v1",
        status=RecallStatus.QUEUED,
    )
    session.add(job)
    await session.flush()
    return job


async def test_an_unsigned_webhook_is_refused(client):
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        json=meta_payload("wamid.1", "cnf:x"),
    )
    assert response.status_code == 403


async def test_a_bad_signature_is_refused(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.webhooks.get_settings",
        lambda: SimpleNamespace(whatsapp_app_secret="shh", whatsapp_verify_token="tok"),
    )
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=b"{}",
        headers={"X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert response.status_code == 403


async def test_a_correct_signature_is_accepted(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.webhooks.get_settings",
        lambda: SimpleNamespace(whatsapp_app_secret="shh", whatsapp_verify_token="tok"),
    )
    body = b'{"entry": []}'
    signature = hmac.new(b"shh", body, hashlib.sha256).hexdigest()
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": f"sha256={signature}", "Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["handled"] == 0


async def test_verification_handshake_echoes_the_challenge(client):
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "pawcare-demo-verify", "hub.challenge": "12345"},
    )
    assert response.status_code == 200
    assert response.text == "12345"


async def test_confirming_books_one_appointment_and_only_once(
    client, seeded, make_patient, session, monkeypatch
):
    created = await make_patient(seeded.clinic_a)
    event = await make_event(session, created.patient, doctor_id=seeded.doctor.id)
    job = await make_job(session, event)
    button = encode_button_id("confirm", job.id)

    monkeypatch.setattr("app.routers.webhooks.valid_signature", lambda body, header: True)
    payload = meta_payload("wamid.abc", button)

    first = await client.post("/api/v1/webhooks/whatsapp", json=payload)
    second = await client.post("/api/v1/webhooks/whatsapp", json=payload)

    assert first.json()["handled"] == 1
    assert second.json()["handled"] == 0
    assert await session.scalar(select(func.count()).select_from(Appointment)) == 1
    await session.refresh(job)
    assert job.status is RecallStatus.RESPONDED
    assert job.response_action is ResponseAction.BOOKED


async def test_opt_out_writes_consent_and_suppresses_other_jobs(
    session, seeded, make_patient
):
    created = await make_patient(seeded.clinic_a)
    first_event = await make_event(session, created.patient, doctor_id=seeded.doctor.id, due_in=7)
    second_event = await make_event(session, created.patient, doctor_id=seeded.doctor.id, due_in=40)
    job = await make_job(session, first_event)
    other = await make_job(session, second_event)

    handled = await handle_button_reply(
        session,
        provider_message_id="wamid.optout",
        from_phone=created.parent.phone,
        button_id=encode_button_id("optout", job.id),
    )

    assert handled is True
    await session.refresh(job)
    await session.refresh(other)
    assert job.status is RecallStatus.SUPPRESSED
    assert other.status is RecallStatus.SUPPRESSED
    revoked = await session.scalar(
        select(func.count())
        .select_from(ConsentEvent)
        .where(
            ConsentEvent.pet_parent_id == created.parent.id,
            ConsentEvent.granted.is_(False),
        )
    )
    assert revoked == 1
    assert await session.scalar(select(func.count()).select_from(InboundEvent)) == 1


async def test_an_unknown_button_payload_is_ignored(session, seeded):
    handled = await handle_button_reply(
        session, provider_message_id="wamid.zzz", from_phone=None, button_id="garbage"
    )
    assert handled is False
