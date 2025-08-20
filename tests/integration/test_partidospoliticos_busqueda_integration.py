# -*- coding: utf-8 -*-
"""
Integration tests for the partidospoliticos_busqueda command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime

from bdns.fetch.commands.partidospoliticos_busqueda import partidospoliticos_busqueda


@pytest.mark.integration
class TestPartidospoliticosBusquedaIntegration:
    """Integration tests for the partidospoliticos_busqueda command."""

    def test_partidospoliticos_busqueda_basic(
        self, get_test_context, cleanup_test_file
    ):
        """Test partidospoliticos_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("partidospoliticos_busqueda.csv")

        try:
            # Act - Test with basic parameters (broader date range)
            partidospoliticos_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2022, 1, 1),
                fechaHasta=datetime(2024, 12, 31),
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
                f"✅ Success: Retrieved {len(data)} partidos politicos search results"
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

    def test_partidospoliticos_busqueda_basic_alternative(
        self, get_test_context, cleanup_test_file
    ):
        """Test partidospoliticos_busqueda command with basic parameters - alternative test from remaining commands."""
        # Arrange
        ctx, output_path = get_test_context("partidospoliticos_busqueda.csv")

        try:
            # Act - Test with proper date range and valid parameters
            partidospoliticos_busqueda(
                ctx,
                vpd="GE",
                fechaDesde=datetime(2022, 1, 1),  # Use proper datetime objects
                fechaHasta=datetime(2024, 12, 31),
                pageSize=5,
                num_pages=1,
                from_page=0,
            )

            # Assert
            assert os.path.exists(output_path), "Output file should exist"
            assert os.path.getsize(output_path) > 0, "Output file should not be empty"

            # Check file contents
            content = Path(output_path).read_text()
            assert "nivel" in content or "descripcion" in content or "id" in content, (
                "File should contain valid data"
            )

            print("✅ Success: Retrieved partidospoliticos busqueda records")

        except Exception as e:
            pytest.fail(f"partidospoliticos_busqueda command failed: {e}")

        finally:
            cleanup_test_file(output_path)
