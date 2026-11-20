import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, SessionDep, VerifiedDep
from app.models import ClinicUser, PetParent, PetParentAccount
from app.schemas.auth import InviteCheckIn, InviteCheckOut, ParentSignupIn, ParentSignupOut
from app.schemas.user import MeOut

logger = logging.getLogger("pawcare.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUser) -> MeOut:
    return MeOut.model_validate(user)


@router.post("/invitation", response_model=InviteCheckOut)
async def invitation(payload: InviteCheckIn, session: SessionDep) -> InviteCheckOut:
    """Strict sign-up gate: only an address a clinic invited may create an account.

    Sign-in stays password-first. This answers one bit about an address (is it on a
    clinic's list, and is that list staff or a family) and never a name, role or pet.
    """
    staff = await session.scalar(
        select(ClinicUser.id)
        .where(
            func.lower(ClinicUser.email) == payload.email,
            ClinicUser.is_active.is_(True),
        )
        .limit(1)
    )
    if staff is not None:
        return InviteCheckOut(invited=True, kind="clinic")

    parent = await session.scalar(
        select(PetParentAccount.id)
        .where(
            func.lower(PetParentAccount.email) == payload.email,
            PetParentAccount.is_active.is_(True),
        )
        .limit(1)
    )
    if parent is not None:
        return InviteCheckOut(invited=True, kind="parent")

    return InviteCheckOut(invited=False)


@router.post("/parent", response_model=ParentSignupOut)
async def parent_signup(
    payload: ParentSignupIn, identity: VerifiedDep, session: SessionDep
) -> ParentSignupOut:
    """Open a pet-parent portal from a verified address (spec 2.1: self-serve signup).

    Idempotent: a returning parent gets their row back. A phone number the clinic
    already knows attaches to that family instead of creating a second one, which is
    how a self-registered parent's records appear once the clinic adds their pet.
    """
    email = (identity.email or "").strip().lower()
    if not email:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Your sign-in has no email address on it"
        )

    account = await session.scalar(
        select(PetParentAccount).where(PetParentAccount.auth_user_id == identity.auth_user_id)
    )
    if account is not None:
        return ParentSignupOut(parent_id=account.pet_parent_id, email=account.email, created=False)

    # A clinic may already have invited this address to a family's portal.
    account = await session.scalar(
        select(PetParentAccount).where(
            func.lower(PetParentAccount.email) == email,
            PetParentAccount.auth_user_id.is_(None),
        )
    )
    if account is not None:
        account.auth_user_id = identity.auth_user_id
        await session.flush()
        logger.info("parent account %s claimed by self-signup", account.id)
        return ParentSignupOut(parent_id=account.pet_parent_id, email=account.email, created=False)

    parent = await session.scalar(select(PetParent).where(PetParent.phone == payload.phone))
    created = False
    if parent is None:
        parent = await session.scalar(
            select(PetParent).where(func.lower(PetParent.email) == email)
        )
    if parent is None:
        parent = PetParent(full_name=payload.full_name, phone=payload.phone, email=email)
        session.add(parent)
        await session.flush()
        created = True
    elif parent.email is None:
        parent.email = email

    existing = await session.scalar(
        select(PetParentAccount).where(PetParentAccount.pet_parent_id == parent.id)
    )
    if existing is not None:
        if existing.auth_user_id is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "That phone number already belongs to a family with its own login",
            )
        existing.auth_user_id = identity.auth_user_id
        await session.flush()
        return ParentSignupOut(parent_id=parent.id, email=existing.email, created=False)

    account = PetParentAccount(
        pet_parent_id=parent.id, email=email, auth_user_id=identity.auth_user_id
    )
    session.add(account)
    await session.flush()
    logger.info("self-serve parent %s registered", parent.id)
    return ParentSignupOut(parent_id=parent.id, email=account.email, created=created)
