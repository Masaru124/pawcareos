from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MessageOutbox
from app.models.enums import OutboxStatus
from app.services.whatsapp import SendError, get_default_sender

BACKOFF_SECONDS = (60, 300, 900, 3600, 21600)
MAX_ATTEMPTS = 5


class Sender(Protocol):
    async def send(self, message: MessageOutbox) -> str: ...


@dataclass(frozen=True)
class DrainResult:
    sent: int
    failed: int
    dead: int


def backoff_seconds(attempt: int) -> int:
    index = min(max(attempt, 1), len(BACKOFF_SECONDS)) - 1
    return BACKOFF_SECONDS[index]


async def enqueue(session: AsyncSession, message: MessageOutbox) -> bool:
    """False when the idempotency key already exists: a duplicate, not an error."""
    existing = await session.scalar(
        select(MessageOutbox.id).where(
            MessageOutbox.idempotency_key == message.idempotency_key
        )
    )
    if existing is not None:
        return False
    try:
        async with session.begin_nested():
            session.add(message)
            await session.flush()
    except IntegrityError:
        # Lost a race with another worker: drop the failed object, keep the caller clean.
        if message in session:
            session.expunge(message)
        return False
    return True


async def drain_outbox(
    session: AsyncSession,
    *,
    limit: int = 50,
    sender: Sender | None = None,
) -> DrainResult:
    active_sender = sender or get_default_sender()
    now = datetime.now(UTC)

    rows = (
        await session.execute(
            select(MessageOutbox)
            .where(
                MessageOutbox.status == OutboxStatus.QUEUED,
                MessageOutbox.next_attempt_at <= now,
            )
            .order_by(MessageOutbox.next_attempt_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    ).scalars().all()

    for row in rows:
        row.status = OutboxStatus.SENDING
    await session.flush()
    await session.commit()

    sent = failed = dead = 0
    for row in rows:
        try:
            provider_message_id = await active_sender.send(row)
        except SendError as exc:
            row.attempts += 1
            row.last_error = str(exc)[:500]
            if row.attempts >= MAX_ATTEMPTS:
                row.status = OutboxStatus.DEAD
                dead += 1
            else:
                row.status = OutboxStatus.QUEUED
                row.next_attempt_at = datetime.now(UTC) + timedelta(
                    seconds=backoff_seconds(row.attempts)
                )
                failed += 1
        else:
            row.status = OutboxStatus.SENT
            row.provider_message_id = provider_message_id
            row.sent_at = datetime.now(UTC)
            sent += 1

    await session.commit()
    return DrainResult(sent=sent, failed=failed, dead=dead)
