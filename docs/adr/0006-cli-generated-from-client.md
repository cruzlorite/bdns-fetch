# 0006. El CLI se genera a partir del cliente

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Un CLI construido sobre una librería tienta a meter detalles del CLI en
la librería: valores por defecto que son objetos de Typer, excepciones que
sugieren flags. Entonces el cliente no se puede usar, tipar ni documentar
sin arrastrar el CLI: las firmas mienten, el editor muestra objetos del
framework y mkdocstrings no puede generar una referencia útil.

La alternativa habitual, escribir los comandos a mano, duplica en dos
listas cada endpoint y cada parámetro, con sus tipos y valores por
defecto, que acaban divergiendo.

## Decisión

El cliente es Python normal, sin importar nada del CLI. El CLI construye
un comando por cada método `fetch_*` leyendo su firma: tipos, valores por
defecto y obligatoriedad salen de ahí. Del catálogo de
[`options`][bdns.fetch.options] solo salen el nombre del flag y el texto
de ayuda, uno por parámetro aunque lo usen veinte endpoints. Las pistas
para el usuario se generan en el CLI a partir de los campos del error.

## Consecuencias

- Añadir un endpoint al cliente añade el comando: no hay una segunda
  lista que mantener.
- Cliente y CLI no pueden discrepar en un default o un tipo.
- Un test comprueba que todo parámetro del cliente tiene flag y ayuda.
- Lo que el CLI necesita distinto del cliente es explícito y escaso
  ([`CLI_DEFAULTS`][bdns.fetch.options.CLI_DEFAULTS]: una página por
  defecto en vez de todas).
