# 0005 — A shared key and a door, not an identity system

## Context

The application is deployed publicly so it can be looked at. Until now
anyone with the URL could read every salary in the organisation, which is
defensible for synthetic data and indefensible as a habit.

[The requirements](../REQUIREMENTS.md) name real authentication as the largest
gap in this build, and that has not changed. The question here is narrower:
what is the least machinery that stops the deployed demo being an open salary
endpoint, without pretending to be access control it is not.

## Decision

Two layers, each doing one thing.

**The API requires a shared key.** Every salary route depends on
`require_api_key`, which compares an `X-API-Key` header against `API_KEY` in
constant time. `/api/health` is exempt, because whatever watches the service
has no key and learns nothing from it but whether the process can reach its
database.

**The frontend is behind HTTP Basic.** `src/proxy.ts` challenges every
request except `/api/health`, checking `DEMO_USER` and `DEMO_PASSWORD`.
(Next 16 calls that file convention "proxy"; it is unrelated to the API
proxy below, which is an awkward collision of Next's naming and ours.)

The key never reaches the browser. Server components attach it themselves;
the browser's one API call — recording a pay change — goes to
`src/app/api/[...path]/route.ts`, which runs on the server and attaches the
key on its way upstream. That route handler replaced a `next.config` rewrite,
which could not add a header.

Locally both are unset and nothing is required. In production, missing
configuration is a start-up failure rather than a quiet opening: `Settings`
refuses to construct when `ENVIRONMENT=production` and `API_KEY` is empty.

## What this is not

It is not authentication. There are no users, so there is no such thing as
who did something. The pay history records that a change happened and when,
and cannot say who made it. For software whose entire subject is salary, that
is the honest limitation to name: a real deployment needs SSO, roles,
field-level permissions and an audit log that survives the people in it.

It is not authorisation either. Anyone through the door can do anything the
app can do, including recording pay changes.

## Trade-offs taken deliberately

**One shared secret, so there is nothing to revoke per person.** Rotating
means changing an environment variable in two places and redeploying. With
one intended audience that is proportionate; with ten it would not be.

**Basic auth has no sign-out.** The browser holds the credentials for the
session and there is no server-side state to end. A login page and a signed
cookie would fix that and cost a session mechanism, which is more moving
parts than a demo gate earns. It does buy something back: no auth cookie
means no CSRF surface, so there is no token machinery here either.

**Credentials travel on every request.** Both hosts are HTTPS-only, so this
is encrypted in transit. Over plain HTTP it would be indefensible.

**Failed-key throttling is per process.** `FailedAttempts` keeps recent
failures per client address in memory: ten inside a minute and that caller
gets 429s. Against this deployment — one instance — that makes guessing the
key pointless. It is not a distributed rate limiter. A second instance would
count separately, and a restart forgets everything. Doing better needs shared
state, and that is infrastructure the rest of the system does not need.

**The Basic auth gate is not rate limited at all.** It runs on Vercel's edge
across instances that share no memory, so the same in-process trick would be
a comfort rather than a control. Doing it properly needs a KV store. The
mitigation is a long generated password rather than a guessable one.

**CORS is configured but unused.** The browser only ever talks to the
frontend's origin, so no cross-origin request should ever reach the API, and
`CORS_ORIGINS` is empty in production. It stays in the configuration as a
second line: if someone later points a browser at the API directly, the
default is refusal rather than permission. Production also refuses to start
with `CORS_ORIGINS=*`, because that is the setting people reach for when
something is broken at five o'clock.

## Consequences

The deployment needs four variables set — `API_KEY` on both sides,
`DEMO_USER` and `DEMO_PASSWORD` on the frontend — and will not work without
them. [Deployment](../DEPLOYMENT.md) lists them.

The credentials are not in this repository and must not be. They are shared
with whoever needs to see the demo, out of band.
