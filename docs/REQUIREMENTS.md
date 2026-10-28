# Salary Management — Requirements

## The problem

ACME's HR team keeps salary data for about 10,000 employees across several
countries in spreadsheets. That works until someone asks a question. *What do we
pay a mid-level engineer in Germany? Who is underpaid relative to their band?
Did last year's merit cycle widen or close the gap between departments?*
Answering any of these today means a VLOOKUP, a pivot table, and a reasonable
chance of getting it wrong.

Spreadsheets are also lossy. A cell overwritten in March destroys the record of
what the person earned in February, so there is no reliable history to reason
about.

## Goal

Give the HR manager one place to maintain salary data and get trustworthy
answers out of it, without exporting anything.

## Who it is for

A single persona: the HR manager. They are trusted with the whole dataset, they
work across every country, and they care about two different things:

- **Operational** — find a person, see what they earn and how that changed,
  record a raise.
- **Analytical** — understand how the organisation pays as a whole, and spot
  where it pays inconsistently.

The second is the reason this exists. If it only did the first, a spreadsheet
would still be fine.

## Scope

**Employee directory.** Search and filter the full 10,000 across country,
department, job family, level and band position. Paginated and sorted on the
server; the browser never receives the whole set.

**Employee detail.** Current compensation plus the full history of changes, each
with its effective date and the reason it happened.

**Recording a change.** A raise, promotion or market adjustment is a new
effective-dated record, not an edit. History is append-only, so the question
"what did we pay this person in Q2" always has an answer.

**Multi-currency.** Salaries are held in the currency they are paid in. For any
cross-country comparison the figures are converted to a single base currency
using the rate in force on the record's effective date, so last night's FX
movement cannot change what a report said about 2023.

**Salary bands.** A minimum, midpoint and maximum per country, job family and
level. Bands turn a salary from a number into a judgement: compa-ratio says
whether someone is paid appropriately for their role and location, which is
the question an HR manager actually has.

**Analytics.** Distribution of pay (median, quartiles) sliced by country,
department, family and level, and who sits outside their band in either
direction. Compa-ratio is the headline number: a salary set against its band
midpoint, which turns "is this person paid a lot" into "is this person paid
appropriately for their role and location".

## Deliberately out of scope

**Payroll execution, tax and payslips.** A different system with heavy
regulatory requirements per country. This software decides what someone should
be paid; it does not pay them.

**Equity, bonus and benefits.** Total compensation is a much larger model, and
base salary is where the HR manager's questions concentrate. Adding the rest
would double the domain for a marginal gain in insight.

**Approval workflows.** Who signs off a raise is specific to each organisation's
policy. Building a generic state machine would add significant complexity
without demonstrating anything the rest of the system does not.

**Real authentication and access control.** The app assumes a single trusted HR
manager and stubs the session. This is the largest gap between this and
something deployable: salary data genuinely needs SSO, role-based access,
field-level permissions and an access audit log. It is omitted for time, not
because it is unimportant, and the architecture keeps it addable.

**Bulk spreadsheet import.** The honest migration path from ACME's current
reality, and valuable in a real rollout. It is mostly file parsing and
validation plumbing, so it loses to features that show more.

**Demographic pay-gap analysis.** Valuable to a real HR manager and a natural
extension of banding, but it needs demographic data nothing else in the product
uses, and against synthetic employees any gap reported would be an artefact of
the seed rather than a finding. Compa-ratio answers the fairness question this
dataset can answer honestly.

**Live FX feeds.** Rates are seeded and snapshotted. Wiring a provider is an
integration detail, not a design question.

**Employee self-service.** A different persona with different access rules.

## Assumptions

ACME is fictional, so the shape is invented but kept realistic:

- Six countries — United States, United Kingdom, Germany, India, Singapore and
  Brazil — chosen for a wide spread of currencies and absolute pay levels, which
  is what makes currency normalisation and banding matter.
- Job levels L1–L8 across a handful of job families, with bands defined per
  country, family and level.
- One active base salary per employee at a time, with a full history behind it.
- Three years of history, including hires, annual merit cycles, promotions and
  some departures, so the analytics have something real to show.

## What success looks like

- The directory stays responsive at 10,000 employees, with filtering and sorting
  done in the database rather than the browser.
- Every compensation change carries an effective date and a reason, and no
  historical record is ever altered.
- The HR manager can answer "what is our median pay for this role in this
  country", "who is outside their band" and "how do two departments compare"
  in under a minute each, without exporting anything.
- The temporal and analytical logic is covered by tests against hand-checked
  numbers, because a wrong salary figure does not crash anything — it just
  quietly misinforms.
