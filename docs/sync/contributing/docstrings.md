# Convenciones de docstrings y documentación

Los docstrings de este proyecto se leen dos veces: en el editor, por quien
está cambiando el código, y en la web de documentación, donde
`mkdocstrings` los convierte en la referencia de la API. Un mismo texto
tiene que servir a los dos. Esa es la restricción que esta convención
existe para cumplir.

## La regla

**Un hecho tiene un solo sitio. El código enlaza a él, nunca lo copia.**

| Lo que quieres dejar escrito | Dónde vive |
| --- | --- |
| Qué hace una función y qué promete a quien la llama | Su docstring |
| Una decisión de diseño que abarca varias funciones | El docstring del módulo |
| Un hecho medido sobre la API de la BDNS | El [comportamiento de la API](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/) de bdns-fetch |
| Lo que este motor decide a partir de ello | [Cómo sincroniza](../explanation/sync-behavior.md) |
| Un aviso para quien consulta las tablas resultantes | [Antes de consultar los datos](../explanation/data-caveats.md) |
| Cómo ejecutar, desplegar o programar la herramienta | Las guías |

Aquí la duplicación no es un problema de estilo, es un problema de
corrección: dos copias de una medición divergen, y nada te dice cuál está
desactualizada.

## Docstrings de funciones y métodos

Secciones en este orden, siempre:

1. **Línea de resumen.** En imperativo, una línea, terminada en punto.
2. **Párrafo del porqué** (opcional). De tres a seis líneas. Ver más
   abajo la prueba de los tres destinos para saber qué va aquí.
3. **`Args` / `Returns` / `Yields` / `Raises`**, estilo Google.

Reglas:

- Imperativo: "Group `items` into lists", no "Groups items" ni "This
  function groups items".
- No repitas los tipos en el texto. Ya los llevan las anotaciones, y
  `mkdocstrings` muestra la firma encima del texto.
- Documenta todos los parámetros, o ninguno. Una lista a medias parece un
  descuido.
- `Raises` es para las excepciones que se espera que maneje quien llama,
  no para toda excepción que físicamente pueda escapar.
- Una función de una línea realmente obvia sigue siendo de una línea.
  [`chunked`][bdns.sync.pipeline.chunked] no necesita bloque `Args`;
  forzarlo añade ruido, no información.

## Dónde va el porqué: la prueba de los tres destinos

Las justificaciones largas son lo más valioso de este código y lo más
fácil de colocar mal. Para cada párrafo, pregúntate de qué trata en
realidad:

- **Una decisión de implementación de esta función** → se queda, recortada
  a entre tres y seis líneas.
- **Una decisión que abarca el módulo** → pasa al docstring del módulo.
- **Una medición empírica de la API** → pasa a la documentación, y el
  docstring enlaza a ella.

No se borra nada. Se archiva en su sitio.

### Ejemplo

`bdns/sync/hashing.py::sorted_delimited_list` llegó a tener veinticinco
líneas que mezclaban las tres categorías. Repartidas:

- Qué campos llegan barajados (`sectorActividad` en minimis, `sectores`
  en ayudasestado): **medición**, va en
  [el comportamiento de la API](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#shuffled-lists).
- Por qué el separador es una expresión regular y no un carácter (los
  nombres CNAE llevan sus propios puntos y coma): **decisión de esta
  función**, se queda.
- Por qué el hash puede ser más grueso que lo almacenado pero nunca más
  fino: **alcance de módulo**, va en el docstring de `policy.py`, que ya
  lo argumenta bien.

### Antes

```python
def prefetch(iterable: Iterable[Any]) -> Iterator[Any]:
    """Yield the items of `iterable`, pulling them on a helper thread that
    reads ahead of the caller.

    While the caller processes one item, the helper is already producing
    the next. The queue holds at most two items: if the caller falls
    behind, the helper blocks instead of filling memory.

    The caller does its work on its own thread. That matters for SQLite
    connections, which must stay on the thread that created them.

    If the helper raises, the exception is re-raised here. If the caller
    stops iterating early, the helper is unblocked and joined before the
    generator exits.
    """
```

### Después

```python
def prefetch(iterable: Iterable[Any]) -> Iterator[Any]:
    """Yield the items of `iterable`, read ahead on a helper thread.

    The queue holds at most two items, so a slow caller blocks the
    helper instead of growing memory. The caller keeps its own thread,
    which SQLite requires: a connection may only be used on the thread
    that opened it.

    Args:
        iterable: Source of items, consumed on the helper thread.

    Yields:
        The items of `iterable`, in order.

    Raises:
        Exception: Whatever `iterable` raised, re-raised on the caller's
            thread. The helper is joined before this generator exits,
            including when the caller stops iterating early.
    """
```

Los mismos hechos, tres líneas menos, y la firma ya no queda enterrada.

## Docstrings de módulo

Todo módulo tiene uno, con esta forma:

1. Una línea de resumen que dice qué vive ahí.
2. El argumento de diseño que da coherencia al módulo.

Aquí es donde caben los ensayos. `bdns/sync/policy.py` es el modelo:
explica por qué las reglas que solo afectan al hash son seguras y las que
afectan a lo almacenado no, que es algo que ninguna función por sí sola
podría sostener.

## Docstrings de clase

Línea de resumen y, en dataclasses y objetos de valor, `Attributes:`. No
escribas un docstring aparte para `__init__`: el de la clase cubre la
construcción.

## Superficie pública: `__all__`

Todo módulo declara `__all__`, y es el contrato: los nombres de `__all__`
no cambian sin una nota de ruptura en el changelog.

Los helpers privados de un módulo llevan guion bajo, y siguen
documentados. La referencia los muestra junto a los públicos, una página
por módulo; el guion bajo es lo que avisa de que un nombre puede cambiar
sin aviso. [`_order_independent`][bdns.sync.hashing._order_independent]
es privado, y su docstring sigue siendo de los más útiles del paquete.

## Enlaces desde el código

Enlaza a la documentación en vez de copiar la evidencia en los
docstrings: las copias se quedan desactualizadas. Cómo se escribe el
enlace depende de si se renderiza.

**En un docstring**, un enlace Markdown. Es relativo a la página donde se
renderiza el docstring, y la página de cada módulo vive en
`docs/reference/api/`:

```python
"""...

Evidence that the order varies is in
[the spurious-changes measurements](../../explanation/sync-behavior.md#spurious-changes).
"""
```

En el editor la ruta sigue diciendo qué fichero abrir; en la web es un
enlace.

**A otro objeto**, una referencia cruzada. Un nombre en el ámbito del
docstring no necesita destino, y cualquier otro lleva su ruta completa:

```python
"""Same shape as [`registration_window`][], for the other date family.

Serialized through [`PortableJSON`][bdns.sync.sinks.sql.schema.PortableJSON].
"""
```

Un nombre entre comillas invertidas sin más se ve como código, no como
enlace.

**En un comentario, un script, un test o el Dockerfile** no se renderiza
nada, así que se escribe la ruta desde la raíz del repositorio:

```python
# See docs/explanation/sync-behavior.md#spurious-changes.
```

En todos los casos:

- Se enlaza un **ancla**, nunca un número de sección. Los números de
  sección se mueven cada vez que se inserta una sección.
- Las anclas son los `<a id="…">` explícitos de los documentos. No
  dependen del idioma: una página en español y su traducción usan las
  mismas.

`scripts/check_doc_refs.py` resuelve todos esos enlaces, se rendericen o
no, y falla si falta un fichero o un ancla. `scripts/check_site_links.py`
lee la web generada y falla ante cualquier mención de un objeto
documentado, un documento o un script que no sea un enlace.

## Idioma

- Código, comentarios y docstrings: **en inglés**, siempre.
- Web: el español es el idioma canónico. `foo.md` es la página en
  español y `foo.en.md` su traducción al inglés; una página sin
  traducción muestra la española (`mkdocs.yml`, plugin `i18n`). Los
  docstrings están en inglés, así que la referencia de la API generada
  está en inglés en los dos idiomas.

## Cómo se comprueba

`ruff` se ocupa de la forma, para que la revisión pueda dedicarse al
contenido:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "D"]
ignore = [
    "E741",  # ambiguous variable name (O is required by API)
    "E501",  # long lines: docstrings/comments carry verified-live evidence
    "D105",  # magic methods: the class docstring covers them
    "D107",  # __init__: documented on the class
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D"]
```

La misma configuración se aplica en bdns-fetch, y el CI ejecuta
`ruff format --check` en los dos.

El CI ejecuta además `mkdocs build --strict`, que falla ante un enlace
interno roto o una referencia que no se resuelve.
