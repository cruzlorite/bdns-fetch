# 0006. La línea de comandos se genera a partir del cliente

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Cuando una herramienta de línea de comandos se construye sobre una librería, es fácil acabar metiendo detalles de la terminal dentro de la librería: valores por defecto que son objetos de Typer, excepciones que recomiendan usar tal o cual opción... Entonces el cliente no se puede usar, tipar ni documentar sin arrastrar con él la parte de la terminal. Las firmas engañan, el editor muestra objetos del framework y mkdocstrings no puede generar una referencia útil.

La alternativa habitual, escribir los comandos a mano, obliga a mantener en dos sitios cada endpoint y cada parámetro, con sus tipos y valores por defecto, y tarde o temprano las dos listas acaban siendo distintas.

## Decisión

El cliente es Python normal y no importa nada de la línea de comandos. La línea de comandos crea un comando por cada método `fetch_*` leyendo su firma: de ahí salen los tipos, los valores por defecto y qué parámetros son obligatorios. Del catálogo de [`options`][bdns.fetch.options] solo salen el nombre de cada opción y su texto de ayuda, una sola vez por parámetro aunque lo usen veinte endpoints. Las pistas que se muestran al usuario cuando hay un error se generan en la línea de comandos a partir de los datos del error.

## Consecuencias

- Al añadir un endpoint al cliente aparece su comando, sin una segunda lista que mantener.
- El cliente y la línea de comandos no pueden tener valores por defecto ni tipos distintos.
- Un test comprueba que todos los parámetros del cliente tienen su opción y su ayuda.
- Lo que la línea de comandos necesita hacer distinto del cliente es poco y está a la vista ([`CLI_DEFAULTS`][bdns.fetch.options.CLI_DEFAULTS]: por ejemplo, una página por defecto en lugar de todas).
