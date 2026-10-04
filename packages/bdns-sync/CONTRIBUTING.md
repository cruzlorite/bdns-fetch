# Cómo contribuir

*English: issues and pull requests in English are welcome. Code, comments, docstrings and commit messages are always in English.*

Gracias por tu interés. BDNS Sync es un proyecto pequeño que se mantiene en el tiempo libre, así que lo que más ayuda es un cambio fácil de revisar.

## Antes de empezar

- **Si has encontrado un fallo**, abre un issue con la plantilla de errores y cuenta lo justo para poder reproducirlo.
- **Si quieres cambiar cómo funciona algo o añadir una funcionalidad**, abre antes un issue para comentarlo. Las decisiones de diseño se registran en las [decisiones de diseño](https://cruzlorite.github.io/bdns-sync/adr/).
- **Si quieres mejorar la documentación**, adelante: los cambios que la corrigen o la aclaran siempre son bienvenidos.

## Preparar el entorno

```bash
git clone https://github.com/cruzlorite/bdns-sync.git
cd bdns-sync
poetry install
make test               # tests unitarios
BDNS_SYNC_TEST_URL=postgresql+psycopg2://... make test   # los mismos tests contra PostgreSQL
make lint && make format
make check-docs         # enlaces, docstrings y generación de la web
```

## Qué debe tener un pull request

- **Tests**: cualquier cambio de comportamiento viene con su test. Los tests unitarios no se conectan a internet.
- **Estilo**: tienen que pasar `ruff check` y `ruff format --check`, con la misma configuración que en bdns-fetch.
- **Docstrings**: en estilo Google, siguiendo las [normas de documentación](https://cruzlorite.github.io/bdns-sync/contributing/docstrings/). Cada cosa se explica en un solo sitio, y desde el código se enlaza a la documentación en lugar de copiarla.
- **Documentación en español**: tiene que leerse como algo escrito directamente en español, no como una traducción.
- **Commits**: en inglés, con el formato de [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`...) y explicando el porqué en el cuerpo cuando no sea evidente. Si el cambio rompe la compatibilidad, márcalo con `!` y `BREAKING CHANGE:`.
- **CHANGELOG**: añade una entrada en `[Unreleased]` si el cambio lo va a notar quien use la herramienta.
- **Compatibilidad**: respeta la [política de compatibilidad](https://cruzlorite.github.io/bdns-sync/compatibility/).

La integración continua ejecuta lo mismo que `make lint`, `make check-docs` y `make test`, y un pull request en rojo no se revisa hasta que esté en verde.

## Licencia

Al contribuir aceptas que tu aportación se distribuya con la [licencia MIT](LICENSE) del proyecto.
