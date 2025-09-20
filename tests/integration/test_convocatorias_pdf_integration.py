# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias_pdf endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestConvocatoriaspdfIntegration:
    """Integration tests for the convocatorias_pdf endpoint."""

    def test_convocatorias_pdf_real_api(self):
        """Test convocatorias_pdf endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act - Test binary endpoint with documented working parameters
        # Using values from API documentation: id=608268, vpd="A07"
        data = client.fetch_convocatorias_pdf(id=608268, vpd="A07")

        # Assert - This endpoint should actually work and return PDF data
        assert isinstance(data, bytes), "Should return binary data (bytes)"
        assert len(data) > 0, "Should return actual PDF data, not empty bytes"

        # Check if it looks like a PDF (starts with %PDF)
        assert data[:4] == b"%PDF", f"Should return valid PDF data, got: {data[:10]}"
        print(f"✅ Success: Retrieved valid PDF document ({len(data)} bytes)")
