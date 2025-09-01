# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias_ultimas endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestConvocatoriasultimasIntegration:
    """Integration tests for the convocatorias_ultimas endpoint."""

    def test_convocatorias_ultimas_real_api(self):
        """Test convocatorias_ultimas endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_convocatorias_ultimas(vpd="GE")
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Should return some convocatorias_ultimas data"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} convocatorias_ultimas records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
