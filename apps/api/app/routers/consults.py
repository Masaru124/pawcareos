from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.deps import CurrentUser, SessionDep, require_permission
from app.rbac import Action
from app.schemas.consult import ConsultIn, ConsultOut
from app.services.consult import complete_consult

router = APIRouter(prefix="/consults", tags=["consults"])


@router.post("", response_model=ConsultOut, status_code=201)
async def create_consult(
    payload: ConsultIn,
    session: SessionDep,
    user: Annotated[
        CurrentUser, Depends(require_permission(Action.CONSULT_WRITE))
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
) -> ConsultOut:
    return await complete_consult(
        session, user=user, payload=payload, idempotency_key=idempotency_key
    )
