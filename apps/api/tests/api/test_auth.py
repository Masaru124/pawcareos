from app.models.enums import UserRole


async def test_valid_token_returns_the_clinic_identity(client, seeded):
    response = await client.get("/api/v1/auth/me", headers=seeded.headers(seeded.doctor))
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "doctor"
    assert body["clinic_id"] == str(seeded.clinic_a.id)
    assert body["full_name"] == seeded.doctor.full_name


async def test_expired_token_is_rejected(client, seeded):
    token = seeded.sign(seeded.doctor.auth_user_id, expired=True)
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_deactivated_user_is_rejected_even_with_a_valid_token(client, seeded, make_user):
    inactive = await make_user(
        seeded.clinic_a,
        role=UserRole.DOCTOR,
        vci="KAR-99999",
        is_active=False,
    )
    token = seeded.sign(inactive.auth_user_id)
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_tampered_signature_is_rejected(client, seeded, jwks):
    token = seeded.sign(seeded.doctor.auth_user_id)
    tampered = token[:-6] + "AAAAAA"
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401


async def test_wrong_audience_is_rejected(client, seeded):
    token = seeded.sign(seeded.doctor.auth_user_id, audience="anon")
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_no_token_is_rejected(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_foreign_patient_returns_404_not_403(client, seeded):
    response = await client.get(
        f"/api/v1/patients/{seeded.patient.id}",
        headers=seeded.headers(seeded.outsider),
    )
    assert response.status_code == 404


async def test_own_patient_is_returned(client, seeded):
    response = await client.get(
        f"/api/v1/patients/{seeded.patient.id}",
        headers=seeded.headers(seeded.receptionist),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Bruno"
