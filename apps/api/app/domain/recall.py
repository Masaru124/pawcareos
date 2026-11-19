import uuid
from datetime import date, timedelta

from app.models.enums import RecallTrigger

QUICK_REPLY_TITLES: tuple[str, ...] = ("Confirm Sat 11am", "Reschedule", "Stop reminders")

BUTTON_PREFIXES = {"confirm": "cnf", "reschedule": "rsc", "optout": "opt"}


def recall_triggers_for(due_on: date, today: date) -> list[RecallTrigger]:
    offset = (due_on - today).days
    if offset == 7:
        return [RecallTrigger.T7]
    if offset == 2:
        return [RecallTrigger.T2]
    if offset < 0:
        return [RecallTrigger.OVERDUE]
    return []


def dispatch_time_for(due_on: date) -> date:
    return due_on - timedelta(days=7)


def encode_button_id(kind: str, recall_job_id: uuid.UUID) -> str:
    prefix = BUTTON_PREFIXES[kind]
    return f"{prefix}:{recall_job_id}"


def decode_button_id(value: str) -> tuple[str, uuid.UUID] | None:
    if ":" not in value:
        return None
    prefix, _, raw = value.partition(":")
    kinds = {code: name for name, code in BUTTON_PREFIXES.items()}
    kind = kinds.get(prefix)
    if kind is None:
        return None
    try:
        return kind, uuid.UUID(raw)
    except ValueError:
        return None
