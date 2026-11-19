import uuid

from sqlalchemy import func, select

from app.models import Consultation, MessageOutbox, RecallJob


def body(patient_id, *, medications=None, vaccinations=None) -> dict:
    return {
        "patient_id": str(patient_id),
        "weight_kg": 24.5,
        "provisional_diagnosis": "Acute gastroenteritis",
        "medications": medications
        if medications is not None
        else [
            {"name": "Metronidazole", "dosage": "250 mg", "frequency": "BD", "duration_days": 5},
        ],
        "vaccinations": vaccinations or [],
    }


async def test_consult_issues_a_readable_code_and_sends_the_passport(client, seeded, make_patient):
    created = await make_patient(seeded.clinic_a)
    response = await client.post(
        "/api/v1/consults",
        json=body(created.patient.id),
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["rx_code"].startswith("RX-BEN-")
    assert payload["passport_url"].endswith(created.patient.passport_slug)
    assert payload["whatsapp_status"] == "queued"


async def test_repeating_the_idempotency_key_returns_the_same_consultation(
    client, seeded, make_patient, session
):
    created = await make_patient(seeded.clinic_a)
    key = str(uuid.uuid4())
    headers = {**seeded.headers(seeded.doctor), "Idempotency-Key": key}

    first = await client.post("/api/v1/consults", json=body(created.patient.id), headers=headers)
    second = await client.post("/api/v1/consults", json=body(created.patient.id), headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["consultation_id"] == second.json()["consultation_id"]
    assert first.json()["rx_code"] == second.json()["rx_code"]

    count = await session.scalar(select(func.count()).select_from(Consultation))
    assert count == 1
    queued = await session.scalar(select(func.count()).select_from(MessageOutbox))
    assert queued == 1


async def test_missing_idempotency_key_is_refused(client, seeded, make_patient):
    created = await make_patient(seeded.clinic_a)
    response = await client.post(
        "/api/v1/consults", json=body(created.patient.id), headers=seeded.headers(seeded.doctor)
    )
    assert response.status_code == 422


async def test_without_consent_the_consult_is_saved_and_nothing_is_sent(
    client, seeded, make_patient, session
):
    created = await make_patient(seeded.clinic_a, consent=False)
    response = await client.post(
        "/api/v1/consults",
        json=body(created.patient.id),
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201
    assert response.json()["whatsapp_status"] == "suppressed"

    assert await session.scalar(select(func.count()).select_from(MessageOutbox)) == 0
    assert await session.scalar(select(func.count()).select_from(Consultation)) == 1


async def test_vaccinations_schedule_the_next_dose(client, seeded, make_patient, session):
    created = await make_patient(seeded.clinic_a)
    response = await client.post(
        "/api/v1/consults",
        json=body(
            created.patient.id,
            medications=[],
            vaccinations=[
                {"kind": "rabies", "vaccine_name": "Rabies", "batch_number": "RAB-1"},
                {"kind": "deworming", "vaccine_name": "Deworming", "batch_number": "DEW-9"},
            ],
        ),
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.text
    assert await session.scalar(select(func.count()).select_from(RecallJob)) == 2


async def test_an_empty_consult_is_refused(client, seeded, make_patient):
    created = await make_patient(seeded.clinic_a)
    response = await client.post(
        "/api/v1/consults",
        json=body(created.patient.id, medications=[], vaccinations=[]),
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert "at least one medication" in response.text


async def test_a_foreign_patient_cannot_be_prescribed(client, seeded, make_patient):
    created = await make_patient(seeded.clinic_b)
    response = await client.post(
        "/api/v1/consults",
        json=body(created.patient.id),
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 404


async def test_codes_increment_per_clinic(client, seeded, make_patient):
    first_patient = await make_patient(seeded.clinic_a, name="Bruno")
    second_patient = await make_patient(seeded.clinic_a, name="Simba")

    first = await client.post(
        "/api/v1/consults",
        json=body(first_patient.patient.id),
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    second = await client.post(
        "/api/v1/consults",
        json=body(second_patient.patient.id),
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert first.json()["rx_code"].endswith("0001")
    assert second.json()["rx_code"].endswith("0002")
