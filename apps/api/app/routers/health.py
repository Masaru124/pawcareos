import subprocess
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session

router = APIRouter(tags=["ops"])


def _version() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


@router.get("/health")
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        db = "ok"
    except (SQLAlchemyError, OSError, TimeoutError):
        db = "unreachable"
    return {"status": "ok", "db": db, "version": _version()}
