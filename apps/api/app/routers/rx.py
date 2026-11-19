from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.deps import CurrentUser, SessionDep, require_permission
from app.rbac import Action
from app.services.pdf import build_prescription_document, render_prescription_pdf

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.get("/{rx_code}/pdf")
async def prescription_pdf(
    rx_code: str,
    session: SessionDep,
    user: Annotated[CurrentUser, Depends(require_permission(Action.PATIENT_READ))],
) -> Response:
    document = await build_prescription_document(
        session, rx_code=rx_code, clinic_id=user.clinic_id
    )
    if document is None:
        from app.deps import NotFoundError

        raise NotFoundError("Prescription not found")
    pdf_bytes = render_prescription_pdf(document)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{rx_code}.pdf"'},
    )
