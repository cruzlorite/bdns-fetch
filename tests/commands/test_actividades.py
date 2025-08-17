# -*- coding: utf-8 -*-
"""
Tests for the actividades command.
"""
import pytest
from unittest.mock import Mock

from bdns.api.commands.actividades import actividades


class TestActividadesCommand:
    """Test class for the actividades command."""

    def test_actividades_with_defaults(self, mocker):
        """Test actividades command with default parameters."""
        # Arrange
        mock_fetch_and_write = mocker.patch('bdns.api.commands.actividades.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.actividades.format_url')
        mock_format_url.return_value = "https://api.test.com/actividades"
        
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": "test_output.csv"}

        # Act
        actividades(mock_ctx, vpd="GE")

        # Assert
        mock_format_url.assert_called_once()
        mock_fetch_and_write.assert_called_once()
        
        # Check that format_url was called with correct params
        call_args = mock_format_url.call_args
        params = call_args[0][1]  # Second argument should be params
        
        assert params["vpd"] == "GE"

    def test_actividades_with_custom_vpd(self, mocker):
        """Test actividades command with custom VPD."""
        # Arrange
        mock_fetch_and_write = mocker.patch('bdns.api.commands.actividades.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.actividades.format_url')
        mock_format_url.return_value = "https://api.test.com/actividades"
        
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": "test_output.csv"}

        # Act
        actividades(mock_ctx, vpd="CUSTOM")

        # Assert
        mock_format_url.assert_called_once()
        call_args = mock_format_url.call_args
        params = call_args[0][1]
        
        assert params["vpd"] == "CUSTOM"

    def test_actividades_calls_fetch_and_write_with_correct_params(self, mocker):
        """Test that actividades calls fetch_and_write with correct parameters."""
        # Arrange
        mock_fetch_and_write = mocker.patch('bdns.api.commands.actividades.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.actividades.format_url')
        mock_format_url.return_value = "https://api.test.com/actividades"
        
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": "test_output.csv"}
        
        # Act
        actividades(mock_ctx, vpd="GE")

        # Assert
        mock_fetch_and_write.assert_called_once_with(
            url="https://api.test.com/actividades",
            output_file=mock_ctx.obj["output_file"]
        )
