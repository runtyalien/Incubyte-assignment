# AI-assisted development record

## Intent

This project used agentic AI as an engineering accelerator, not as an
unreviewed code generator. The goal was to shorten the feedback loop for
research, implementation, test design and review while keeping the author
accountable for the product choices, correctness and shipped result.

The Git history is deliberately part of the evidence. A number of commits name
Claude Opus 5 as a co-author; the commit messages retain the reasoning,
alternatives and verification performed for each slice. This document is a map
to that evidence rather than a claim that an AI tool autonomously built the
system.

## How AI was used

I used a tight **frame → delegate → verify → record** loop:

1. **Frame the problem before implementation.** I established the HR persona,
   the success criteria, non-goals and the important domain invariants. AI was
   useful for challenging omissions and enumerating trade-offs; I selected the
   scope and wrote it down before the first domain feature.
2. **Delegate bounded work, not an open-ended application build.** A slice had
   a clear contract—for example, "current compensation as of a date",
   "directory query with a bounded page", or "record a pay change". This keeps
   generated changes reviewable and makes each commit independently
   understandable.
3. **Ask different AI passes to implement, criticise and test.** I treated
   implementation and review as separate jobs. In particular, I asked for
   adversarial cases (currency precision, historical changes, invalid band
   ranges, migration drift and unstable pagination), then converted the
   important ones into executable tests.
4. **Verify outside the model.** Proposed code was checked against hand-worked
   examples, database constraints, migration output, real query plans,
   deterministic seed data and the normal test/build commands. AI output was
   never accepted because it sounded plausible.
5. **Record the decision and its limits.** When a choice has meaningful
   alternatives, the repository contains an ADR, measurement or commit note.
   That is both useful to a future maintainer and a guard against post-hoc
   rationalisation.

## Evidence in this repository

| Engineering question | AI-assisted exploration, then accountable decision | Evidence |
| --- | --- | --- |
| What should the product do? | Scoped to a trusted HR-manager workflow: a searchable directory, effective-dated pay changes and organisation-level compensation answers. Payroll, generic approvals and demographic-gap claims were explicitly excluded because they need different data, policy or regulation. | [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md), commit `299ae66` |
| What is the right source of truth for salary? | Chose append-only, effective-dated compensation records instead of a mutable `salary` column. This supports future-dated changes, correction history and point-in-time reporting. | [`docs/adr/0001-effective-dated-compensation.md`](docs/adr/0001-effective-dated-compensation.md), commits `3b5e0c4`, `26da391`, `3568437` |
| How do we keep financial calculations reliable? | Rejected binary floats and stored integer minor units. Currency precision is explicit (including zero-decimal JPY), and historical FX conversion is snapshotted with each record. | [`docs/adr/0002-money-as-integer-minor-units.md`](docs/adr/0002-money-as-integer-minor-units.md), [`docs/adr/0003-snapshot-fx-rates.md`](docs/adr/0003-snapshot-fx-rates.md), commits `777e4b8`, `16fc0b8` |
| Will the directory work at 10,000 employees? | Used a reproducible benchmark and `EXPLAIN QUERY PLAN` to replace a materialised ranking query with a correlated current-pay lookup. The repository names the remaining deep-pagination trade-off instead of claiming a universal optimum. | [`docs/PERFORMANCE.md`](docs/PERFORMANCE.md), [`backend/scripts/benchmark_directory.py`](backend/scripts/benchmark_directory.py), commit `8d1d75c` |
| Are analytics merely plausible, or correct? | Tests start from numbers worked out by hand, including odd/even medians, nearest-rank quartiles, rounding and band boundaries. This caught SQL division behaviour that would otherwise return believable but wrong results. | [`backend/tests/test_analytics.py`](backend/tests/test_analytics.py), commits `0db1cc8`, `80c2796` |
| What stops invalid salary data entering through another path? | Business validation lives in the service layer and database `CHECK` constraints provide an independent backstop. Migration tests assert that the deployed schema—not just ORM metadata—contains the constraints. | [`backend/tests/test_constraints.py`](backend/tests/test_constraints.py), [`backend/tests/test_migrations.py`](backend/tests/test_migrations.py), commits `79b5bb6`, `5d2ec31` |
| Is the sample organisation credible and repeatable? | The 10,000-person data set is deterministic by seed, shaped deliberately and tested for properties that downstream screens rely on, rather than filled with arbitrary rows. A duplicate-name issue was found and corrected in its own commit. | [`backend/app/seed/shape.py`](backend/app/seed/shape.py), [`backend/tests/test_seed.py`](backend/tests/test_seed.py), commits `daed13c`, `9f16485` |
| Did we revisit decisions when new evidence appeared? | The UI initially avoided a component library, then adopted shadcn/ui because the brief explicitly requested one. That reversal is documented rather than hidden. | commits `4fe3f2b`, `4784a37`, `79af6a8` |

## Quality gates used for AI-generated changes

- **Thin boundaries, testable core.** Routes deal with HTTP; services own pay
  rules; repositories own SQL; models own persistence. This makes an AI
  suggestion easy to locate and replace instead of letting generated logic
  spread through the application. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
- **Tests target failure modes.** The suite covers money conversion and
  precision, temporal compensation selection, query count, pagination,
  analytics arithmetic, API behaviour, seed properties, migrations and
  database constraints. Test intent is documented beside the assertions, not
  inferred from test names alone.
- **Measurements are repeatable.** The performance document links to the
  committed benchmark and labels historical A/B measurements that cannot be
  rerun. This avoids presenting AI-generated performance claims as fact.
- **Production concerns were checked explicitly.** Containerisation, health
  semantics, configuration, cold-start behaviour and free-tier persistence
  limits are documented in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). The
  `f625245` fix is a good example: the health check was tested with the actual
  platform-provided port rather than assumed to use `8000`.
- **Commit history remains readable.** Each commit represents one concern—
  scaffolding, schema, a domain rule, a UI capability, a test gap or a
  deployment adjustment—so a reviewer can audit the sequence or bisect it.

## What AI did not decide

AI did not set product policy, decide what data is safe to model, approve an
architecture, declare tests sufficient, or make deployment trade-offs on its
own. In this submission, those decisions are intentionally inspectable in the
requirements, ADRs, measurements, tests and incremental commits. That
traceability is the important outcome of using agents well: faster iteration
without outsourcing engineering judgement.
