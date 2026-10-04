# 0004. Sacar `beneficiario` del hash

**Estado:** aceptada · **Fecha:** 2026-09-03, limitada a dos entidades el 2026-09-04

## Contexto

El hash del registro decide si se crea una versión nueva. Si la API reescribe un campo sin que el dato cambie de verdad, cada ejecución crea una versión que no responde a nada real.

Esto es lo que vimos al comprobarlo contra el servicio real:

- En `concesiones_busqueda`, de las claves cuyo nombre cambió más de una vez, el **67% vuelve a una grafía que ya había tenido** (`ASOCIACIÓN` → `ASOCIACION` → `ASOCIACIÓN`), siempre con el mismo `idPersona`. Con el campo dentro del hash se creaban versiones nuevas para el **58% de la tabla**.
- En `grandesbeneficiarios_busqueda` era todavía peor: seis variantes del nombre de un mismo `idPersona` en once días, siempre con el mismo importe.

## Decisión

En esas dos entidades, `beneficiario` sale del hash. **Se sigue guardando entero**; simplemente deja de contar como cambio.

La identidad no cambia: sigue siendo `idPersona`.

La exclusión se aplica entidad a entidad y solo donde se ha medido que el valor va y vuelve (se limitó así el 2026-09-04). No es una regla general sobre el campo.

## Consecuencias

- Deja de darse por cambio algo que se sabe que es ruido, y nunca se inventa un cambio que no existe.
- El hash pasa a ser **menos estricto** que lo que se guarda: dos registros distintos pueden tener el mismo hash. Eso no entraña riesgo, y lo contrario sí; el razonamiento completo está en [qué se guarda y qué cuenta como un cambio](../sync/explanation/payload-policy.md).
- Si la regla resultara equivocada, tiene arreglo: el dato sigue guardado, se cambia la regla y a partir de la siguiente ejecución se vuelven a crear versiones. Lo que se pierde es detalle en el histórico durante ese tiempo, no el dato.
- Si una persona cambia de nombre de verdad manteniendo el mismo `idPersona`, no se crea una versión nueva. Es el precio que se acepta.
