# -*- coding: utf-8 -*-
"""
Integration tests for commands with enum parameters.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.reglamentos import reglamentos
from bdns.fetch.commands.grandesbeneficiarios_anios import grandesbeneficiarios_anios
from bdns.fetch.commands.convocatorias_ultimas import convocatorias_ultimas
from bdns.fetch.types import Ambito


@pytest.mark.integration
class TestEnumCommandsIntegration:
    """Integration tests for commands with enum parameters."""

    def test_reglamentos_real_api_concesiones(
        self, get_test_context, cleanup_test_file
    ):
        """Test reglamentos command with real API - Concesiones scope."""
        # Arrange
        ctx, output_path = get_test_context("reglamentos_concesiones.csv")

        try:
            # Act - Test with Ambito.C (Concesiones)
            reglamentos(ctx, vpd="GE", ambtio=Ambito.C)

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
            reglamentos(ctx, vpd="GE", ambtio=Ambito.A)

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

    def test_convocatorias_ultimas_real_api(self, get_test_context, cleanup_test_file):
        """Test convocatorias_ultimas command with real API - basic test."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias_ultimas.csv")

        try:
            # Act - Test with basic parameters (pageSize=10 to keep response small)
            convocatorias_ultimas(
                ctx,
                vpd="GE",
                pageSize=10,
                num_pages=1,
                from_page=0,
                order=None,
                direccion=None,
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

            print(f"✅ Success: Retrieved {len(data)} latest convocatorias records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
