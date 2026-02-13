FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements-prod.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-prod.txt

FROM python:3.11-slim

ARG APP_VERSION_COMMIT_SHA=unknown
ARG APP_VERSION_BUILD_TIME=unknown

ENV APP_VERSION_COMMIT_SHA=${APP_VERSION_COMMIT_SHA} \
    APP_VERSION_BUILD_TIME=${APP_VERSION_BUILD_TIME} \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /install /usr/local

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser \
    && mkdir -p /data && chown appuser:appuser /data

COPY bot/ bot/

USER appuser

EXPOSE 8080

CMD ["python", "-m", "bot"]
