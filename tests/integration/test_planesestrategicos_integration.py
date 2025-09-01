# -*- coding: utf-8 -*-
"""
Integration tests for the planesestrategicos endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestPlanesestrategicosIntegration:
    """Integration tests for the planesestrategicos endpoint."""

    def test_planesestrategicos_real_api(self):
        """Test planesestrategicos endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_planesestrategicos(idPES=1)
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Should return some planesestrategicos data"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} planesestrategicos records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
