# 0001. Guardar el registro entero y versionar por hash

**Estado:** aceptada · **Fecha:** 2026-07-08 (anterior al historial registrado)

## Contexto

La API de la BDNS expone una veintena larga de entidades con formas
distintas, y sus campos cambian sin aviso. Un esquema con una columna por
campo obligaría a una migración cada vez que el origen añade o quita algo,
y a mantener veintitantos esquemas a mano.

Además hace falta detectar cambios entre ejecuciones sin comparar campo a
campo, que no escala a decenas de millones de filas.

## Decisión

Una tabla por endpoint, todas con el **mismo esquema genérico**. El
registro se guarda entero en una columna `payload`, en JSON sobre texto.
El resto de columnas son metadatos de versionado SCD2.

Los cambios se detectan por `_row_hash`, un SHA-256 del payload
canonicalizado.

## Consecuencias

- Un campo nuevo o desaparecido no requiere migración: se detecta por el
  hash y se versiona como cualquier otro cambio.
- Las versiones cerradas no se borran nunca. El histórico solo crece.
- El payload no es consultable con SQL nativo de JSON en todos los
  motores, porque se guarda como texto por portabilidad. Este código
  nunca lo consulta en SQL, solo lo lee de vuelta como dict en Python.
- La canonicalización tiene que ser estable, o el hash reporta cambios
  que no existen. De ahí salen [0004](0004-beneficiario-fuera-del-hash.md)
  y las reglas de política de payload.
