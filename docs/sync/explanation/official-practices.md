# Buenas prácticas oficiales

El diseño sigue el documento oficial ["Buenas prácticas API SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf):

- **Límite de 10 peticiones por segundo y por IP**, que `bdns-fetch` respeta espaciando las peticiones a 9,5 por segundo, sin ráfagas.
- **Paginación al tamaño máximo** (10.000 registros por llamada) y siempre **todas las páginas**, que es lo que hace `bdns-fetch` por defecto. Una respuesta cortada a una sola página pasa desapercibida (visto en real: `grandesbeneficiarios_busqueda` llegó a devolver 10.000 filas de 142.260), por eso `bdns-fetch` avisa cuando deja páginas sin descargar.
- **Cadencia diaria/semanal/mensual/anual por fecha de registro**, tal como recomienda el documento.
- **El endpoint `terceros` no se usa**: el propio documento lo da por redundante.
- **Reconciliación para detectar bajas**: las ayudas se retiran de la BDNS a los 4 años naturales siguientes a la concesión. Los catálogos completos detectan las bajas comparando contra todo el estado actual; en los endpoints incrementales grandes, donde esa comparación no sale a cuenta, se compara solo dentro del rango de fechas de registro (ver [detección de bajas acotada por ventana](sync-behavior.md#windowed-deletions)).
