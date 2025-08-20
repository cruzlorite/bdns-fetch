# -*- coding: utf-8 -*-
"""
Integration tests for the planesestrategicos command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.planesestrategicos import planesestrategicos


@pytest.mark.integration
class TestPlanesestrategicosIntegration:
    """Integration tests for the planesestrategicos command."""

    @pytest.mark.integration
    def test_planesestrategicos_basic(self, get_test_context, cleanup_test_file):
        """Test planesestrategicos command with specific plan ID."""
        ctx, output_path = get_test_context("planesestrategicos_test.jsonl")

        try:
            planesestrategicos(
                ctx,
                idPES=459,  # Example ID from API documentation
            )

            # Check that file was created and has content
            assert output_path.exists(), f"Output file {output_path} was not created"

            # Read and parse the output
            with open(output_path, "r") as f:
                content = f.read().strip()
                if content:
                    lines = content.split("\n")
                    data = [json.loads(line) for line in lines if line.strip()]
                    print(
                        f"✅ Success: Retrieved {len(data)} planesestrategicos records"
                    )
                    if data:
                        print(f"Sample: {data[0].get('descripcion', 'N/A')}")
                else:
                    print(
                        "✅ Success: planesestrategicos command executed (empty result)"
                    )

        finally:
            cleanup_test_file(output_path)
