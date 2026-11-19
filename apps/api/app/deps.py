import logging
import uuid
from typing import Annotated, NamedTuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import unauthorized, verify_supabase_jwt
from app.config import Settings, get_settings
from app.db import get_session
from app.models import ClinicUser, Patient, PetParent, PetParentAccount
from app.rbac import Action, can
from app.services.audit import record_audit

logger = logging.getLogger("pawcare.auth")
bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


async def current_user(
    credentials: CredentialsDep,
    session: SessionDep,
    settings: SettingsDep,
) -> ClinicUser:
    if credentials is None:
        raise unauthorized()
    claims = await verify_supabase_jwt(credentials.credentials, settings)
    try:
        auth_user_id = uuid.UUID(claims.sub)
    except ValueError as exc:
        raise unauthorized("Token subject is not a user id") from exc
    user = await session.scalar(
        select(ClinicUser).where(
            ClinicUser.auth_user_id == auth_user_id,
            ClinicUser.is_active.is_(True),
        )
    )
    if user is None:
        user = await _claim_invitation(session, auth_user_id, claims.email)
    if user is None:
        raise unauthorized()
    return user


async def _claim_invitation(
    session: AsyncSession,
    auth_user_id: uuid.UUID,
    email: str | None,
) -> ClinicUser | None:
    """First sign-in binds an invited row by email. Supabase has already verified the address."""
    if not email:
        return None
    invitation = await session.scalar(
        select(ClinicUser).where(
            func.lower(ClinicUser.email) == email.strip().lower(),
            ClinicUser.auth_user_id.is_(None),
            ClinicUser.is_active.is_(True),
        )
    )
    if invitation is None:
        return None
    invitation.auth_user_id = auth_user_id
    await session.flush()
    await record_audit(
        session,
        actor_id=invitation.id,
        clinic_id=invitation.clinic_id,
        action="user.claimed",
        subject_type="clinic_user",
        subject_id=invitation.id,
    )
    logger.info("clinic user %s claimed by sign-in", invitation.id)
    return invitation


CurrentUser = Annotated[ClinicUser, Depends(current_user)]


class ParentIdentity(NamedTuple):
    account: PetParentAccount
    parent: PetParent


async def current_parent(
    credentials: CredentialsDep,
    session: SessionDep,
    settings: SettingsDep,
) -> ParentIdentity:
    """The third principal. A pet parent is never a clinic user."""
    if credentials is None:
        raise unauthorized()
    claims = await verify_supabase_jwt(credentials.credentials, settings)
    try:
        auth_user_id = uuid.UUID(claims.sub)
    except ValueError as exc:
        raise unauthorized("Token subject is not a user id") from exc

    account = await session.scalar(
        select(PetParentAccount).where(
            PetParentAccount.auth_user_id == auth_user_id,
            PetParentAccount.is_active.is_(True),
        )
    )
    if account is None:
        account = await _claim_parent_account(session, auth_user_id, claims.email)
    if account is None:
        raise unauthorized(
            "No pet records are linked to this account yet. Ask your clinic to add this email."
        )

    parent = await session.get(PetParent, account.pet_parent_id)
    if parent is None:
        raise unauthorized()
    return ParentIdentity(account=account, parent=parent)


async def _claim_parent_account(
    session: AsyncSession,
    auth_user_id: uuid.UUID,
    email: str | None,
) -> PetParentAccount | None:
    """First verified sign-in binds the invited parent row. Same rule as clinic staff."""
    if not email:
        return None
    account = await session.scalar(
        select(PetParentAccount).where(
            func.lower(PetParentAccount.email) == email.strip().lower(),
            PetParentAccount.auth_user_id.is_(None),
            PetParentAccount.is_active.is_(True),
        )
    )
    if account is None:
        return None
    account.auth_user_id = auth_user_id
    await session.flush()

    clinic_id = await session.scalar(
        select(Patient.primary_clinic_id).where(Patient.parent_id == account.pet_parent_id).limit(1)
    )
    if clinic_id is not None:
        # The audit row belongs to the clinic whose record was opened, and has no staff actor.
        await record_audit(
            session,
            actor_id=None,
            clinic_id=clinic_id,
            action="parent.claimed",
            subject_type="pet_parent_account",
            subject_id=account.id,
        )
    logger.info("pet parent account %s claimed by sign-in", account.id)
    return account


ParentDep = Annotated[ParentIdentity, Depends(current_parent)]


async def require_patient(
    patient_id: uuid.UUID,
    user: ClinicUser,
    session: AsyncSession,
) -> Patient:
    """Foreign records are indistinguishable from missing ones: always 404."""
    patient = await session.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.primary_clinic_id == user.clinic_id,
        )
    )
    if patient is None:
        raise NotFoundError("Patient not found")
    return patient


def require_permission(action: Action):
    async def guard(user: CurrentUser) -> ClinicUser:
        if not can(user.role, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role cannot perform this action",
            )
        return user

    return guard
