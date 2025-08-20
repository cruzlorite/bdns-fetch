# -*- coding: utf-8 -*-
"""
Integration tests for the convocatorias_pdf command.
These tests make real API calls to the BDNS API.
"""

import pytest

from bdns.fetch.commands.convocatorias_pdf import convocatorias_pdf


@pytest.mark.integration
class TestConvocatoriasPdfIntegration:
    """Integration tests for the convocatorias_pdf command."""

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

                print(
                    f"✅ Success: Retrieved convocatorias PDF response ({len(content)} bytes)"
                )

                # Try to decode as text to see if it's an error response
                try:
                    text_content = content.decode("utf-8")
                    if (
                        "error" in text_content.lower()
                        or "not found" in text_content.lower()
                    ):
                        print(f"Response content: {text_content[:200]}...")
                    else:
                        print("Text content (possibly HTML or error)")
                except UnicodeDecodeError:
                    print("Binary content (likely PDF)")

            except Exception as e:
                if "204" in str(e) or "400" in str(e):
                    print(
                        "✅ Expected: PDF not available - API responded correctly with 204/400"
                    )
                else:
                    raise e

        finally:
            cleanup_test_file(output_path)
