from pydantic import BaseModel


class BadgeOut(BaseModel):
    label: str
    valid_until: str
    state: str
    doctor_name: str


class PetOut(BaseModel):
    name: str
    species: str
    breed: str | None
    age_label: str
    sex_label: str
    microchip_masked: str | None
    passport_slug: str


class PrescriptionRefOut(BaseModel):
    date: str
    doctor_name: str
    rx_code: str


class ClinicRefOut(BaseModel):
    name: str
    address: str
    phone: str


class PassportView(BaseModel):
    pet: PetOut
    status: str
    badges: list[BadgeOut]
    prescriptions: list[PrescriptionRefOut]
    clinic: ClinicRefOut
