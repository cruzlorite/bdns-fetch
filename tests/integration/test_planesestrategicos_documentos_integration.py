# -*- coding: utf-8 -*-
"""
Integration tests for the planesestrategicos_documentos command.
These tests make real API calls to the BDNS API.
"""

import pytest

from bdns.fetch.commands.planesestrategicos_documentos import (
    planesestrategicos_documentos,
)


@pytest.mark.integration
class TestPlanesestrategicosDocumentosIntegration:
    """Integration tests for the planesestrategicos_documentos command."""

    @pytest.mark.integration
    def test_planesestrategicos_documentos_basic(
        self, get_test_context, cleanup_test_file
    ):
        """Test planesestrategicos_documentos command with specific document ID."""
        ctx, output_path = get_test_context("planesestrategicos_documentos_test.jsonl")

        try:
            # Try with multiple document IDs to find one that works
            test_ids = ["651938"]

            for doc_id in test_ids:
                try:
                    planesestrategicos_documentos(
                        ctx,
                        idDocumento=int(doc_id),
                    )

                    # Check that file was created and has content
                    assert output_path.exists(), (
                        f"Output file {output_path} was not created"
                    )

                    # Read and validate content
                    with open(output_path, "rb") as f:
                        content = f.read()

                    print(
                        f"✅ Success: Retrieved planesestrategicos documentos response ({len(content)} bytes) for ID {doc_id}"
                    )
                    if len(content) > 0:
                        print("Binary document content (likely a document file)")
                        break  # Found working document ID, exit loop
                    else:
                        print(f"Empty document for ID {doc_id}, trying next...")
                        continue

                except Exception as e:
                    if "400" in str(e) or "No se ha podido obtener" in str(e):
                        print(f"No document found for ID {doc_id}, trying next...")
                        continue
                    else:
                        raise e
            else:
                # If we get here, no working document IDs were found
                pytest.fail("Error: No valid document IDs found")

            print(
                "✅ Success: planesestrategicos_documentos command executed successfully"
            )

        except Exception as e:
            # No document found should be treated as test failure per user feedback
            pytest.fail(
                f"planesestrategicos_documentos failed - no valid document found: {e}"
            )
        finally:
            cleanup_test_file(output_path)
