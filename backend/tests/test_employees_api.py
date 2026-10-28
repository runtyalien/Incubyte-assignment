from datetime import date

import pytest

from app.seed.run import seed_database

TODAY = date(2026, 1, 15)
HEADCOUNT = 200


@pytest.fixture
def directory(session):
    seed_database(session, headcount=HEADCOUNT, rng_seed=99, today=TODAY)
    return session


def get(client, **params):
    params.setdefault("as_of", TODAY.isoformat())
    response = client.get("/api/employees", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_lists_a_page_with_its_totals(client, directory):
    body = get(client, page_size=25)

    assert len(body["items"]) == 25
    assert body["page"] == 1
    assert body["page_size"] == 25
    assert 0 < body["total"] <= HEADCOUNT


def test_paging_does_not_repeat_people(client, directory):
    first = get(client, page=1, page_size=20)
    second = get(client, page=2, page_size=20)

    assert {row["id"] for row in first["items"]}.isdisjoint(row["id"] for row in second["items"])


def test_filters_by_country(client, directory):
    body = get(client, country="IN")

    assert body["items"]
    assert {row["country"] for row in body["items"]} == {"IN"}


def test_filters_by_several_levels_at_once(client, directory):
    body = get(client, level=["L1", "L2"], page_size=100)

    assert body["items"]
    assert {row["level"] for row in body["items"]} <= {"L1", "L2"}


def test_searches_by_staff_number(client, directory):
    everyone = get(client, page_size=1)
    target = everyone["items"][0]

    body = get(client, q=target["staff_number"])

    assert [row["id"] for row in body["items"]] == [target["id"]]


def test_searches_by_partial_name(client, directory):
    someone = get(client, page_size=1)["items"][0]
    surname = someone["name"].split()[-1]

    body = get(client, q=surname, page_size=100)

    assert any(row["id"] == someone["id"] for row in body["items"])


def test_sorts_by_salary_in_the_database(client, directory):
    body = get(client, sort="salary", order="desc", page_size=50)

    paid = [float(row["base_pay"]["amount"]) for row in body["items"] if row["base_pay"]]
    assert paid == sorted(paid, reverse=True)


def test_sorting_by_salary_spans_pages(client, directory):
    first = get(client, sort="salary", order="desc", page=1, page_size=10)
    second = get(client, sort="salary", order="desc", page=2, page_size=10)

    # Paging has to happen after sorting, or page two is just the next twenty
    # rows by id with a sort applied to them.
    cheapest_on_page_one = float(first["items"][-1]["base_pay"]["amount"])
    dearest_on_page_two = float(second["items"][0]["base_pay"]["amount"])
    assert cheapest_on_page_one >= dearest_on_page_two


def test_filters_to_people_paid_below_their_band(client, directory):
    body = get(client, position="below", page_size=100)

    assert body["items"]
    for row in body["items"]:
        assert row["band_position"] == "below"
        assert float(row["compa_ratio"]) < 1


def test_money_is_serialised_as_a_string(client, directory):
    row = get(client, page_size=1)["items"][0]

    # A JSON number would arrive in the browser as a float, which is the one
    # thing the whole money design is trying to avoid.
    assert isinstance(row["pay"]["amount"], str)
    assert isinstance(row["compa_ratio"], str)


def test_a_page_costs_the_same_number_of_queries_however_large(client, directory, count_queries):
    with count_queries() as small:
        get(client, page_size=5)
    with count_queries() as large:
        get(client, page_size=100)

    assert small["queries"] == large["queries"]


def test_page_size_is_capped(client, directory):
    response = client.get("/api/employees", params={"page_size": 5000})

    assert response.status_code == 422


def test_detail_includes_the_whole_pay_history(client, directory):
    someone = get(client, page_size=1)["items"][0]

    response = client.get(f"/api/employees/{someone['id']}", params={"as_of": TODAY.isoformat()})
    body = response.json()

    assert response.status_code == 200
    assert body["id"] == someone["id"]
    assert body["history"]
    assert body["history"][0]["reason"] == "hire"

    dates = [entry["effective_from"] for entry in body["history"]]
    assert dates == sorted(dates)


def test_detail_reports_the_band(client, directory):
    someone = get(client, page_size=1)["items"][0]

    body = client.get(f"/api/employees/{someone['id']}").json()
    band = body["band"]

    low, mid, high = (float(band[key]["amount"]) for key in ("low", "mid", "high"))
    assert low < mid < high


def test_unknown_employee_is_a_404(client, directory):
    assert client.get("/api/employees/999999").status_code == 404


def test_as_of_reports_pay_as_it_was(client, directory):
    someone = get(client, sort="hired", page_size=1)["items"][0]
    history = client.get(f"/api/employees/{someone['id']}").json()["history"]

    if len(history) < 2:
        pytest.skip("needs an employee with more than one record")

    before_the_second_change = history[1]["effective_from"]
    body = client.get(
        f"/api/employees/{someone['id']}", params={"as_of": before_the_second_change}
    ).json()

    assert body["pay"]["amount"] == history[1]["amount"]["amount"]
