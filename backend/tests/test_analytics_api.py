"""The HTTP surface. The arithmetic is covered in test_analytics.py; these
check the wiring, the currency rule and the shape of the response."""

from datetime import date

import pytest

from app.seed.run import seed_database

TODAY = date(2026, 1, 15)


@pytest.fixture
def directory(session):
    seed_database(session, headcount=300, rng_seed=77, today=TODAY)
    return session


def fetch(client, path, **params):
    params.setdefault("as_of", TODAY.isoformat())
    response = client.get(f"/api/analytics/{path}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_overview_reports_the_whole_organisation(client, directory):
    body = fetch(client, "overview")

    assert body["headcount"] > 0
    assert body["payroll"]["currency"] == "USD"
    assert float(body["payroll"]["amount"]) > 0
    assert body["as_of"] == TODAY.isoformat()


def test_overview_spread_is_ordered(client, directory):
    pay = fetch(client, "overview")["pay"]

    amounts = [float(pay[key]["amount"]) for key in ("lowest", "p25", "median", "p75", "highest")]
    assert amounts == sorted(amounts)


def test_band_counts_add_up_to_the_headcount(client, directory):
    body = fetch(client, "overview")
    band = body["band"]

    assert band["below"] + band["within"] + band["above"] == body["headcount"]


def test_distribution_groups_by_country(client, directory):
    body = fetch(client, "distribution", by="country")

    assert body["dimension"] == "country"
    assert body["basis"] == "base"
    assert len(body["groups"]) > 1
    assert all(len(group["key"]) == 2 for group in body["groups"])


def test_levels_come_back_in_seniority_order(client, directory):
    groups = fetch(client, "distribution", by="level")["groups"]

    # L10 would sort before L2 as text; the rank column is what orders these.
    assert [group["key"] for group in groups] == sorted(
        (group["key"] for group in groups), key=lambda code: int(code[1:])
    )


def test_group_headcounts_sum_to_the_overview(client, directory):
    total = fetch(client, "overview")["headcount"]
    groups = fetch(client, "distribution", by="department")["groups"]

    assert sum(group["headcount"] for group in groups) == total


def test_filters_narrow_the_analytics_the_same_way_as_the_directory(client, directory):
    everyone = fetch(client, "overview")["headcount"]
    indians = fetch(client, "overview", country="IN")["headcount"]
    listed = client.get(
        "/api/employees", params={"country": "IN", "page_size": 1, "as_of": TODAY.isoformat()}
    ).json()["total"]

    assert 0 < indians < everyone
    # The directory counts people without pay in effect; analytics cannot.
    assert indians <= listed


def test_local_currency_is_allowed_when_grouping_by_country(client, directory):
    body = fetch(client, "distribution", by="country", local="true")

    assert body["basis"] == "local"
    currencies = {group["pay"]["median"]["currency"] for group in body["groups"]}
    assert len(currencies) > 1


def test_local_currency_is_allowed_when_filtered_to_one_country(client, directory):
    body = fetch(client, "distribution", by="level", local="true", country="IN")

    assert {group["pay"]["median"]["currency"] for group in body["groups"]} == {"INR"}


def test_local_currency_across_mixed_countries_is_refused(client, directory):
    response = client.get(
        "/api/analytics/distribution",
        params={"by": "level", "local": "true", "as_of": TODAY.isoformat()},
    )

    # Rupees and dollars in one median is not a number anyone should act on.
    assert response.status_code == 400
    assert "single currency" in response.json()["detail"]


def test_an_unknown_dimension_is_rejected(client, directory):
    response = client.get("/api/analytics/distribution", params={"by": "favourite_colour"})

    assert response.status_code == 422


def test_money_is_serialised_as_a_string(client, directory):
    median = fetch(client, "overview")["pay"]["median"]

    assert isinstance(median["amount"], str)


def test_as_of_changes_the_answer(client, directory):
    now = fetch(client, "overview")["headcount"]
    earlier = fetch(client, "overview", as_of="2020-01-01")["headcount"]

    assert earlier < now


def test_reference_lists_the_filter_values(client, directory):
    body = client.get("/api/reference").json()

    assert {c["code"] for c in body["countries"]} >= {"US", "IN"}
    assert "Engineering" in body["departments"]
    assert body["families"]
    # Levels come back in seniority order so the UI does not have to sort them.
    assert [level["rank"] for level in body["levels"]] == sorted(
        level["rank"] for level in body["levels"]
    )
