import uuid

from pydantic import BaseModel, Field, field_validator

PHONE_PATTERN = r"^\+[1-9]\d{9,14}$"


class InviteCheckIn(BaseModel):
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def normalise(cls, value: str) -> str:
        email = value.strip().lower()
        local, _, domain = email.partition("@")
        if not local or "." not in domain:
            raise ValueError("Enter a valid email address")
        return email


class InviteCheckOut(BaseModel):
    """Whether an address may create an account, and which door it opens."""

    invited: bool
    kind: str | None = None


class ParentSignupIn(BaseModel):
    """What a pet parent gives to open their own portal (spec 2.1: name, phone, email)."""

    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(pattern=PHONE_PATTERN)

    @field_validator("full_name")
    @classmethod
    def tidy_name(cls, value: str) -> str:
        name = " ".join(value.split())
        if len(name) < 2:
            raise ValueError("Enter your full name")
        return name


class ParentSignupOut(BaseModel):
    parent_id: uuid.UUID
    email: str
    created: bool
