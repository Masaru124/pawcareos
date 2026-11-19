from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.config import get_settings
from app.deps import SessionDep, SettingsDep
from app.models import MessageOutbox, RecallJob
from app.services.inbound import handle_button_reply
from app.services.outbox import DrainResult, drain_outbox
from app.services.recall import generate_recall_jobs
from app.services.whatsapp import demo_sender

router = APIRouter(prefix="/ops", tags=["ops"])


def require_cron_secret(
    settings: SettingsDep,
    x_cron_secret: Annotated[str | None, Header(alias="X-Cron-Secret")] = None,
) -> None:
    if x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad cron secret")


Cron = Annotated[None, Depends(require_cron_secret)]


class RecallRunOut(BaseModel):
    created: int
    enqueued: int
    suppressed: int


@router.post("/recalls/run", response_model=RecallRunOut)
async def run_recalls(session: SessionDep, _: Cron) -> RecallRunOut:
    result = await generate_recall_jobs(session)
    return RecallRunOut(created=result.created, enqueued=result.enqueued, suppressed=result.suppressed)


@router.post("/outbox/drain")
async def run_drain(session: SessionDep, _: Cron) -> DrainResult:
    return await drain_outbox(session)


@router.get("/outbox")
async def list_outbox(session: SessionDep, _: Cron) -> list[dict]:
    rows = (
        await session.execute(
            select(MessageOutbox).order_by(MessageOutbox.created_at.desc()).limit(25)
        )
    ).scalars().all()
    return [
        {
            "idempotency_key": row.idempotency_key,
            "kind": row.kind.value,
            "template": row.template_name,
            "to": f"***{row.to_phone[-4:]}",
            "status": row.status.value,
            "attempts": row.attempts,
            "provider_message_id": row.provider_message_id,
        }
        for row in rows
    ]


@router.get("/demo-sends")
async def list_demo_sends(_: Cron) -> list[dict]:
    """What the demo sender would have delivered. Empty in live mode."""
    return demo_sender().sent


class SimulateTapIn(BaseModel):
    recall_job_id: UUID
    action: str = "confirm"


@router.post("/simulate-tap")
async def simulate_tap(payload: SimulateTapIn, session: SessionDep, _: Cron) -> dict:
    """Demo only: stand in for a WhatsApp button tap without Meta credentials."""
    if get_settings().whatsapp_mode == "live":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo taps are disabled when WHATSAPP_MODE=live",
        )
    job = await session.get(RecallJob, payload.recall_job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recall job not found")

    from app.domain.recall import encode_button_id

    handled = await handle_button_reply(
        session,
        provider_message_id=f"demo-{payload.recall_job_id}-{payload.action}",
        from_phone=None,
        button_id=encode_button_id(payload.action, job.id),
    )
    return {"handled": handled, "action": payload.action}
