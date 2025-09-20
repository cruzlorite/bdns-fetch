# -*- coding: utf-8 -*-
"""
Integration tests for the organos_agrupacion endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.types import TipoAdministracion

from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestOrganosagrupacionIntegration:
    """Integration tests for the organos_agrupacion endpoint."""

    def test_organos_agrupacion_real_api(self):
        """Test organos_agrupacion endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act
        data_generator = client.fetch_organos_agrupacion(
            vpd="GE", idAdmon=TipoAdministracion.L
        )
        data = list(data_generator)

        # Assert
        assert len(data) > 0, "Should return some organos_agrupacion data"

        # Validate data structure if we have data
        if len(data) > 0:
            for record in data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each record should be a dictionary"

        print(f"✅ Success: Retrieved {len(data)} organos_agrupacion records")
        if len(data) > 0:
            print(f"Available fields: {list(data[0].keys())}")
