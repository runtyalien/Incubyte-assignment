"""The temporal rules. Get these wrong and nothing raises — the numbers are
just quietly wrong, everywhere."""

from datetime import date, timedelta

from app.repository import compensation as comp
from tests.factories import add_employee, add_pay

JAN = date(2024, 1, 1)
JUN = date(2024, 6, 1)
DEC = date(2024, 12, 1)


def test_employee_with_no_records_has_no_current_pay(session, org):
    employee = add_employee(session, org)

    assert comp.current(session, employee.id, as_of=JUN) is None


def test_single_record_is_the_current_one(session, org):
    employee = add_employee(session, org)
    add_pay(session, employee, JAN, "100000")

    current = comp.current(session, employee.id, as_of=JUN)

    assert current is not None
    assert current.amount_minor == 10_000_000


def test_latest_record_that_has_taken_effect_wins(session, org):
    employee = add_employee(session, org)
    add_pay(session, employee, JAN, "100000")
    add_pay(session, employee, JUN, "110000")

    current = comp.current(session, employee.id, as_of=DEC)

    assert current.amount_minor == 11_000_000


def test_record_effective_on_the_as_of_date_counts(session, org):
    employee = add_employee(session, org)
    add_pay(session, employee, JAN, "100000")
    add_pay(session, employee, JUN, "110000")

    # The boundary is inclusive: a raise effective today is in force today.
    current = comp.current(session, employee.id, as_of=JUN)

    assert current.amount_minor == 11_000_000


def test_future_records_are_ignored(session, org):
    employee = add_employee(session, org)
    add_pay(session, employee, JAN, "100000")
    add_pay(session, employee, DEC, "130000")

    current = comp.current(session, employee.id, as_of=JUN)

    assert current.amount_minor == 10_000_000


def test_only_future_records_means_no_current_pay(session, org):
    employee = add_employee(session, org)
    add_pay(session, employee, DEC, "130000")

    assert comp.current(session, employee.id, as_of=JUN) is None


def test_the_later_row_wins_when_two_share_an_effective_date(session, org):
    employee = add_employee(session, org)
    add_pay(session, employee, JUN, "110000")
    correction = add_pay(session, employee, JUN, "112000")

    # Same-day corrections are a real occurrence, so insertion order breaks the
    # tie rather than the result being arbitrary.
    current = comp.current(session, employee.id, as_of=JUN)

    assert current.id == correction.id
    assert current.amount_minor == 11_200_000


def test_as_of_defaults_to_today(session, org):
    today = date.today()
    employee = add_employee(session, org)
    add_pay(session, employee, today - timedelta(days=1), "100000")
    add_pay(session, employee, today + timedelta(days=1), "200000")

    current = comp.current(session, employee.id)

    assert current.amount_minor == 10_000_000


def test_current_many_returns_the_right_record_for_each_employee(session, org):
    first = add_employee(session, org)
    second = add_employee(session, org)

    add_pay(session, first, JAN, "100000")
    add_pay(session, first, JUN, "110000")
    add_pay(session, second, JAN, "90000")
    add_pay(session, second, DEC, "99000")

    found = comp.current_many(session, [first.id, second.id], as_of=JUN)

    assert found[first.id].amount_minor == 11_000_000
    assert found[second.id].amount_minor == 9_000_000


def test_current_many_omits_employees_with_nothing_in_effect(session, org):
    paid = add_employee(session, org)
    unpaid = add_employee(session, org)
    add_pay(session, paid, JAN, "100000")

    found = comp.current_many(session, [paid.id, unpaid.id], as_of=JUN)

    assert set(found) == {paid.id}


def test_current_many_takes_one_query_regardless_of_size(session, org, count_queries):
    employees = [add_employee(session, org) for _ in range(20)]
    for employee in employees:
        add_pay(session, employee, JAN, "100000")

    with count_queries() as counted:
        comp.current_many(session, [e.id for e in employees], as_of=JUN)

    assert counted["queries"] == 1


def test_current_many_with_no_ids_does_not_hit_the_database(session, org, count_queries):
    with count_queries() as counted:
        found = comp.current_many(session, [], as_of=JUN)

    assert found == {}
    assert counted["queries"] == 0


def test_history_is_oldest_first_and_includes_future_changes(session, org):
    employee = add_employee(session, org)
    add_pay(session, employee, JUN, "110000")
    add_pay(session, employee, JAN, "100000")
    add_pay(session, employee, DEC, "130000")

    timeline = comp.history(session, employee.id)

    assert [r.effective_from for r in timeline] == [JAN, JUN, DEC]
