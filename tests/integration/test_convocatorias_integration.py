# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.convocatorias import convocatorias


@pytest.mark.integration
class TestConvocatoriasIntegration:
    """Integration tests for the convocatorias command."""

    def test_convocatorias_with_known_id(self, get_test_context, cleanup_test_file):
        """Test convocatorias command with a known convocatoria number."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias.csv")

        try:
            # Act - Test with a common convocatoria format (try a simple number)
            convocatorias(ctx, vpd="GE", numConv="123456")

            # Assert
            assert output_path.exists(), (
                f"Output file should be created at {output_path}"
            )

            # Read and validate JSON data
            data = []
            with open(output_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line.strip()))

            print(f"✅ Success: Retrieved {len(data)} convocatoria records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
