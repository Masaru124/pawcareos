import enum

from app.models.enums import UserRole


class Action(enum.StrEnum):
    PATIENT_READ = "patient:read"
    PATIENT_WRITE = "patient:write"
    CONSULT_WRITE = "consult:write"
    RX_SEND = "rx:send"
    BILLING_WRITE = "billing:write"
    CLINIC_MANAGE = "clinic:manage"
    REPORT_READ = "report:read"


PERMISSIONS: dict[UserRole, frozenset[Action]] = {
    UserRole.OWNER: frozenset(Action),
    UserRole.DOCTOR: frozenset(
        {
            Action.PATIENT_READ,
            Action.PATIENT_WRITE,
            Action.CONSULT_WRITE,
            Action.RX_SEND,
            Action.REPORT_READ,
        }
    ),
    UserRole.RECEPTIONIST: frozenset(
        {
            Action.PATIENT_READ,
            Action.PATIENT_WRITE,
            Action.BILLING_WRITE,
            Action.REPORT_READ,
        }
    ),
}


def can(role: UserRole, action: Action) -> bool:
    return action in PERMISSIONS.get(role, frozenset())
