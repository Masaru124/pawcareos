import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.deps import CurrentUser, SessionDep, require_patient, require_permission
from app.rbac import Action
from app.schemas.intake import IntakeIn, IntakeOut, PatientListOut
from app.schemas.patient import PatientOut
from app.services.patients import create_intake, search_patients

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=IntakeOut, status_code=201)
async def intake(
    payload: IntakeIn,
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.PATIENT_WRITE))],
) -> IntakeOut:
    return await create_intake(
        session, clinic_id=user.clinic_id, actor_id=user.id, payload=payload
    )


@router.get("", response_model=PatientListOut)
async def search(
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.PATIENT_READ))],
    q: Annotated[str | None, Query(min_length=2, max_length=60)] = None,
) -> PatientListOut:
    # The directory opens with no query; a query narrows it.
    items = await search_patients(session, clinic_id=user.clinic_id, query=q, limit=20 if q else 50)
    return PatientListOut(items=items)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(require_permission(Action.PATIENT_READ))],
    session: SessionDep,
) -> PatientOut:
    patient = await require_patient(patient_id, user, session)
    return PatientOut.model_validate(patient)
