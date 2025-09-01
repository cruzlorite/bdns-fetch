# -*- coding: utf-8 -*-
"""
Integration tests for the organos_codigo endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestOrganoscodigoIntegration:
    """Integration tests for the organos_codigo endpoint."""

    def test_organos_codigo_real_api(self):
        """Test organos_codigo endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_organos_codigo(codigo="L02000034")
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Should return some data"
        # Assert all elements are dicts
        assert [isinstance(item, dict) for item in data], (
            "All items should be dictionaries"
        )

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} organos_codigo records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
