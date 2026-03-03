# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY --from=builder /app/.venv /app/.venv
COPY sensor_generator/ ./sensor_generator/
COPY profiles/ ./profiles/

USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TARGET_URL="http://inference-api:8000" \
    PROFILE="normal" \
    SENSOR_ID="sensor-01"

CMD ["sh", "-c", "python -m sensor_generator --profile ${PROFILE} --url ${TARGET_URL} --sensor-id ${SENSOR_ID}"]
