# -*- coding: utf-8 -*-
"""
Integration tests for the planesestrategicos_busqueda endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestPlanesestrategicosbusquedaIntegration:
    """Integration tests for the planesestrategicos_busqueda endpoint."""

    def test_planesestrategicos_busqueda_real_api(self):
        """Test planesestrategicos_busqueda endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_planesestrategicos_busqueda(
            vpd="GE", pageSize=5, num_pages=1, from_page=0
        )
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Validate data structure
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} planesestrategicos_busqueda records")
        print(f"Available fields: {list(data[0].keys())}")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
