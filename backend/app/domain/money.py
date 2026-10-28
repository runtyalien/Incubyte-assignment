"""Salaries are integers in the currency's minor unit. See docs/adr/0002."""

from decimal import ROUND_HALF_UP, Decimal

BASE_CURRENCY = "USD"

MICROS = Decimal(1_000_000)

# ISO 4217 minor unit exponents. Two is common but not universal, and getting
# this wrong on JPY is a factor of a hundred.
MINOR_UNITS = {
    "USD": 2,
    "GBP": 2,
    "EUR": 2,
    "INR": 2,
    "SGD": 2,
    "BRL": 2,
    "JPY": 0,
}


class UnknownCurrency(ValueError):
    def __init__(self, currency: str):
        super().__init__(f"No minor unit known for {currency!r}")
        self.currency = currency


def exponent(currency: str) -> int:
    try:
        return MINOR_UNITS[currency]
    except KeyError:
        raise UnknownCurrency(currency) from None


def to_minor(amount: Decimal | int | str, currency: str) -> int:
    scale = Decimal(10) ** exponent(currency)
    return int((Decimal(amount) * scale).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def to_major(minor: int, currency: str) -> Decimal:
    places = exponent(currency)
    return (Decimal(minor) / Decimal(10) ** places).quantize(Decimal(1).scaleb(-places))


def to_base(minor: int, currency: str, rate_micros: int) -> int:
    """Convert a local amount into the base currency at a given rate.

    Goes through Decimal rather than multiplying the minor units directly,
    because the two currencies can have different exponents.
    """
    if currency == BASE_CURRENCY:
        return minor

    local = to_major(minor, currency)
    return to_minor(local * Decimal(rate_micros) / MICROS, BASE_CURRENCY)


def rate_to_micros(rate: Decimal | str) -> int:
    return int((Decimal(rate) * MICROS).quantize(Decimal(1), rounding=ROUND_HALF_UP))
