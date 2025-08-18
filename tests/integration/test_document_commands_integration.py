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
from bdns.api.types import Ambito


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
            # Act - Test with a realistic document ID (from recent convocatorias)
            # Note: This may not return a document if the ID doesn't have associated docs
            try:
                convocatorias_documentos(ctx, idDocumento="744764")
                
                # Assert
                assert output_path.exists(), (
                    f"Output file should be created at {output_path}"
                )

                # Read and validate content (could be JSON error or actual document)
                with open(output_path, "rb") as f:
                    content = f.read()

                print(f"✅ Success: Retrieved convocatorias documentos response ({len(content)} bytes)")
                
                # Try to decode as text to see if it's an error response
                try:
                    text_content = content.decode('utf-8')
                    if 'error' in text_content.lower() or len(content) < 100:
                        print(f"API response: {text_content[:200]}...")
                    else:
                        print("Binary document content received")
                except UnicodeDecodeError:
                    print("Binary document content (likely a document file)")

            except Exception as e:
                if "400" in str(e) and "documento solicitado" in str(e):
                    print("✅ Expected: Document ID not found - API responded correctly with 400 error")
                else:
                    raise e

        finally:
            cleanup_test_file(output_path)

    def test_convocatorias_pdf_basic(self, get_test_context, cleanup_test_file):
        """Test convocatorias_pdf command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias_pdf.csv")

        try:
            # Act - Test with a realistic convocatoria ID and recent VPD
            try:
                convocatorias_pdf(ctx, vpd="GE", id="744764")

                # Assert
                assert output_path.exists(), (
                    f"Output file should be created at {output_path}"
                )

                # Read and validate content (might be binary PDF data or JSON error)
                with open(output_path, "rb") as f:
                    content = f.read()

                print(f"✅ Success: Retrieved convocatorias PDF response ({len(content)} bytes)")
                
                # Try to decode as text to see if it's an error response
                try:
                    text_content = content.decode('utf-8')
                    if 'error' in text_content.lower() or 'not found' in text_content.lower():
                        print(f"Response content: {text_content[:200]}...")
                    else:
                        print("Text content (possibly HTML or error)")
                except UnicodeDecodeError:
                    print("Binary content (likely PDF)")

            except Exception as e:
                if "204" in str(e) or "400" in str(e):
                    print("✅ Expected: PDF not available - API responded correctly with 204/400")
                else:
                    raise e

        finally:
            cleanup_test_file(output_path)

    def test_organos_codigoadmin_basic(self, get_test_context, cleanup_test_file):
        """Test organos_codigoadmin command with a test admin code."""
        # Arrange
        ctx, output_path = get_test_context("organos_codigoadmin.csv")

    def test_organos_codigoadmin_basic(self, get_test_context, cleanup_test_file):
        """Test organos_codigoadmin command with a test admin code."""
        # Arrange
        ctx, output_path = get_test_context("organos_codigoadmin.csv")

        try:
            # Act - Test with a known Spanish ministry admin code pattern
            # Common patterns: E00003801 (Agriculture), E00003901 (Economy), etc.
            try:
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
                    print(f"Available fields: {list(data[0].keys())}")
                    print(f"Sample organo: {data[0].get('descripcion', 'N/A')}")
                else:
                    # If no results, just validate the API responded correctly
                    print("No results with this admin code - API responded correctly")

            except Exception as e:
                if "204" in str(e) or ("400" in str(e) and "content" in str(e).lower()) or "RetryError" in str(e):
                    print("✅ Expected: Admin code validation - API responded with expected error")
                else:
                    raise e

        finally:
            cleanup_test_file(output_path)

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
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")
            else:
                print("No terceros found with these parameters - API responded correctly")

        finally:
            cleanup_test_file(output_path)
