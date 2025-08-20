# -*- coding: utf-8 -*-
"""
Integration tests for the reglamentos command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.reglamentos import reglamentos
from bdns.fetch.types import Ambito


@pytest.mark.integration
class TestReglamentosIntegration:
    """Integration tests for the reglamentos command."""

    def test_reglamentos_real_api_concesiones(
        self, get_test_context, cleanup_test_file
    ):
        """Test reglamentos command with real API - Concesiones scope."""
        # Arrange
        ctx, output_path = get_test_context("reglamentos_concesiones.csv")

        try:
            # Act - Test with Ambito.C (Concesiones)
            reglamentos(ctx, vpd="GE", ambito=Ambito.C)

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

            print(
                f"✅ Success: Retrieved {len(data)} reglamentos records for Concesiones"
            )
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_reglamentos_real_api_ayudas_estado(
        self, get_test_context, cleanup_test_file
    ):
        """Test reglamentos command with real API - Ayudas de Estado scope."""
        # Arrange
        ctx, output_path = get_test_context("reglamentos_ayudas.csv")

        try:
            # Act - Test with Ambito.A (Ayudas de Estado)
            reglamentos(ctx, vpd="GE", ambito=Ambito.A)

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

            print(
                f"✅ Success: Retrieved {len(data)} reglamentos records for Ayudas de Estado"
            )
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
