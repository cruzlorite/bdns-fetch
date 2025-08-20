# -*- coding: utf-8 -*-
"""
Integration tests for the objetivos command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.objetivos import objetivos


@pytest.mark.integration
class TestObjetivosIntegration:
    """Integration tests for the objetivos command."""

    def test_objetivos_real_api(self, get_test_context, cleanup_test_file):
        """Test objetivos command with real API."""
        # Arrange
        ctx, output_path = get_test_context("objetivos.csv")

        try:
            # Act
            objetivos(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some objetivos data"

            print(f"✅ Success: Retrieved {len(data)} objetivos records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
