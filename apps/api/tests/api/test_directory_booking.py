import uuid
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.models import Appointment, MessageOutbox, Patient, UserRole

TZ = ZoneInfo("Asia/Kolkata")


def slot_two_days_out(hour: int = 10) -> datetime:
    """Far enough ahead that both reminders are still in the future."""
    day = (datetime.now(TZ) + timedelta(days=2)).date()
    return datetime.combine(day, time(hour, 0), tzinfo=TZ)


def booking_body(doctor_id, starts_at: datetime, phone: str) -> dict:
    return {
        "doctor_id": str(doctor_id),
        "starts_at": starts_at.isoformat(),
        "parent": {"full_name": "Priya Sharma", "phone": phone},
        "patient": {"name": "Bruno", "species": "Canine", "breed": "Golden Retriever"},
        "consent": True,
    }


async def test_directory_returns_only_verified_active_doctors(client, seeded, make_user):
    hidden = await make_user(seeded.clinic_a, role=UserRole.DOCTOR, is_active=False)

    response = await client.get("/api/v1/directory/doctors", params={"q": "Shanti"})
    assert response.status_code == 200
    body = response.json()
    ids = [item["doctor_id"] for item in body]

    assert str(seeded.doctor.id) in ids
    assert str(hidden.id) not in ids
    entry = next(item for item in body if item["doctor_id"] == str(seeded.doctor.id))
    assert entry["clinic"]["name"] == "Shanti Vet Clinic"
    assert entry["vci_suffix"] == "…2345"
    assert "12345" not in entry["vci_suffix"] or entry["vci_suffix"].startswith("…")


async def test_availability_hides_the_past_and_published_slots(client, seeded):
    day = (datetime.now(TZ) + timedelta(days=2)).date().isoformat()
    response = await client.get(
        f"/api/v1/directory/doctors/{seeded.doctor.id}/availability", params={"date": day}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["timezone"] == "Asia/Kolkata"
    # 09:00 to 18:00 in 30 minute steps.
    assert len(body["slots"]) == 18
    assert body["slots"][0]["label"] == "09:00"


async def test_booking_creates_the_pet_and_queues_two_reminders(client, seeded, session):
    starts_at = slot_two_days_out()
    phone = f"+9199{uuid.uuid4().int % 10**8:08d}"

    response = await client.post(
        "/api/v1/directory/bookings",
        json=booking_body(seeded.doctor.id, starts_at, phone),
    )
    assert response.status_code == 201, response.text
    body = response.json()

    assert len(body["passport_slug"]) == 10
    assert body["passport_url"].endswith(f"/p/{body['passport_slug']}")
    assert body["reminders_queued"] == 2

    reminders = (
        await session.execute(
            select(MessageOutbox).where(
                MessageOutbox.correlation_id == str(body["appointment_id"])
            )
        )
    ).scalars().all()
    assert len(reminders) == 2
    assert {reminder.template_name for reminder in reminders} == {
        "appointment_reminder_t24_v1",
        "appointment_reminder_t2_v1",
    }
    assert all(reminder.to_phone == phone for reminder in reminders)

    appointment = await session.get(Appointment, uuid.UUID(body["appointment_id"]))
    assert appointment is not None
    assert appointment.source.value == "web"

    patient = await session.scalar(select(Patient).where(Patient.passport_slug == body["passport_slug"]))
    assert patient is not None and patient.name == "Bruno"


async def test_a_second_booking_of_the_same_slot_is_refused(client, seeded, session):
    starts_at = slot_two_days_out(hour=11)
    first = await client.post(
        "/api/v1/directory/bookings",
        json=booking_body(seeded.doctor.id, starts_at, f"+9199{uuid.uuid4().int % 10**8:08d}"),
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/directory/bookings",
        json=booking_body(seeded.doctor.id, starts_at, f"+9199{uuid.uuid4().int % 10**8:08d}"),
    )
    assert second.status_code == 409
    assert "just booked" in second.json()["detail"]

    taken = await session.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.starts_at == starts_at)
    )
    assert taken == 1


async def test_a_time_off_the_grid_is_refused(client, seeded):
    off_grid = slot_two_days_out().replace(hour=3)
    response = await client.post(
        "/api/v1/directory/bookings",
        json=booking_body(seeded.doctor.id, off_grid, f"+9199{uuid.uuid4().int % 10**8:08d}"),
    )
    assert response.status_code == 422
    assert "booking grid" in response.json()["detail"]


async def test_a_booked_slot_disappears_from_availability(client, seeded):
    day = (datetime.now(TZ) + timedelta(days=2)).date()
    starts_at = datetime.combine(day, time(9, 0), tzinfo=TZ)

    await client.post(
        "/api/v1/directory/bookings",
        json=booking_body(seeded.doctor.id, starts_at, f"+9199{uuid.uuid4().int % 10**8:08d}"),
    )

    response = await client.get(
        f"/api/v1/directory/doctors/{seeded.doctor.id}/availability",
        params={"date": day.isoformat()},
    )
    labels = [slot["label"] for slot in response.json()["slots"]]
    assert "09:00" not in labels
    assert "09:30" in labels


async def test_an_online_consult_books_at_any_hour_with_a_room(client, seeded):
    day = (datetime.now(TZ) + timedelta(days=2)).date()
    starts_at = datetime.combine(day, time(3, 0), tzinfo=TZ)
    body = booking_body(seeded.doctor.id, starts_at, f"+9199{uuid.uuid4().int % 10**8:08d}")
    body["mode"] = "online"

    response = await client.post("/api/v1/directory/bookings", json=body)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["mode"] == "online"
    assert data["room_url"].startswith("https://meet.jit.si/pawcare-")

    availability = await client.get(
        f"/api/v1/directory/doctors/{seeded.doctor.id}/availability",
        params={"date": day.isoformat(), "mode": "online"},
    )
    assert availability.status_code == 200
    assert availability.json()["mode"] == "online"
    # Every half hour across the whole day, minus the 03:00 just booked above.
    labels = [slot["label"] for slot in availability.json()["slots"]]
    assert len(labels) == 47
    assert "03:00" not in labels
    assert "00:00" in labels and "23:30" in labels

    room = await client.get(f"/api/v1/directory/rooms/{data['appointment_id']}")
    assert room.status_code == 200
    assert room.json()["room_url"] == data["room_url"]


async def test_a_clinic_visit_cannot_be_booked_at_three_in_the_morning(client, seeded):
    day = (datetime.now(TZ) + timedelta(days=2)).date()
    starts_at = datetime.combine(day, time(3, 0), tzinfo=TZ)
    response = await client.post(
        "/api/v1/directory/bookings",
        json=booking_body(seeded.doctor.id, starts_at, f"+9199{uuid.uuid4().int % 10**8:08d}"),
    )
    assert response.status_code == 422
