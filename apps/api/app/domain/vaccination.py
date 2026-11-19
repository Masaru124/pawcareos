import calendar
import enum
from datetime import date


class VaccineKind(enum.StrEnum):
    RABIES = "rabies"
    DHPPIL = "dhppil"
    DEWORMING = "deworming"
    TRICAT = "tricat"
    KENNEL_COUGH = "kennel_cough"


VACCINE_SCHEDULE_MONTHS: dict[VaccineKind, int] = {
    VaccineKind.RABIES: 12,
    VaccineKind.DHPPIL: 12,
    VaccineKind.DEWORMING: 3,
    VaccineKind.TRICAT: 12,
    VaccineKind.KENNEL_COUGH: 12,
}


def next_due_date(
    kind: VaccineKind,
    administered_on: date,
    *,
    months: int | None = None,
) -> date:
    """Add calendar months, clamping the day to the target month's length."""
    if not isinstance(administered_on, date):
        raise TypeError("invalid date")
    span = VACCINE_SCHEDULE_MONTHS[kind] if months is None else months
    year = administered_on.year + (administered_on.month - 1 + span) // 12
    month = (administered_on.month - 1 + span) % 12 + 1
    day = min(administered_on.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
