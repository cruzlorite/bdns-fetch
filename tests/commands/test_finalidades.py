# -*- coding: utf-8 -*-
"""
Tests for the finalidades command.
"""
import pytest
from unittest.mock import Mock

from bdns.api.commands.finalidades import finalidades


class TestFinalidadesCommand:
    """Test class for the finalidades command."""

    def test_finalidades_with_defaults(self, mock_typer_context, mock_fetch_and_write, mock_format_url):
        """Test finalidades command with default parameters."""
        # Act
        finalidades(mock_typer_context)

        # Assert
        mock_format_url.assert_called_once()
        mock_fetch_and_write.assert_called_once()
        
        # Check that format_url was called with correct params
        call_args = mock_format_url.call_args
        params = call_args[0][1]  # Second argument should be params
        
        assert params["vpd"] == "GE"

    def test_finalidades_with_custom_vpd(self, mock_typer_context, mock_fetch_and_write, mock_format_url):
        """Test finalidades command with custom VPD."""
        # Act
        finalidades(mock_typer_context, vpd="CUSTOM")

        # Assert
        mock_format_url.assert_called_once()
        call_args = mock_format_url.call_args
        params = call_args[0][1]
        
        assert params["vpd"] == "CUSTOM"

    def test_finalidades_calls_fetch_and_write_with_correct_params(
        self, mock_typer_context, mock_fetch_and_write, mock_format_url
    ):
        """Test that finalidades calls fetch_and_write with correct parameters."""
        mock_format_url.return_value = "https://api.test.com/finalidades"
        
        # Act
        finalidades(mock_typer_context)

        # Assert
        mock_fetch_and_write.assert_called_once_with(
            url="https://api.test.com/finalidades",
            output_file=mock_typer_context.obj["output_file"]
        )
