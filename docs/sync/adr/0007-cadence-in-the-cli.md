# 0007. La periodicidad se decide en la línea de comandos, con código probado

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Una instalación en producción necesita hacer lo mismo cada día: comprobar que la API no ha cambiado, sincronizar las entidades completas y las incrementales con el periodo que toque (semanal por defecto, mensual los lunes y anual tres días al año), seguir aunque falle alguna entidad y terminar con un código de salida que haga saltar la alerta. Y una carga del histórico tiene que recorrer cada entidad año a año desde el principio de su histórico.

Si esa lógica está en un script de shell, nadie la prueba: la regla de qué periodo toca cada día, la lista de entidades y lo que pasa cuando algo falla solo se comprueban en producción. Además, obliga a mantener una lista de entidades fuera del código.

Un fichero de configuración tampoco encaja, porque la periodicidad no es algo que cada instalación tenga que inventarse, sino una consecuencia de cómo se comporta la API (registros que llegan con días de retraso, bajas que solo se detectan dentro del periodo que se sincroniza).

## Decisión

`bdns-sync delta` y `bdns-sync backfill` construyen un plan a partir del registro de entidades ([`orchestration`][bdns.sync.orchestration]) y lo ejecutan de forma que un fallo no detenga el resto. La regla de qué periodo toca cada día está en [`cadence_window`][bdns.sync.windows.cadence_window]. Los dos comandos admiten `--dry-run`, que muestra el plan con las fechas concretas, y `sync` sigue existiendo para sincronizar una sola entidad.

Los scripts se quedan como una sola línea que llama a estos comandos, para que los crontab que ya los usan sigan funcionando.

## Consecuencias

- La periodicidad y el tratamiento de los fallos tienen tests.
- Programar la herramienta es una sola línea: `bdns-sync delta` una vez al día.
- La herramienta tiene en cuenta en qué día se ejecuta. Si alguien necesita otra periodicidad, puede forzar el periodo con `--window` o combinar llamadas a `sync`.
