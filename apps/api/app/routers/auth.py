from fastapi import APIRouter

from app.deps import CurrentUser
from app.schemas.user import MeOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUser) -> MeOut:
    return MeOut.model_validate(user)
