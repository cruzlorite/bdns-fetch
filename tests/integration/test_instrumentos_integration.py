# -*- coding: utf-8 -*-
"""
Integration tests for the instrumentos endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestInstrumentosIntegration:
    """Integration tests for the instrumentos endpoint."""

    def test_instrumentos_real_api(self):
        """Test instrumentos endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_instrumentos(vpd="GE")
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Assert all elements are dicts
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} instrumentos records")
        print(f"Available fields: {list(data[0].keys())}")
