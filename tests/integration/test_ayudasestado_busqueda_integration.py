# -*- coding: utf-8 -*-
"""
Integration tests for the ayudasestado_busqueda command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json
from datetime import datetime

from bdns.fetch.commands.ayudasestado_busqueda import ayudasestado_busqueda
from bdns.fetch.types import TipoAdministracion


@pytest.mark.integration
class TestAyudasestadoBusquedaIntegration:
    """Integration tests for the ayudasestado_busqueda command."""

    def test_ayudasestado_busqueda_basic(self, get_test_context, cleanup_test_file):
        """Test ayudasestado_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("ayudasestado_busqueda.csv")

        try:
            # Act - Test with basic parameters only (no free text)
            ayudasestado_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2020, 1, 1),
                fechaHasta=datetime(2020, 12, 31),
                tipoAdministracion=TipoAdministracion.C,
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

            print(f"✅ Success: Retrieved {len(data)} ayudas estado search results")
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
