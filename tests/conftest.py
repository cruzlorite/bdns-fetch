# -*- coding: utf-8 -*-
"""
Configuration for all tests.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def get_test_context():
    """Create a test context for integration tests."""

    def _create_context(output_filename: str = "test_output.csv"):
        # Create a temporary directory for output
        temp_dir = tempfile.mkdtemp()
        output_path = Path(temp_dir) / output_filename

        # Mock typer context
        mock_ctx = Mock()
        mock_ctx.obj = {
            "output_file": str(output_path),
            "max_concurrent_requests": 5,  # Default value for paginated commands
        }

        return mock_ctx, output_path

    return _create_context


@pytest.fixture
def cleanup_test_file():
    """Clean up test output files."""

    def _cleanup(file_path: Path):
        if file_path.exists():
            file_path.unlink()
        # Also try to remove the parent directory if empty
        try:
            file_path.parent.rmdir()
        except OSError:
            pass  # Directory not empty or doesn't exist

    return _cleanup
