# 1. Compensation is a sequence of effective-dated records

Date: 2026-10-25
Status: accepted

## Context

An employee's salary changes over time, and the HR manager needs to ask
questions about both the present and the past. What is this person paid now;
what were they paid in June; what did the last merit cycle cost; has the gap
between two departments narrowed since last year.

The obvious model is a `salary` column on the employee row, updated when it
changes. That is also what the spreadsheet this replaces does, and it is the
reason the spreadsheet cannot answer any of those questions. An update destroys
the previous value.

The usual patch is an audit table that records changes alongside the current
value. That introduces two sources of truth which drift the first time anything
writes to one and not the other.

## Decision

There is no salary column. An employee has many `compensation_record` rows,
each with an effective date, an amount, a currency and a reason. Current salary
is derived: the most recent record whose effective date is not in the future.

Records are append-only. A correction is a new record, not an edit.

## Consequences

History comes free and cannot be lost, because nothing is ever overwritten.
Point-in-time reporting is a change of one parameter rather than a different
feature. A promotion effective next month can be entered today and will not
appear in this month's figures.

The price is that reading a current salary is no longer a column read. It is a
per-employee lookup of the latest qualifying row, which is the one query in the
system that needs care: done naively across a page of employees it is an N+1,
and across the whole organisation it is slow. It wants a window function and an
index, and a test that asserts the query count so the naive version cannot
quietly return.

Corrections are visible rather than silent. For a salary system that is the
right trade, but it does mean a typo and its fix both appear in the timeline,
so the UI needs to distinguish a correction from a real change.

## Alternatives considered

**Salary column plus audit log.** Faster to read and familiar. Rejected because
the two can disagree, and the audit log is then the only honest record while the
column is the one everything queries.

**Valid-from / valid-to ranges on each record.** Makes point-in-time queries a
simple `BETWEEN` and avoids the window function. Rejected because closing the
previous row on every insert reintroduces mutation, and overlapping or gapped
ranges are a class of bug that open-ended records cannot have.
