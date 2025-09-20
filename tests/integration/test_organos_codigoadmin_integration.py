# -*- coding: utf-8 -*-
"""
Integration tests for the organos_codigoadmin endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestOrganoscodigoadminIntegration:
    """Integration tests for the organos_codigoadmin endpoint."""

    def test_organos_codigoadmin_real_api(self):
        """Test organos_codigoadmin endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_organos_codigoadmin(codigoAdmin="C31")
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Must return at least one element"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} organos_codigoadmin records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
