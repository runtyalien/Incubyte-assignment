# 2. Money is stored as integer minor units

Date: 2026-10-25
Status: accepted

## Context

Salaries need to be stored, summed, averaged and converted between currencies.
Three options exist in a Python and SQLite stack: a float, a decimal, or an
integer count of the currency's smallest unit.

Floats are the default almost everywhere and are wrong for money. Binary
floating point cannot represent 0.1 exactly, so errors accumulate under
addition. Across 10,000 salaries that drift becomes large enough to be visible
in a total, and the resulting number is both wrong and plausible, which is the
worst combination.

SQLite makes this sharper than usual: it has no native decimal type, so a
`Numeric` column is stored as text or float underneath and arithmetic happens
outside the database or loses precision inside it.

## Decision

Amounts are integers in the currency's minor unit — cents for USD, pence for
GBP, paise for INR. A salary of 120,000.00 USD is stored as `12000000`.

Each amount carries its currency code alongside it. The number is meaningless
without it, and minor units differ: JPY has none, so the same integer means a
thousand times more than it would in USD.

Conversion to display units happens once, at the API boundary.

## Consequences

Addition and comparison are exact. Totals are reproducible. No rounding policy
is needed for storage, only for the places where division genuinely occurs —
percentiles and compa-ratio — where it can be made explicit rather than
accidental.

Every read and write needs conversion, which is a small tax paid in one place
each way. Raw rows are harder to eyeball in a database client, since `12000000`
does not read as a salary.

The real risk is a currency's minor-unit count being assumed rather than
looked up. Two decimal places is not universal. The exponent lives with the
currency rather than being hardcoded.

## Alternatives considered

**Python `Decimal` with a `Numeric` column.** Exact and more readable in the
database. Rejected because SQLite has no decimal type, so the guarantee is only
as good as the adapter and some arithmetic silently happens in float anyway.

**Float.** Rejected outright. There is no amount of care that makes binary
floating point safe for money.
