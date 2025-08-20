# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Created on Sat May 17 16:23:45 2025
Author: josemariacruzlorite@gmail.com
"""

from enum import Enum


class Order(str, Enum):
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
    asc = "asc"
    desc = "desc"


class TipoAdministracion(str, Enum):
    C = "C"  # Administración del Estado
    A = "A"  # Comunidad Autónoma
    L = "L"  # Entidad Local
    O = "O"  # Otros Órganos  # noqa: E741


class DescripcionTipoBusqueda(str, Enum):
    exacta = "0"  # Frase exacta
    todas = "1"  # Todas las palabras
    alguna = "2"  # Alguna palabra


class Ambito(str, Enum):
    C = "C"  # Concesiones
    A = "A"  # Ayudas de Estado
    M = "M"  # de Minimis
    S = "S"  # Sanciones
    P = "P"  # Partidos políticos
    G = "G"  # Grandes Beneficiarios
