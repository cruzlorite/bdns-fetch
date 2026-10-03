# Cómo contribuir

*English: issues and pull requests in English are welcome. Code, comments, docstrings and commit messages are always in English.*

Gracias por el interés. BDNS Sync es un proyecto pequeño mantenido en el tiempo libre, así que lo que más ayuda es un cambio fácil de revisar.

## Antes de empezar

- **Fallos**: abre un issue con la plantilla de bug, con lo justo para reproducirlo.
- **Cambios de comportamiento o funcionalidades nuevas**: abre antes un issue para hablarlo. Una decisión de diseño se registra como [ADR](https://cruzlorite.github.io/bdns-sync/adr/).
- **Documentación**: los PR que corrigen o aclaran la documentación son siempre bienvenidos.

## Entorno

```bash
git clone https://github.com/cruzlorite/bdns-sync.git
cd bdns-sync
poetry install
make test               # tests unitarios
BDNS_SYNC_TEST_URL=postgresql+psycopg2://... make test   # la misma suite contra PostgreSQL
make lint && make format
make check-docs         # referencias, docstrings y build del sitio
```

## Qué se espera de un PR

- **Tests**: todo cambio de comportamiento trae su test. Los tests unitarios no acceden a la red.
- **Estilo**: `ruff check` y `ruff format --check` pasan; la configuración es la misma en toda la familia.
- **Docstrings**: estilo Google, según la [convención de docstrings](https://cruzlorite.github.io/bdns-sync/contributing/docstrings/). Un hecho tiene un solo sitio: el código enlaza a la documentación, no la copia.
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`...), en inglés, explicando el porqué en el cuerpo cuando no es obvio. Un cambio incompatible se marca con `!` y `BREAKING CHANGE:`.
- **CHANGELOG**: añade una entrada en `[Unreleased]` si el cambio lo nota quien usa la herramienta.
- **Compatibilidad**: respeta la [política de compatibilidad](https://cruzlorite.github.io/bdns-sync/compatibility/).

El CI ejecuta lo mismo que `make lint`, `make check-docs` y `make test`; un PR en rojo no se revisa hasta que pase.

## Licencia

Al contribuir aceptas que tu aportación se distribuya bajo la [licencia MIT](LICENSE) del proyecto.
