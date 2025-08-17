# -*- coding: utf-8 -*-
"""Integration tests for remaining BDNS API commands."""

import pytest
import os
from pathlib import Path

from bdns.api.commands.terceros import terceros
from bdns.api.commands.minimis_busqueda import minimis_busqueda
from bdns.api.commands.partidospoliticos_busqueda import partidospoliticos_busqueda
from bdns.api.types import Ambito


class TestRemainingCommandsIntegration:
    """Integration tests for remaining BDNS API commands."""

    def test_terceros_basic(self, get_test_context, cleanup_test_file):
        """Test terceros command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("terceros.csv")

        try:
            # Act - Test with required ambito parameter (State Aid)
            terceros(ctx, vpd="2024", ambito=Ambito.A, busqueda=None, idPersona=None)

            # Assert
            assert os.path.exists(output_path), "Output file should exist"
            assert os.path.getsize(output_path) > 0, "Output file should not be empty"

            # Check file contents
            content = Path(output_path).read_text()
            assert "nivel" in content or "descripcion" in content or "id" in content, (
                "File should contain valid data"
            )

            print("✅ Success: Retrieved terceros records")

        except Exception as e:
            pytest.fail(f"terceros command failed: {e}")

    def test_terceros_with_ambito(self, get_test_context, cleanup_test_file):
        """Test terceros command with ambito parameter."""
        # Arrange
        ctx, output_path = get_test_context("terceros_ambito.csv")

        try:
            # Act - Test with ambito parameter
            terceros(ctx, vpd="2024", ambito=Ambito.A, busqueda=None, idPersona=None)

            # Assert
            assert os.path.exists(output_path), "Output file should exist"
            assert os.path.getsize(output_path) > 0, "Output file should not be empty"

            # Check file contents
            content = Path(output_path).read_text()
            assert "nivel" in content or "descripcion" in content or "id" in content, (
                "File should contain valid data"
            )

            print("✅ Success: Retrieved terceros records with ambito A")

        except Exception as e:
            pytest.fail(f"terceros command with ambito failed: {e}")

    def test_minimis_busqueda_basic(self, get_test_context, cleanup_test_file):
        """Test minimis_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("minimis_busqueda.csv")

        try:
            # Act - Test with minimal parameters to avoid complex date/text issues
            minimis_busqueda(
                ctx,
                vpd="2024",
                fechaDesde=None,  # Explicitly pass None for date parameters
                fechaHasta=None,
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

            print("✅ Success: Retrieved minimis busqueda records")

        except Exception as e:
            pytest.fail(f"minimis_busqueda command failed: {e}")

    def test_partidospoliticos_busqueda_basic(
        self, get_test_context, cleanup_test_file
    ):
        """Test partidospoliticos_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("partidospoliticos_busqueda.csv")

        try:
            # Act - Test with minimal parameters to avoid complex date/text issues
            partidospoliticos_busqueda(
                ctx,
                vpd="2024",
                fechaDesde=None,  # Explicitly pass None for date parameters
                fechaHasta=None,
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
