# 4. SQLite as the datastore

Date: 2026-10-25
Status: accepted

## Context

The dataset is 10,000 employees and roughly 40,000 compensation records. The
workload is one HR manager reading, filtering and aggregating, with occasional
writes. There is no concurrency to speak of.

Postgres is the default reflex for anything with money in it, and would be the
right answer for a real deployment with several HR users, row-level security and
a backup policy. For this it would mean a container to run, a connection to
configure and a service to deploy, in exchange for capabilities the workload
does not use.

## Decision

SQLite, through SQLAlchemy, with Alembic migrations.

The code targets portable SQL. No SQLite-specific types, no reliance on its
loose typing. Moving to Postgres is a connection string and a migration run.

## Consequences

Cloning the repository and running it requires nothing to be installed or
started. Tests run against an in-memory database, so the suite is fast and
leaves nothing behind between runs.

The constraints that come with it are real and worth naming. Writes serialise
on a single lock, which is irrelevant for one user and would not be for fifty.
Concurrent access needs WAL mode. There is no network access, so the API
process and the database share a filesystem — meaning the deployed backend
needs a persistent disk, not an ephemeral one, and it cannot scale to more than
one instance without changing this decision first.

SQLite's type affinity will accept a string into an integer column rather than
refusing it. Schema correctness therefore depends on the SQLAlchemy layer rather
than the database, which is an argument for keeping writes going through the
models and not through raw SQL.

Median is the one place the choice shows up in the code. SQLite has no
percentile function, so quartiles are computed with window functions rather than
a built-in. It works and it is tested, but it is more code than the Postgres
equivalent would be.

## Alternatives considered

**Postgres.** The right production answer, and what this would migrate to under
real multi-user load. Rejected here as infrastructure the workload does not
earn, and because requiring a running database makes the project meaningfully
harder for a reviewer to start.

**DuckDB.** Genuinely better at the analytical half — native percentiles and
columnar aggregates. Rejected because the transactional half is the larger part
of the application, and running two engines to avoid writing one window function
is a poor trade.
