FROM node:26-bookworm-slim AS builder

WORKDIR /app/

RUN apt-get update && apt-get install -y python3 python-is-python3 curl bash gcc build-essential && rm -rf /var/lib/apt/lists/*

# Install uv for Python dependency syncing and build_assets runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY app/ .

COPY .env.template .

RUN uv venv /opt/venv

RUN uv sync --frozen --no-install-project --active

RUN cp .env.template .env

RUN python bin/build_assets

RUN python bin/generate_vapid_keys



FROM python:3.14-slim AS runner

WORKDIR /app/

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    gcc \
    build-essential \
    gettext \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/\#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/\#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/
ENV PYTHONUNBUFFERED=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/\#caching
ENV UV_LINK_MODE=copy

# Install dependencies using uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/\#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=app/uv.lock,target=uv.lock \
    --mount=type=bind,source=app/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --active

# Copy application code and built assets from the builder stage
COPY app/ .
COPY --from=builder /app/assets ./assets
COPY --from=builder /app/credentials ./credentials
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

RUN chmod +x /app/docker-entrypoint.sh

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${APP_PORT:-5555}/health || exit 1'

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["bin/run_server"]
