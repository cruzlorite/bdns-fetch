# 0004. Los registros se devuelven como `dict`, sin modelos tipados

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Lo habitual en un cliente moderno es devolver modelos tipados (dataclasses, Pydantic), que dan autocompletado, validación y documentación de cada campo.

Pero la API de la BDNS cambia sin avisar: aparecen campos nuevos, campos que normalmente vienen rellenos llegan vacíos y otros cambian de formato ([comportamiento de la API](../explanation/api-behavior.md#intermittent-fields)). Un modelo estricto haría fallar las descargas en cuanto la API cambiara, y uno permisivo no aportaría nada. Además, quien más usa el cliente, `bdns-sync`, guarda el registro entero precisamente para no perder nada de lo que llega.

## Decisión

Los métodos devuelven los registros como `dict`, **exactamente** como los devuelve la API: sin cambiar nombres, sin convertir tipos y sin quitar campos.

## Consecuencias

- Un campo nuevo llega a quien usa el cliente sin esperar a una nueva versión de `bdns-fetch`.
- No se pierde ni se transforma nada por el camino: lo que se guarda es lo que publicó la Administración.
- No hay autocompletado de campos ni validación. Quien la necesite puede añadirla en su propio código, donde sabe qué campos le interesan.
