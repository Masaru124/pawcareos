"""Each role gets its own answers, and only legal state changes go through."""

from datetime import datetime, time
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Appointment, AppointmentSource, AppointmentStatus, ConsultMode, UserRole

ZONE = ZoneInfo("Asia/Kolkata")


async def _appointment(
    session: AsyncSession,
    seeded: SimpleNamespace,
    *,
    doctor_id,
    hour: int = 10,
    status: AppointmentStatus = AppointmentStatus.BOOKED,
) -> Appointment:
    appointment = Appointment(
        clinic_id=seeded.clinic_a.id,
        patient_id=seeded.patient.id,
        doctor_id=doctor_id,
        starts_at=datetime.combine(datetime.now(ZONE).date(), time(hour, 0), tzinfo=ZONE),
        status=status,
        source=AppointmentSource.WEB,
        mode=ConsultMode.IN_CLINIC,
    )
    session.add(appointment)
    await session.flush()
    return appointment


async def test_doctor_board_shows_only_their_own_day(
    client: AsyncClient, seeded: SimpleNamespace, make_user, session: AsyncSession
) -> None:
    other_doctor = await make_user(seeded.clinic_a, role=UserRole.DOCTOR, vci="KAR-99999")
    mine = await _appointment(session, seeded, doctor_id=seeded.doctor.id, hour=10)
    theirs = await _appointment(session, seeded, doctor_id=other_doctor.id, hour=11)

    response = await client.get("/api/v1/dashboard/doctor", headers=seeded.headers(seeded.doctor))

    assert response.status_code == 200
    body = response.json()
    ids = {row["id"] for row in body["appointments"]}
    assert str(mine.id) in ids
    assert str(theirs.id) not in ids
    assert body["counts"]["total"] == 1
    assert body["counts"]["waiting"] == 1
    assert body["next_up"]["id"] == str(mine.id)


async def test_front_desk_board_lists_the_whole_clinic(
    client: AsyncClient, seeded: SimpleNamespace, make_user, session: AsyncSession
) -> None:
    other_doctor = await make_user(seeded.clinic_a, role=UserRole.DOCTOR, vci="KAR-99999")
    first = await _appointment(session, seeded, doctor_id=seeded.doctor.id, hour=10)
    second = await _appointment(session, seeded, doctor_id=other_doctor.id, hour=11)

    response = await client.get(
        "/api/v1/dashboard/frontdesk", headers=seeded.headers(seeded.receptionist)
    )

    assert response.status_code == 200
    body = response.json()
    ids = {row["id"] for row in body["arriving"]}
    assert ids == {str(first.id), str(second.id)}
    assert body["arriving"][0]["parent_phone_suffix"]
    assert body["counts"]["waiting"] == 2


@pytest.mark.parametrize("role", [UserRole.DOCTOR, UserRole.RECEPTIONIST])
async def test_boards_are_scoped_to_the_role_that_owns_them(
    client: AsyncClient, seeded: SimpleNamespace, role: UserRole
) -> None:
    headers = seeded.headers(seeded.doctor if role is UserRole.DOCTOR else seeded.receptionist)

    doctor = await client.get("/api/v1/dashboard/doctor", headers=headers)
    desk = await client.get("/api/v1/dashboard/frontdesk", headers=headers)

    if role is UserRole.DOCTOR:
        assert doctor.status_code == 200
        assert desk.status_code == 403
    else:
        assert doctor.status_code == 403
        assert desk.status_code == 200


async def test_pet_parents_cannot_open_a_clinic_board(client: AsyncClient, seeded: SimpleNamespace) -> None:
    assert (await client.get("/api/v1/dashboard/frontdesk")).status_code == 401
    assert (await client.get("/api/v1/dashboard/doctor")).status_code == 401


async def test_appointment_moves_from_due_to_seen(
    client: AsyncClient, seeded: SimpleNamespace, session: AsyncSession
) -> None:
    appointment = await _appointment(session, seeded, doctor_id=seeded.doctor.id)
    headers = seeded.headers(seeded.receptionist)
    path = f"/api/v1/appointments/{appointment.id}/status"

    checked_in = await client.post(path, json={"status": "confirmed"}, headers=headers)
    assert checked_in.status_code == 200, checked_in.text
    assert checked_in.json()["status"] == "confirmed"

    seen = await client.post(path, json={"status": "completed"}, headers=headers)
    assert seen.status_code == 200
    assert seen.json()["status"] == "completed"

    backwards = await client.post(path, json={"status": "booked"}, headers=headers)
    assert backwards.status_code == 409


async def test_a_booking_cannot_skip_the_waiting_room(
    client: AsyncClient, seeded: SimpleNamespace, session: AsyncSession
) -> None:
    appointment = await _appointment(session, seeded, doctor_id=seeded.doctor.id)

    response = await client.post(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "completed"},
        headers=seeded.headers(seeded.doctor),
    )

    assert response.status_code == 409
    assert "booked cannot become completed" in response.json()["detail"]


async def test_other_clinics_cannot_touch_this_board(
    client: AsyncClient, seeded: SimpleNamespace, session: AsyncSession
) -> None:
    appointment = await _appointment(session, seeded, doctor_id=seeded.doctor.id)

    response = await client.post(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "cancelled"},
        headers=seeded.headers(seeded.outsider),
    )

    assert response.status_code == 404
