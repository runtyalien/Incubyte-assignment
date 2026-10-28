FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Four slashes: an absolute path at /data, which is where a mounted disk
    # lands. Without one the file still works, it just does not survive a
    # restart -- see docs/DEPLOYMENT.md.
    DATABASE_URL=sqlite:////data/salary.db

WORKDIR /srv

# Dependencies first so they stay cached when only application code changes.
COPY pyproject.toml ./
COPY app ./app
# Retries and a longer timeout: image builds on a cold network drop
# packages often enough that the default single attempt fails the build.
RUN pip install --no-cache-dir --retries 5 --timeout 60 .

COPY alembic.ini ./
COPY migrations ./migrations
COPY start.sh ./
RUN chmod +x start.sh

# Run as nobody in particular rather than root.
RUN useradd --system --uid 1000 --create-home api \
    && mkdir -p /data \
    && chown -R api:api /data /srv
USER api

EXPOSE 8000
# Reads PORT because the platform chooses it -- Render hands the container
# its own, and a check pinned to 8000 would fail against a healthy server.
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=5 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/api/health')"

CMD ["./start.sh"]
