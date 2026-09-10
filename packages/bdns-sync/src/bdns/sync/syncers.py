# SPDX-License-Identifier: GPL-3.0-or-later

"""One named `sync_*` function per synced entity.

Most are a one-liner delegating to the shared runners in
`bdns.sync.generic`. convocatorias, grandesbeneficiarios and
planesestrategicos have real multi-step logic, discovery plus per-code
detail calls, so they are longer, but they are still just functions in
this same file. None of them needs its own module.

Every `sync_*` function returns the sink's per-run counters: `fetched`,
`inserted`, `updated`, `touched`, `soft_deleted` and `skipped`.

Verified API behavior (date-parameter families, per-field registration
dates, retention depths) is documented once in docs/bdns-api-behavior.md.
Comments here only state which behavior applies, never the evidence.
"""

import logging
from collections.abc import Callable, Collection, Iterable, Iterator
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
from bdns.sync.policy import DEFAULT_POLICY, PayloadPolicy
from bdns.sync.sinks import Sink

__all__ = [
    "FULL_SYNCERS",
    "POLICIES",
    "SEARCH_SYNCERS",
    "discover_convocatoria_codes",
    "discover_pes_ids",
    "fetch_convocatoria_details",
    "fetch_pes_details",
    "fetch_pes_vigencias",
    "policy_for",
    "sync_actividades",
    "sync_ayudasestado_busqueda",
    "sync_beneficiarios",
    "sync_concesiones_busqueda",
    "sync_convocatorias",
    "sync_convocatorias_busqueda",
    "sync_finalidades",
    "sync_grandesbeneficiarios_anios",
    "sync_grandesbeneficiarios_busqueda",
    "sync_instrumentos",
    "sync_minimis_busqueda",
    "sync_objetivos",
    "sync_organos",
    "sync_organos_agrupacion",
    "sync_partidospoliticos_busqueda",
    "sync_planesestrategicos",
    "sync_planesestrategicos_busqueda",
    "sync_planesestrategicos_vigencia",
    "sync_regiones",
    "sync_reglamentos",
    "sync_sanciones_busqueda",
    "sync_sectores",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Sourced from bdns-fetch's own enums rather than hand-copied, so a new
# value added upstream (a new tipo de administración or ámbito) is picked
# up automatically instead of silently missing from the sweep.
ADMIN_TYPES: tuple[str, ...] = tuple(TipoAdministracion)
REGLAMENTOS_AMBITOS: tuple[str, ...] = tuple(Ambito)


# --- per-entity payload policies -----------------------------------------
#
# The measured rules for each entity, in one place. Every one is a finding,
# not a preference; the evidence is in
# docs/bdns-api-behavior.md#spurious-changes. Entities absent from this map
# take the default: store what arrived, hash all of it.
#
# This map is the definition, and the syncers read it through `policy_for`
# rather than naming a constant of their own. That is what keeps the policy
# a `--dry-run` prints identical to the one the sync applies.

POLICIES: dict[str, PayloadPolicy] = {
    # `beneficiario` oscillates: of the keys whose name changed more than
    # once, 67% return to a spelling they already had (ASOCIACIÓN ->
    # ASOCIACION -> ASOCIACIÓN), with `idPersona` unchanged throughout.
    # Hashing it re-versioned 58% of the table.
    "concesiones_busqueda": PayloadPolicy(hash_exclude=("beneficiario",)),
    # Same field, worse: the API returns a different spelling from one hour
    # to the next, six variants for one idPersona in eleven days, same
    # amount each time.
    "grandesbeneficiarios_busqueda": PayloadPolicy(hash_exclude=("beneficiario",)),
    # `sectores` is a list joined with "#" that comes back shuffled. The
    # separator is unambiguous here, so the pattern is just that character.
    "ayudasestado_busqueda": PayloadPolicy(delimited_lists={"sectores": "#"}),
    # `sectorActividad` is shuffled too, but ";" alone cannot split it:
    # several CNAE names carry a semicolon of their own ("Administración
    # Pública y defensa; Seguridad Social obligatoria"). The pattern splits
    # before the start of an element instead, leaving those whole.
    "minimis_busqueda": PayloadPolicy(
        delimited_lists={"sectorActividad": r";\s*(?=[A-Z0-9][A-Z0-9.]*\s*-\s)"}
    ),
}


def policy_for(endpoint: str) -> PayloadPolicy:
    """Return the rules that apply to one entity's records.

    Args:
        endpoint: Entity name, as used for its table.

    Returns:
        Its declared policy, or `DEFAULT_POLICY` if it declares none.
    """
    return POLICIES.get(endpoint, DEFAULT_POLICY)


def _skip_malformed(
    items: Iterator[Any], context: str, errors: Optional[list[dict[str, str]]] = None
) -> Iterator[dict]:
    """Yield only the well-formed records, logging and recording the rest.

    The backend sometimes returns an HTML error page instead of JSON for
    one specific record (see docs/bdns-api-behavior.md#api-issues).
    Skipping beats crashing a whole batch over one bad record.

    Args:
        items: Raw records from the client.
        context: What was being fetched, recorded with each skip so a bad
            record can be traced back to its call.
        errors: If given, each skip appends a `{"context", "content"}`
            dict to it. The caller passes that list to the sink as
            `skipped=`, which persists it to the error log.

    Yields:
        The records that were dicts.
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
    """Sync the `sectores` catalog: one call, full reconciliation every run."""
    return sync_full_catalog(sink, client, "sectores", "fetch_sectores", ("id",))


def sync_actividades(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync the `actividades` catalog: one call, full reconciliation every run."""
    return sync_full_catalog(sink, client, "actividades", "fetch_actividades", ("id",))


def sync_finalidades(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync the `finalidades` catalog: one call, full reconciliation every run."""
    return sync_full_catalog(sink, client, "finalidades", "fetch_finalidades", ("id",))


def sync_beneficiarios(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync the `beneficiarios` catalog: one call, full reconciliation every run."""
    return sync_full_catalog(sink, client, "beneficiarios", "fetch_beneficiarios", ("id",))


def sync_instrumentos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync the `instrumentos` catalog: one call, full reconciliation every run."""
    return sync_full_catalog(sink, client, "instrumentos", "fetch_instrumentos", ("id",))


def sync_objetivos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync the `objetivos` catalog: one call, full reconciliation every run."""
    return sync_full_catalog(sink, client, "objetivos", "fetch_objetivos", ("id",))


def sync_regiones(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync the `regiones` catalog: one call, full reconciliation every run.

    Tree-shaped, but still a single call. Unlike organos*, there is no
    idAdmon sweep here.
    """
    return sync_full_catalog(sink, client, "regiones", "fetch_regiones", ("id",))


def sync_sanciones_busqueda(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync `sanciones_busqueda`: one call, full reconciliation every run.

    The source exposes no id field, so the natural key is a best-effort
    composite of three fields.
    """
    return sync_full_catalog(
        sink,
        client,
        "sanciones_busqueda",
        "fetch_sanciones_busqueda",
        ("numeroConvocatoria", "sancionado", "fechaSancion"),
    )


# --- swept entities (sweep a param, merge into one table before diffing) --


def sync_organos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync `organos`, sweeping `idAdmon` across every administration type."""
    return sync_swept_catalog(
        sink, client, "organos", "fetch_organos", "idAdmon", ADMIN_TYPES, ("idAdmon", "id")
    )


def sync_organos_agrupacion(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync `organos_agrupacion`, sweeping `idAdmon` as `sync_organos` does."""
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
    """Sync `reglamentos`, sweeping `ambito` across every scope."""
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
# field was confirmed live per entity; see
# docs/bdns-api-behavior.md#windowed-deletions.


def sync_concesiones_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    """Sync `concesiones_busqueda` for a reg-date window or a backfill range.

    The largest entity by far. `beneficiario` is excluded from the hash;
    see `POLICIES`.

    Args:
        sink: Where the rows are applied.
        client: The BDNS API client.
        window: A cascade window name, or None.
        since: First day of an explicit backfill range. Wins over
            `window`.
        until: Last day of that range. Defaults to yesterday.

    Returns:
        The sink's per-run counters.
    """
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
        policy=policy_for("concesiones_busqueda"),
    )


def sync_ayudasestado_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    """Sync `ayudasestado_busqueda` for a reg-date window or a backfill range.

    `sectores` is a "#"-joined list that comes back shuffled and is
    sorted before hashing; see `POLICIES`. Arguments are those of
    `sync_concesiones_busqueda`.
    """
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
        policy=policy_for("ayudasestado_busqueda"),
    )


def sync_minimis_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    """Sync `minimis_busqueda` for a reg-date window or a backfill range.

    `sectorActividad` is a ";"-joined list that comes back shuffled and
    is sorted before hashing; see `POLICIES`. Arguments are those of
    `sync_concesiones_busqueda`.
    """
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
        policy=policy_for("minimis_busqueda"),
    )


def sync_partidospoliticos_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    """Sync `partidospoliticos_busqueda` for a window or a backfill range.

    No `reg_date_field`: this payload carries no registration-date field,
    confirmed live and unlike what the official documentation implies, so
    windowed deletion detection is not possible here. See
    docs/bdns-api-behavior.md#windowed-deletions. Arguments are those of
    `sync_concesiones_busqueda`.
    """
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
# Details in docs/bdns-api-behavior.md#upper-bound.


def sync_convocatorias_busqueda(
    sink: Sink,
    client: BDNSClient,
    window: Optional[str] = None,
    *,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> dict[str, int]:
    """Sync `convocatorias_busqueda`, the discovery listing, as its own table.

    It gets its own run in `_sync_runs`, so it can be synced, fail and be
    retried independently of the expensive detail phase.

    The listing is not a substitute for the `convocatorias` detail table:
    it carries only 10 of the ~30 detail fields, and its hash changing,
    or not changing, says nothing about detail-only fields. Never use it
    to skip a detail fetch. Arguments are those of
    `sync_concesiones_busqueda`.
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
    """Find every `numeroConvocatoria` registered in `[start, end]`.

    `fechaHasta` is inclusive, so `chunk_end` is sent as-is. It must not
    go through `to_api_upper_bound`, which would over-fetch one day.

    Args:
        client: The BDNS API client.
        start: First day of the range, inclusive.
        end: Last day of the range, inclusive.

    Returns:
        The discovered codes. Each one costs a detail call later.
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
    keys: Collection[Any],
    fetch_single: Callable[[Any], Iterable[Any]],
    context_for: Callable[[Any], str],
    errors: Optional[list[dict[str, str]]],
    label: str,
    transform: Optional[Callable[[Any, dict], dict]] = None,
    max_workers: int = DETAIL_WORKERS,
) -> Iterator[dict]:
    """Fetch one detail record per discovered key, in parallel.

    Each detail response is a single record, so the client's page-level
    parallelism never kicks in and a sequential loop stays far below the
    10 req/s budget just from latency. `rate_limited_map` spreads request
    starts so the pool can approach the limit without bursting past it.

    Every step of the two-step syncs goes through here.

    Args:
        keys: The discovered keys. Sized, so progress can be logged.
        fetch_single: Called with one key, returns that key's records.
        context_for: Called with one key, returns the label recorded
            against any malformed record from it.
        errors: Malformed-record descriptors are appended here.
            `_skip_malformed` runs on the consuming thread, so this list
            is only ever touched from one thread.
        label: Name used in the progress log, written every 500 keys.
        transform: Called as `transform(key, item)` on each surviving
            record. Used where an endpoint does not echo its own key
            back.
        max_workers: Size of the detail pool.

    Yields:
        The detail records, in completion order.
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
    """Fetch the full detail record for each discovered convocatoria code.

    One real API call per code, paced and parallel; see `_fetch_details`.
    This is the costly step of the two-step discover-then-detail flow.
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
    """Sync `convocatorias`: discover codes for the range, then fetch detail.

    The detail record is what gets versioned, under `codigoBDNS`.
    Arguments are those of `sync_concesiones_busqueda`.
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
    """Sync `grandesbeneficiarios_anios`, the catalog of queryable years."""
    return sync_full_catalog(
        sink,
        client,
        "grandesbeneficiarios_anios",
        "fetch_grandesbeneficiarios_anios",
        ("id",),
    )


def sync_grandesbeneficiarios_busqueda(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync `grandesbeneficiarios_busqueda`, sweeping the years it declares.

    The years come from `grandesbeneficiarios_anios` at call time rather
    than from a hardcoded list, per the official documentation.

    `beneficiario` is left out of the content hash: the API returns a
    different spelling of the same name on almost every call, so hashing
    it re-versioned half the table daily. Identity is `idPersona`, and
    the name is still stored; it just no longer counts as a change. See
    docs/bdns-api-behavior.md#spurious-changes.
    """
    anios = [item["id"] for item in client.fetch_grandesbeneficiarios_anios()]
    return sink.sync_full(
        "grandesbeneficiarios_busqueda",
        all_pages(client.fetch_grandesbeneficiarios_busqueda)(anios=anios),
        ("idPersona", "ejercicio"),
        policy=policy_for("grandesbeneficiarios_busqueda"),
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
    """Sync `planesestrategicos_busqueda`, which doubles as the discovery step."""
    return sync_full_catalog(
        sink,
        client,
        "planesestrategicos_busqueda",
        "fetch_planesestrategicos_busqueda",
        ("id",),
    )


def discover_pes_ids(client: BDNSClient) -> set[int]:
    """Return every `idPES` in the listing, the key for both detail tables."""
    return {item["id"] for item in all_pages(client.fetch_planesestrategicos_busqueda)()}


def _tag_id_pes(id_pes: int, item: dict) -> dict:
    """Tag `idPES` onto a record, since neither detail nor vigencia echoes it."""
    return {**item, "idPES": id_pes}


def fetch_pes_details(
    client: BDNSClient, ids: set[int], errors: Optional[list[dict[str, str]]] = None
) -> Iterator[dict]:
    """Fetch one detail record per `idPES`, tagging `idPES` onto each one."""
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
    """Fetch one validity record per `idPES`, tagging `idPES` onto each one."""
    return _fetch_details(
        ids,
        lambda id_pes: client.fetch_planesestrategicos_vigencia(idPES=id_pes),
        lambda id_pes: f"planesestrategicos_vigencia idPES={id_pes}",
        errors,
        "planesestrategicos_vigencia",
        transform=_tag_id_pes,
    )


def sync_planesestrategicos(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync `planesestrategicos`: discover every idPES, then fetch its detail."""
    ids = discover_pes_ids(client)
    errors: list[dict[str, str]] = []

    return sink.sync_full(
        "planesestrategicos",
        fetch_pes_details(client, ids, errors),
        ("idPES",),
        skipped=errors,
    )


def sync_planesestrategicos_vigencia(sink: Sink, client: BDNSClient) -> dict[str, int]:
    """Sync `planesestrategicos_vigencia`: same discovery, validity records."""
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
