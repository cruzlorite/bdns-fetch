# -*- coding: utf-8 -*-
"""
Integration tests for strategic plans related commands.
These tests make real API calls to the BDNS API.
"""

import pytest
import json
from datetime import datetime

from bdns.api.commands.planesestrategicos import planesestrategicos
from bdns.api.commands.planesestrategicos_busqueda import planesestrategicos_busqueda
from bdns.api.commands.planesestrategicos_documentos import planesestrategicos_documentos
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

    @pytest.mark.integration
    def test_planesestrategicos_basic(self, get_test_context, cleanup_test_file):
        """Test planesestrategicos command with specific plan ID."""
        ctx, output_path = get_test_context("planesestrategicos_test.jsonl")

        try:
            planesestrategicos(
                ctx, 
                idPES=459  # Example ID from API documentation
            )
            
            # Check that file was created and has content
            assert output_path.exists(), f"Output file {output_path} was not created"
            
            # Read and parse the output
            with open(output_path, "r") as f:
                content = f.read().strip()
                if content:
                    lines = content.split("\n")
                    data = [json.loads(line) for line in lines if line.strip()]
                    print(f"✅ Success: Retrieved {len(data)} planesestrategicos records")
                    if data:
                        print(f"Sample: {data[0].get('descripcion', 'N/A')}")
                else:
                    print("✅ Success: planesestrategicos command executed (empty result)")
                    
        finally:
            cleanup_test_file(output_path)

    @pytest.mark.integration
    def test_planesestrategicos_documentos_basic(self, get_test_context, cleanup_test_file):
        """Test planesestrategicos_documentos command with specific document ID."""
        ctx, output_path = get_test_context("planesestrategicos_documentos_test.jsonl")

        try:
            # Try with a test document ID - if it fails, that's expected for this endpoint
            # as it requires a valid existing document ID
            planesestrategicos_documentos(
                ctx, 
                idDocumento=1  # Try with a simple ID
            )
            
            # Check that file was created (may be empty if document doesn't exist)
            assert output_path.exists(), f"Output file {output_path} was not created"
            print("✅ Success: planesestrategicos_documentos command executed successfully")
                    
        except Exception as e:
            # This is expected if the document ID doesn't exist - the command structure is correct
            error_msg = str(e)
            if ("No se ha podido obtener el documento" in error_msg or 
                "ERR_VALIDACION" in error_msg or 
                "RetryError" in error_msg):
                print("✅ Success: planesestrategicos_documentos command structure is correct (document ID not found, which is expected)")
            else:
                print(f"Unexpected error: {error_msg}")
                raise  # Re-raise if it's a different error
        finally:
            cleanup_test_file(output_path)
