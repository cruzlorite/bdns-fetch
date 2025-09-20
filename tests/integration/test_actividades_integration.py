# -*- coding: utf-8 -*-
"""
Integration tests for the actividades endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestActividadesIntegration:
    """Integration tests for the actividades endpoint."""

    def test_actividades_real_api(self):
        """Test actividades endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_actividades(vpd="GE")
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Assert all elements are dicts
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} actividades records")
        print(f"Available fields: {list(data[0].keys())}")
