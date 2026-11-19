import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    DOCTOR = "doctor"
    RECEPTIONIST = "receptionist"


class ConsultStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_CONSULT = "in_consult"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VaccineStatus(str, enum.Enum):
    ADMINISTERED = "administered"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class RecallTrigger(str, enum.Enum):
    T7 = "T-7"
    T2 = "T-2"
    OVERDUE = "OVERDUE"


class RecallStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    RESPONDED = "responded"
    SUPPRESSED = "suppressed"


class ResponseAction(str, enum.Enum):
    BOOKED = "booked"
    POSTPONED = "postponed"
    OPTED_OUT = "opted_out"


class AppointmentStatus(str, enum.Enum):
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppointmentSource(str, enum.Enum):
    RECALL = "recall"
    WALK_IN = "walk_in"
    PHONE = "phone"
    WEB = "web"


class ConsultMode(str, enum.Enum):
    IN_CLINIC = "in_clinic"
    ONLINE = "online"


class ConsentChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"


class ConsentSource(str, enum.Enum):
    INTAKE_TAP = "intake_tap"
    RECEPTIONIST_SCRIPT = "receptionist_script"
    WHATSAPP_REPLY = "whatsapp_reply"
    WEB_FORM = "web_form"


class OutboxKind(str, enum.Enum):
    RX_DELIVERY = "rx_delivery"
    RECALL = "recall"
    CONFIRMATION = "confirmation"
    CERTIFICATE = "certificate"
    APPOINTMENT_REMINDER = "appointment_reminder"


class OutboxStatus(str, enum.Enum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    DEAD = "dead"
