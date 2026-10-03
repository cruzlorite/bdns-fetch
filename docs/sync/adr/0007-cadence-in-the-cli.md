# 0007. La cadencia vive en el CLI, como código probado

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Una instalación en producción necesita lo mismo cada día: comprobar que
la API no ha cambiado, sincronizar las entidades completas y las de
ventana con la ventana que toque ese día (semanal por defecto, mensual
los lunes, anual tres días al año), seguir aunque una entidad falle y
terminar con un código de salida que dispare la alerta. Una carga
histórica necesita recorrer cada entidad año a año desde el inicio de su
histórico.

Esa lógica, en un script de shell, no la prueba nadie: la regla de qué
ventana toca un día, la lista de entidades y el manejo de fallos solo se
verifican en producción. Y obliga a mantener una lista de entidades
fuera del código.

Un fichero de configuración tampoco encaja: la cadencia no es algo que
cada instalación deba reinventar, sino una consecuencia de cómo se
comporta la API (registros que llegan con días de retraso, bajas que solo
se detectan dentro de la ventana).

## Decisión

`bdns-sync delta` y `bdns-sync backfill` construyen un plan a partir del
registro de entidades ([`orchestration`][bdns.sync.orchestration]) y lo
ejecutan, aislando los fallos. La regla de cadencia es
[`cadence_window`][bdns.sync.windows.cadence_window]. Los dos comandos
admiten `--dry-run`, que imprime el plan con sus fechas concretas.
`sync` sigue existiendo para una entidad suelta.

Los scripts quedan como envoltorios de una línea, para no romper los
crontab que los llaman.

## Consecuencias

- La cadencia y el aislamiento de fallos tienen tests.
- Programar la herramienta es una línea: `bdns-sync delta` a diario.
- La herramienta sabe qué día es. Quien necesite otra cadencia fuerza la
  ventana con `--window` o compone llamadas a `sync`.
