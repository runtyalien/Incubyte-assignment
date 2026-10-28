"""Analytics against numbers worked out by hand.

A wrong median does not raise anything. It reports a plausible figure and
every decision taken on it is quietly wrong, so these assert the arithmetic
rather than that the code agrees with itself.
"""

from datetime import date
from decimal import Decimal

from app.repository import analytics
from app.repository.analytics import Dimension
from app.repository.directory import Filters, Status
from tests.factories import add_band, add_employee, add_location, add_pay, paid

AS_OF = date(2024, 6, 1)


def band(session, org, low="80000", mid="100000", high="120000"):
    return add_band(session, org, low=low, mid=mid, high=high)


def only(session, **kwargs):
    groups = analytics.distribution(session, Dimension.COUNTRY, as_of=AS_OF, **kwargs)
    assert len(groups) == 1
    return groups[0]


def test_one_employee_is_their_own_every_statistic(session, org):
    band(session, org)
    paid(session, org, "100000")

    pay = only(session).pay

    assert pay.lowest == pay.p25 == pay.median == pay.p75 == pay.highest == 10_000_000


def test_median_of_an_odd_count_is_the_middle_value(session, org):
    band(session, org)
    for amount in ("100000", "110000", "120000"):
        paid(session, org, amount)

    assert only(session).pay.median == 11_000_000


def test_median_of_an_even_count_is_the_mean_of_the_middle_two(session, org):
    band(session, org)
    for amount in ("100000", "110000", "120000", "130000"):
        paid(session, org, amount)

    # (110,000 + 120,000) / 2
    assert only(session).pay.median == 11_500_000


def test_quartiles_use_nearest_rank(session, org):
    band(session, org, low="5000", mid="25000", high="50000")
    for amount in ("10000", "20000", "30000", "40000"):
        paid(session, org, amount)

    pay = only(session).pay

    # Ranks ceil(4 x 0.25) = 1 and ceil(4 x 0.75) = 3, so 10,000 and 30,000.
    # Interpolating would give 15,000 and 35,000; this does not interpolate.
    assert pay.p25 == 1_000_000
    assert pay.median == 2_500_000
    assert pay.p75 == 3_000_000
    assert pay.lowest == 1_000_000
    assert pay.highest == 4_000_000


def test_a_median_landing_on_half_a_cent_rounds_up(session, org):
    band(session, org)
    for amount in ("100000.01", "100000.02"):
        paid(session, org, amount)

    # 10,000,001 and 10,000,002 average to 10,000,001.5
    assert only(session).pay.median == 10_000_002


def test_order_of_insertion_does_not_change_the_median(session, org):
    band(session, org)
    for amount in ("130000", "100000", "120000", "110000"):
        paid(session, org, amount)

    assert only(session).pay.median == 11_500_000


def test_band_position_is_counted_per_group(session, org):
    band(session, org, low="80000", mid="100000", high="120000")
    paid(session, org, "70000")  # below
    paid(session, org, "80000")  # exactly the floor, so within
    paid(session, org, "100000")  # within
    paid(session, org, "120000")  # exactly the ceiling, so within
    paid(session, org, "130000")  # above

    group = only(session)

    assert (group.below, group.within, group.above) == (1, 3, 1)
    assert group.headcount == 5


def test_compa_median_is_pay_against_the_band_midpoint(session, org):
    band(session, org, mid="100000")
    for amount in ("90000", "100000", "110000"):
        paid(session, org, amount)

    assert only(session).compa_median == Decimal("1.0000")


def test_compa_median_of_an_even_count(session, org):
    band(session, org, mid="100000")
    for amount in ("90000", "100000"):
        paid(session, org, amount)

    # 0.9 and 1.0 average to 0.95
    assert only(session).compa_median == Decimal("0.9500")


def test_groups_split_by_country(session, org):
    band(session, org)
    germany = add_location(session, "DE", "Germany", "USD")
    add_band(session, org, low="80000", mid="100000", high="120000", location=germany)

    paid(session, org, "100000")
    paid(session, org, "110000")
    paid(session, org, "200000", location_id=germany.id)

    groups = analytics.distribution(session, Dimension.COUNTRY, as_of=AS_OF)

    assert [(g.key, g.headcount) for g in groups] == [("DE", 1), ("US", 2)]
    assert groups[0].pay.median == 20_000_000
    assert groups[1].pay.median == 10_500_000


def test_levels_are_ordered_by_seniority_not_name(session, org):
    band(session, org)
    paid(session, org, "100000")

    groups = analytics.distribution(session, Dimension.LEVEL, as_of=AS_OF)

    assert [g.key for g in groups] == ["L4"]


def test_someone_whose_pay_has_not_started_is_left_out_and_counted(session, org):
    band(session, org)
    paid(session, org, "100000")
    future = add_employee(session, org)
    add_pay(session, future, date(2025, 1, 1), "500000")

    group = only(session)
    missing = analytics.unmeasured(session, filters=Filters(), as_of=AS_OF)

    assert group.headcount == 1
    assert group.pay.median == 10_000_000
    assert missing == 1


def test_a_role_with_no_band_is_left_out_and_counted(session, org):
    # No band created at all.
    paid(session, org, "100000")

    groups = analytics.distribution(session, Dimension.COUNTRY, as_of=AS_OF)
    missing = analytics.unmeasured(session, filters=Filters(), as_of=AS_OF)

    assert groups == []
    assert missing == 1


def test_leavers_are_excluded_unless_asked_for(session, org):
    band(session, org)
    paid(session, org, "100000")
    paid(session, org, "200000", left_on=date(2023, 1, 1))

    active = only(session)
    everyone = analytics.distribution(
        session, Dimension.COUNTRY, filters=Filters(status=Status.ALL), as_of=AS_OF
    )

    assert active.headcount == 1
    assert everyone[0].headcount == 2


def test_as_of_reports_the_pay_in_force_then(session, org):
    band(session, org)
    employee = add_employee(session, org)
    add_pay(session, employee, date(2021, 1, 4), "100000")
    add_pay(session, employee, date(2024, 1, 1), "150000")

    before = analytics.distribution(session, Dimension.COUNTRY, as_of=date(2023, 6, 1))
    after = analytics.distribution(session, Dimension.COUNTRY, as_of=AS_OF)

    assert before[0].pay.median == 10_000_000
    assert after[0].pay.median == 15_000_000


def test_overview_totals_the_payroll(session, org):
    band(session, org)
    paid(session, org, "100000")
    paid(session, org, "150000")

    total = analytics.overview(session, as_of=AS_OF)

    assert total.headcount == 2
    assert total.payroll_minor == 25_000_000
    assert total.pay.median == 12_500_000
    assert total.currency == "USD"


def test_local_currency_reports_the_amount_actually_paid(session, org):
    india = add_location(session, "IN", "India", "INR")
    add_band(
        session,
        org,
        low="2000000",
        mid="2500000",
        high="3000000",
        location=india,
        currency="INR",
    )
    employee = add_employee(session, org, location_id=india.id)
    add_pay(session, employee, date(2021, 1, 4), "2500000", currency="INR", rate_micros=12_000)

    local = analytics.distribution(session, Dimension.COUNTRY, as_of=AS_OF, local=True)
    base = analytics.distribution(session, Dimension.COUNTRY, as_of=AS_OF)

    assert local[0].currency == "INR"
    assert local[0].pay.median == 250_000_000  # 2,500,000 rupees
    assert base[0].currency == "USD"
    assert base[0].pay.median == 3_000_000  # at 0.012, that is 30,000 dollars


def test_an_empty_organisation_reports_nothing_rather_than_failing(session, org):
    assert analytics.distribution(session, Dimension.COUNTRY, as_of=AS_OF) == []

    total = analytics.overview(session, as_of=AS_OF)

    assert total.headcount == 0
    assert total.payroll_minor == 0
    assert total.pay.median == 0
