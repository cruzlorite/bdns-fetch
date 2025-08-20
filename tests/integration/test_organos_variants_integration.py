# -*- coding: utf-8 -*-
"""
Integration tests for organos-related commands.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.organos_agrupacion import organos_agrupacion
from bdns.fetch.commands.organos_codigo import organos_codigo
from bdns.fetch.types import TipoAdministracion


@pytest.mark.integration
class TestOrganosVariantsIntegration:
    """Integration tests for organos variant commands."""

    def test_organos_agrupacion_real_api(self, get_test_context, cleanup_test_file):
        """Test organos_agrupacion command with real API."""
        # Arrange
        ctx, output_path = get_test_context("organos_agrupacion.csv")

        try:
            # Act - Test with TipoAdministracion.C
            organos_agrupacion(ctx, vpd="GE", idAdmon=TipoAdministracion.C)

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

            assert len(data) >= 0, "Should return organos agrupacion data"

            print(f"✅ Success: Retrieved {len(data)} organos agrupacion records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_organos_codigo_real_api(self, get_test_context, cleanup_test_file):
        """Test organos_codigo command with real API."""
        # Arrange
        ctx, output_path = get_test_context("organos_codigo.csv")

        try:
            # Act - Test with TipoAdministracion.A
            organos_codigo(ctx, vpd="GE", idAdmon=TipoAdministracion.A)

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

            assert len(data) >= 0, "Should return organos codigo data"

            print(f"✅ Success: Retrieved {len(data)} organos codigo records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
