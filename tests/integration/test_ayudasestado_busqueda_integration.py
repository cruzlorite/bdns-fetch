# -*- coding: utf-8 -*-
"""
Integration tests for the ayudasestado_busqueda endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from datetime import datetime

from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestAyudasestadobusquedaIntegration:
    """Integration tests for the ayudasestado_busqueda endpoint."""

    def test_ayudasestado_busqueda_real_api(self):
        """Test ayudasestado_busqueda endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_ayudasestado_busqueda(
            vpd="GE",
            pageSize=5,
            num_pages=1,
            from_page=0,
            fechaDesde=datetime(2020, 1, 1),
            fechaHasta=datetime(2020, 12, 31),
        )
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Assert all elements are dicts
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} ayudasestado_busqueda records")
        print(f"Available fields: {list(data[0].keys())}")
