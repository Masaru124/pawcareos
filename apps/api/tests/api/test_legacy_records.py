import uuid

from app.models import PetParent
from app.services import records as record_store

INVITE_EMAIL = "vault.portal@example.com"


async def _parent_headers(client, seeded, session, email: str = INVITE_EMAIL) -> dict[str, str]:
    parent = await session.get(PetParent, seeded.patient.parent_id)
    invite = await client.post(
        "/api/v1/portal/invites",
        json={"parent_phone": parent.phone, "email": email},
        headers=seeded.headers(seeded.doctor),
    )
    assert invite.status_code == 201, invite.text
    return {"Authorization": f"Bearer {seeded.sign(uuid.uuid4(), email=email)}"}


def _upload(client, patient_id, headers, content=b"%PDF-1.4 old vaccine card", **overrides):
    data = {"record_type": "VACCINE_CARD", **overrides.pop("data", {})}
    files = {"file": overrides.pop("files", ("card.pdf", content, "application/pdf"))}
    return client.post(
        f"/api/v1/portal/pets/{patient_id}/records",
        data=data,
        files=files,
        headers=headers,
    )


async def test_a_parent_digitises_a_paper_record(client, seeded, session, tmp_path, monkeypatch):
    monkeypatch.setattr(record_store, "storage_root", lambda settings: tmp_path)
    headers = await _parent_headers(client, seeded, session)

    upload = await _upload(
        client,
        seeded.patient.id,
        headers,
        data={"description": "  Rabies card from 2019  "},
    )
    assert upload.status_code == 201, upload.text
    body = upload.json()
    assert body["record_type"] == "VACCINE_CARD"
    assert body["description"] == "Rabies card from 2019"
    assert body["content_type"] == "application/pdf"
    assert body["size_bytes"] > 0

    records = await client.get(
        f"/api/v1/portal/pets/{seeded.patient.id}/records", headers=headers
    )
    assert records.status_code == 200, records.text
    stored = records.json()["legacy_records"]
    assert [item["file_name"] for item in stored] == ["card.pdf"]

    download = await client.get(
        f"/api/v1/portal/pets/{seeded.patient.id}/records/{body['id']}/file", headers=headers
    )
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content == b"%PDF-1.4 old vaccine card"

    # The bytes live outside the database, under their own opaque key.
    assert len(list(tmp_path.iterdir())) == 1


async def test_another_family_cannot_read_or_add_to_the_record(client, seeded, session, tmp_path, monkeypatch):
    monkeypatch.setattr(record_store, "storage_root", lambda settings: tmp_path)
    headers = await _parent_headers(client, seeded, session)

    assert (await _upload(client, uuid.uuid4(), headers)).status_code == 404

    upload = await _upload(client, seeded.patient.id, headers)
    assert upload.status_code == 201
    record_id = upload.json()["id"]

    assert (
        await client.get(
            f"/api/v1/portal/pets/{uuid.uuid4()}/records/{record_id}/file", headers=headers
        )
    ).status_code == 404


async def test_a_family_withdraws_its_own_upload(client, seeded, session, tmp_path, monkeypatch):
    monkeypatch.setattr(record_store, "storage_root", lambda settings: tmp_path)
    headers = await _parent_headers(client, seeded, session)

    upload = await _upload(client, seeded.patient.id, headers)
    assert upload.status_code == 201
    record_id = upload.json()["id"]
    assert len(list(tmp_path.iterdir())) == 1

    removed = await client.delete(
        f"/api/v1/portal/pets/{seeded.patient.id}/records/{record_id}", headers=headers
    )
    assert removed.status_code == 204

    records = await client.get(
        f"/api/v1/portal/pets/{seeded.patient.id}/records", headers=headers
    )
    assert records.json()["legacy_records"] == []
    assert not list(tmp_path.iterdir())

    gone = await client.get(
        f"/api/v1/portal/pets/{seeded.patient.id}/records/{record_id}/file", headers=headers
    )
    assert gone.status_code == 404


async def test_the_vault_refuses_what_it_cannot_read(client, seeded, session, tmp_path, monkeypatch):
    monkeypatch.setattr(record_store, "storage_root", lambda settings: tmp_path)
    headers = await _parent_headers(client, seeded, session)

    wrong_type = await _upload(
        client,
        seeded.patient.id,
        headers,
        files=("notes.txt", b"hello", "text/plain"),
    )
    assert wrong_type.status_code == 415

    empty = await _upload(client, seeded.patient.id, headers, content=b"")
    assert empty.status_code == 400

    huge = b"x" * (record_store.MAX_UPLOAD_BYTES + 1)
    assert (await _upload(client, seeded.patient.id, headers, content=huge)).status_code == 413

    assert not list(tmp_path.iterdir())
