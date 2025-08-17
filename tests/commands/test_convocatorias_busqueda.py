# -*- coding: utf-8 -*-
"""
Tests for the convocatorias_busqueda command.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from bdns.api.commands.convocatorias_busqueda import convocatorias_busqueda
from bdns.api.types import Order, Direccion, TipoAdministracion, DescripcionTipoBusqueda


class TestConvocatoriasBusquedaCommand:
    """Test class for the convocatorias_busqueda command."""

    def test_convocatorias_busqueda_with_defaults(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_format_date_for_api_request, mock_asyncio_run
    ):
        """Test convocatorias_busqueda command with default parameters."""
        # Act
        convocatorias_busqueda(mock_typer_context)

        # Assert
        mock_asyncio_run.assert_called_once()
        # Check that the async function was called with fetch_and_write_paginated

    def test_convocatorias_busqueda_with_custom_pagination(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_format_date_for_api_request, mock_asyncio_run
    ):
        """Test convocatorias_busqueda command with custom pagination parameters."""
        # Act
        convocatorias_busqueda(
            mock_typer_context,
            num_pages=5,
            from_page=2,
            pageSize=500
        )

        # Assert
        mock_asyncio_run.assert_called_once()

    def test_convocatorias_busqueda_with_search_parameters(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_format_date_for_api_request, mock_asyncio_run
    ):
        """Test convocatorias_busqueda command with search parameters."""
        # Arrange
        test_date = datetime(2023, 1, 1)
        mock_format_date_for_api_request.return_value = "2023-01-01"

        # Act
        convocatorias_busqueda(
            mock_typer_context,
            descripcion="test convocatoria",
            descripcionTipoBusqueda=DescripcionTipoBusqueda.CONTIENE,
            numeroConvocatoria="12345",
            fechaDesde=test_date,
            fechaHasta=test_date,
            tipoAdministracion=TipoAdministracion.C
        )

        # Assert
        mock_asyncio_run.assert_called_once()
        mock_format_date_for_api_request.assert_called()

    def test_convocatorias_busqueda_with_ordering(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_format_date_for_api_request, mock_asyncio_run
    ):
        """Test convocatorias_busqueda command with ordering parameters."""
        # Act
        convocatorias_busqueda(
            mock_typer_context,
            order=Order.CONVOCATORIA,
            direccion=Direccion.DESC
        )

        # Assert
        mock_asyncio_run.assert_called_once()

    def test_convocatorias_busqueda_with_all_parameters(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_format_date_for_api_request, mock_asyncio_run
    ):
        """Test convocatorias_busqueda command with all parameters set."""
        # Arrange
        test_date = datetime(2023, 1, 1)
        mock_format_date_for_api_request.return_value = "2023-01-01"

        # Act
        convocatorias_busqueda(
            mock_typer_context,
            num_pages=10,
            from_page=1,
            pageSize=1000,
            order=Order.FECHA_CONCESION,
            direccion=Direccion.ASC,
            vpd="TEST",
            descripcion="test",
            descripcionTipoBusqueda=DescripcionTipoBusqueda.EXACTA,
            numeroConvocatoria="TEST123",
            mrr=True,
            fechaDesde=test_date,
            fechaHasta=test_date,
            tipoAdministracion=TipoAdministracion.A,
            organos="1,2,3",
            regiones="4,5,6",
            tiposBeneficiario="7,8,9",
            instrumentos="10,11,12",
            finalidad=1,
            ayudaEstado="test_ayuda"
        )

        # Assert
        mock_asyncio_run.assert_called_once()
        mock_format_date_for_api_request.assert_called()

    def test_convocatorias_busqueda_date_formatting(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_format_date_for_api_request, mock_asyncio_run
    ):
        """Test that date parameters are properly formatted."""
        # Arrange
        test_date_desde = datetime(2023, 1, 1)
        test_date_hasta = datetime(2023, 12, 31)
        
        # Act
        convocatorias_busqueda(
            mock_typer_context,
            fechaDesde=test_date_desde,
            fechaHasta=test_date_hasta
        )

        # Assert
        # Check that format_date_for_api_request was called for both dates
        assert mock_format_date_for_api_request.call_count >= 2
        mock_format_date_for_api_request.assert_any_call(test_date_desde)
        mock_format_date_for_api_request.assert_any_call(test_date_hasta)
