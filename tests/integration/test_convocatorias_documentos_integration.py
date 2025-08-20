# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias_documentos command.
These tests make real API calls to the BDNS API.
"""

import pytest

from bdns.fetch.commands.convocatorias_documentos import convocatorias_documentos


@pytest.mark.integration
class TestConvocatoriasDocumentosIntegration:
    """Integration tests for the convocatorias_documentos command."""

    def test_convocatorias_documentos_basic(self, get_test_context, cleanup_test_file):
        """Test convocatorias_documentos command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias_documentos.csv")

        try:
            # Act - Test with various document IDs to find one that works
            # Test with various document IDs to find working ones
            test_ids = ["36605", "744764", "700000", "500000", "600000", "800000"]

            for doc_id in test_ids:
                try:
                    convocatorias_documentos(ctx, idDocumento=doc_id)

                    # Assert
                    assert output_path.exists(), (
                        f"Output file should be created at {output_path}"
                    )

                    # Read and validate content
                    with open(output_path, "rb") as f:
                        content = f.read()

                    print(
                        f"✅ Success: Retrieved convocatorias documentos response ({len(content)} bytes) for ID {doc_id}"
                    )

                    # Try to decode as text to analyze content
                    try:
                        text_content = content.decode("utf-8")
                        if len(text_content.strip()) > 0:
                            print("Document content retrieved successfully")
                            # Look for JSON structure
                            if text_content.strip().startswith(
                                "["
                            ) or text_content.strip().startswith("{"):
                                print("JSON document data received")
                            else:
                                print("Text document content received")
                            break  # Found working ID, exit loop
                    except UnicodeDecodeError:
                        print("Binary document content (likely a document file)")
                        break  # Found working ID, exit loop

                except Exception as e:
                    if (
                        "No se ha podido obtener el documento" in str(e)
                        or "ERR_VALIDACION" in str(e)
                        or "400" in str(e)
                    ):
                        print(f"No document found for ID {doc_id}, trying next...")
                        continue
                    else:
                        raise e
            else:
                # If all IDs failed, that's an error - we should find at least one working document
                pytest.fail(
                    "❌ Error: No valid document IDs found - all test IDs failed to return documents"
                )

        finally:
            cleanup_test_file(output_path)
