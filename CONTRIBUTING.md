# Cómo contribuir

*English: issues and pull requests in English are welcome. Code, comments, docstrings and commit messages are always in English.*

Gracias por tu interés. BDNS Tools es un proyecto pequeño que se mantiene en el tiempo libre, así que lo que más ayuda es un cambio fácil de revisar.

## Antes de empezar

- **Si has encontrado un fallo**, abre un issue con la plantilla de errores y cuenta lo justo para poder reproducirlo.
- **Si quieres cambiar cómo funciona algo o añadir una funcionalidad**, abre antes un issue para comentarlo. Las decisiones se registran en las [decisiones de diseño](https://cruzlorite.github.io/bdns-tools/adr/).
- **Si quieres mejorar la documentación**, adelante: los cambios que la corrigen o la aclaran siempre son bienvenidos.

## Preparar el entorno

Necesitas [uv](https://docs.astral.sh/uv/), que instala por su cuenta la versión de Python que haga falta.

```bash
git clone https://github.com/cruzlorite/bdns-tools.git
cd bdns-tools
make install            # el paquete, sus extras y las herramientas de desarrollo
make test               # tests unitarios, sin conexión
make test-integration   # tests contra la API real (opcional)
BDNS_SYNC_TEST_URL=postgresql+psycopg2://... make test-sync   # los tests de bdns.sync contra PostgreSQL
make lint && make format
make check-docs         # enlaces, docstrings y generación de la web
```

## Qué debe tener un pull request

- **Tests**: cualquier cambio de comportamiento viene con su test. Los tests unitarios no se conectan a internet.
- **Estilo**: tienen que pasar `ruff check` y `ruff format --check`.
- **Docstrings**: en estilo Google, siguiendo las [normas de documentación](https://cruzlorite.github.io/bdns-tools/contributing/docstrings/). Cada cosa se explica en un solo sitio, y desde el código se enlaza a la documentación en lugar de copiarla.
- **Documentación en español**: tiene que leerse como algo escrito directamente en español, no como una traducción.
- **Commits**: en inglés, con el formato de [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`...) y explicando el porqué en el cuerpo cuando no sea evidente. Si el cambio rompe la compatibilidad, márcalo con `!` y `BREAKING CHANGE:`.
- **CHANGELOG**: añade una entrada en `[Unreleased]` si el cambio lo va a notar quien use la herramienta.
- **Compatibilidad**: respeta la [política de compatibilidad](https://cruzlorite.github.io/bdns-tools/compatibility/). [`bdns.fetch`](https://cruzlorite.github.io/bdns-tools/fetch/reference/api/) nunca importa [`bdns.sync`](https://cruzlorite.github.io/bdns-tools/sync/reference/api/), y un test lo comprueba.

La integración continua ejecuta lo mismo que `make lint`, `make check-docs` y `make test` (los de la sincronización, además, con PostgreSQL y DuckDB) y construye la imagen de Docker, y un pull request en rojo no se revisa hasta que esté en verde.

## Publicar una versión

Esto solo lo hace quien mantiene el proyecto:

1. En el CHANGELOG, cambia `[Unreleased]` por `[X.Y.Z] - AAAA-MM-DD` y deja encima un `[Unreleased]` vacío. De ese apartado salen las notas de la release de GitHub.
2. Sube la versión con `uv version X.Y.Z` y haz commit en `main`.
3. Crea la etiqueta y súbela: `git tag vX.Y.Z && git push origin vX.Y.Z`.

El resto lo hace `publish.yml`: comprueba que la etiqueta coincide con la versión de `pyproject.toml` y que el CHANGELOG tiene su apartado, pasa los tests sobre el código y sobre el paquete ya construido, y publica en PyPI. Solo si eso sale bien publica la imagen en `ghcr.io`, crea la release de GitHub, con esas notas y los mismos ficheros que recibió PyPI, y actualiza la web. Si algo falla antes de llegar a PyPI, corrígelo, borra la etiqueta (`git push --delete origin vX.Y.Z`) y vuelve a crearla.

## Licencia

Al contribuir aceptas que tu aportación se distribuya con la [licencia MIT](https://github.com/cruzlorite/bdns-tools/blob/main/LICENSE) del proyecto.
