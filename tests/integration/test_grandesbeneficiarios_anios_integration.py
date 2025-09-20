# -*- coding: utf-8 -*-
"""
Integration tests for the grandesbeneficiarios_anios endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestGrandesbeneficiariosaniosIntegration:
    """Integration tests for the grandesbeneficiarios_anios endpoint."""

    def test_grandesbeneficiarios_anios_real_api(self):
        """Test grandesbeneficiarios_anios endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_grandesbeneficiarios_anios()
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Should return some grandesbeneficiarios_anios data"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} grandesbeneficiarios_anios records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
