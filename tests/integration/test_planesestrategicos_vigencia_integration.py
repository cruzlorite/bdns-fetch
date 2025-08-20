# -*- coding: utf-8 -*-
"""
Integration tests for the planesestrategicos_vigencia command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.planesestrategicos_vigencia import planesestrategicos_vigencia


@pytest.mark.integration
class TestPlanesestrategicosVigenciaIntegration:
    """Integration tests for the planesestrategicos_vigencia command."""

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
