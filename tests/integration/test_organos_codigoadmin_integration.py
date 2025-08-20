# -*- coding: utf-8 -*-
"""
Integration tests for the organos_codigoadmin command.
These tests make real API calls to the BDNS API.
"""

import pytest
import json

from bdns.fetch.commands.organos_codigoadmin import organos_codigoadmin
from bdns.fetch.exceptions import BDNSWarning


@pytest.mark.integration
class TestOrganosCodigoadminIntegration:
    """Integration tests for the organos_codigoadmin command."""

    def test_organos_codigoadmin_basic(self, get_test_context, cleanup_test_file):
        """Test organos_codigoadmin command with a test admin code."""
        # Arrange
        ctx, output_path = get_test_context("organos_codigoadmin.csv")

        try:
            # Act - Test with more common admin codes that should have data
            # Using codes from Spanish central administration that are more likely to exist
            test_codes = ["C32", "C31", "C01", "C02", "C03", "C04", "C05"]
            found_data = False

            for code in test_codes:
                try:
                    organos_codigoadmin(ctx, codigoAdmin=code)

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

                    if len(data) > 0:
                        print(
                            f"✅ Success: Retrieved {len(data)} organos by admin code {code}"
                        )
                        print(f"Available fields: {list(data[0].keys())}")
                        print(f"Sample organo: {data[0].get('descripcion', 'N/A')}")
                        found_data = True
                        break  # Found working code, exit loop
                    else:
                        print(f"No results for code {code}, trying next...")
                        continue

                except BDNSWarning:
                    print(f"No data for code {code} (BDNSWarning), trying next...")
                    continue
                except Exception as e:
                    if "204" in str(e) or "RetryError" in str(e):
                        print(f"No data for code {code} (Exception), trying next...")
                        continue
                    else:
                        raise e

            # Ensure we found at least one working admin code with data
            if not found_data:
                pytest.fail(
                    "❌ Error: No valid admin codes found - all test codes failed to return organos data. "
                    f"Tested codes: {test_codes}"
                )

        finally:
            cleanup_test_file(output_path)
