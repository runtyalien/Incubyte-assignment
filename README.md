# ACME Salary Management

Web software that lets an HR manager maintain salary data for ~10,000 employees
across multiple countries, and answer questions about how the organisation pays
people.

> **Status: scaffold.** Design is documented; the domain model, seed data and HR
> features are not built yet.

## Documents

- [Requirements](docs/REQUIREMENTS.md) — goal, scope, and what is deliberately
  left out
- [Architecture](docs/ARCHITECTURE.md) — layering, data model, performance and
  testing approach
- Decision records:
  - [Effective-dated compensation](docs/adr/0001-effective-dated-compensation.md)
  - [Money as integer minor units](docs/adr/0002-money-as-integer-minor-units.md)
  - [Snapshotted FX rates](docs/adr/0003-snapshot-fx-rates.md)
  - [SQLite as the datastore](docs/adr/0004-sqlite-as-datastore.md)

## Stack

| Layer    | Choice                                         |
| -------- | ---------------------------------------------- |
| Backend  | Python, FastAPI, Pydantic, pytest              |
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS |
| Database | SQLite (not wired up yet)                      |

## Layout

```
backend/    FastAPI service
  app/      application code
  tests/    pytest suite
frontend/   Next.js app
  src/app/  routes
  src/lib/  API client
docs/       requirements, architecture, decision records
```

## Running locally

Two terminals. The frontend expects the API on port 8000.

### Backend

PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

bash / zsh:

```bash
cd backend
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

API docs are then at <http://localhost:8000/docs>.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. The landing page reports whether it can reach the
backend.

If port 3000 or 8000 is already taken, pass another one — `npm run dev -- --port
3001`, or `--port 8001` on uvicorn. The frontend finds the API through
`NEXT_PUBLIC_API_URL`, so change that too if you move the backend.

## Seed data

The database starts empty. To fill it with a synthetic organisation of 10,000
people across six countries, with roughly 50,000 compensation records covering
ten years of hires, merit cycles and promotions:

```powershell
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m app.seed
```

Takes about two seconds. The same seed always produces the same organisation,
so screenshots and demos stay reproducible. Pass `--employees 500` for a
smaller set, `--seed N` for a different one, and `--reset` to replace data that
is already there — without it, seeding a populated database is refused rather
than doubling it.

What the generated organisation looks like — headcount per country, the level
pyramid, how markets are priced relative to the US, where salaries sit in band
— is all in [`app/seed/shape.py`](backend/app/seed/shape.py).

## Tests

PowerShell:

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
```

bash / zsh:

```bash
cd backend
.venv/bin/python -m pytest
```

Lint and type-check the frontend with `npm run lint` and `npm run build`.

## Configuration

Both halves ship a `.env.example`. Copy it — `.env` for the backend, `.env.local`
for the frontend — and adjust as needed.
