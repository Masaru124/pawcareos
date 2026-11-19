from datetime import UTC, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    Appointment,
    AppointmentStatus,
    AuditLog,
    Clinic,
    ClinicUser,
    ConsultMode,
    Patient,
    UserRole,
    VaccineEvent,
    VaccineStatus,
)
from app.rbac import Action
from app.schemas.admin import (
    ActivityOut,
    AdminCountsOut,
    AdminOverviewOut,
    ClinicAdminOut,
    StaffInviteIn,
    StaffOut,
)
from app.services.audit import record_audit

router = APIRouter(prefix="/admin", tags=["admin"])


def _zone(clinic: Clinic | None) -> ZoneInfo:
    try:
        return ZoneInfo(clinic.timezone if clinic else "Asia/Kolkata")
    except Exception:  # noqa: BLE001 - a bad stored zone must not block the panel
        return ZoneInfo("Asia/Kolkata")


@router.get("/overview", response_model=AdminOverviewOut)
async def overview(
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.CLINIC_MANAGE))],
) -> AdminOverviewOut:
    """Owner-only. One request answers 'how is the clinic doing today'."""
    clinic = await session.get(Clinic, user.clinic_id)
    if clinic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clinic not found")

    zone = _zone(clinic)
    now = datetime.now(UTC)
    local_today = datetime.now(zone).date()
    day_start = datetime.combine(local_today, time(0, 0), tzinfo=zone)
    day_end = day_start + timedelta(days=1)

    async def count(statement) -> int:
        return await session.scalar(statement) or 0

    counts = AdminCountsOut(
        patients=await count(
            select(func.count())
            .select_from(Patient)
            .where(Patient.primary_clinic_id == clinic.id, Patient.is_active.is_(True))
        ),
        appointments_today=await count(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.clinic_id == clinic.id,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.starts_at >= day_start,
                Appointment.starts_at < day_end,
            )
        ),
        online_today=await count(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.clinic_id == clinic.id,
                Appointment.mode == ConsultMode.ONLINE,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.starts_at >= day_start,
                Appointment.starts_at < day_end,
            )
        ),
        upcoming_week=await count(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.clinic_id == clinic.id,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.starts_at >= now,
                Appointment.starts_at < now + timedelta(days=7),
            )
        ),
        overdue_vaccines=await count(
            select(func.count())
            .select_from(VaccineEvent)
            .where(
                VaccineEvent.clinic_id == clinic.id,
                VaccineEvent.status == VaccineStatus.ADMINISTERED,
                VaccineEvent.next_due_date < local_today,
            )
        ),
        doctors=await count(
            select(func.count())
            .select_from(ClinicUser)
            .where(
                ClinicUser.clinic_id == clinic.id,
                ClinicUser.role == UserRole.DOCTOR,
                ClinicUser.is_active.is_(True),
            )
        ),
        staff=await count(
            select(func.count())
            .select_from(ClinicUser)
            .where(ClinicUser.clinic_id == clinic.id, ClinicUser.is_active.is_(True))
        ),
    )

    staff_rows = (
        await session.execute(
            select(ClinicUser)
            .where(ClinicUser.clinic_id == clinic.id)
            .order_by(ClinicUser.role, ClinicUser.full_name)
        )
    ).scalars()

    activity_rows = (
        await session.execute(
            select(AuditLog, ClinicUser)
            .outerjoin(ClinicUser, AuditLog.actor_id == ClinicUser.id)
            .where(AuditLog.clinic_id == clinic.id)
            .order_by(AuditLog.created_at.desc())
            .limit(10)
        )
    ).all()

    return AdminOverviewOut(
        clinic=ClinicAdminOut(
            name=clinic.name,
            city=clinic.city,
            address=clinic.address_street,
            phone=clinic.phone,
            timezone=str(zone),
            opens_at=clinic.opens_at.strftime("%H:%M"),
            closes_at=clinic.closes_at.strftime("%H:%M"),
        ),
        counts=counts,
        staff=[
            StaffOut(
                id=member.id,
                full_name=member.full_name,
                email=member.email,
                role=member.role.value,
                claimed=member.auth_user_id is not None,
                is_active=member.is_active,
                vci_suffix=(
                    f"…{member.vci_registration_no[-4:]}"
                    if member.vci_registration_no
                    else None
                ),
            )
            for member in staff_rows
        ],
        activity=[
            ActivityOut(
                action=entry.action,
                subject_type=entry.subject_type,
                created_at=entry.created_at,
                actor_name=actor.full_name if actor else None,
            )
            for entry, actor in activity_rows
        ],
    )


@router.post("/staff", response_model=StaffOut, status_code=201)
async def invite_staff(
    payload: StaffInviteIn,
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.CLINIC_MANAGE))],
) -> StaffOut:
    """An owner adds a colleague. The first verified sign-in claims the row."""
    if payload.role is UserRole.DOCTOR and not payload.vci_registration_no:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A doctor needs a VCI registration number",
        )

    existing = await session.scalar(
        select(ClinicUser).where(func.lower(ClinicUser.email) == payload.email)
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "That address already belongs to a clinic user",
        )

    member = ClinicUser(
        clinic_id=user.clinic_id,
        full_name=payload.full_name,
        email=payload.email,
        vci_registration_no=payload.vci_registration_no,
        role=payload.role,
    )
    session.add(member)
    await session.flush()

    await record_audit(
        session,
        actor_id=user.id,
        clinic_id=user.clinic_id,
        action="staff.invited",
        subject_type="clinic_user",
        subject_id=member.id,
    )

    return StaffOut(
        id=member.id,
        full_name=member.full_name,
        email=member.email,
        role=member.role.value,
        claimed=False,
        is_active=True,
        vci_suffix=(
            f"…{member.vci_registration_no[-4:]}" if member.vci_registration_no else None
        ),
    )
