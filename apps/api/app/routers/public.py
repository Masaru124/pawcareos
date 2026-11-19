from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Response

from app.deps import NotFoundError, SessionDep
from app.schemas.passport import PassportView
from app.services.passport_view import build_passport_view
from app.services.pdf import render_certificate_pdf

router = APIRouter(prefix="/p", tags=["public"])


@router.get("/{slug}", response_model=PassportView)
async def get_passport(slug: str, session: SessionDep) -> PassportView:
    view = await build_passport_view(session, slug=slug)
    if view is None:
        raise NotFoundError("Passport not found")
    return view


@router.get("/{slug}/certificate.pdf")
async def get_certificate(slug: str, session: SessionDep) -> Response:
    view = await build_passport_view(session, slug=slug)
    if view is None:
        raise NotFoundError("Passport not found")
    issued_on = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y")
    return Response(
        content=render_certificate_pdf(view, issued_on=issued_on),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{slug}-certificate.pdf"'},
    )
