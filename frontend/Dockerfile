# syntax=docker/dockerfile:1

# Debian rather than Alpine, and Node 24 to match the toolchain the lockfile
# was written with.

FROM node:24-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./

# `npm install`, not `npm ci`, and not by preference. On Linux the dependency
# tree reaches @tailwindcss/oxide-wasm32-wasi, which needs @emnapi/core and
# @emnapi/runtime at versions npm will not write into the lock file from a
# Windows host -- regenerating it with --os=linux does not add them either.
# `npm ci` refuses to install anything at all in that state; `npm install`
# honours the lock file where it can and resolves the gap. The lock file is
# still committed, so this is not a free-for-all.
RUN npm install --no-audit --no-fund

FROM node:24-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next writes its rewrite rules at build time, so the backend address has to be
# known now rather than at start-up. See docs/DEPLOYMENT.md.
ARG API_URL=http://localhost:8000
ENV API_URL=$API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:24-slim AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN groupadd --gid 1001 web && useradd --uid 1001 --gid web --create-home web

# `output: standalone` emits a server bundle with only the dependencies it
# actually uses, so node_modules is not copied.
COPY --from=build --chown=web:web /app/.next/standalone ./
COPY --from=build --chown=web:web /app/.next/static ./.next/static
COPY --from=build --chown=web:web /app/public ./public

USER web
EXPOSE 3000
CMD ["node", "server.js"]
