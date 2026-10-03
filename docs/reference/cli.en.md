# CLI

```console
$ bdns-fetch [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

Records are written as [JSON Lines](https://jsonlines.org/), one per line; documents, as they are. On an API error the CLI prints the message and exits with code 1; incorrect usage exits with 2.

## Global options

They go **before** the command.

| Option | Default | Description |
|---|---|---|
| `--output-file`, `-o` | `-` (stdout) | Output file |
| `--max-retries` | `3` | Retries for transient failures; 0 disables them |
| `--wait-time` | `2` | Initial wait between retries (s); doubles, up to 60 |
| `--max-workers` | `5` | Threads fetching pages (1-20) |
| `--rate-limit` | `9.5` | Requests per second (at most 10). Lower it when several processes share an IP |
| `--progress` / `--no-progress` | automatic | Progress bar; by default only when stderr is a terminal |
| `--verbose`, `-v` | off | Log every HTTP request and error details |
| `--version` | | Show the version |

## Endpoint commands

One per `fetch_*` method of the client, named after the method without `fetch_`, with hyphens. The underscore form (`concesiones_busqueda`), the one `bdns-sync` uses, works too.

Each command's options are the API's parameters, spelled the same way (`--fechaDesde`, `--nifCif`). Dates are written `YYYY-MM-DD` or `DD/MM/YYYY`. `bdns-fetch COMMAND --help` lists each command's options.

| Command | Paginated |
|---|---|
| `actividades`, `beneficiarios`, `finalidades`, `instrumentos`, `objetivos`, `regiones`, `reglamentos`, `sectores` | |
| `organos`, `organos-agrupacion`, `organos-codigo`, `organos-codigoadmin` | |
| `convocatorias`, `convocatorias-ultimas` | |
| `convocatorias-busqueda` | yes |
| `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda`, `partidospoliticos-busqueda` | yes |
| `grandesbeneficiarios-anios` | |
| `grandesbeneficiarios-busqueda`, `sanciones-busqueda` | yes |
| `planesestrategicos`, `planesestrategicos-vigencia` | |
| `planesestrategicos-busqueda` | yes |
| `terceros` | |
| `convocatorias-pdf`, `convocatorias-documentos`, `planesestrategicos-documentos` | document |

On paginated ones, `--num-pages` (default **1**; 0 = all), `--from-page` and `--pageSize` (at most 10000) control pagination. A warning on stderr says when pages were left out.

!!! warning "`--fechaRegFin` is exclusive"
    Options are the API's parameters, untranslated. To include the 31st in `--fechaRegFin`, pass the 1st of the next month. See [API behaviour](../explanation/api-behavior.md#upper-bound).

## Tools

### `get`

```console
$ bdns-fetch get PATH [-p KEY=VALUE]... [--binary]
```

Requests any API path, with the same retries and rate limit. Writes the JSON document on one line, or the body as is with `--binary`. See [endpoints without a method](../guides/other-endpoints.md).

### `check-api`

```console
$ bdns-fetch check-api [--day YYYY-MM-DD]
```

Checks against the live service that the date filters still have the documented semantics. Exits 1 only when the API returned valid data contradicting them; an empty day or a passing error is reported and exits 0. See [incremental downloads](../guides/incremental.md#check-that-the-api-has-not-changed).
