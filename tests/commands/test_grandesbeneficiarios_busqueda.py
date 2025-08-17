# -*- coding: utf-8 -*-
"""
Tests for the grandesbeneficiarios_busqueda command.
"""
import pytest
from unittest.mock import Mock

from bdns.api.commands.grandesbeneficiarios_busqueda import grandesbeneficiarios_busqueda
from bdns.api.types import Order, Direccion


class TestGrandesBeneficiariosBusquedaCommand:
    """Test class for the grandesbeneficiarios_busqueda command."""

    def test_grandesbeneficiarios_busqueda_with_defaults(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_asyncio_run
    ):
        """Test grandesbeneficiarios_busqueda command with default parameters."""
        # Arrange
        mock_typer_context.obj["max_concurrent_requests"] = 5
        
        # Act
        grandesbeneficiarios_busqueda(mock_typer_context)

        # Assert
        mock_asyncio_run.assert_called_once()

    def test_grandesbeneficiarios_busqueda_with_search_parameters(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_asyncio_run
    ):
        """Test grandesbeneficiarios_busqueda command with search parameters."""
        # Arrange
        mock_typer_context.obj["max_concurrent_requests"] = 10
        
        # Act
        grandesbeneficiarios_busqueda(
            mock_typer_context,
            vpd="TEST",
            anios="2022,2023",
            nifCif="12345678A",
            beneficiario=12345
        )

        # Assert
        mock_asyncio_run.assert_called_once()

    def test_grandesbeneficiarios_busqueda_with_pagination(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_asyncio_run
    ):
        """Test grandesbeneficiarios_busqueda command with pagination parameters."""
        # Arrange
        mock_typer_context.obj["max_concurrent_requests"] = 5
        
        # Act
        grandesbeneficiarios_busqueda(
            mock_typer_context,
            num_pages=5,
            from_page=2,
            pageSize=100
        )

        # Assert
        mock_asyncio_run.assert_called_once()

    def test_grandesbeneficiarios_busqueda_with_ordering(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_asyncio_run
    ):
        """Test grandesbeneficiarios_busqueda command with ordering parameters."""
        # Arrange
        mock_typer_context.obj["max_concurrent_requests"] = 5
        
        # Act
        grandesbeneficiarios_busqueda(
            mock_typer_context,
            order=Order.BENEFICIARIO,
            direccion=Direccion.DESC
        )

        # Assert
        mock_asyncio_run.assert_called_once()

    def test_grandesbeneficiarios_busqueda_context_object_access(
        self, mock_typer_context, mock_fetch_and_write_paginated, 
        mock_format_url, mock_asyncio_run
    ):
        """Test that the command accesses context object properties correctly."""
        # Arrange
        mock_typer_context.obj = {
            "output_file": "/test/output.json",
            "max_concurrent_requests": 15
        }
        
        # Act
        grandesbeneficiarios_busqueda(mock_typer_context)

        # Assert
        mock_asyncio_run.assert_called_once()
        # The context object values should be accessed within the async call
