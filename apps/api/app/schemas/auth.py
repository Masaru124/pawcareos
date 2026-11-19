from pydantic import BaseModel, Field, field_validator


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
