# Convenciones de docstrings y documentación

Estas convenciones son comunes a la familia BDNS. El texto completo, con
ejemplos, está en la
[guía de contribución de bdns-sync](https://cruzlorite.github.io/bdns-sync/contributing/docstrings/);
esta página es el resumen que aplica aquí.

## La regla

**Un hecho tiene un solo sitio. El código enlaza a él, nunca lo copia.**
Un hecho medido sobre la API vive en
[comportamiento de la API](../explanation/api-behavior.md); una decisión,
en su [ADR](../adr/index.md); lo que promete una función, en su docstring.

## Docstrings

- Estilo Google: una línea de resumen en imperativo, terminada en punto;
  un párrafo opcional con el porqué, de tres a seis líneas; después
  `Args`, `Returns`, `Yields`, `Raises`.
- No repitas los tipos en el texto: ya los lleva la firma.
- Documenta todos los parámetros o ninguno: una lista a medias parece un
  descuido.
- Todo módulo tiene docstring y declara `__all__`, que es su contrato.
- Desde un docstring, un documento se enlaza con una ruta relativa a
  `docs/reference/api/` (`../../explanation/api-behavior.md#upper-bound`)
  y un objeto con una referencia cruzada
  (`[`split_range`][bdns.fetch.dates.split_range]`). Se enlazan anclas,
  nunca números de sección.

## Idioma

El código, los comentarios y los docstrings van en inglés. La web va
primero en español: `foo.md` es la página en español y `foo.en.md` su
traducción al inglés. La referencia de la API Python se genera de los
docstrings, así que está en inglés en los dos idiomas.

## Cómo se comprueba

`make check-docs` ejecuta lo mismo que el CI: `scripts/check_doc_refs.py`
(todo enlace desde el código resuelve), `scripts/check_docstrings.py` (los
docstrings coinciden con las firmas), `mkdocs build --strict` y
`scripts/check_site_links.py` (ninguna referencia sin enlazar en la web
generada). `ruff` comprueba la forma de los docstrings, con la misma
configuración que bdns-sync.
