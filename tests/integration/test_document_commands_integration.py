# -*- coding: utf-8 -*-
"""
Integration tests for document and specific lookup commands.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.api.commands.convocatorias import convocatorias
from bdns.api.commands.convocatorias_documentos import convocatorias_documentos
from bdns.api.commands.convocatorias_pdf import convocatorias_pdf
from bdns.api.commands.organos_codigoadmin import organos_codigoadmin
from bdns.api.commands.terceros import terceros


@pytest.mark.integration
class TestDocumentCommandsIntegration:
    """Integration tests for document and lookup commands."""

    def test_convocatorias_with_known_id(self, get_test_context, cleanup_test_file):
        """Test convocatorias command with a known convocatoria number."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias.csv")

        try:
            # Act - Test with a common convocatoria format (try a simple number)
            convocatorias(ctx, vpd="GE", numConv="123456")

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

            print(f"✅ Success: Retrieved {len(data)} convocatoria records")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_convocatorias_documentos_basic(self, get_test_context, cleanup_test_file):
        """Test convocatorias_documentos command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias_documentos.csv")

        try:
            # Act - Test with basic parameters (try common document ID)
            convocatorias_documentos(ctx, idDocumento="1")

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

            print(f"✅ Success: Retrieved {len(data)} convocatorias documentos records")
            if len(data) > 0:
                print(f"Sample: {data[0]}")

        finally:
            cleanup_test_file(output_path)

    def test_convocatorias_pdf_basic(self, get_test_context, cleanup_test_file):
        """Test convocatorias_pdf command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias_pdf.csv")

        try:
            # Act - Test with basic parameters
            convocatorias_pdf(ctx, vpd="GE", id="1")

            # Assert
            assert output_path.exists(), (
                f"Output file should be created at {output_path}"
            )

            # Read and validate content (might be binary PDF data)
            with open(output_path, "rb") as f:
                content = f.read()

            print(f"✅ Success: Retrieved convocatorias PDF ({len(content)} bytes)")

        finally:
            cleanup_test_file(output_path)

    def test_organos_codigoadmin_basic(self, get_test_context, cleanup_test_file):
        """Test organos_codigoadmin command with a test admin code."""
        # Arrange
        ctx, output_path = get_test_context("organos_codigoadmin.csv")

        try:
            # Act - Test with a common admin code pattern
            organos_codigoadmin(ctx, vpd="GE", codigoAdmin="E00003801")

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

            print(f"✅ Success: Retrieved {len(data)} organos by admin code")
            if len(data) > 0:
                print(f"Sample: {data[0]['descripcion']}")

        finally:
            cleanup_test_file(output_path)

    def test_terceros_basic(self, get_test_context, cleanup_test_file):
        """Test terceros command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("terceros.csv")

        try:
            # Act - Test with basic parameters (using minimal required params)
            terceros(ctx, vpd="GE", ambito="C", busqueda="", idPersona=1)

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
                print(f"Sample: {data[0]}")

        finally:
            cleanup_test_file(output_path)
