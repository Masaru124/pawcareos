import uuid

from app.models import UserRole


async def test_only_the_owner_sees_the_admin_overview(client, seeded, make_user):
    owner = await make_user(seeded.clinic_a, role=UserRole.OWNER, vci=None)

    response = await client.get("/api/v1/admin/overview", headers=seeded.headers(owner))
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["clinic"]["name"] == "Shanti Vet Clinic"
    assert body["counts"]["patients"] >= 1
    assert body["counts"]["doctors"] >= 1
    assert any(member["role"] == "doctor" for member in body["staff"])
    assert all("vci_registration_no" not in member for member in body["staff"])

    for user in (seeded.doctor, seeded.receptionist):
        denied = await client.get("/api/v1/admin/overview", headers=seeded.headers(user))
        assert denied.status_code == 403


async def test_the_owner_invites_a_colleague_who_then_claims_it(client, seeded, make_user):
    owner = await make_user(seeded.clinic_a, role=UserRole.OWNER, vci=None)
    email = f"new.vet.{uuid.uuid4().hex[:6]}@example.com"

    invited = await client.post(
        "/api/v1/admin/staff",
        json={
            "full_name": "Dr. New Vet",
            "email": email,
            "role": "doctor",
            "vci_registration_no": "KAR-99881",
        },
        headers=seeded.headers(owner),
    )
    assert invited.status_code == 201, invited.text
    assert invited.json()["claimed"] is False
    assert invited.json()["role"] == "doctor"

    again = await client.post(
        "/api/v1/admin/staff",
        json={"full_name": "Someone Else", "email": email, "role": "receptionist"},
        headers=seeded.headers(owner),
    )
    assert again.status_code == 409

    # The invited doctor signs in with the same address and lands in the clinic.
    token = seeded.sign(uuid.uuid4(), email=email)
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "doctor"
    assert me.json()["full_name"] == "Dr. New Vet"


async def test_a_doctor_needs_a_vci_number_to_be_invited(client, seeded, make_user):
    owner = await make_user(seeded.clinic_a, role=UserRole.OWNER, vci=None)

    response = await client.post(
        "/api/v1/admin/staff",
        json={
            "full_name": "Dr. No Number",
            "email": "no.number@example.com",
            "role": "doctor",
        },
        headers=seeded.headers(owner),
    )
    assert response.status_code == 422
    assert "VCI" in response.json()["detail"]


async def test_a_doctor_cannot_invite_staff(client, seeded):
    response = await client.post(
        "/api/v1/admin/staff",
        json={"full_name": "Sneaky", "email": "sneaky@example.com", "role": "receptionist"},
        headers=seeded.headers(seeded.doctor),
    )
    assert response.status_code == 403
