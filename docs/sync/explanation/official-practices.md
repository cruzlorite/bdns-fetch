# Buenas prácticas oficiales

El diseño sigue el documento oficial ["Buenas prácticas API SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf):

- **Límite de 10 peticiones por segundo y por IP**, que aplica `bdns-fetch`.
- **Paginación al tamaño máximo** (10.000 registros por llamada) y siempre **todas las páginas**: el parámetro `num_pages` de `bdns-fetch` vale 1 por defecto, lo que corta en silencio cualquier respuesta de más de una página (visto en real: `grandesbeneficiarios_busqueda` devolvía 10.000 filas de 142.260). El envoltorio `generic.all_pages` fuerza `num_pages=0` en todo método paginado, que reconoce por la firma.
- **Cadencia diaria/semanal/mensual/anual por fecha de registro**, tal como recomienda el documento.
- **El endpoint `terceros` no se usa**: el propio documento lo da por redundante.
- **Reconciliación para detectar bajas**: las ayudas se retiran de la BDNS a los 4 años naturales siguientes a la concesión. Los catálogos completos detectan las bajas comparando contra todo el estado actual; en los endpoints incrementales grandes, donde esa comparación no sale a cuenta, se compara solo dentro del rango de fechas de registro (ver [detección de bajas acotada por ventana](bdns-api-behavior.md#windowed-deletions)).
