def make_rx_code(city: str, year: int, seq: int) -> str:
    letters = "".join(character for character in city.upper() if character.isalpha())
    code = letters[:3] or "IND"
    return f"RX-{code}-{year}-{seq:04d}"
