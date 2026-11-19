import io
import uuid

from pypdf import PdfReader


async def issue_consult(client, seeded, patient_id) -> str:
    response = await client.post(
        "/api/v1/consults",
        json={
            "patient_id": str(patient_id),
            "provisional_diagnosis": "Acute gastroenteritis",
            "medications": [
                {"name": "Metronidazole", "dosage": "250 mg", "frequency": "BD", "duration_days": 5}
            ],
            "dietary_advice": "Boiled chicken and rice for three days",
        },
        headers={**seeded.headers(seeded.doctor), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.text
    return response.json()["rx_code"]


def text_of(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


async def test_the_prescription_pdf_names_the_drug_the_pet_and_the_clinic(
    client, seeded, make_patient
):
    created = await make_patient(seeded.clinic_a)
    rx_code = await issue_consult(client, seeded, created.patient.id)

    response = await client.get(
        f"/api/v1/prescriptions/{rx_code}/pdf", headers=seeded.headers(seeded.doctor)
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    text = text_of(response.content)
    assert "PRESCRIPTION" in text
    assert "Metronidazole" in text
    assert "Bruno" in text
    assert rx_code in text
    assert "Boiled chicken" in text


async def test_another_clinic_cannot_fetch_the_pdf(client, seeded, make_patient):
    created = await make_patient(seeded.clinic_a)
    rx_code = await issue_consult(client, seeded, created.patient.id)

    response = await client.get(
        f"/api/v1/prescriptions/{rx_code}/pdf", headers=seeded.headers(seeded.outsider)
    )
    assert response.status_code == 404
