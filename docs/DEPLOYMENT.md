# Deployment

Two deployables: the Next.js app on Vercel, the API on Render. Containers are
defined for both, so the same thing runs locally under Docker Compose.

## The shape of it

```
browser ──▶ Vercel (Next.js) ──┬──▶ its own server components
                               └──▶ /api/* rewritten ──▶ Render (FastAPI ──▶ SQLite)
```

The browser only ever talks to one origin. Next rewrites `/api/*` through to
the API, which means no CORS configuration, no backend URL in the JavaScript
bundle, and nothing to go wrong between the two when a hostname changes.

Server components skip the proxy and call the API directly, because they are
already on the server and the extra hop would be free of any benefit.

## Two things about this that are easy to get wrong

**The backend address is needed at build time, not just at run time.** Next
turns `rewrites()` into a manifest when it builds, so `API_URL` has to be set
for the build. On Vercel that means a project environment variable, not a
runtime one; in Docker it is a build argument. Change the API's address and the
frontend needs rebuilding, not just restarting.

**The database is wiped on every restart of a free instance.** There is no
persistent disk on Render's free plan, so `/data` is empty each time the
container starts. `start.sh` handles that: it migrates, then seeds if and only
if the database has no employees in it. A cold start comes up with the full
10,000 and takes about two seconds longer.

What that costs: pay changes recorded through the deployed UI survive until the
instance restarts, and no further. For a demonstration that is the right
trade — a persistent disk is a paid plan for data that is synthetic anyway. For
anything real, attach the disk (see the commented block in `render.yaml`) and
the behaviour changes without a code change, because the seed refuses a
populated database.

## API, on Render

The repository has a `render.yaml`, so a Blueprint deploy picks everything up.
By hand instead:

| Setting | Value |
| --- | --- |
| Runtime | Docker |
| Dockerfile path | `./backend/Dockerfile` |
| Docker context | `./backend` |
| Health check path | `/api/health` |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `sqlite:////data/salary.db` |

Four slashes in that URL. Three would be a relative path and would put the
database somewhere different depending on the working directory.

`PORT` is supplied by Render and `start.sh` reads it.

## Frontend, on Vercel

| Setting | Value |
| --- | --- |
| Root directory | `frontend` |
| Framework | Next.js (detected) |
| `API_URL` | the Render URL, e.g. `https://salary-api.onrender.com` |

No trailing slash: the rewrite appends `/api/:path*` and two slashes give a
404 that looks like a routing bug.

`API_URL` is deliberately not prefixed `NEXT_PUBLIC_`. That prefix would put
the address into the browser bundle, and the whole point of the rewrite is that
the browser does not need it.

Vercel does not use `frontend/Dockerfile` — it builds Next natively. The
Dockerfile exists for Compose and for anywhere else this might run.

## Running the whole thing locally

```bash
docker compose up --build
```

UI on <http://localhost:3000>, API docs on <http://localhost:8000/docs>. The
database lives in a named volume, so it survives `docker compose down`; remove
it with `docker compose down -v` to start from a fresh seed.

Compose passes `API_URL=http://api:8000` — the service name, not `localhost`,
because inside the network `localhost` is the container itself.

## Known limitations

**Cold starts.** A free Render instance sleeps after about 15 minutes idle, and
the first request afterwards waits roughly 50 seconds for it to wake. The
frontend shows its loading state rather than an error, but it is slow enough to
look broken. Worth a warning next to any link you hand someone.

**One instance only.** SQLite serialises writes and lives on the container's
own filesystem, so this cannot be scaled horizontally as it stands. See
[ADR 0004](adr/0004-sqlite-as-datastore.md); the move is to Postgres, which is
a connection string and a migration run.

**No authentication.** The deployed app is open to anyone with the URL. The
data is synthetic, which is the only reason that is acceptable — it is the
largest gap between this and something you could put in front of a real HR
team, and it is recorded as a deliberate omission in
[the requirements](REQUIREMENTS.md).
