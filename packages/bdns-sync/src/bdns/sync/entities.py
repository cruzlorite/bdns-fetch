# SPDX-License-Identifier: MIT

"""Every synced entity, declared once.

An [`Entity`][bdns.sync.entities.Entity] says everything the engine needs
to know about one table: how its rows are fetched, what identifies a
record, whether a run covers the whole entity or a registration-date
window, which payload rules apply, and how far back its history goes. The
CLI, the delta and backfill plans, `--dry-run` and the documentation all
read the same registry, [`ENTITIES`][bdns.sync.entities.ENTITIES], so they
cannot disagree about which entities exist or how they behave.

There are two kinds:

- **full**: each run fetches the entity's complete current state, so a
  key missing from it was withdrawn and its version is closed.
- **windowed**: each run fetches the records registered in a date range.
  Absence proves nothing, except for entities that expose their own
  registration date, where a stored row inside the same range that is
  missing from the batch is closed
  ([why](../../explanation/sync-behavior.md#windowed-deletions)).

Measured facts about the API (date semantics, retention, spurious
changes) are documented by bdns-fetch; each rule here links to them.
"""

import logging
from collections.abc import Callable, Collection, Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from bdns.fetch import Ambito, BDNSClient, TipoAdministracion
from bdns.fetch.dates import period_range, registration_range, split_range
from bdns.sync.pipeline import bounded_map
from bdns.sync.policy import DEFAULT_POLICY, PayloadPolicy
from bdns.sync.sinks import Sink, SyncStats
from bdns.sync.windows import resolve_when

__all__ = [
    "ENTITIES",
    "Entity",
    "full_entities",
    "get_entity",
    "sync_entity",
    "windowed_entities",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

Errors = list[dict[str, str]]
FullRows = Callable[[BDNSClient, Errors], Iterable[dict]]
WindowRows = Callable[[BDNSClient, date, date, Errors], Iterable[dict]]


@dataclass(frozen=True)
class Entity:
    """One synced entity, which is also one table.

    Attributes:
        name: Entity and table name, the API path with underscores.
        kind: `"full"` or `"windowed"`; see the module docstring.
        key_fields: Payload fields forming the natural key, in order.
        rows: Produces the records. For a full entity it is called as
            `rows(client, errors)`; for a windowed one, as
            `rows(client, first, last, errors)` with an inclusive range.
            Malformed records it can attribute to a key go to `errors`.
        reg_date_field: Payload field with the record's own registration
            date. Enables deletion detection on windowed runs.
        policy: Rules applied to each record before storing and hashing.
        history_start: First day worth backfilling (windowed entities).
            Earlier days return empty weeks; see the retention notes.
    """

    name: str
    kind: Literal["full", "windowed"]
    key_fields: tuple[str, ...]
    rows: Callable[..., Iterable[dict]]
    reg_date_field: str | None = None
    policy: PayloadPolicy = DEFAULT_POLICY
    history_start: date | None = None


# --- row sources -----------------------------------------------------------


def catalog(method: str) -> FullRows:
    """Rows of a full entity fetched with one call."""

    def rows(client: BDNSClient, errors: Errors) -> Iterable[dict]:
        return getattr(client, method)()

    return rows


def swept(method: str, param: str, values: Collection[str]) -> FullRows:
    """Rows of a full entity fetched once per value of `param`, merged.

    All values are merged into one batch before reconciling: reconciling
    per value would close the other values' rows as missing. The API does
    not echo `param` back, so it is tagged onto each record, and belongs in
    the natural key.
    """

    def rows(client: BDNSClient, errors: Errors) -> Iterator[dict]:
        fetch = getattr(client, method)
        for value in values:
            for item in fetch(**{param: value}):
                yield {**item, param: value}

    return rows


def registration_window(method: str) -> WindowRows:
    """Rows registered in a range, by `fechaRegInicio`/`fechaRegFin`, a week at a time."""

    def rows(client: BDNSClient, first: date, last: date, errors: Errors) -> Iterator[dict]:
        fetch = getattr(client, method)
        for start, end in split_range(first, last):
            logger.info("%s: chunk [%s .. %s]", method, start, end)
            yield from fetch(**registration_range(start, end))

    return rows


def period_window(method: str) -> WindowRows:
    """Rows in a range, by `fechaDesde`/`fechaHasta`, a week at a time."""

    def rows(client: BDNSClient, first: date, last: date, errors: Errors) -> Iterator[dict]:
        fetch = getattr(client, method)
        for start, end in split_range(first, last):
            logger.info("%s: chunk [%s .. %s]", method, start, end)
            yield from fetch(**period_range(start, end))

    return rows


# --- discover-then-detail sources --------------------------------------------

DETAIL_WORKERS = 8
"""Threads fetching detail records. The client spaces their requests, so this
only needs to cover latency."""


def _skip_malformed(items: Iterable[Any], context: str, errors: Errors) -> Iterator[dict]:
    """Yield only the records that are JSON objects, recording the rest.

    The backend sometimes returns an HTML error page instead of JSON for
    one specific record
    ([known issue](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#api-issues)).
    Skipping it beats failing a batch of thousands over one record; the
    reject ceiling still fails the run if skips stop looking like noise.
    """
    for item in items:
        if isinstance(item, dict):
            yield item
        else:
            content = str(item)[:200]
            logger.warning("skipping malformed record (%s): %r", context, content)
            errors.append({"context": context, "content": content})


def _details(
    keys: Collection[Any],
    fetch_one: Callable[[Any], Iterable[Any]],
    label: str,
    key_param: str,
    errors: Errors,
    tag: str | None = None,
) -> Iterator[dict]:
    """Fetch the detail records of every discovered key, in parallel.

    Args:
        keys: The discovered keys.
        fetch_one: Returns one key's records.
        label: Name used in logs and in recorded skips.
        key_param: Name of the key's API parameter, so a recorded skip
            reads like the call that produced it (`numConv=...`).
        errors: Malformed records are appended here, from this thread.
        tag: If given, the key is added to each record under this name,
            for endpoints that do not echo their own key back.

    Yields:
        Detail records, in completion order.
    """
    total = len(keys)
    for done, (key, items) in enumerate(
        bounded_map(keys, lambda key: list(fetch_one(key)), DETAIL_WORKERS), start=1
    ):
        if done % 500 == 0 or done == total:
            logger.info("%s: detail %d/%d keys", label, done, total)
        for item in _skip_malformed(items, f"{label} {key_param}={key}", errors):
            yield {**item, tag: key} if tag else item


def convocatoria_details(
    client: BDNSClient, first: date, last: date, errors: Errors
) -> Iterator[dict]:
    """Detail records of the calls received in a range.

    The listing (`convocatorias_busqueda`) discovers the codes; each code
    then costs one detail call, and the detail record is what is stored.
    The listing carries only a third of the detail's fields, so its hash
    says nothing about whether the detail changed.
    """
    codes = {
        item["numeroConvocatoria"]
        for start, end in split_range(first, last)
        for item in client.fetch_convocatorias_busqueda(**period_range(start, end))
    }
    return _details(
        codes,
        lambda code: client.fetch_convocatorias(numConv=code),
        "convocatorias",
        "numConv",
        errors,
    )


def grandesbeneficiarios(client: BDNSClient, errors: Errors) -> Iterable[dict]:
    """Large beneficiaries for every year the API declares, read at run time."""
    anios = [item["id"] for item in client.fetch_grandesbeneficiarios_anios()]
    return client.fetch_grandesbeneficiarios_busqueda(anios=anios)


def _pes_ids(client: BDNSClient) -> set[int]:
    """Every strategic plan id in the listing."""
    return {item["id"] for item in client.fetch_planesestrategicos_busqueda()}


def pes_details(client: BDNSClient, errors: Errors) -> Iterator[dict]:
    """Detail record of every strategic plan, tagged with its `idPES`."""
    return _details(
        _pes_ids(client),
        lambda id_pes: client.fetch_planesestrategicos(idPES=id_pes),
        "planesestrategicos",
        "idPES",
        errors,
        tag="idPES",
    )


def pes_vigencias(client: BDNSClient, errors: Errors) -> Iterator[dict]:
    """Validity records of every strategic plan, tagged with its `idPES`."""
    return _details(
        _pes_ids(client),
        lambda id_pes: client.fetch_planesestrategicos_vigencia(idPES=id_pes),
        "planesestrategicos_vigencia",
        "idPES",
        errors,
        tag="idPES",
    )


# --- the registry ------------------------------------------------------------

_ADMIN_TYPES = tuple(t.value for t in TipoAdministracion)
_AMBITOS = tuple(a.value for a in Ambito)

# Payload rules. Each is a measurement, not a preference; the evidence is
# in bdns-fetch's API behaviour notes, and the criterion for excluding a
# field from the hash in docs/explanation/sync-behavior.md#hash-exclusion-criterion.
#
# `beneficiario` is rebuilt unstably for the same idPersona and oscillates
# between spellings: hashing it re-versioned 58% of concesiones and almost
# all of grandesbeneficiarios daily. Stored, but not a change.
_BENEFICIARIO_UNSTABLE = PayloadPolicy(hash_exclude=("beneficiario",))

_ENTITIES: tuple[Entity, ...] = (
    # Full entities, in the order a delta run syncs them.
    Entity("sectores", "full", ("id",), catalog("fetch_sectores")),
    Entity("actividades", "full", ("id",), catalog("fetch_actividades")),
    Entity("finalidades", "full", ("id",), catalog("fetch_finalidades")),
    Entity("beneficiarios", "full", ("id",), catalog("fetch_beneficiarios")),
    Entity("instrumentos", "full", ("id",), catalog("fetch_instrumentos")),
    Entity("objetivos", "full", ("id",), catalog("fetch_objetivos")),
    Entity("organos", "full", ("idAdmon", "id"), swept("fetch_organos", "idAdmon", _ADMIN_TYPES)),
    Entity(
        "organos_agrupacion",
        "full",
        ("idAdmon", "id"),
        swept("fetch_organos_agrupacion", "idAdmon", _ADMIN_TYPES),
    ),
    # A tree, but still a single call.
    Entity("regiones", "full", ("id",), catalog("fetch_regiones")),
    Entity("reglamentos", "full", ("ambito", "id"), swept("fetch_reglamentos", "ambito", _AMBITOS)),
    # No id field in the source: the key is a best-effort composite, which
    # is why a key conflict fails the run instead of being absorbed.
    Entity(
        "sanciones_busqueda",
        "full",
        ("numeroConvocatoria", "sancionado", "fechaSancion"),
        catalog("fetch_sanciones_busqueda"),
    ),
    Entity(
        "grandesbeneficiarios_anios", "full", ("id",), catalog("fetch_grandesbeneficiarios_anios")
    ),
    Entity(
        "grandesbeneficiarios_busqueda",
        "full",
        ("idPersona", "ejercicio"),
        grandesbeneficiarios,
        policy=_BENEFICIARIO_UNSTABLE,
    ),
    Entity(
        "planesestrategicos_busqueda", "full", ("id",), catalog("fetch_planesestrategicos_busqueda")
    ),
    Entity("planesestrategicos", "full", ("idPES",), pes_details),
    Entity("planesestrategicos_vigencia", "full", ("idPES",), pes_vigencias),
    # Windowed entities. history_start is a conservative floor under each
    # endpoint's retention, not its first record.
    Entity(
        "concesiones_busqueda",
        "windowed",
        ("id",),
        registration_window("fetch_concesiones_busqueda"),
        reg_date_field="fechaAlta",
        policy=_BENEFICIARIO_UNSTABLE,
        history_start=date(2020, 1, 1),
    ),
    Entity(
        "ayudasestado_busqueda",
        "windowed",
        ("idConcesion",),
        registration_window("fetch_ayudasestado_busqueda"),
        reg_date_field="fechaAlta",
        # A "#"-joined list that comes back shuffled; "#" never occurs
        # inside an element.
        policy=PayloadPolicy(delimited_lists={"sectores": "#"}),
        history_start=date(2015, 1, 1),
    ),
    Entity(
        "minimis_busqueda",
        "windowed",
        ("idConcesion",),
        registration_window("fetch_minimis_busqueda"),
        reg_date_field="fechaRegistro",
        # Shuffled too, but several CNAE names carry their own ";", so the
        # pattern splits before the start of an element instead.
        policy=PayloadPolicy(
            delimited_lists={"sectorActividad": r";\s*(?=[A-Z0-9][A-Z0-9.]*\s*-\s)"}
        ),
        history_start=date(2015, 1, 1),
    ),
    # No registration-date field in the payload, so no deletion detection.
    Entity(
        "partidospoliticos_busqueda",
        "windowed",
        ("id",),
        registration_window("fetch_partidospoliticos_busqueda"),
        history_start=date(2020, 1, 1),
    ),
    Entity(
        "convocatorias_busqueda",
        "windowed",
        ("numeroConvocatoria",),
        period_window("fetch_convocatorias_busqueda"),
        reg_date_field="fechaRecepcion",
        history_start=date(2013, 1, 1),
    ),
    Entity(
        "convocatorias",
        "windowed",
        ("codigoBDNS",),
        convocatoria_details,
        reg_date_field="fechaRecepcion",
        history_start=date(2013, 1, 1),
    ),
)

ENTITIES: dict[str, Entity] = {entity.name: entity for entity in _ENTITIES}
"""Every synced entity by name, in the order a delta run syncs them."""


def get_entity(name: str) -> Entity:
    """Look an entity up by name, accepting hyphens for underscores.

    Raises:
        KeyError: If there is no such entity.
    """
    try:
        return ENTITIES[name.replace("-", "_")]
    except KeyError:
        raise KeyError(f"unknown entity: {name}") from None


def full_entities() -> list[Entity]:
    """The entities each run syncs whole, in sync order."""
    return [e for e in ENTITIES.values() if e.kind == "full"]


def windowed_entities() -> list[Entity]:
    """The entities each run syncs by registration-date window, in sync order."""
    return [e for e in ENTITIES.values() if e.kind == "windowed"]


def sync_entity(
    entity: Entity | str,
    sink: Sink,
    client: BDNSClient,
    window: str | None = None,
    *,
    since: date | None = None,
    until: date | None = None,
) -> SyncStats:
    """Sync one entity into `sink`.

    Args:
        entity: The entity, or its name.
        sink: Where the rows are applied.
        client: The BDNS API client.
        window: For a windowed entity, a named window
            ([`WINDOWS`][bdns.sync.windows.WINDOWS]).
        since: For a windowed entity, the first day of an explicit range.
            Wins over `window`.
        until: Last day of that range. Defaults to yesterday.

    Returns:
        What the run did.

    Raises:
        ValueError: If a windowed entity gets neither `window` nor `since`.
    """
    if isinstance(entity, str):
        entity = get_entity(entity)
    errors: Errors = []
    if entity.kind == "full":
        return sink.sync_full(
            entity.name,
            entity.rows(client, errors),
            entity.key_fields,
            policy=entity.policy,
            skipped=errors,
        )
    start, end, run_type = resolve_when(window, since, until)
    return sink.sync_window(
        entity.name,
        entity.rows(client, start, end, errors),
        entity.key_fields,
        window_start=start,
        window_end=end,
        run_type=run_type,
        reg_date_field=entity.reg_date_field,
        policy=entity.policy,
        skipped=errors,
    )
