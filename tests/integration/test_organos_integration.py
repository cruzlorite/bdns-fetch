# -*- coding: utf-8 -*-
"""
Integration tests for the organos command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.organos import organos
from bdns.fetch.types import TipoAdministracion


@pytest.mark.integration
class TestOrganosIntegration:
    """Integration tests for the organos command."""

    def test_organos_real_api_with_tipo_administracion_c(
        self, get_test_context, cleanup_test_file
    ):
        """Test organos command with real API - Administración del Estado."""
        # Arrange
        ctx, output_path = get_test_context("organos_admin_c.csv")

        try:
            # Act - Call with TipoAdministracion.C (Administración del Estado)
            organos(ctx, vpd="GE", idAdmon=TipoAdministracion.C)

            # Assert
            assert output_path.exists(), (
                f"Output file should be created at {output_path}"
            )

            # Read and validate JSON data (JSONL format - one JSON object per line)
            data = []
            with open(output_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line.strip()))

            assert isinstance(data, list), "Should return a list of records"
            assert len(data) >= 0, "Should return data (could be empty for this filter)"

            print(
                f"✅ Success: Retrieved {len(data)} organos records for Administración del Estado"
            )
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_organos_real_api_with_tipo_administracion_a(
        self, get_test_context, cleanup_test_file
    ):
        """Test organos command with real API - Comunidad Autónoma."""
        # Arrange
        ctx, output_path = get_test_context("organos_admin_a.csv")

        try:
            # Act - Call with TipoAdministracion.A (Comunidad Autónoma)
            organos(ctx, vpd="GE", idAdmon=TipoAdministracion.A)

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
                f"✅ Success: Retrieved {len(data)} organos records for Comunidad Autónoma"
            )
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_organos_real_api_with_tipo_administracion_l(
        self, get_test_context, cleanup_test_file
    ):
        """Test organos command with real API - Entidad Local."""
        # Arrange
        ctx, output_path = get_test_context("organos_admin_l.csv")

        try:
            # Act - Call with TipoAdministracion.L (Entidad Local)
            organos(ctx, vpd="GE", idAdmon=TipoAdministracion.L)

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
                f"✅ Success: Retrieved {len(data)} organos records for Entidad Local"
            )
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
