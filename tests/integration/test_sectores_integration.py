# -*- coding: utf-8 -*-
"""
Integration tests for the sectores endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestSectoresIntegration:
    """Integration tests for the sectores endpoint."""

    def test_sectores_real_api(self):
        """Test sectores endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_sectores()
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Assert all elements are dicts
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} sectores records")
        print(f"Available fields: {list(data[0].keys())}")
