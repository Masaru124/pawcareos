import uuid

from sqlalchemy import func, select

from app.models import AuditLog, PetParent

INVITE_EMAIL = "priya.portal@example.com"


async def _parent_phone(session, patient) -> str:
    parent = await session.get(PetParent, patient.parent_id)
    return parent.phone


def parent_headers(seeded, email: str = INVITE_EMAIL) -> dict[str, str]:
    return {"Authorization": f"Bearer {seeded.sign(uuid.uuid4(), email=email)}"}


async def test_staff_invite_then_the_parent_claims_by_email(client, seeded, session):
    phone = await _parent_phone(session, seeded.patient)

    invite = await client.post(
        "/api/v1/portal/invites",
        json={"parent_phone": phone, "email": INVITE_EMAIL},
        headers=seeded.headers(seeded.receptionist),
    )
    assert invite.status_code == 201, invite.text
    assert invite.json()["already_claimed"] is False

    subject = uuid.uuid4()
    first = {"Authorization": f"Bearer {seeded.sign(subject, email=INVITE_EMAIL)}"}
    me = await client.get("/api/v1/portal/me", headers=first)
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["parent_name"] == "Priya"
    assert [pet["name"] for pet in body["pets"]] == ["Bruno"]
    assert body["pets"][0]["passport_slug"] == seeded.patient.passport_slug

    audit = await session.scalar(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "parent.claimed")
    )
    assert audit == 1

    # This subject is bound by id now, so a changed email in the token cannot move it.
    moved = {"Authorization": f"Bearer {seeded.sign(subject, email='other@example.com')}"}
    assert (await client.get("/api/v1/portal/me", headers=moved)).status_code == 200

    # An unrelated subject claiming the same email finds nothing to claim.
    stranger = parent_headers(seeded, INVITE_EMAIL)
    assert (await client.get("/api/v1/portal/me", headers=stranger)).status_code == 401


async def test_a_doctor_cannot_open_the_parent_portal(client, seeded):
    response = await client.get("/api/v1/portal/me", headers=seeded.headers(seeded.doctor))
    assert response.status_code == 401


async def test_a_parent_cannot_read_the_clinic_queue(client, seeded, session):
    email = "queue.boundary@example.com"
    phone = await _parent_phone(session, seeded.patient)
    invite = await client.post(
        "/api/v1/portal/invites",
        json={"parent_phone": phone, "email": email},
        headers=seeded.headers(seeded.doctor),
    )
    assert invite.status_code == 201

    # The claim itself works, and still cannot reach a clinic endpoint.
    assert (await client.get("/api/v1/portal/me", headers=parent_headers(seeded, email))).status_code == 200
    response = await client.get("/api/v1/appointments", headers=parent_headers(seeded, email))
    assert response.status_code == 401


async def test_invite_refuses_a_phone_from_another_clinic(client, seeded, session):
    phone = await _parent_phone(session, seeded.patient)
    response = await client.post(
        "/api/v1/portal/invites",
        json={"parent_phone": phone, "email": "outsider.invite@example.com"},
        headers=seeded.headers(seeded.outsider),
    )
    assert response.status_code == 404


async def test_invite_rejects_a_malformed_email(client, seeded, session):
    phone = await _parent_phone(session, seeded.patient)
    response = await client.post(
        "/api/v1/portal/invites",
        json={"parent_phone": phone, "email": "not-an-email"},
        headers=seeded.headers(seeded.doctor),
    )
    assert response.status_code == 422


async def test_a_parent_reads_the_full_record_but_only_for_their_own_pet(client, seeded, session):
    email = "records.portal@example.com"
    phone = await _parent_phone(session, seeded.patient)
    invite = await client.post(
        "/api/v1/portal/invites",
        json={"parent_phone": phone, "email": email},
        headers=seeded.headers(seeded.doctor),
    )
    assert invite.status_code == 201

    consult = await client.post(
        "/api/v1/consults",
        json={
            "patient_id": str(seeded.patient.id),
            "provisional_diagnosis": "Otitis externa",
            "medications": [
                {"name": "Ear drops", "dosage": "2 drops", "frequency": "BD", "duration_days": 7}
            ],
        },
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert consult.status_code == 201, consult.text

    headers = parent_headers(seeded, email)
    records = await client.get(f"/api/v1/portal/pets/{seeded.patient.id}/records", headers=headers)
    assert records.status_code == 200, records.text
    body = records.json()
    assert body["name"] == "Bruno"
    assert body["clinic_name"] == "Shanti Vet Clinic"
    assert len(body["prescriptions"]) == 1
    assert body["prescriptions"][0]["diagnosis"] == "Otitis externa"
    assert body["prescriptions"][0]["items"][0]["medication_name"] == "Ear drops"

    stranger = await client.get(f"/api/v1/portal/pets/{uuid.uuid4()}/records", headers=headers)
    assert stranger.status_code == 404
