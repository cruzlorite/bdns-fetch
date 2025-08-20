# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias_ultimas command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.convocatorias_ultimas import convocatorias_ultimas


@pytest.mark.integration
class TestConvocatoriasUltimasIntegration:
    """Integration tests for the convocatorias_ultimas command."""

    def test_convocatorias_ultimas_real_api(self, get_test_context, cleanup_test_file):
        """Test convocatorias_ultimas command with real API - basic test."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias_ultimas.csv")

        try:
            # Act - Test with basic parameters (pageSize=10 to keep response small)
            convocatorias_ultimas(
                ctx,
                vpd="GE",
                pageSize=10,
                num_pages=1,
                from_page=0,
                order=None,
                direccion=None,
            )

            # Assert
            assert output_path.exists(), (
                f"Output file should be created at {output_path}"
            )

            # Read and validate JSON data (JSONL format)
            data = []
            with open(output_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line.strip()))

            print(f"✅ Success: Retrieved {len(data)} latest convocatorias records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
