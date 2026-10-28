#!/bin/sh
# Container entrypoint: bring the schema up to date, make sure there is data to
# look at, then serve.
set -e

echo "==> Applying migrations"
python -m alembic upgrade head

# On a fresh disk this fills the database; on a warm restart it does nothing
# and still exits 0, so a redeploy never fails here.
echo "==> Seeding if empty"
python -m app.seed --if-empty

# exec so uvicorn becomes PID 1 and gets SIGTERM directly, otherwise the
# platform waits out its grace period on every deploy.
echo "==> Starting API on port ${PORT:-8000}"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
