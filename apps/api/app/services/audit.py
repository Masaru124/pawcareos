import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def record_audit(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    clinic_id: uuid.UUID,
    action: str,
    subject_type: str,
    subject_id: uuid.UUID | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_id=actor_id,
            clinic_id=clinic_id,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
        )
    )
