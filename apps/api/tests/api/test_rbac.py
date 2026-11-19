from app.models.enums import UserRole
from app.rbac import Action, can


def test_receptionist_can_bill_but_cannot_prescribe():
    assert can(UserRole.RECEPTIONIST, Action.BILLING_WRITE) is True
    assert can(UserRole.RECEPTIONIST, Action.RX_SEND) is False
    assert can(UserRole.RECEPTIONIST, Action.CONSULT_WRITE) is False


def test_doctor_can_prescribe_but_cannot_manage_the_clinic():
    assert can(UserRole.DOCTOR, Action.RX_SEND) is True
    assert can(UserRole.DOCTOR, Action.CONSULT_WRITE) is True
    assert can(UserRole.DOCTOR, Action.CLINIC_MANAGE) is False


def test_owner_can_do_everything():
    assert all(can(UserRole.OWNER, action) for action in Action)
