FROM python:3.12-slim AS builder

ENV POETRY_VERSION=2.1.1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl git \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/poetry-venv \
 && /opt/poetry-venv/bin/pip install --upgrade pip \
 && /opt/poetry-venv/bin/pip install "poetry==${POETRY_VERSION}"
ENV PATH="/opt/poetry-venv/bin:$PATH"

WORKDIR /app

COPY packages ./packages

COPY apps/payment-service/pyproject.toml apps/payment-service/poetry.lock ./apps/payment-service/

WORKDIR /app/apps/payment-service

RUN POETRY_VIRTUALENVS_IN_PROJECT=true \
    poetry install --no-root --only main -n

COPY apps/payment-service/src ./src
COPY apps/payment-service/alembic ./alembic
COPY apps/payment-service/alembic.ini ./alembic.ini
COPY apps/payment-service/README.md ./README.md

FROM python:3.12-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/packages ./packages
COPY --from=builder /app/apps/payment-service/pyproject.toml /app/apps/payment-service/poetry.lock ./apps/payment-service/

WORKDIR /app/apps/payment-service

COPY --from=builder /app/apps/payment-service/.venv ./.venv
COPY --from=builder /app/apps/payment-service/src ./src
COPY --from=builder /app/apps/payment-service/alembic ./alembic
COPY --from=builder /app/apps/payment-service/alembic.ini ./alembic.ini
COPY --from=builder /app/apps/payment-service/README.md ./README.md

ENV PATH="/app/apps/payment-service/.venv/bin:$PATH"

EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -fsS http://localhost:8002/docs >/dev/null || exit 1

CMD sh -c 'alembic upgrade head && uvicorn src.cli.fastapi_app:app --host 0.0.0.0 --port 8002'
