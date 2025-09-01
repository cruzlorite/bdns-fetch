# -*- coding: utf-8 -*-
"""
Integration tests for the organos endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.types import TipoAdministracion

from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestOrganosIntegration:
    """Integration tests for the organos endpoint."""

    def test_organos_real_api(self):
        """Test organos endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_organos(vpd="GE", idAdmon=TipoAdministracion.L)
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Should return some organos data"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} organos records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
