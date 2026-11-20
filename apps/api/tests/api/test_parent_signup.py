import uuid

from app.models import PetParent


async def _signup(client, seeded, email: str, phone: str, name: str = "New Parent"):
    headers = {"Authorization": f"Bearer {seeded.sign(uuid.uuid4(), email=email)}"}
    response = await client.post(
        "/api/v1/auth/parent",
        json={"full_name": name, "phone": phone},
        headers=headers,
    )
    return response, headers


async def test_a_parent_signs_up_without_an_invitation(client, seeded, session):
    email = "selfserve.parent@example.com"
    response, headers = await _signup(client, seeded, email, "+919812340001", "Anita Rao")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] is True
    assert body["email"] == email

    me = await client.get("/api/v1/portal/me", headers=headers)
    assert me.status_code == 200, me.text
    assert me.json()["parent_name"] == "Anita Rao"
    assert me.json()["pets"] == []
    assert me.json()["phone_suffix"] == "0001"


async def test_signing_up_twice_keeps_one_family(client, seeded):
    email = "twice.parent@example.com"
    first, headers = await _signup(client, seeded, email, "+919812340002")
    second = await client.post(
        "/api/v1/auth/parent",
        json={"full_name": "Someone Else", "phone": "+919812340009"},
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["created"] is False
    assert second.json()["parent_id"] == first.json()["parent_id"]


async def test_the_phone_the_clinic_knows_attaches_the_family(client, seeded, session):
    parent = await session.get(PetParent, seeded.patient.parent_id)
    response, headers = await _signup(
        client, seeded, "bruno.household@example.com", parent.phone, "Priya Sharma"
    )
    assert response.status_code == 200, response.text
    assert response.json()["created"] is False
    assert str(response.json()["parent_id"]) == str(parent.id)

    # The family's existing pet is visible straight away.
    me = await client.get("/api/v1/portal/me", headers=headers)
    assert me.status_code == 200
    assert [pet["name"] for pet in me.json()["pets"]] == ["Bruno"]


async def test_a_signed_up_parent_is_never_clinic_staff(client, seeded):
    email = "staff.blocked@example.com"
    _, headers = await _signup(client, seeded, email, "+919812340003")
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 401
    assert (await client.get("/api/v1/appointments", headers=headers)).status_code == 401


async def test_the_signup_refuses_a_phone_that_is_already_a_login(client, seeded, session):
    parent = await session.get(PetParent, seeded.patient.parent_id)
    first, _ = await _signup(
        client, seeded, "first.owner@example.com", parent.phone, "Priya Sharma"
    )
    assert first.status_code == 200

    # A second verified address offering the same number must not take over the login.
    second, _ = await _signup(
        client, seeded, "impostor@example.com", parent.phone, "Not Priya"
    )
    assert second.status_code == 409


async def test_the_signup_rejects_a_malformed_phone(client, seeded):
    headers = {"Authorization": f"Bearer {seeded.sign(uuid.uuid4(), email='bad.phone@example.com')}"}
    response = await client.post(
        "/api/v1/auth/parent",
        json={"full_name": "Bad Phone", "phone": "9812340000"},
        headers=headers,
    )
    assert response.status_code == 422

