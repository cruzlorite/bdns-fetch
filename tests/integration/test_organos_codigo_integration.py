# -*- coding: utf-8 -*-
"""
Integration tests for the organos_codigo command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.organos_codigo import organos_codigo


@pytest.mark.integration
class TestOrganosCodigoIntegration:
    """Integration tests for the organos_codigo command."""

    def test_organos_codigo_real_api(self, get_test_context, cleanup_test_file):
        """Test organos_codigo command with real API."""
        # Arrange
        ctx, output_path = get_test_context("organos_codigo.csv")

        try:
            # Act - Test with various codigo values to find working ones
            test_codes = ["L02000034"]

            for code in test_codes:
                try:
                    organos_codigo(ctx, codigo=code)

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

                    print(
                        f"✅ Success: Retrieved {len(data)} organos codigo records for code {code}"
                    )
                    if len(data) > 0:
                        print(
                            f"Sample: tipoAdmon={data[0]['tipoAdmon']}, ids={data[0]['ids']}"
                        )
                        break  # Found working code, exit loop
                    else:
                        print(f"No results for code {code}, trying next...")
                        continue

                except Exception as e:
                    if "204" in str(e) or "RetryError" in str(e):
                        print(f"No content for code {code}, trying next...")
                        continue
                    else:
                        raise e
            else:
                # If all codes return no data, that's an error - we should find at least one working code
                pytest.fail(
                    "❌ Error: No valid organos codes found - all test codes failed to return data"
                )

        finally:
            cleanup_test_file(output_path)
