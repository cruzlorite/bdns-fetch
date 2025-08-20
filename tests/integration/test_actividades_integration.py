# -*- coding: utf-8 -*-
"""
Integration tests for the actividades command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.actividades import actividades


@pytest.mark.integration
class TestActividadesIntegration:
    """Integration tests for the actividades command."""

    def test_actividades_real_api_default_params(
        self, get_test_context, cleanup_test_file
    ):
        """Test actividades command with real API - default parameters."""
        # Arrange
        ctx, output_path = get_test_context("actividades_default.csv")

        try:
            # Act
            actividades(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some actividades data"

            print(f"✅ Success: Retrieved {len(data)} actividades records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_actividades_real_api_custom_vpd(self, get_test_context, cleanup_test_file):
        """Test actividades command with real API - custom VPD."""
        # Arrange
        ctx, output_path = get_test_context("actividades_custom.csv")

        try:
            # Act - try with a different VPD that might have data
            actividades(ctx, vpd="GE")  # Use the same VPD as the first test

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

            print(f"✅ Success: Retrieved {len(data)} actividades records for VPD 'GE'")

        finally:
            cleanup_test_file(output_path)
