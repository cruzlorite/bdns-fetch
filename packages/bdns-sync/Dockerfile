# bdns-sync with the BigQuery extra, plus the orchestration scripts.
# The default command runs the daily delta; override it freely:
#
#   docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync            # delta_load.sh
#   docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync \
#     bdns-sync sync sectores                                                      # any CLI command
#
# See docs/guides/deployment.md for running this on a schedule in the cloud.

# Dependencies come from poetry.lock, pinned by hash, so an image built today
# and one built next month run the same code. Poetry itself stays in this
# stage and out of the final image.
FROM python:3.12-slim AS requirements
RUN pip install --no-cache-dir poetry==2.2.1 poetry-plugin-export==1.9.0
WORKDIR /src
COPY pyproject.toml poetry.lock ./
RUN poetry export --only main --extras bigquery --format requirements.txt --output requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=requirements /src/requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

COPY scripts ./scripts

RUN useradd --create-home app
USER app

CMD ["/app/scripts/delta_load.sh"]
