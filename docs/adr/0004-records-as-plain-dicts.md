# 0004. Registros como `dict`, sin modelos tipados

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Un cliente "moderno" suele devolver modelos tipados (dataclasses,
Pydantic): autocompletado, validación, documentación de cada campo.

La API de la BDNS cambia de forma sin aviso: campos que aparecen, que
llegan `null` cuando normalmente vienen rellenos, o que cambian de
formato ([comportamiento de la API](../explanation/api-behavior.md#intermittent-fields)).
Un modelo estricto rompería las descargas en cuanto la API cambiara; uno
laxo no aportaría nada. Y el principal consumidor, `bdns-sync`, guarda el
registro entero precisamente para no perder nada de lo que llega.

## Decisión

Los métodos devuelven los registros como `dict`, **exactamente** como los
devuelve la API: sin renombrar, sin convertir tipos, sin descartar
campos.

## Consecuencias

- Un campo nuevo llega al consumidor sin esperar a una versión de
  `bdns-fetch`.
- Nada se pierde ni se transforma en el camino: lo que se guarda es lo
  que publicó la Administración.
- No hay autocompletado de campos ni validación. Quien la necesite la
  pone en su capa, donde conoce qué campos le importan.
