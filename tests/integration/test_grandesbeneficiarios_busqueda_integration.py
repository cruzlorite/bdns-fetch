# -*- coding: utf-8 -*-
"""
Integration tests for the grandesbeneficiarios_busqueda command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.grandesbeneficiarios_busqueda import (
    grandesbeneficiarios_busqueda,
)


@pytest.mark.integration
class TestGrandesbeneficiariosBusquedaIntegration:
    """Integration tests for the grandesbeneficiarios_busqueda command."""

    def test_grandesbeneficiarios_busqueda_basic(
        self, get_test_context, cleanup_test_file
    ):
        """Test grandesbeneficiarios_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("grandesbeneficiarios_busqueda.csv")

        try:
            # Act - Test with basic parameters (using a common year)
            grandesbeneficiarios_busqueda(
                ctx, anio="2023", pageSize=5, num_pages=1, from_page=0
            )

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

            print(
                f"✅ Success: Retrieved {len(data)} grandes beneficiarios search results"
            )
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(
                    f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}"
                )

        finally:
            cleanup_test_file(output_path)
