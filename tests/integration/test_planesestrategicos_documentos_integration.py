# -*- coding: utf-8 -*-
"""
Integration tests for the planesestrategicos_documentos endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestPlanesestrategicosdocumentosIntegration:
    """Integration tests for the planesestrategicos_documentos endpoint."""

    def test_planesestrategicos_documentos_real_api(self):
        """Test planesestrategicos_documentos endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act - Test binary endpoint with valid document ID from a real strategic plan
        # Using document ID 1272508 from strategic plan 1711
        data = client.fetch_planesestrategicos_documentos(idDocumento=1272508)

        # Assert - This endpoint should actually work and return document data
        assert isinstance(data, bytes), "Should return binary data (bytes)"
        assert len(data) > 0, "Should return actual document data, not empty bytes"
        print(f"✅ Success: Retrieved strategic plan document ({len(data)} bytes)")
