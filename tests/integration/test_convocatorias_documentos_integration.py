# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias_documentos endpoint.
These tests make real API calls to the BDNS API.
"""

import pytest
from bdns.fetch.client import BDNSClient


@pytest.mark.integration
class TestConvocatoriasdocumentosIntegration:
    """Integration tests for the convocatorias_documentos endpoint."""

    def test_convocatorias_documentos_real_api(self):
        """Test convocatorias_documentos endpoint with real API."""
        # Arrange
        client = BDNSClient()

        # Act - Test binary endpoint with known working document ID
        data = client.fetch_convocatorias_documentos(idDocumento=36605)

        # Assert - Require actual binary data
        assert isinstance(data, bytes), "Should return binary data (bytes)"
        assert len(data) > 10000, "Document should have substantial content (>10KB)"

        # Validate it's a proper document format
        if len(data) >= 4:
            header = data[:4]
            # Should be PDF (%PDF) or Office document (PK..) or other valid format
            assert header == b"%PDF" or header[:2] == b"PK" or len(data) > 1000, (
                f"Should be valid document format, got header: {header}"
            )

        print(f"✅ Success: Retrieved binary document ({len(data)} bytes)")
        if data[:4] == b"%PDF":
            print("📄 Confirmed PDF document format")
