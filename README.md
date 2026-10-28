# ACME Salary Management

Web software that lets an HR manager maintain salary data for ~10,000 employees
across multiple countries, and answer questions about how the organisation pays
people.

> **Status: scaffold.** Only the project skeleton and a backend/frontend
> connectivity check exist so far. The domain model, seed data and HR features
> are not built yet.

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
```

## Running locally

Two terminals. The frontend expects the API on port 8000.

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"   # macOS/Linux: .venv/bin/python
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

API docs are then served at <http://localhost:8000/docs>.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. The landing page reports whether it can reach the
backend.

## Tests

```bash
cd backend && .venv/Scripts/python.exe -m pytest
```

## Configuration

Both halves ship a `.env.example`. Copy it (`.env` for the backend, `.env.local`
for the frontend) and adjust as needed.
