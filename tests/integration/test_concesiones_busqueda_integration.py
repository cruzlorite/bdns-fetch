# -*- coding: utf-8 -*-
"""
Integration tests for the concesiones_busqueda endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from datetime import datetime

from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestConcesionesbusquedaIntegration:
    """Integration tests for the concesiones_busqueda endpoint."""

    def test_concesiones_busqueda_real_api(self):
        """Test concesiones_busqueda endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_concesiones_busqueda(
            vpd="GE",
            pageSize=10,
            num_pages=1,
            from_page=0,
            fechaDesde=datetime(2015, 1, 1),
            fechaHasta=datetime(2024, 12, 31),
        )
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Assert all elements are dicts
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} concesiones_busqueda records")
        print(f"Available fields: {list(data[0].keys())}")
