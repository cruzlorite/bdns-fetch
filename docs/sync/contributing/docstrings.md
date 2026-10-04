# Docstrings y documentación

Los docstrings de este proyecto se leen dos veces: en el editor, por quien está cambiando el código, y en la web de documentación, donde `mkdocstrings` los convierte en la referencia de Python. Un mismo texto tiene que servir para las dos cosas, y estas normas existen para conseguirlo.

## La regla principal

**Cada cosa se explica en un solo sitio, y desde el código se enlaza, nunca se copia.**

| Lo que quieres dejar escrito | Dónde va |
| --- | --- |
| Qué hace una función y qué garantiza a quien la llama | En su docstring |
| Una decisión de diseño que afecta a varias funciones | En el docstring del módulo |
| Algo que se ha medido sobre la API de la BDNS | En el [comportamiento de la API](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/) de bdns-fetch |
| Lo que este proyecto decide a partir de ello | En [cómo sincroniza](../explanation/sync-behavior.md) |
| Un aviso para quien consulta las tablas | En [antes de consultar los datos](../explanation/data-caveats.md) |
| Cómo ejecutar, desplegar o programar la herramienta | En las guías |

Aquí repetir información no es una cuestión de estilo, sino de corrección: dos copias de una medición acaban siendo distintas, y nada te dice cuál está desactualizada.

## Docstrings de funciones y métodos

Siempre con estas secciones y en este orden:

1. **Línea de resumen**, en imperativo, en una sola línea y terminada en punto.
2. **Párrafo con el porqué**, si hace falta, de tres a seis líneas (más abajo se explica qué va aquí).
3. **`Args`, `Returns`, `Yields` y `Raises`**, en estilo Google.

Algunas normas:

- En imperativo: "Group `items` into lists", no "Groups items" ni "This function groups items".
- No repitas los tipos en el texto, porque ya están en las anotaciones y `mkdocstrings` muestra la firma encima.
- Documenta todos los parámetros o ninguno: una lista a medias parece un descuido.
- `Raises` es para las excepciones que se espera que trate quien llama, no para todas las que podrían llegar a salir.
- Una función de una línea que es realmente obvia se queda en una línea. [`chunked`][bdns.sync.pipeline.chunked] no necesita bloque `Args`, y obligarle a tenerlo añadiría ruido, no información.

## Dónde va el porqué

Las explicaciones largas son lo más valioso de este código y lo más fácil de poner en el sitio equivocado. Para cada párrafo, pregúntate de qué trata en realidad:

- **De una decisión de esta función en concreto**: se queda, reducida a entre tres y seis líneas.
- **De una decisión que afecta a todo el módulo**: pasa al docstring del módulo.
- **De algo que se ha medido sobre la API**: pasa a la documentación, y el docstring enlaza a ella.

No se borra nada; se coloca donde corresponde.

### Un ejemplo

`bdns/sync/hashing.py::sorted_delimited_list` llegó a tener veinticinco líneas que mezclaban los tres casos. Repartidas, quedan así:

- Qué campos llegan desordenados (`sectorActividad` en minimis, `sectores` en ayudasestado) es algo **medido**, y va en [el comportamiento de la API](https://cruzlorite.github.io/bdns-fetch/explanation/api-behavior/#shuffled-lists).
- Por qué el separador es una expresión regular y no un carácter (algunas descripciones de la CNAE llevan su propio punto y coma) es una **decisión de esta función**, y se queda.
- Por qué el hash puede ser menos estricto que lo que se guarda, pero nunca más, afecta a **todo el módulo**, y va en el docstring de `policy.py`, que ya lo explica bien.

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

Dice lo mismo, con tres líneas menos, y la firma ya no queda escondida.

## Docstrings de módulo

Todos los módulos tienen uno, con esta forma:

1. Una línea de resumen que dice qué hay en el módulo.
2. La idea de diseño que da sentido al módulo.

Aquí es donde caben las explicaciones largas. `bdns/sync/policy.py` es un buen ejemplo: explica por qué las reglas que solo afectan al hash no entrañan riesgo y las que cambian lo que se guarda sí, algo que ninguna función podría explicar por sí sola.

## Docstrings de clase

Una línea de resumen y, en las dataclasses y objetos de valor, la sección `Attributes:`. No escribas un docstring aparte para `__init__`, porque el de la clase ya explica cómo se construye.

## Lo público: `__all__`

Todos los módulos declaran `__all__`, y eso es lo que se considera público: los nombres de `__all__` no cambian sin avisarlo en el CHANGELOG como cambio incompatible.

Las funciones internas de un módulo empiezan por guion bajo y también se documentan. La referencia las muestra junto a las públicas, en la página de cada módulo, y es el guion bajo lo que avisa de que pueden cambiar sin aviso. [`_order_independent`][bdns.sync.hashing._order_independent] es interna, y aun así su docstring es de los más útiles del paquete.

## Enlaces desde el código

Enlaza a la documentación en lugar de copiar las pruebas en los docstrings, porque las copias acaban desactualizadas. Cómo se escribe el enlace depende de si se va a mostrar en la web.

**En un docstring**, con un enlace Markdown relativo a la página donde se muestra el docstring, que para todos los módulos está en `docs/reference/api/`:

```python
"""...

Evidence that the order varies is in
[the spurious-changes measurements](../../explanation/sync-behavior.md#spurious-changes).
"""
```

En el editor la ruta sigue diciendo qué fichero abrir, y en la web es un enlace.

**A otro objeto**, con una referencia cruzada. Si el nombre está al alcance del docstring no hace falta indicar el destino; si no, se escribe la ruta completa:

```python
"""Same shape as [`registration_window`][], for the other date family.

Serialized through [`PortableJSON`][bdns.sync.sinks.sql.schema.PortableJSON].
"""
```

Un nombre entre comillas invertidas, sin más, se muestra como código y no como enlace.

**En un comentario, un script, un test o el Dockerfile** no se muestra nada en la web, así que se escribe la ruta desde la raíz del repositorio:

```python
# See docs/explanation/sync-behavior.md#spurious-changes.
```

En todos los casos:

- Se enlaza a un **ancla**, nunca a un número de apartado, porque los números cambian cada vez que se añade un apartado.
- Las anclas son los `<a id="…">` que hay en los documentos, y son iguales en todos los idiomas: la página en español y su traducción usan las mismas.

`scripts/check_doc_refs.py` comprueba todos estos enlaces, se muestren o no en la web, y falla si falta un fichero o un ancla. `scripts/check_site_links.py` revisa la web ya generada y falla si se menciona un objeto documentado, un documento o un script sin enlazarlo.

## Idioma

- El código, los comentarios y los docstrings van **en inglés**, siempre.
- La web va primero en español: `foo.md` es la página en español y `foo.en.md`, su traducción al inglés; si una página no tiene traducción, se muestra la española (`mkdocs.yml`, plugin `i18n`). La referencia de Python se genera a partir de los docstrings, así que está en inglés en los dos idiomas.
- Lo que escribas en español tiene que leerse como algo escrito directamente en español y no como una traducción: tutea, enlaza las ideas en frases completas en lugar de usar frases sueltas, evita los calcos del inglés y usa el vocabulario de la BDNS (periodo, llamada, fecha de registro, Código BDNS...).

## Cómo se comprueba

`ruff` se encarga de la forma, para que al revisar se pueda prestar atención al contenido:

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

bdns-fetch usa la misma configuración, y la integración continua ejecuta `ruff format --check` en los dos proyectos.

Además, la integración continua ejecuta `mkdocs build --strict`, que falla si hay un enlace interno roto o una referencia que no lleva a ningún sitio.
