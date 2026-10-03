# SPDX-License-Identifier: GPL-3.0-or-later

"""Paths of the BDNS API endpoints, relative to [`BDNS_API_BASE_URL`][bdns.fetch.endpoints.BDNS_API_BASE_URL].

Only the endpoints that have a `fetch_*` method are listed. Any other path
can be requested with [`BDNSClient.get`][bdns.fetch.client.BDNSClient.get].
"""

BDNS_API_BASE_URL = "https://www.infosubvenciones.es/bdnstrans/api"

# Catalogs
ACTIVIDADES = "/actividades"
BENEFICIARIOS = "/beneficiarios"
FINALIDADES = "/finalidades"
INSTRUMENTOS = "/instrumentos"
OBJETIVOS = "/objetivos"
REGIONES = "/regiones"
REGLAMENTOS = "/reglamentos"
SECTORES = "/sectores"
GRANDESBENEFICIARIOS_ANIOS = "/grandesbeneficiarios/anios"

# Administrative bodies
ORGANOS = "/organos"
ORGANOS_AGRUPACION = "/organos/agrupacion"
ORGANOS_CODIGO = "/organos/codigo"
ORGANOS_CODIGOADMIN = "/organos/codigoAdmin"

# Calls for applications
CONVOCATORIAS = "/convocatorias"
CONVOCATORIAS_BUSQUEDA = "/convocatorias/busqueda"
CONVOCATORIAS_ULTIMAS = "/convocatorias/ultimas"
CONVOCATORIAS_DOCUMENTOS = "/convocatorias/documentos"
CONVOCATORIAS_PDF = "/convocatorias/pdf"

# Searches
CONCESIONES_BUSQUEDA = "/concesiones/busqueda"
AYUDASESTADO_BUSQUEDA = "/ayudasestado/busqueda"
MINIMIS_BUSQUEDA = "/minimis/busqueda"
PARTIDOSPOLITICOS_BUSQUEDA = "/partidospoliticos/busqueda"
GRANDESBENEFICIARIOS_BUSQUEDA = "/grandesbeneficiarios/busqueda"
SANCIONES_BUSQUEDA = "/sanciones/busqueda"
TERCEROS = "/terceros"

# Strategic plans
PLANESESTRATEGICOS = "/planesestrategicos"
PLANESESTRATEGICOS_BUSQUEDA = "/planesestrategicos/busqueda"
PLANESESTRATEGICOS_DOCUMENTOS = "/planesestrategicos/documentos"
PLANESESTRATEGICOS_VIGENCIA = "/planesestrategicos/vigencia"
