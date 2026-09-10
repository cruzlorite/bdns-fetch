# 0004. Excluir `beneficiario` del hash de contenido

**Estado:** aceptada · **Fecha:** 2026-09-03, acotada el 2026-09-04

## Contexto

El hash del payload decide si se abre una versión nueva. Si el origen
reescribe un campo sin que el dato cambie, cada ejecución abre una versión
que no corresponde a ningún hecho.

Medido contra el servicio real:

- En `concesiones_busqueda`, de las claves cuyo nombre cambió más de una
  vez, el **67% vuelve a una grafía que ya había tenido** (`ASOCIACIÓN` →
  `ASOCIACION` → `ASOCIACIÓN`), con `idPersona` invariable. Hashearlo
  reversionaba el **58% de la tabla**.
- En `grandesbeneficiarios_busqueda`, peor: seis variantes para un mismo
  `idPersona` en once días, con el importe idéntico.

## Decisión

`beneficiario` sale del hash en esas dos entidades. **Se sigue guardando
entero**; simplemente deja de contar como cambio.

La identidad no la toca: sigue siendo `idPersona`.

La exclusión se declara por entidad, solo donde la oscilación está medida
(acotado el 2026-09-04). No es una regla general sobre el campo.

## Consecuencias

- Se deja de reportar una diferencia que se sabe que es ruido. Nunca se
  inventa una.
- El hash pasa a ser **más grueso** que lo almacenado: dos payloads
  distintos pueden compartir hash. Eso es seguro; el sentido contrario no
  lo sería. El argumento completo está en
  [qué se guarda y qué cuenta como un cambio](../explanation/payload-policy.md).
- Si la regla resultara equivocada, el coste es recuperable: el dato sigue
  almacenado, se cambia la regla y se reversiona desde la siguiente
  ejecución. Se pierde granularidad de histórico del periodo, no el dato.
- Un cambio real de nombre para el mismo `idPersona` no abre versión. Es
  el precio aceptado.
