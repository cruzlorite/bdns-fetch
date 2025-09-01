# -*- coding: utf-8 -*-
"""
Integration tests for the terceros endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestTercerosIntegration:
    """Integration tests for the terceros endpoint."""

    def test_terceros_real_api(self):
        """Test terceros endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_terceros(
            vpd="A02", ambito="C", busqueda="asociacion"
        )
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Validate data structure
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} terceros records")
        print(f"Available fields: {list(data[0].keys())}")
