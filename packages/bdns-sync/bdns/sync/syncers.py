# SPDX-License-Identifier: GPL-3.0-or-later

"""One named `sync_*` function per synced entity.
Most are a one-liner delegating to the shared runners in `bdns.sync.generic`.
convocatorias, grandesbeneficiarios, and planesestrategicos have real
multi-step logic (discovery plus per-code detail calls), so they're longer,
but they're still just functions in this same file. None of them needs its
own module.

Verified API behavior (date-parameter families, per-field registration
dates, retention depths) is documented once in docs/bdns-api-behavior.md;
comments here only state which behavior applies, not the evidence.
"""

import logging
from collections.abc import Iterator
from datetime import date
from typing import Any, Optional

from bdns.fetch import BDNSClient, TipoAdministracion
from bdns.fetch.types import Ambito
from bdns.sync.generic import (
    all_pages,
    iter_date_chunks,
    resolve_when,
    sync_full_catalog,
    sync_search_range,
    sync_search_range_inclusive,
    sync_swept_catalog,
)
from bdns.sync.pipeline import rate_limited_map
from bdns.sync.sinks import Sink

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Sourced from bdns-fetch's own enums rather than hand-copied, so a new
# value added upstream (a new tipo de administración or ámbito) is picked
# up automatically instead of silently missing from the sweep.
ADMIN_TYPES: tuple[str, ...] = tuple(TipoAdministracion)
REGLAMENTOS_AMBITOS: tuple[str, ...] = tuple(Ambito)


def _skip_malformed(
    items: Iterator[Any], context: str, errors: Optional[list[dict[str, str]]] = None
) -> Iterator[dict]:
    """Individual records can come back malformed: the backend sometimes
    returns an HTML error page instead of JSON for one specific record (see
    section 8 of docs/bdns-api-behavior.md). Skip and log rather than
    crashing the whole batch over one bad record.

    When `errors` is given, each skip appends a `{"context", "content"}`
    dict to it; the caller passes that list to the sink (`skipped=`), which
    persists it to its error log.
    """
    for item in items:
        if not isinstance(item, dict):
            content = str(item)[:200]
            logger.warning("skipping malformed record (%s): %r", context, content)
            if errors is not None:
                errors.append({"context": context, "content": content})
            continue
        yield item


# --- full-replace-every-run entities (single call, natural key `id`) ------


def sync_sectores(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(sink, client, "sectores", "fetch_sectores", ("id",))


def sync_actividades(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(sink, client, "actividades", "fetch_actividades", ("id",))


def sync_finalidades(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(sink, client, "finalidades", "fetch_finalidades", ("id",))


def sync_beneficiarios(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(sink, client, "beneficiarios", "fetch_beneficiarios", ("id",))


def sync_instrumentos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(sink, client, "instrumentos", "fetch_instrumentos", ("id",))


def sync_objetivos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(sink, client, "objetivos", "fetch_objetivos", ("id",))


def sync_convocatorias_ultimas(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(
        sink, client, "convocatorias_ultimas", "fetch_convocatorias_ultimas", ("id",)
    )


def sync_regiones(sink: Sink, client: BDNSClient) -> dict[str, int]:
    # Tree-shaped, but still a single call. Unlike organos*, there's no idAdmon sweep here.
    return sync_full_catalog(sink, client, "regiones", "fetch_regiones", ("id",))


def sync_sanciones_busqueda(sink: Sink, client: BDNSClient) -> dict[str, int]:
    # There's no real id field in the source, so this is a best-effort composite of 3 fields.
    return sync_full_catalog(
        sink,
        client,
        "sanciones_busqueda",
        "fetch_sanciones_busqueda",
        ("numeroConvocatoria", "sancionado", "fechaSancion"),
    )


# --- swept entities (sweep a param, merge into one table before diffing) --


def sync_organos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_swept_catalog(
        sink, client, "organos", "fetch_organos", "idAdmon", ADMIN_TYPES, ("idAdmon", "id")
    )


def sync_organos_agrupacion(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_swept_catalog(
        sink,
        client,
        "organos_agrupacion",
        "fetch_organos_agrupacion",
        "idAdmon",
        ADMIN_TYPES,
        ("idAdmon", "id"),
    )


def sync_reglamentos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_swept_catalog(
        sink,
        client,
        "reglamentos",
        "fetch_reglamentos",
        "ambito",
        REGLAMENTOS_AMBITOS,
        ("ambito", "id"),
    )


# --- big search entities (reg-date incremental) --------------------------
#
# Each takes either a cascade `window` name (the daily/weekly/monthly/annual
# re-verification passes) or an explicit `since`/`until` range (a historical
# backfill). `resolve_when` collapses the two into one (start, end, run_type)
# so the engine treats a one-day window and a ten-year backfill identically.
#
# `reg_date_field` names the payload's own registration-date field, which
# enables window-scoped deletion detection (see `Sink.sync_window`). Each
# field was confirmed live per entity; see section 5 of docs/bdns-api-behavior.md.


def sync_concesiones_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    start, end, run_type = resolve_when(window, since, until)
    return sync_search_range(
        sink,
        client,
        "concesiones_busqueda",
        "fetch_concesiones_busqueda",
        ("id",),
        start,
        end,
        run_type,
        reg_date_field="fechaAlta",
    )


def sync_ayudasestado_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    start, end, run_type = resolve_when(window, since, until)
    return sync_search_range(
        sink,
        client,
        "ayudasestado_busqueda",
        "fetch_ayudasestado_busqueda",
        ("idConcesion",),
        start,
        end,
        run_type,
        reg_date_field="fechaAlta",
    )


def sync_minimis_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    start, end, run_type = resolve_when(window, since, until)
    return sync_search_range(
        sink,
        client,
        "minimis_busqueda",
        "fetch_minimis_busqueda",
        ("idConcesion",),
        start,
        end,
        run_type,
        reg_date_field="fechaRegistro",
    )


def sync_partidospoliticos_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    # No `reg_date_field`: this payload carries no registration-date field
    # (confirmed live, unlike what the official doc implies), so windowed
    # deletion detection isn't possible here. See section 5 of
    # docs/bdns-api-behavior.md.
    start, end, run_type = resolve_when(window, since, until)
    return sync_search_range(
        sink,
        client,
        "partidospoliticos_busqueda",
        "fetch_partidospoliticos_busqueda",
        ("id",),
        start,
        end,
        run_type,
    )


# --- convocatorias: two-step discover-then-detail -------------------------
#
# `convocatorias_busqueda` doubles as the discovery step: it yields
# `numeroConvocatoria` codes for a window, and each code then costs one real
# detail call (`fetch_convocatorias(numConv=X)`). The detail record is what
# gets versioned into the `convocatorias` table, under `codigoBDNS`, the
# same value as the listing's `numeroConvocatoria` (confirmed live).
#
# Both endpoints use the `fechaDesde`/`fechaHasta` date-parameter family
# (INCLUSIVE upper bound), not the `fechaRegInicio`/`fechaRegFin` family
# (exclusive) the four big search endpoints use. That is why this section
# calls `sync_search_range_inclusive` and never `to_api_upper_bound`.
# Details in section 2 of docs/bdns-api-behavior.md.


def sync_convocatorias_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    """The discovery listing stored as its own incremental table, with its
    own run in `_sync_runs`, so it can be synced (and fail, and be retried)
    independently of the expensive detail phase.

    The listing is NOT a substitute for the `convocatorias` detail table: it
    carries only 10 of the ~30 detail fields, and its hash changing (or not)
    says nothing about detail-only fields. Never use it to skip a detail
    fetch.
    """
    start, end, run_type = resolve_when(window, since, until)
    return sync_search_range_inclusive(
        sink,
        client,
        "convocatorias_busqueda",
        "fetch_convocatorias_busqueda",
        ("numeroConvocatoria",),
        start,
        end,
        run_type,
        reg_date_field="fechaRecepcion",
    )


def discover_convocatoria_codes(client: BDNSClient, start: date, end: date) -> set[str]:
    """Find every `numeroConvocatoria` registered in [start, end] (inclusive).

    `fechaHasta` is inclusive, so `chunk_end` is sent as-is. It must NOT
    go through `to_api_upper_bound`; that would over-fetch one extra day.
    """
    codes: set[str] = set()
    for chunk_start, chunk_end in iter_date_chunks(start, end):
        for item in all_pages(client.fetch_convocatorias_busqueda)(
            fechaDesde=chunk_start, fechaHasta=chunk_end
        ):
            codes.add(item["numeroConvocatoria"])
    return codes


DETAIL_WORKERS = 8

# Minimum gap between request starts across all detail workers. The official
# limit is 10 req/s per IP. The client's token bucket keeps the average under
# that, but the bucket starts full, so a fresh worker pool fires its first
# requests all at once and the server 429s the burst (confirmed live). The
# same server accepts a sustained 9.8 req/s with zero 429s when starts are
# spaced; 105ms keeps a small margin under the cap.
DETAIL_SPACING_SECONDS = 0.105


def _fetch_details(
    keys,
    fetch_single,
    context_for,
    errors: Optional[list[dict[str, str]]],
    label: str,
    transform=None,
    max_workers: int = DETAIL_WORKERS,
) -> Iterator[dict]:
    """Fetch one detail record per discovered key, in parallel.

    Each detail response is a single record, so the client's page-level
    parallelism never kicks in, and a sequential loop stays far below the
    10 req/s budget just from latency. `rate_limited_map` spreads request
    starts (`DETAIL_SPACING_SECONDS`) so the pool can approach the limit
    without bursting past it.

    Every step of the two-step syncs goes through here: convocatorias,
    planesestrategicos, and planesestrategicos_vigencia. `_skip_malformed`
    runs on the consuming thread, so `errors` is only touched from one
    thread. `transform(key, item)`, if given, tags each surviving item
    (some endpoints don't echo their own key back). Progress is logged
    every 500 keys.
    """
    total = len(keys)
    completed = 0
    for key, items in rate_limited_map(
        keys, lambda key: list(fetch_single(key)), DETAIL_SPACING_SECONDS, max_workers
    ):
        completed += 1
        if completed % 500 == 0 or completed == total:
            logger.info("%s: detail %d/%d keys", label, completed, total)
        for item in _skip_malformed(items, context_for(key), errors):
            yield transform(key, item) if transform else item


def fetch_convocatoria_details(
    client: BDNSClient,
    codes: set[str],
    errors: Optional[list[dict[str, str]]] = None,
    max_workers: int = DETAIL_WORKERS,
) -> Iterator[dict]:
    """One real API call per code, paced and parallel (see `_fetch_details`).
    This is the costly step in the two-step discover-then-detail flow.
    """
    return _fetch_details(
        codes,
        lambda code: client.fetch_convocatorias(numConv=code),
        lambda code: f"convocatorias numConv={code}",
        errors,
        "convocatorias",
        max_workers=max_workers,
    )


def sync_convocatorias(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    """Two-step: discover codes for the reg-date range, then fetch full
    detail per code and apply incrementally.
    """
    start, end, run_type = resolve_when(window, since, until)
    codes = discover_convocatoria_codes(client, start, end)
    errors: list[dict[str, str]] = []

    return sink.sync_window(
        "convocatorias",
        fetch_convocatoria_details(client, codes, errors),
        ("codigoBDNS",),
        window_start=start,
        window_end=end,
        run_type=run_type,
        reg_date_field="fechaRecepcion",
        skipped=errors,
    )


# --- grandesbeneficiarios: two tables for one entity ----------------------
#
# `_anios` is a trivial flat catalog (the valid years to query). `_busqueda`
# is the actual data, but it needs `anios` swept dynamically from `_anios`
# first, rather than from a hardcoded year list, per the doc. That's why
# this doesn't reduce to a plain sync_full_catalog call.


def sync_grandesbeneficiarios_anios(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(
        sink,
        client,
        "grandesbeneficiarios_anios",
        "fetch_grandesbeneficiarios_anios",
        ("id",),
    )


def sync_grandesbeneficiarios_busqueda(sink: Sink, client: BDNSClient) -> dict[str, int]:
    anios = [item["id"] for item in client.fetch_grandesbeneficiarios_anios()]
    return sink.sync_full(
        "grandesbeneficiarios_busqueda",
        all_pages(client.fetch_grandesbeneficiarios_busqueda)(anios=anios),
        ("idPersona", "ejercicio"),
    )


# --- planesestrategicos: three tables for one entity ----------------------
#
# `_busqueda` is a trivial full-crawl catalog (~2,000 rows) that doubles as
# the discovery step for the other two: detail and validity, each looked up
# by idPES and looped over the full discovered set every run. No cascading
# windows are needed; this volume is cheap enough (same reasoning as
# convocatorias, just smaller). Neither the detail nor the vigencia response
# echoes back idPES, confirmed live, so it's tagged onto the payload
# explicitly, the same pattern used for organos' idAdmon tag.


def sync_planesestrategicos_busqueda(sink: Sink, client: BDNSClient) -> dict[str, int]:
    return sync_full_catalog(
        sink,
        client,
        "planesestrategicos_busqueda",
        "fetch_planesestrategicos_busqueda",
        ("id",),
    )


def discover_pes_ids(client: BDNSClient) -> set[int]:
    return {item["id"] for item in all_pages(client.fetch_planesestrategicos_busqueda)()}


def _tag_id_pes(id_pes, item):
    # Neither detail nor vigencia echoes idPES back, confirmed live.
    return {**item, "idPES": id_pes}


def fetch_pes_details(
    client: BDNSClient, ids: set[int], errors: Optional[list[dict[str, str]]] = None
) -> Iterator[dict]:
    return _fetch_details(
        ids,
        lambda id_pes: client.fetch_planesestrategicos(idPES=id_pes),
        lambda id_pes: f"planesestrategicos idPES={id_pes}",
        errors,
        "planesestrategicos",
        transform=_tag_id_pes,
    )


def fetch_pes_vigencias(
    client: BDNSClient, ids: set[int], errors: Optional[list[dict[str, str]]] = None
) -> Iterator[dict]:
    return _fetch_details(
        ids,
        lambda id_pes: client.fetch_planesestrategicos_vigencia(idPES=id_pes),
        lambda id_pes: f"planesestrategicos_vigencia idPES={id_pes}",
        errors,
        "planesestrategicos_vigencia",
        transform=_tag_id_pes,
    )


def sync_planesestrategicos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    ids = discover_pes_ids(client)
    errors: list[dict[str, str]] = []

    return sink.sync_full(
        "planesestrategicos",
        fetch_pes_details(client, ids, errors),
        ("idPES",),
        skipped=errors,
    )


def sync_planesestrategicos_vigencia(sink: Sink, client: BDNSClient) -> dict[str, int]:
    ids = discover_pes_ids(client)
    errors: list[dict[str, str]] = []

    return sink.sync_full(
        "planesestrategicos_vigencia",
        fetch_pes_vigencias(client, ids, errors),
        ("idPES",),
        skipped=errors,
    )


# --- registries consumed directly by cli.py --------------------------------

# endpoint name -> sync(sink, client)
FULL_SYNCERS = {
    "sectores": sync_sectores,
    "actividades": sync_actividades,
    "finalidades": sync_finalidades,
    "beneficiarios": sync_beneficiarios,
    "instrumentos": sync_instrumentos,
    "objetivos": sync_objetivos,
    "convocatorias_ultimas": sync_convocatorias_ultimas,
    "regiones": sync_regiones,
    "sanciones_busqueda": sync_sanciones_busqueda,
    "organos": sync_organos,
    "organos_agrupacion": sync_organos_agrupacion,
    "reglamentos": sync_reglamentos,
    "grandesbeneficiarios_anios": sync_grandesbeneficiarios_anios,
    "grandesbeneficiarios_busqueda": sync_grandesbeneficiarios_busqueda,
    "planesestrategicos_busqueda": sync_planesestrategicos_busqueda,
    "planesestrategicos": sync_planesestrategicos,
    "planesestrategicos_vigencia": sync_planesestrategicos_vigencia,
}

# endpoint name -> sync(sink, client, window=None, *, since=None, until=None)
SEARCH_SYNCERS = {
    "concesiones_busqueda": sync_concesiones_busqueda,
    "ayudasestado_busqueda": sync_ayudasestado_busqueda,
    "minimis_busqueda": sync_minimis_busqueda,
    "partidospoliticos_busqueda": sync_partidospoliticos_busqueda,
    "convocatorias_busqueda": sync_convocatorias_busqueda,
    # Two-step discover-then-detail, but same signature and same reg-date
    # window semantics as the plain search endpoints, so same registry.
    "convocatorias": sync_convocatorias,
}
