# Performance

Measured on the seeded dataset: 10,000 employees, around 50,500 compensation
records,
SQLite on a laptop. The end-to-end figures below come from
`python scripts/benchmark_directory.py`, which is in the repository — run it
after seeding and you should see roughly the same numbers. Each is the best of
five runs after a warm-up, and they held to within a few percent across
repeated runs.

## The problem

There is no current-salary column. Current pay is the most recent compensation
record that has taken effect ([ADR 0001](adr/0001-effective-dated-compensation.md)),
so the directory cannot read it, sort by it or filter on it without resolving
it first — for every employee the query touches.

That resolution is the whole performance story of this feature.

## Two ways to resolve it

**Rank every record in a subquery.** Number the records per employee with a
window function, keep the first of each, join that to employees. It reads well
and it is the obvious answer.

**Look it up per employee row.** A correlated scalar subquery finds the id of
the record in force for the employee on the current row, and the record joins
on that id.

Both were written as raw SQL and measured against the real dataset before
choosing. These figures are not reproducible from the repository, because the
ranking version was not kept once it lost:

| Query                   | Ranked subquery | Correlated lookup |
| ----------------------- | --------------: | ----------------: |
| First page, by name     |          129 ms |        **0.4 ms** |
| First page, by salary   |          138 ms |         **52 ms** |
| First page, by compa    |          169 ms |         **54 ms** |
| Deep page (offset 7450) |          162 ms |         **95 ms** |
| Count of all matches    |          157 ms |         **20 ms** |

Ranking loses because it does the same work regardless of what was asked for.
`EXPLAIN QUERY PLAN` showed `MATERIALIZE` — every one of the 50,000-odd
records numbered and
spooled to a temporary table before `LIMIT` came anywhere near being applied.
Fifty rows cost the same as ten thousand.

The correlated lookup is evaluated only for employee rows the query actually
visits, and rides the `(employee_id, effective_from)` index. Sorting by name
walks the name index, stops after fifty rows, and resolves pay fifty times.
Sorting by salary still resolves all ten thousand, because you cannot order by
a value you have not computed — that cost is real but it is paid only when
someone sorts by pay.

A covering index on `(employee_id, effective_from DESC, id DESC)` was tried and
made no measurable difference, so it was not added. An index that does not earn
its write cost is a liability.

## End to end, through the repository

The before column is the ranked-subquery implementation measured through the
same repository function, so the two columns are like for like.

| Query                      | Before |     After |
| -------------------------- | -----: | --------: |
| First page, by name        | 275 ms | **10 ms** |
| First page, by salary      | 290 ms | **37 ms** |
| First page, by compa-ratio | 291 ms | **39 ms** |
| Page 150, deep offset      | 293 ms | **118 ms** |
| Search by surname          | 336 ms | **34 ms** |
| One employee with history  | 142 ms |  **2 ms** |

Filtering to people paid below their band lands around 50 ms. It has no
comparable before figure — that case was measured with an extra country filter
on the first pass, so quoting it as a speedup would be dishonest.

## Analytics

| Query                              |  Time |
| ---------------------------------- | ----: |
| Overview of the whole organisation | 215 ms |
| Distribution by country            | 156 ms |
| Distribution by level              | 159 ms |
| By level, one country, local pay   |  40 ms |

These are slower than the directory and that is inherent rather than sloppy.
The directory resolves current pay only for the rows a page returns; an
aggregate has to resolve it for everyone in scope — about 9,200 people — and
then rank them twice, once by pay and once by compa-ratio, before grouping.

The overview carries an extra query on top: the count of people with no pay in
effect or no band for their role. Folding it into the main statement would need
outer joins where the aggregate needs inner ones, which would make one query do
two jobs badly.

Filtering is what brings this down. Narrowed to one country the same query runs
in 40 ms, because the expensive part scales with how many people are in scope
rather than how many exist. A dashboard that loads three charts unfiltered
spends about half a second; the same dashboard filtered spends a tenth of that.

That is acceptable for a page someone opens and reads. If it stopped being
acceptable the fix is not a cleverer query — it is caching the aggregates,
since they only change when someone records a pay change.

## Other decisions

**The count query drops the pay and band joins** unless a band filter is
active. Both are outer joins and cannot change the row count, so carrying them
through a count is pure cost.

**N+1s are tested for, not hoped against.** `current_many` resolves a page of
employees in one query and a test counts cursor executions, failing if that
changes. A second test asserts that a page of 5 and a page of 100 cost the same
number of queries.

**Pagination, filtering and sorting all happen in SQL.** The API never returns
an unbounded list; `page_size` is capped at 200 and a larger request is
rejected rather than quietly clamped.

## Known limits

**Deep offsets degrade.** Page 150 costs about 118 ms because the rows before it
still have to be walked, and it gets worse the further back you go. Keyset
pagination would fix it at the cost of jump-to-page. For a directory people
filter and sort rather than page to the end of, offset is the better trade —
but it is a trade, not an oversight.

**These are single-user numbers.** SQLite serialises writes, so none of this
says anything about concurrency. See [ADR 0004](adr/0004-sqlite-as-datastore.md).

**On Postgres the shape would change.** `LATERAL` expresses the same lookup
more directly, and a partial index on the latest record per employee becomes
practical. The correlated form was chosen for the database actually in use.
