# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestConvocatoriasIntegration:
    """Integration tests for the convocatorias endpoint."""

    def test_convocatorias_real_api(self):
        """Test convocatorias endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_convocatorias(vpd="GE", numConv="123456")
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Should return some convocatorias data"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} convocatorias records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
