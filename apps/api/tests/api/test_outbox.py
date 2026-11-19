import uuid

from app.models import MessageOutbox
from app.models.enums import OutboxKind, OutboxStatus
from app.services.outbox import MAX_ATTEMPTS, drain_outbox
from app.services.whatsapp import SendError


class FakeSender:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[str] = []

    async def send(self, message: MessageOutbox) -> str:
        if self.fail:
            raise SendError("provider down")
        self.sent.append(message.idempotency_key)
        return f"fake.{len(self.sent)}"


async def make_message(session, clinic_id, *, key: str | None = None) -> MessageOutbox:
    message = MessageOutbox(
        clinic_id=clinic_id,
        correlation_id=str(uuid.uuid4()),
        kind=OutboxKind.RX_DELIVERY,
        to_phone="+919900011122",
        template_name="rx_delivery_v1",
        template_version=1,
        payload={"rx_code": "RX-BLR-2026-0001"},
        idempotency_key=key or str(uuid.uuid4()),
    )
    session.add(message)
    await session.flush()
    return message


async def test_a_queued_message_is_sent_exactly_once(session, seeded):
    message = await make_message(session, seeded.clinic_a.id)
    sender = FakeSender()

    first = await drain_outbox(session, sender=sender)
    second = await drain_outbox(session, sender=sender)

    assert first.sent == 1
    assert second.sent == 0
    await session.refresh(message)
    assert message.status is OutboxStatus.SENT
    assert message.provider_message_id


async def test_a_failure_backs_off_instead_of_losing_the_message(session, seeded):
    message = await make_message(session, seeded.clinic_a.id)
    result = await drain_outbox(session, sender=FakeSender(fail=True))

    assert result.failed == 1
    await session.refresh(message)
    assert message.status is OutboxStatus.QUEUED
    assert message.attempts == 1
    assert message.last_error == "provider down"


async def test_a_message_dies_after_the_attempt_ceiling(session, seeded):
    message = await make_message(session, seeded.clinic_a.id)
    message.attempts = MAX_ATTEMPTS - 1
    await session.flush()

    result = await drain_outbox(session, sender=FakeSender(fail=True))

    assert result.dead == 1
    await session.refresh(message)
    assert message.status is OutboxStatus.DEAD


async def test_the_same_idempotency_key_is_never_queued_twice(session, seeded):
    from app.services.outbox import enqueue

    key = "rx:duplicate-test"
    first = await make_message(session, seeded.clinic_a.id, key=key)
    duplicate = MessageOutbox(
        clinic_id=seeded.clinic_a.id,
        correlation_id=str(uuid.uuid4()),
        kind=OutboxKind.RX_DELIVERY,
        to_phone="+919900011122",
        template_name="rx_delivery_v1",
        template_version=1,
        payload={},
        idempotency_key=key,
    )
    assert await enqueue(session, duplicate) is False

    from sqlalchemy import func, select

    count = await session.scalar(
        select(func.count()).select_from(MessageOutbox).where(MessageOutbox.idempotency_key == key)
    )
    assert count == 1
    assert first.idempotency_key == key
