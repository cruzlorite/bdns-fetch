# bdns-tools with the BigQuery extra, to run bdns-sync on a schedule:
#
#   docker build -t bdns-sync .
#
# The default command runs the daily delta; override it freely:
#
#   docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync            # bdns-sync delta
#   docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync \
#     bdns-sync sync sectores                                                      # any CLI command
#
# See docs/sync/guides/deployment.md for running this on a schedule in the cloud.

# Dependencies come from uv.lock, pinned by hash, so an image built today and
# one built next month run the same code. uv itself stays in this stage and
# out of the final image.
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-default-groups --no-editable --extra bigquery

# The virtualenv keeps the path it was built at, so it is copied to the same
# one; its interpreter is the base image's, identical in both stages.
FROM python:3.12-slim
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home app
USER app

CMD ["bdns-sync", "delta"]
