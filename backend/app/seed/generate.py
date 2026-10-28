from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from random import Random

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.domain.money import rate_to_micros, to_base, to_minor
from app.models import (
    CompensationRecord,
    Department,
    Employee,
    FxRate,
    JobFamily,
    JobLevel,
    Location,
    PayChangeReason,
    SalaryBand,
)
from app.seed import shape
from app.seed.names import FIRST_NAMES, LAST_NAMES

CHUNK = 5_000

# Rejection sampling needs a way out if the bounds are ever tuned to something
# the distribution cannot reach. At the current spread this gives up with a
# probability too small to write down.
MAX_DRAWS = 100


@dataclass
class Summary:
    employees: int
    compensation_records: int
    bands: int
    fx_rates: int

    def __str__(self) -> str:
        return (
            f"{self.employees:,} employees, "
            f"{self.compensation_records:,} compensation records, "
            f"{self.bands:,} bands, {self.fx_rates:,} FX rates"
        )


class RateBook:
    """Quarterly rates per currency, with a lookup for the one in force on a
    given day. Built once and held in memory — doing this per compensation
    record would be tens of thousands of queries."""

    def __init__(self, rows: list[dict]):
        self._by_currency: dict[str, tuple[list[date], list[int]]] = {}
        for row in sorted(rows, key=lambda r: r["effective_from"]):
            dates, rates = self._by_currency.setdefault(row["currency"], ([], []))
            dates.append(row["effective_from"])
            rates.append(row["rate_micros"])

    def __len__(self) -> int:
        return sum(len(dates) for dates, _ in self._by_currency.values())

    def on(self, currency: str, when: date) -> int:
        dates, rates = self._by_currency[currency]
        position = bisect_right(dates, when)
        # Anything dated before the series starts uses the opening rate.
        return rates[max(position - 1, 0)]


def build(session: Session, headcount: int, rng_seed: int, today: date | None = None) -> Summary:
    rng = Random(rng_seed)
    today = today or date.today()

    locations = _insert_locations(session)
    departments = _insert_departments(session)
    families = _insert_families(session)
    levels = _insert_levels(session)

    rates = _insert_fx(session, rng, today)
    bands = _insert_bands(session, locations, families, levels, rates, today)

    employees, records = _insert_people(
        session, rng, today, headcount, locations, departments, families, levels, bands, rates
    )

    session.commit()
    return Summary(employees, records, len(bands), len(rates))


def _insert_locations(session: Session) -> dict[str, dict]:
    rows = [
        {"id": i, "country_code": code, "name": name, "currency": currency}
        for i, (code, name, currency, _factor, _weight) in enumerate(shape.LOCATIONS, start=1)
    ]
    session.execute(insert(Location), rows)
    return {row["country_code"]: row for row in rows}


def _insert_departments(session: Session) -> dict[str, dict]:
    rows = [
        {"id": i, "name": name}
        for i, (name, _weight, _families) in enumerate(shape.DEPARTMENTS, start=1)
    ]
    session.execute(insert(Department), rows)
    return {row["name"]: row for row in rows}


def _insert_families(session: Session) -> dict[str, dict]:
    rows = [
        {"id": i, "name": name} for i, (name, _factor) in enumerate(shape.JOB_FAMILIES, start=1)
    ]
    session.execute(insert(JobFamily), rows)
    return {row["name"]: row for row in rows}


def _insert_levels(session: Session) -> dict[str, dict]:
    rows = [
        {"id": i, "code": code, "rank": rank}
        for i, (code, rank, _mid, _weight) in enumerate(shape.LEVELS, start=1)
    ]
    session.execute(insert(JobLevel), rows)
    return {row["code"]: row for row in rows}


def _insert_fx(session: Session, rng: Random, today: date) -> RateBook:
    start = date(today.year - shape.HISTORY_YEARS - 1, 1, 1)
    quarters = []
    cursor = start
    while cursor <= today:
        quarters.append(cursor)
        month = cursor.month + 3
        year = cursor.year + (month - 1) // 12
        cursor = date(year, (month - 1) % 12 + 1, 1)

    rows = []
    next_id = 1
    for currency, opening in shape.FX_START.items():
        rate = Decimal(opening)
        for when in quarters:
            if currency != shape.BASE_CURRENCY:
                drift = Decimal(str(rng.uniform(-1, 1))) * Decimal(str(shape.FX_QUARTERLY_DRIFT))
                rate = rate * (1 + drift)
            rows.append(
                {
                    "id": next_id,
                    "currency": currency,
                    "effective_from": when,
                    "rate_micros": rate_to_micros(rate),
                }
            )
            next_id += 1

    session.execute(insert(FxRate), rows)
    return RateBook(rows)


def _insert_bands(
    session: Session,
    locations: dict[str, dict],
    families: dict[str, dict],
    levels: dict[str, dict],
    rates: RateBook,
    today: date,
) -> dict[tuple[int, int, int], dict]:
    """A band per location, family and level.

    Midpoints are set in dollars, scaled by how the market pays relative to the
    US, then expressed in local currency at the current rate. Bands are not
    effective-dated: in reality they are re-benchmarked annually, and that is a
    deliberate simplification.
    """
    rows = []
    next_id = 1

    for code, _name, currency, market, _weight in shape.LOCATIONS:
        location = locations[code]
        rate = Decimal(rates.on(currency, today)) / Decimal(1_000_000)

        for family_name, family_factor in shape.JOB_FAMILIES:
            family = families[family_name]

            for level_code, _rank, usd_mid, _weight in shape.LEVELS:
                level = levels[level_code]

                mid_usd = Decimal(usd_mid) * Decimal(str(family_factor)) * Decimal(str(market))
                mid_local = mid_usd / rate
                low = mid_local * Decimal(str(shape.BAND_MIN_FACTOR))
                high = mid_local * Decimal(str(shape.BAND_MAX_FACTOR))

                rows.append(
                    {
                        "id": next_id,
                        "location_id": location["id"],
                        "job_family_id": family["id"],
                        "job_level_id": level["id"],
                        "currency": currency,
                        "min_minor": to_minor(low, currency),
                        "mid_minor": to_minor(mid_local, currency),
                        "max_minor": to_minor(high, currency),
                    }
                )
                next_id += 1

    session.execute(insert(SalaryBand), rows)
    return {(r["location_id"], r["job_family_id"], r["job_level_id"]): r for r in rows}


PayEvent = tuple[date, PayChangeReason, float]


def _pay_events(rng: Random, hired_on: date, until: date) -> list[PayEvent]:
    """Every change after the hire record: the annual merit cycle, plus the
    promotions and market corrections that land off-cycle."""
    events: list[PayEvent] = []
    eligible_from = hired_on + timedelta(days=180)

    for year in range(hired_on.year, until.year + 1):
        merit = date(year, shape.MERIT_MONTH, shape.MERIT_DAY)
        if merit > until or merit < eligible_from:
            continue

        events.append((merit, PayChangeReason.MERIT, rng.uniform(*shape.MERIT_RAISE)))

        if rng.random() < shape.PROMOTION_CHANCE_PER_YEAR:
            when = merit + timedelta(days=rng.randint(60, 300))
            if when <= until:
                events.append(
                    (when, PayChangeReason.PROMOTION, rng.uniform(*shape.PROMOTION_RAISE))
                )

        if rng.random() < shape.MARKET_CHANCE_PER_YEAR:
            when = merit + timedelta(days=rng.randint(30, 330))
            if when <= until:
                events.append(
                    (when, PayChangeReason.MARKET_ADJUSTMENT, rng.uniform(*shape.MARKET_RAISE))
                )

    events.sort(key=lambda event: event[0])
    return events


def _compa_ratio(rng: Random) -> float:
    """Where in their band someone sits, drawn again until it lands in range.

    Clamping the tails to the bounds instead would stack everyone who overshot
    onto the two edges — at this spread about one person in two hundred, all
    reporting an identical compa-ratio. It is invisible in a list and obvious
    the moment anyone plots a distribution.
    """
    for _ in range(MAX_DRAWS):
        ratio = rng.gauss(shape.COMPA_MEAN, shape.COMPA_SD)
        if shape.COMPA_FLOOR <= ratio <= shape.COMPA_CEILING:
            return ratio

    raise ValueError(
        f"No compa-ratio inside [{shape.COMPA_FLOOR}, {shape.COMPA_CEILING}] after "
        f"{MAX_DRAWS} draws from a distribution centred on {shape.COMPA_MEAN} "
        f"with a spread of {shape.COMPA_SD}. Check the constants in shape.py."
    )


def _insert_people(
    session: Session,
    rng: Random,
    today: date,
    headcount: int,
    locations: dict[str, dict],
    departments: dict[str, dict],
    families: dict[str, dict],
    levels: dict[str, dict],
    bands: dict[tuple[int, int, int], dict],
    rates: RateBook,
) -> tuple[int, int]:
    location_codes = [code for code, *_ in shape.LOCATIONS]
    location_weights = [weight for *_, weight in shape.LOCATIONS]
    department_names = [name for name, *_ in shape.DEPARTMENTS]
    department_weights = [weight for _name, weight, _families in shape.DEPARTMENTS]
    level_codes = [code for code, *_ in shape.LEVELS]
    level_weights = [weight for *_, weight in shape.LEVELS]
    families_by_department = {name: fams for name, _weight, fams in shape.DEPARTMENTS}

    # Drawn in bulk: far quicker than one weighted pick per employee, and the
    # sequence is still reproducible from the seed.
    chosen_locations = rng.choices(location_codes, weights=location_weights, k=headcount)
    chosen_departments = rng.choices(department_names, weights=department_weights, k=headcount)
    chosen_levels = rng.choices(level_codes, weights=level_weights, k=headcount)

    span = shape.HISTORY_YEARS * 365
    employee_rows: list[dict] = []
    record_rows: list[dict] = []
    next_record_id = 1

    for index in range(headcount):
        employee_id = index + 1
        country = chosen_locations[index]
        location = locations[country]
        currency = location["currency"]

        department = departments[chosen_departments[index]]
        family = families[rng.choice(families_by_department[chosen_departments[index]])]
        level = levels[chosen_levels[index]]

        hired_on = today - timedelta(days=int(rng.triangular(0, span, span * 0.28)))
        tenure = (today - hired_on).days

        left_on = None
        if tenure > shape.MIN_TENURE_DAYS and rng.random() < shape.LEAVER_FRACTION:
            left_on = hired_on + timedelta(days=rng.randint(shape.MIN_TENURE_DAYS, tenure))

        first = rng.choice(FIRST_NAMES[country])
        last = rng.choice(LAST_NAMES[country])
        staff_number = f"ACM{employee_id:06d}"

        employee_rows.append(
            {
                "id": employee_id,
                "staff_number": staff_number,
                "first_name": first,
                "last_name": last,
                # The staff number carries uniqueness; names repeat, as they do.
                "email": f"{first.split()[0].lower()}.{last.lower()}.{employee_id}@acme.test",
                "hired_on": hired_on,
                "left_on": left_on,
                "location_id": location["id"],
                "department_id": department["id"],
                "job_family_id": family["id"],
                "job_level_id": level["id"],
            }
        )

        band = bands[(location["id"], family["id"], level["id"])]
        current = Decimal(band["mid_minor"]) * Decimal(str(_compa_ratio(rng)))

        until = left_on - timedelta(days=1) if left_on else today
        events = _pay_events(rng, hired_on, until)

        # Worked backwards from the salary we want them on now, so the intended
        # position in band survives however many raises happened on the way.
        amounts: list[tuple[date, PayChangeReason, Decimal]] = []
        running = current
        for when, reason, raise_pct in reversed(events):
            amounts.append((when, reason, running))
            running = running / (1 + Decimal(str(raise_pct)))

        history = [(hired_on, PayChangeReason.HIRE, running), *reversed(amounts)]

        for when, reason, amount in history:
            minor = int(amount)
            rate_micros = rates.on(currency, when)
            record_rows.append(
                {
                    "id": next_record_id,
                    "employee_id": employee_id,
                    "effective_from": when,
                    "amount_minor": minor,
                    "currency": currency,
                    "base_amount_minor": to_base(minor, currency, rate_micros),
                    "fx_rate_micros": rate_micros,
                    "reason": reason,
                    "note": None,
                }
            )
            next_record_id += 1

    for start in range(0, len(employee_rows), CHUNK):
        session.execute(insert(Employee), employee_rows[start : start + CHUNK])
    for start in range(0, len(record_rows), CHUNK):
        session.execute(insert(CompensationRecord), record_rows[start : start + CHUNK])

    return len(employee_rows), len(record_rows)
