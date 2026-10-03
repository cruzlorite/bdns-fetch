# SPDX-License-Identifier: GPL-3.0-or-later

"""Enumerations for the BDNS API parameters that take a closed set of values.

Member names match what the API documents, so they read the same as the
query parameter values they stand for.
"""

from enum import Enum

__all__ = [
    "Ambito",
    "DescripcionTipoBusqueda",
    "Direccion",
    "Order",
    "TipoAdministracion",
]


class Order(str, Enum):
    """Field to sort search results by (`order`)."""

    nivel1 = "nivel1"
    nivel2 = "nivel2"
    nivel3 = "nivel3"
    codConcesion = "codConcesion"
    numeroConvocatoria = "numeroConvocatoria"
    convocatoria = "convocatoria"
    descripcionCooficial = "descripcionCooficial"
    instrumento = "instrumento"
    urlBR = "urlBR"
    fechaConcesion = "fechaConcesion"
    beneficiario = "beneficiario"
    importe = "importe"
    ayudaEquivalente = "ayudaEquivalente"
    tieneProyecto = "tieneProyecto"


class Direccion(str, Enum):
    """Sort direction (`direccion`)."""

    asc = "asc"
    desc = "desc"


class TipoAdministracion(str, Enum):
    """Type of administrative body (`tipoAdministracion`, `idAdmon`)."""

    C = "C"  # Administración del Estado
    A = "A"  # Comunidad Autónoma
    L = "L"  # Entidad Local
    O = "O"  # Otros órganos


class DescripcionTipoBusqueda(str, Enum):
    """How `descripcion` is matched (`descripcionTipoBusqueda`)."""

    exacta = "0"  # Frase exacta
    todas = "1"  # Todas las palabras
    alguna = "2"  # Alguna palabra


class Ambito(str, Enum):
    """Area a search runs over (`ambito`)."""

    C = "C"  # Concesiones
    A = "A"  # Ayudas de Estado
    M = "M"  # de Minimis
    S = "S"  # Sanciones
    P = "P"  # Partidos políticos
    G = "G"  # Grandes beneficiarios
