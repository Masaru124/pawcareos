from datetime import date

import pytest

from app.domain.passport import is_valid_passport_slug, make_passport_slug
from app.domain.rx_code import make_rx_code
from app.domain.vaccination import VaccineKind, next_due_date


@pytest.mark.parametrize(
    ("kind", "administered", "expected"),
    [
        (VaccineKind.RABIES, date(2026, 1, 1), date(2027, 1, 1)),
        (VaccineKind.DEWORMING, date(2026, 1, 1), date(2026, 4, 1)),
        (VaccineKind.DEWORMING, date(2026, 11, 1), date(2027, 2, 1)),
        (VaccineKind.RABIES, date(2026, 2, 29 - 1), date(2027, 2, 28)),
        (VaccineKind.DHPPIL, date(2027, 12, 31), date(2028, 12, 31)),
    ],
)
def test_next_due_date(kind: VaccineKind, administered: date, expected: date) -> None:
    assert next_due_date(kind, administered) == expected


def test_explicit_months_override_the_default_schedule() -> None:
    assert next_due_date(VaccineKind.RABIES, date(2026, 1, 31), months=1) == date(2026, 2, 28)


def test_passport_slugs_are_ten_characters_and_unambiguous() -> None:
    slugs = {make_passport_slug() for _ in range(200)}
    assert len(slugs) == 200
    assert all(is_valid_passport_slug(slug) for slug in slugs)
    assert not any(character in "01lo" for slug in slugs for character in slug)


def test_rx_code_is_human_readable_and_zero_padded() -> None:
    assert make_rx_code("Bengaluru", 2026, 7) == "RX-BEN-2026-0007"
    assert make_rx_code("", 2026, 1) == "RX-IND-2026-0001"
