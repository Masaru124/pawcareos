async def test_the_public_page_hides_the_middle_of_a_microchip(
    client, seeded, make_patient
):
    created = await make_patient(seeded.clinic_a, microchip="900123456789012")
    response = await client.get(f"/p/{created.patient.passport_slug}")

    assert response.status_code == 200
    body = response.json()
    assert body["pet"]["name"] == "Bruno"
    assert body["pet"]["microchip_masked"].endswith("9012")
    assert "23456789" not in body["pet"]["microchip_masked"]
    assert body["clinic"]["name"] == seeded.clinic_a.name


async def test_an_unknown_slug_is_404(client):
    response = await client.get("/p/aaaaaaaaaa")
    assert response.status_code == 404


async def test_status_reflects_the_nearest_due_date(client, seeded, make_patient, session):
    from datetime import date, timedelta

    from app.models import VaccineEvent
    from app.models.enums import VaccineStatus

    created = await make_patient(seeded.clinic_a)
    session.add(
        VaccineEvent(
            patient_id=created.patient.id,
            clinic_id=seeded.clinic_a.id,
            doctor_id=seeded.doctor.id,
            vaccine_name="Rabies",
            batch_number="RAB-1",
            administered_date=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=5),
            status=VaccineStatus.ADMINISTERED,
        )
    )
    await session.flush()

    body = (await client.get(f"/p/{created.patient.passport_slug}")).json()
    assert body["status"] == "due_soon"
    assert body["badges"][0]["state"] == "due_soon"


async def test_the_certificate_is_a_pdf(client, seeded, make_patient):
    created = await make_patient(seeded.clinic_a)
    response = await client.get(f"/p/{created.patient.passport_slug}/certificate.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
