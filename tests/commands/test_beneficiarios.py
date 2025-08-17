# -*- coding: utf-8 -*-
"""
Tests for the beneficiarios command.
"""
import pytest
from unittest.mock import Mock

from bdns.api.commands.beneficiarios import beneficiarios


class TestBeneficiariosCommand:
    """Test class for the beneficiarios command."""

    def test_beneficiarios_with_defaults(self, mocker):
        """Test beneficiarios command with default parameters."""
        # Arrange
        mock_fetch_and_write = mocker.patch('bdns.api.commands.beneficiarios.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.beneficiarios.format_url')
        mock_format_url.return_value = "https://api.test.com/beneficiarios"
        
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": "test_output.csv"}

        # Act
        beneficiarios(mock_ctx)

        # Assert
        mock_format_url.assert_called_once()
        mock_fetch_and_write.assert_called_once()
        
        # Check that format_url was called with correct params
        call_args = mock_format_url.call_args
        params = call_args[0][1]  # Second argument should be params
        
        assert params["vpd"] == "GE"

    def test_beneficiarios_with_custom_vpd(self, mocker):
        """Test beneficiarios command with custom VPD."""
        # Arrange
        mock_fetch_and_write = mocker.patch('bdns.api.commands.beneficiarios.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.beneficiarios.format_url')
        mock_format_url.return_value = "https://api.test.com/beneficiarios"
        
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": "test_output.csv"}

        # Act
        beneficiarios(mock_ctx, vpd="CUSTOM")

        # Assert
        mock_format_url.assert_called_once()
        call_args = mock_format_url.call_args
        params = call_args[0][1]
        
        assert params["vpd"] == "CUSTOM"

    def test_beneficiarios_calls_fetch_and_write_with_correct_params(self, mocker):
        """Test that beneficiarios calls fetch_and_write with correct parameters."""
        # Arrange
        mock_fetch_and_write = mocker.patch('bdns.api.commands.beneficiarios.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.beneficiarios.format_url')
        mock_format_url.return_value = "https://api.test.com/beneficiarios"
        
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": "test_output.csv"}
        
        # Act
        beneficiarios(mock_ctx)

        # Assert
        mock_fetch_and_write.assert_called_once_with(
            url="https://api.test.com/beneficiarios",
            output_file=mock_ctx.obj["output_file"]
        )
