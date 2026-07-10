# bdns-sync with the BigQuery extra, plus the orchestration scripts.
# The default command runs the daily delta; override it freely:
#
#   docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync            # delta_load.sh
#   docker run -e BDNS_SYNC_TARGET_URL=... ghcr.io/cruzlorite/bdns-sync \
#     bdns-sync sync sectores                                                      # any CLI command
#
# See docs/deployment.md for running this on a schedule in the cloud.
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY bdns ./bdns
RUN pip install --no-cache-dir .[bigquery]

COPY scripts ./scripts

RUN useradd --create-home app
USER app

CMD ["/app/scripts/delta_load.sh"]
