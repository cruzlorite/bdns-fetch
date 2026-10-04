# Buenas prácticas oficiales

El diseño sigue las ["Buenas prácticas para el uso del interfaz API-REST del SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) que publica la IGAE:

- **Como mucho 10 peticiones por segundo y por IP.** `bdns-fetch` espacia las peticiones a 9,5 por segundo y no deja pasar ráfagas.
- **Nada de llamadas en paralelo.** Por defecto se hace una llamada cada vez; quien quiera ir más rápido puede subirlo con `--max-workers`, sabiendo que se aparta de la recomendación.
- **Páginas del tamaño máximo** (10.000 registros por llamada) y siempre **todas las páginas**, que es lo que hace `bdns-fetch` por defecto. Una respuesta cortada a una sola página pasa desapercibida (nos ocurrió con `grandesbeneficiarios_busqueda`, que llegó a devolver 10.000 filas de 142.260), y por eso `bdns-fetch` avisa cuando deja páginas sin descargar.
- **Descargas diarias, semanales, mensuales y anuales por fecha de registro**, tal y como propone la propia guía para mantener las concesiones al día.
- **No se usa el endpoint `terceros`**, porque la guía lo considera inútil: `concesiones_busqueda` ya trae los datos del beneficiario.
- **Se comprueba qué ha desaparecido para detectar bajas.** Las concesiones se retiran del portal cuando pasan los cuatro años naturales siguientes a la concesión. En las entidades completas, las bajas se detectan comparando con todo lo que existe; en las incrementales grandes, donde esa comparación sería demasiado cara, se compara solo dentro del periodo de fecha de registro que se está sincronizando (lo explicamos en [detección de bajas por periodo](sync-behavior.md#windowed-deletions)).
