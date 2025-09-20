# -*- coding: utf-8 -*-
"""
Integration tests for the reglamentos endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest

from bdns.fetch.client import BDNSClient
from bdns.fetch.types import Ambito


@pytest.mark.integration
class TestReglamentosIntegration:
    """Integration tests for the reglamentos endpoint."""

    def test_reglamentos_real_api(self):
        """Test reglamentos endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_reglamentos(vpd="GE", ambito=Ambito.C)
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} reglamentos records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
