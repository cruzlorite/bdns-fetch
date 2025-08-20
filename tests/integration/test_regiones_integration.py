# -*- coding: utf-8 -*-
"""
Integration tests for the regiones command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.regiones import regiones


@pytest.mark.integration
class TestRegionesIntegration:
    """Integration tests for the regiones command."""

    def test_regiones_real_api(self, get_test_context, cleanup_test_file):
        """Test regiones command with real API."""
        # Arrange
        ctx, output_path = get_test_context("regiones.csv")

        try:
            # Act
            regiones(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some regiones data"

            print(f"✅ Success: Retrieved {len(data)} regiones records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
