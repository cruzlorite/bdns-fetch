# -*- coding: utf-8 -*-
"""
Integration tests for the grandesbeneficiarios_anios command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.grandesbeneficiarios_anios import grandesbeneficiarios_anios


@pytest.mark.integration
class TestGrandesbeneficiariosAniosIntegration:
    """Integration tests for the grandesbeneficiarios_anios command."""

    def test_grandesbeneficiarios_anios_real_api(
        self, get_test_context, cleanup_test_file
    ):
        """Test grandesbeneficiarios_anios command with real API."""
        # Arrange
        ctx, output_path = get_test_context("grandesbeneficiarios_anios.csv")

        try:
            # Act
            grandesbeneficiarios_anios(ctx)

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

            assert len(data) > 0, "Should return some years data"

            print(
                f"✅ Success: Retrieved {len(data)} available years for grandes beneficiarios"
            )
            if len(data) > 0:
                print(f"Sample year: {data[0]}")

        finally:
            cleanup_test_file(output_path)
