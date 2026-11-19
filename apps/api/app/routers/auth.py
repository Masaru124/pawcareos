from fastapi import APIRouter
from sqlalchemy import func, select

from app.deps import CurrentUser, SessionDep
from app.models import ClinicUser, PetParentAccount
from app.schemas.auth import InviteCheckIn, InviteCheckOut
from app.schemas.user import MeOut

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
