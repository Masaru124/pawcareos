import uuid

from app.models import ClinicUser, PetParentAccount, UserRole


async def test_first_sign_in_claims_an_invited_row_by_email(client, seeded, session, jwks):
    email = "new.doctor@example.com"
    invitation = ClinicUser(
        clinic_id=seeded.clinic_a.id,
        auth_user_id=None,
        full_name="Dr. New",
        email=email,
        role=UserRole.DOCTOR,
        vci_registration_no="KAR-7777",
    )
    session.add(invitation)
    await session.flush()

    subject = uuid.uuid4()
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {jwks.sign(subject, email=email)}"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Dr. New"
    await session.refresh(invitation)
    assert invitation.auth_user_id == subject

    second = uuid.uuid4()
    refused = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {jwks.sign(second, email=email)}"},
    )
    assert refused.status_code == 401


async def test_an_unknown_email_cannot_claim_anything(client, seeded, jwks):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {jwks.sign(uuid.uuid4(), email='stranger@example.com')}"},
    )
    assert response.status_code == 401


async def test_only_an_invited_address_may_create_an_account(client, seeded, session):
    staff = await client.post(
        "/api/v1/auth/invitation",
        json={"email": f"  {seeded.doctor.email.upper()}  "},
    )
    assert staff.status_code == 200
    assert staff.json() == {"invited": True, "kind": "clinic"}

    session.add(
        PetParentAccount(pet_parent_id=seeded.patient.parent_id, email="family@example.com")
    )
    await session.flush()
    family = await client.post(
        "/api/v1/auth/invitation", json={"email": "family@example.com"}
    )
    assert family.json() == {"invited": True, "kind": "parent"}

    stranger = await client.post(
        "/api/v1/auth/invitation", json={"email": "stranger@example.com"}
    )
    assert stranger.json() == {"invited": False, "kind": None}


async def test_a_deactivated_staff_row_is_not_an_invitation(client, seeded, make_user):
    former = await make_user(
        seeded.clinic_a, role=UserRole.RECEPTIONIST, vci=None, is_active=False
    )
    response = await client.post(
        "/api/v1/auth/invitation", json={"email": former.email}
    )
    assert response.json()["invited"] is False
