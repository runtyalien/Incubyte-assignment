from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.money import BASE_CURRENCY, MICROS
from app.models import FxRate

PAR = int(MICROS)


class NoRateAvailable(LookupError):
    def __init__(self, currency: str, when: date):
        super().__init__(f"No {currency} rate in force on {when}")
        self.currency = currency
        self.when = when


def rate_on(session: Session, currency: str, when: date) -> int:
    """The rate in force on a date, in micros.

    Rates are stepwise: a row holds until a later one supersedes it, so this
    takes the most recent row dated on or before the day in question. A date
    before the series starts has no answer and raises rather than reaching for
    the oldest rate, because silently pricing a salary at a rate that was not
    in force is the kind of wrong that never gets noticed.
    """
    if currency == BASE_CURRENCY:
        return PAR

    rate = session.scalar(
        select(FxRate.rate_micros)
        .where(FxRate.currency == currency, FxRate.effective_from <= when)
        .order_by(FxRate.effective_from.desc())
        .limit(1)
    )

    if rate is None:
        raise NoRateAvailable(currency, when)

    return rate
