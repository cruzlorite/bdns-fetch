# Docstrings y documentación

Estas normas son comunes a los dos proyectos. El texto completo, con ejemplos, está en la [guía de contribución de bdns-sync](https://cruzlorite.github.io/bdns-sync/contributing/docstrings/); aquí tienes el resumen de lo que aplica en este.

## La regla principal

**Cada cosa se explica en un solo sitio, y desde el código se enlaza, nunca se copia.** Lo que se ha medido sobre la API va en [comportamiento de la API](../explanation/api-behavior.md); una decisión, en su página de [decisiones de diseño](../adr/index.md); lo que hace una función, en su docstring.

## Docstrings

- Estilo Google: una primera línea en imperativo que termina en punto, si hace falta un párrafo de tres a seis líneas con el porqué, y después `Args`, `Returns`, `Yields` y `Raises`.
- No repitas los tipos en el texto, que ya están en la firma.
- Documenta todos los parámetros o ninguno: una lista a medias parece un descuido.
- Todos los módulos tienen docstring y declaran `__all__`, que es lo que se considera público.
- Desde un docstring, los documentos se enlazan con una ruta relativa a `docs/reference/api/` (`../../explanation/api-behavior.md#upper-bound`) y los objetos con una referencia cruzada (`[`split_range`][bdns.fetch.dates.split_range]`). Se enlaza siempre a un ancla, nunca a un número de apartado.

## Idioma

El código, los comentarios y los docstrings van en inglés. La web va primero en español: `foo.md` es la página en español y `foo.en.md`, su traducción. La referencia de Python se genera a partir de los docstrings, así que está en inglés en los dos idiomas.

Al escribir en español, ten en cuenta que tiene que leerse como algo escrito directamente en español y no como una traducción: tutea, enlaza las ideas en frases completas en lugar de usar frases sueltas, evita los calcos del inglés y usa el vocabulario de la BDNS (periodo, llamada, fecha de registro, Código BDNS...).

## Cómo se comprueba

`make check-docs` ejecuta lo mismo que la integración continua: `scripts/check_doc_refs.py` (todos los enlaces desde el código llevan a algún sitio), `scripts/check_docstrings.py` (los docstrings coinciden con las firmas), `mkdocs build --strict` y `scripts/check_site_links.py` (ninguna referencia queda sin enlazar en la web generada). `ruff` comprueba el formato de los docstrings con la misma configuración que bdns-sync.
