# 3. FX rates are snapshotted onto the compensation record

Date: 2026-10-25
Status: accepted

## Context

Salaries are paid in six currencies. Any question that spans countries — median
pay across the organisation, cost of a merit cycle, how two departments compare
— needs them in one currency to be answerable at all.

Converting at read time using today's rate produces a report that changes when
nothing about the underlying data has changed. Run the same 2023 report twice a
month apart and it gives two different answers. For a report an HR manager might
act on, or repeat to a regulator, that is not acceptable.

It also makes year-on-year comparison meaningless. A 6% gap between two years
might be a pay decision or might be sterling moving, and nothing in the data
distinguishes them.

## Decision

When a compensation record is created, the FX rate in force on its effective
date is looked up and stored on the record, together with the converted
base-currency amount.

Reports read the stored conversion. They do not convert.

## Consequences

A historical report gives the same answer forever. Changes between periods
reflect pay decisions, not currency movement, which is what the HR manager is
actually asking about.

The denormalisation is deliberate: the converted amount is derivable from the
rate and the original amount, and it is stored anyway so aggregates do not
multiply across 10,000 rows at query time.

The limitation is that this measures pay in local terms translated once, not
purchasing power today. A salary set in 2023 at a 2023 rate is not what that
money is worth now. For "how do we pay people relative to their market" that is
the right frame, since the band is also local. For "what does our payroll cost
us today" it is not, and that question would need a second view converting at
the current rate. Only the first is in scope.

Backfilling a corrected rate means rewriting affected records, which is a
deliberate operation rather than something that happens by accident.

## Alternatives considered

**Convert at read time using the current rate.** Simplest, and right for a
treasury view of present-day cost. Rejected because historical reports become
unstable and pay changes become indistinguishable from currency movement.

**Store only the rate, convert on read.** Stable and avoids the duplicated
amount. Rejected narrowly: it puts a multiplication inside every aggregate for
no real gain, since the stored amount is cheap and the rate is immutable once
written.
