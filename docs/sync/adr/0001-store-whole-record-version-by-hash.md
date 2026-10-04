# 0001. Guardar el registro entero y detectar los cambios por hash

**Estado:** aceptada · **Fecha:** 2026-07-08 (anterior al primer commit del repositorio)

## Contexto

La API de la BDNS ofrece más de veinte entidades con estructuras distintas, y sus campos cambian sin avisar. Con una columna por campo habría que migrar el esquema cada vez que la API añade o quita algo, y mantener a mano más de veinte esquemas.

Además, hay que detectar los cambios entre ejecuciones sin comparar campo a campo, algo que no se puede hacer con decenas de millones de filas.

## Decisión

Una tabla por entidad, todas con **las mismas columnas**. El registro se guarda entero en la columna `payload`, en JSON sobre una columna de texto, y el resto de columnas sirven para llevar el control de las versiones (SCD2).

Los cambios se detectan con `_row_hash`, un SHA-256 del registro normalizado.

## Consecuencias

- Si aparece o desaparece un campo no hay que migrar nada: el hash lo detecta y se guarda como cualquier otro cambio.
- Las versiones cerradas no se borran nunca, así que el histórico solo crece.
- El contenido no se puede consultar con las funciones JSON nativas de todas las bases de datos, porque se guarda como texto para que funcione igual en todas. Este código nunca lo consulta con SQL; solo lo lee de vuelta como un `dict` en Python.
- La normalización tiene que ser estable, porque si no el hash daría cambios que no existen. De ahí salen la [decisión 0004](0004-beneficiario-out-of-hash.md) y las reglas de la política de cada entidad.
