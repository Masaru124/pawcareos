import uuid

from app.models import ClinicUser, UserRole


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
