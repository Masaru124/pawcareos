import secrets

ALPHABET = "abcdefghijkmnpqrstuvwxyz234567"
SLUG_LENGTH = 10


def make_passport_slug() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(SLUG_LENGTH))


def is_valid_passport_slug(value: str) -> bool:
    return len(value) == SLUG_LENGTH and all(character in ALPHABET for character in value)
