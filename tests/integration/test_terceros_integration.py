# -*- coding: utf-8 -*-
"""
Integration tests for the terceros command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json
import os
from pathlib import Path

from bdns.fetch.commands.terceros import terceros
from bdns.fetch.types import Ambito


@pytest.mark.integration
class TestTercerosIntegration:
    """Integration tests for the terceros command."""

    def test_terceros_basic(self, get_test_context, cleanup_test_file):
        """Test terceros command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("terceros.csv")

        try:
            # Act - Test with valid ambito and minimal parameters
            # Use proper VPD format (GE instead of string) and valid search term
            terceros(ctx, vpd="GE", ambito=Ambito.C, busqueda="empresa", idPersona=None)

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

            print(f"✅ Success: Retrieved {len(data)} terceros records")
            if len(data) > 0:
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(
                    f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}"
                )
            else:
                print(
                    "No terceros found with these parameters - API responded correctly"
                )

        finally:
            cleanup_test_file(output_path)

    def test_terceros_basic_alternative(self, get_test_context, cleanup_test_file):
        """Test terceros command with basic parameters - alternative test from remaining commands."""
        # Arrange
        ctx, output_path = get_test_context("terceros.csv")

        try:
            # Act - Test with required ambito parameter using proper enum and working search term
            terceros(ctx, vpd="GE", ambito=Ambito.C, busqueda="empresa", idPersona=None)

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
            # 400 errors or no data should be treated as test failures
            pytest.fail(f"terceros command failed: {e}")

        finally:
            cleanup_test_file(output_path)

    def test_terceros_with_ambito(self, get_test_context, cleanup_test_file):
        """Test terceros command with ambito parameter."""
        # Arrange
        ctx, output_path = get_test_context("terceros_ambito.csv")

        try:
            # Act - Test with ambito parameter and proper VPD and working search term
            terceros(ctx, vpd="GE", ambito=Ambito.A, busqueda="empresa", idPersona=None)

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
            # 400 errors or no data should be treated as test failures
            pytest.fail(f"terceros command with ambito failed: {e}")

        finally:
            cleanup_test_file(output_path)
