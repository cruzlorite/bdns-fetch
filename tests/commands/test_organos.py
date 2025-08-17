# -*- coding: utf-8 -*-
"""
Tests for the organos command.
"""
import pytest
from unittest.mock import Mock
from pathlib import Path

from bdns.api.commands.organos import organos
from bdns.api.types import TipoAdministracion


class TestOrganosCommand:
    """Test class for the organos command."""

    def test_organos_with_defaults(self, mocker):
        """Test organos command with default parameters."""
        # Arrange
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": Path("-")}
        mock_fetch_and_write = mocker.patch('bdns.api.commands.organos.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.organos.format_url')
        mock_format_url.return_value = "https://api.example.com/test"

        # Act
        organos(mock_ctx, vpd="GE", idAdmon=None)

        # Assert
        mock_format_url.assert_called_once()
        mock_fetch_and_write.assert_called_once()
        
        # Check that format_url was called with correct params
        call_args = mock_format_url.call_args
        params = call_args[0][1]  # Second argument should be params
        
        assert params["vpd"] == "GE"
        assert params["idAdmon"] is None

    def test_organos_with_custom_vpd(self, mocker):
        """Test organos command with custom VPD."""
        # Arrange
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": Path("-")}
        mock_fetch_and_write = mocker.patch('bdns.api.commands.organos.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.organos.format_url')
        mock_format_url.return_value = "https://api.example.com/test"

        # Act
        organos(mock_ctx, vpd="CUSTOM", idAdmon=None)

        # Assert
        mock_format_url.assert_called_once()
        call_args = mock_format_url.call_args
        params = call_args[0][1]
        
        assert params["vpd"] == "CUSTOM"
        assert params["idAdmon"] is None

    def test_organos_with_id_admon(self, mocker):
        """Test organos command with idAdmon parameter."""
        # Arrange
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": Path("-")}
        mock_fetch_and_write = mocker.patch('bdns.api.commands.organos.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.organos.format_url')
        mock_format_url.return_value = "https://api.example.com/test"

        # Act
        organos(mock_ctx, vpd="GE", idAdmon=TipoAdministracion.C)

        # Assert
        mock_format_url.assert_called_once()
        call_args = mock_format_url.call_args
        params = call_args[0][1]
        
        assert params["vpd"] == "GE"
        assert params["idAdmon"] == "C"

    def test_organos_with_all_parameters(self, mocker):
        """Test organos command with all parameters set."""
        # Arrange
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": Path("-")}
        mock_fetch_and_write = mocker.patch('bdns.api.commands.organos.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.organos.format_url')
        mock_format_url.return_value = "https://api.example.com/test"

        # Act
        organos(
            mock_ctx, 
            vpd="TEST", 
            idAdmon=TipoAdministracion.A
        )

        # Assert
        mock_format_url.assert_called_once()
        call_args = mock_format_url.call_args
        params = call_args[0][1]
        
        assert params["vpd"] == "TEST"
        assert params["idAdmon"] == "A"

    def test_organos_calls_fetch_and_write_with_correct_params(self, mocker):
        """Test that organos calls fetch_and_write with correct parameters."""
        # Arrange
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": Path("-")}
        mock_fetch_and_write = mocker.patch('bdns.api.commands.organos.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.organos.format_url')
        mock_format_url.return_value = "https://api.test.com/organos"
        
        # Act
        organos(mock_ctx, vpd="GE", idAdmon=None)

        # Assert
        mock_fetch_and_write.assert_called_once_with(
            url="https://api.test.com/organos",
            output_file=mock_ctx.obj["output_file"]
        )

    def test_organos_enum_value_extraction(self, mocker):
        """Test that enum values are properly extracted."""
        # Arrange
        mock_ctx = Mock()
        mock_ctx.obj = {"output_file": Path("-")}
        mock_fetch_and_write = mocker.patch('bdns.api.commands.organos.fetch_and_write')
        mock_format_url = mocker.patch('bdns.api.commands.organos.format_url')
        mock_format_url.return_value = "https://api.example.com/test"
        
        # Test each enum value
        test_cases = [
            (TipoAdministracion.C, "C"),
            (TipoAdministracion.A, "A"), 
            (TipoAdministracion.L, "L"),
            (TipoAdministracion.O, "O"),
            (None, None)
        ]
        
        for enum_value, expected_string in test_cases:
            mock_format_url.reset_mock()
            
            # Act
            organos(mock_ctx, vpd="GE", idAdmon=enum_value)
            
            # Assert
            call_args = mock_format_url.call_args
            params = call_args[0][1]
            assert params["idAdmon"] == expected_string
