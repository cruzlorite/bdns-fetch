# -*- coding: utf-8 -*-
"""
Integration tests for simple commands with basic parameters.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.api.commands.regiones import regiones
from bdns.api.commands.instrumentos import instrumentos
from bdns.api.commands.sectores import sectores
from bdns.api.commands.finalidades import finalidades
from bdns.api.commands.beneficiarios import beneficiarios
from bdns.api.commands.objetivos import objetivos


@pytest.mark.integration
class TestSimpleCommandsIntegration:
    """Integration tests for commands with only vpd parameter."""

    def test_regiones_real_api(self, get_test_context, cleanup_test_file):
        """Test regiones command with real API."""
        # Arrange
        ctx, output_path = get_test_context("regiones.csv")

        try:
            # Act
            regiones(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some regiones data"

            print(f"✅ Success: Retrieved {len(data)} regiones records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_instrumentos_real_api(self, get_test_context, cleanup_test_file):
        """Test instrumentos command with real API."""
        # Arrange
        ctx, output_path = get_test_context("instrumentos.csv")

        try:
            # Act
            instrumentos(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some instrumentos data"

            print(f"✅ Success: Retrieved {len(data)} instrumentos records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_sectores_real_api(self, get_test_context, cleanup_test_file):
        """Test sectores command with real API."""
        # Arrange
        ctx, output_path = get_test_context("sectores.csv")

        try:
            # Act
            sectores(ctx)

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

            assert len(data) > 0, "Should return some sectores data"

            print(f"✅ Success: Retrieved {len(data)} sectores records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_finalidades_real_api(self, get_test_context, cleanup_test_file):
        """Test finalidades command with real API."""
        # Arrange
        ctx, output_path = get_test_context("finalidades.csv")

        try:
            # Act
            finalidades(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some finalidades data"

            print(f"✅ Success: Retrieved {len(data)} finalidades records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_beneficiarios_real_api(self, get_test_context, cleanup_test_file):
        """Test beneficiarios command with real API."""
        # Arrange
        ctx, output_path = get_test_context("beneficiarios.csv")

        try:
            # Act
            beneficiarios(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some beneficiarios data"

            print(f"✅ Success: Retrieved {len(data)} beneficiarios records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_objetivos_real_api(self, get_test_context, cleanup_test_file):
        """Test objetivos command with real API."""
        # Arrange
        ctx, output_path = get_test_context("objetivos.csv")

        try:
            # Act
            objetivos(ctx, vpd="GE")

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

            assert len(data) > 0, "Should return some objetivos data"

            print(f"✅ Success: Retrieved {len(data)} objetivos records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)
