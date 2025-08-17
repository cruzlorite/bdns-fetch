# -*- coding: utf-8 -*-
"""
Integration tests for strategic plans related commands.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.api.commands.planesestrategicos_busqueda import planesestrategicos_busqueda
from bdns.api.commands.planesestrategicos_vigencia import planesestrategicos_vigencia


@pytest.mark.integration
class TestPlanesEstrategicosIntegration:
    """Integration tests for strategic plans commands."""

    def test_planesestrategicos_vigencia(self, get_test_context, cleanup_test_file):
        """Test planesestrategicos_vigencia command."""
        # Arrange
        ctx, output_path = get_test_context("planesestrategicos_vigencia.csv")

        try:
            # Act
            planesestrategicos_vigencia(ctx)

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
                f"✅ Success: Retrieved {len(data)} planes estrategicos vigencia records"
            )
            if len(data) > 0:
                print(f"Sample: {data[0]}")

        finally:
            cleanup_test_file(output_path)

    def test_planesestrategicos_busqueda_basic(
        self, get_test_context, cleanup_test_file
    ):
        """Test planesestrategicos_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("planesestrategicos_busqueda.csv")

        try:
            # Act - Test with basic parameters (minimal to avoid complex free text)
            planesestrategicos_busqueda(
                ctx,
                vigenciaDesde=None,  # Explicitly pass None for date parameters
                vigenciaHasta=None,
                pageSize=5,
                num_pages=1,
                from_page=0,
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
                f"✅ Success: Retrieved {len(data)} planes estrategicos search results"
            )
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
