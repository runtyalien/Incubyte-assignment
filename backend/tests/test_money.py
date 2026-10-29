from decimal import Decimal

import pytest

from app.domain.money import (
    UnknownCurrency,
    exponent,
    has_valid_precision,
    rate_to_micros,
    to_base,
    to_major,
    to_minor,
)


def test_major_to_minor_for_a_two_decimal_currency():
    assert to_minor("1234.56", "USD") == 123_456


def test_yen_has_no_minor_unit():
    # The trap this guards: assuming two decimals everywhere is off by 100x.
    assert exponent("JPY") == 0
    assert to_minor("1234", "JPY") == 1234


def test_round_trip_preserves_the_amount():
    assert to_major(to_minor("98765.43", "GBP"), "GBP") == Decimal("98765.43")


def test_fractional_minor_units_round_half_up():
    assert to_minor("0.005", "USD") == 1
    assert to_minor("0.004", "USD") == 0


def test_base_currency_converts_to_itself_untouched():
    assert to_base(10_000_000, "USD", rate_to_micros("1.0")) == 10_000_000


def test_conversion_applies_the_rate():
    # 80,000 GBP at 1.27 is 101,600 USD.
    assert to_base(to_minor("80000", "GBP"), "GBP", rate_to_micros("1.27")) == 10_160_000


def test_conversion_between_different_exponents():
    # 5,000,000 JPY (no minor unit) at 0.0067 is 33,500 USD (two decimals).
    converted = to_base(to_minor("5000000", "JPY"), "JPY", rate_to_micros("0.0067"))

    assert converted == to_minor("33500", "USD")


def test_unknown_currency_is_rejected_rather_than_guessed():
    with pytest.raises(UnknownCurrency):
        to_minor("100", "XYZ")


def test_an_amount_that_fits_the_minor_unit_is_exact():
    assert has_valid_precision("1234.56", "USD")


def test_a_third_decimal_does_not_fit_a_cent():
    # to_minor would answer 123457 here, which is a different salary.
    assert not has_valid_precision("1234.567", "USD")


def test_trailing_zeros_are_not_extra_precision():
    assert has_valid_precision("1234.5600", "USD")


def test_a_whole_number_always_fits():
    assert has_valid_precision("1234", "USD")


def test_yen_has_nowhere_to_put_a_fraction():
    # Two decimals are fine in USD and meaningless in JPY, which is the whole
    # reason this is a per-currency question rather than a fixed two places.
    assert has_valid_precision("1234.50", "USD")
    assert not has_valid_precision("1234.50", "JPY")
    assert has_valid_precision("1234", "JPY")


def test_a_half_minor_unit_is_rejected_rather_than_rounded():
    # Exactly the midpoint, where ROUND_HALF_UP is at its most confident.
    assert not has_valid_precision("0.005", "USD")
