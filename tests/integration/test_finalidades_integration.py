# -*- coding: utf-8 -*-
"""
Integration tests for the finalidades command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.finalidades import finalidades


@pytest.mark.integration
class TestFinalidadesIntegration:
    """Integration tests for the finalidades command."""

    def test_finalidades_real_api(self, get_test_context, cleanup_test_file):
        """Test finalidades command with real API."""
        # Arrange
        ctx, output_path = get_test_context("finalidades.csv")

        try:
            # Act
            finalidades(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some finalidades data"

            print(f"✅ Success: Retrieved {len(data)} finalidades records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
