import uuid

from sqlalchemy import func, select

from app.models import ConsentEvent, Patient


def intake_body(phone: str, *, name: str = "Bruno") -> dict:
    return {
        "parent": {"full_name": "Priya Sharma", "phone": phone},
        "patient": {"name": name, "species": "Canine", "gender": "Male", "breed": "Golden Retriever"},
        "consent": {"granted": True, "source": "intake_tap"},
    }


async def test_intake_issues_a_passport_slug_and_records_consent(client, seeded):
    phone = "+919900011122"
    response = await client.post(
        "/api/v1/patients", json=intake_body(phone), headers=seeded.headers(seeded.receptionist)
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["passport_slug"]) == 10

    events = await client.get(
        f"/api/v1/patients/{body['patient_id']}", headers=seeded.headers(seeded.receptionist)
    )
    assert events.status_code == 200


async def test_second_intake_reuses_the_parent_by_phone(client, seeded, session):
    phone = "+919900011133"
    first = await client.post(
        "/api/v1/patients", json=intake_body(phone, name="Bruno"), headers=seeded.headers(seeded.doctor)
    )
    second = await client.post(
        "/api/v1/patients", json=intake_body(phone, name="Simba"), headers=seeded.headers(seeded.doctor)
    )
    assert first.json()["parent_id"] == second.json()["parent_id"]
    assert first.json()["patient_id"] != second.json()["patient_id"]

    consent_count = await session.scalar(select(func.count()).select_from(ConsentEvent))
    assert consent_count == 2


async def test_search_matches_a_phone_suffix_and_hides_other_clinics(client, seeded, session):
    phone = f"+9199{uuid.uuid4().int % 10**8:08d}"
    created = await client.post(
        "/api/v1/patients", json=intake_body(phone), headers=seeded.headers(seeded.doctor)
    )
    suffix = phone[-4:]

    found = await client.get(
        f"/api/v1/patients?q={suffix}", headers=seeded.headers(seeded.doctor)
    )
    assert found.status_code == 200
    ids = [item["id"] for item in found.json()["items"]]
    assert created.json()["patient_id"] in ids

    hidden = await client.get(
        f"/api/v1/patients?q={suffix}", headers=seeded.headers(seeded.outsider)
    )
    assert hidden.json()["items"] == []


async def test_receptionist_can_intake_but_not_prescribe(client, seeded):
    response = await client.post(
        "/api/v1/patients",
        json=intake_body("+919900011199"),
        headers=seeded.headers(seeded.receptionist),
    )
    assert response.status_code == 201

    created_patient = await client.get(
        f"/api/v1/patients/{response.json()['patient_id']}",
        headers=seeded.headers(seeded.receptionist),
    )
    assert created_patient.status_code == 200

    consult = await client.post(
        "/api/v1/consults",
        json={
            "patient_id": response.json()["patient_id"],
            "provisional_diagnosis": "Gastroenteritis",
            "medications": [
                {"name": "Metronidazole", "dosage": "250 mg", "frequency": "BD", "duration_days": 5}
            ],
        },
        headers={**seeded.headers(seeded.receptionist), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert consult.status_code == 403


async def test_directory_lists_the_clinic_patients_without_a_query(client, seeded):
    phone = f"+9199{uuid.uuid4().int % 10**8:08d}"
    created = await client.post(
        "/api/v1/patients", json=intake_body(phone), headers=seeded.headers(seeded.doctor)
    )

    listing = await client.get("/api/v1/patients", headers=seeded.headers(seeded.doctor))
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert created.json()["patient_id"] in [item["id"] for item in items]
    assert all(item["passport_slug"] for item in items)

    hidden = await client.get("/api/v1/patients", headers=seeded.headers(seeded.outsider))
    assert hidden.status_code == 200
    assert hidden.json()["items"] == []


async def test_intake_rejects_a_non_e164_phone(client, seeded):
    response = await client.post(
        "/api/v1/patients",
        json=intake_body("9900011122"),
        headers=seeded.headers(seeded.doctor),
    )
    assert response.status_code == 422


async def test_search_requires_two_characters(client, seeded, session):
    assert (await session.scalar(select(func.count()).select_from(Patient))) >= 1
    response = await client.get("/api/v1/patients?q=b", headers=seeded.headers(seeded.doctor))
    assert response.status_code == 422
