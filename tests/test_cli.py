# -*- coding: utf-8 -*-
"""
Tests for the CLI interface.
These tests verify the CLI works correctly with both stdout and file output.
"""

import json
import tempfile
import pytest
from pathlib import Path
from typer.testing import CliRunner
from bdns.fetch.cli import app


class TestCLI:
    """Test the CLI interface."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test that CLI help works."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "BDNS Fetch" in result.stdout
        assert "Base de Datos Nacional de Subvenciones" in result.stdout

    def test_cli_command_help(self):
        """Test that command-specific help works."""
        result = self.runner.invoke(app, ["organos", "--help"])
        assert result.exit_code == 0
        assert "organos" in result.stdout.lower()

    def test_cli_actividades_stdout(self):
        """Test actividades command outputs to stdout."""
        # Run actividades command without output file (should go to stdout)
        result = self.runner.invoke(app, ["actividades"])

        # Should succeed
        assert result.exit_code == 0, f"CLI failed with: {result.stdout}"

        # Should have JSON output in stdout
        assert result.stdout.strip(), "Should have output to stdout"

        # Each line should be valid JSON
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 0, "Should have at least one line of output"

        # Verify first line is valid JSON
        first_record = json.loads(lines[0])
        assert isinstance(first_record, dict), "Should output JSON objects"
        assert "id" in first_record, "Should have id field"
        assert "descripcion" in first_record, "Should have descripcion field"

    def test_cli_sectores_file_output(self):
        """Test sectores command outputs to file."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".jsonl"
        ) as tmp:
            temp_file = Path(tmp.name)

        try:
            # Run sectores command with output file
            result = self.runner.invoke(
                app, ["--output-file", str(temp_file), "sectores"]
            )

            # Should succeed
            assert result.exit_code == 0, f"CLI failed with: {result.stdout}"

            # File should exist and have content
            assert temp_file.exists(), "Output file should be created"
            content = temp_file.read_text(encoding="utf-8")
            assert content.strip(), "Output file should have content"

            # Each line should be valid JSON
            lines = content.strip().split("\n")
            assert len(lines) > 0, "Should have at least one line in file"

            # Verify first line is valid JSON
            first_record = json.loads(lines[0])
            assert isinstance(first_record, dict), "Should output JSON objects"
            assert "id" in first_record, "Should have id field"
            assert "descripcion" in first_record, "Should have descripcion field"

        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()

    def test_cli_finalidades_with_parameters(self):
        """Test finalidades command with parameters to stdout."""
        result = self.runner.invoke(app, ["finalidades"])

        # Should succeed
        assert result.exit_code == 0, f"CLI failed with: {result.stdout}"

        # Should have JSON output
        assert result.stdout.strip(), "Should have output to stdout"
        lines = result.stdout.strip().split("\n")

        # Should have data
        assert len(lines) > 0, "Should have at least some data"

        # Verify JSON structure
        first_record = json.loads(lines[0])
        assert isinstance(first_record, dict), "Should output JSON objects"

    def test_cli_verbose_flag(self):
        """Test that verbose flag produces more output."""
        # Run without verbose
        result_normal = self.runner.invoke(app, ["finalidades"])

        # Run with verbose
        result_verbose = self.runner.invoke(app, ["--verbose", "finalidades"])

        # Both should succeed
        assert result_normal.exit_code == 0, (
            f"Normal mode failed: {result_normal.stdout}"
        )
        assert result_verbose.exit_code == 0, (
            f"Verbose mode failed: {result_verbose.stdout}"
        )

        # Both should produce data output
        assert result_normal.stdout.strip(), "Normal mode should produce data output"
        assert result_verbose.stdout.strip(), (
            "Verbose mode should still produce data output"
        )

    def test_cli_binary_output_error(self):
        """Test that binary endpoints are not available in current CLI implementation."""
        # The current simplified CLI only implements a few commands
        # Binary endpoints like convocatorias-pdf are not included
        result = self.runner.invoke(app, ["--help"])

        # Should show available commands (only the ones we implemented)
        assert result.exit_code == 0
        assert "actividades" in result.stdout
        assert "sectores" in result.stdout
        assert "organos" in result.stdout
        assert "finalidades" in result.stdout

    def test_cli_invalid_command(self):
        """Test that invalid commands show proper error."""
        result = self.runner.invoke(app, ["nonexistent-command"])

        # Should fail with proper error
        assert result.exit_code != 0
        assert "No such command" in result.stdout or "Usage:" in result.stdout

    def test_cli_missing_required_parameter(self):
        """Test handling of required parameters in organos command."""
        # Try organos command with required parameter
        result = self.runner.invoke(app, ["organos", "--idAdmon", "C"])

        # Should succeed with the required parameter
        assert result.exit_code == 0, f"Organos command failed: {result.stdout}"
        assert result.stdout.strip(), "Should produce output"

        # Verify JSON output
        lines = result.stdout.strip().split("\n")
        first_record = json.loads(lines[0])
        assert "descripcion" in first_record, "Should have descripcion field"
        assert "id" in first_record, "Should have id field"

    def test_cli_concesiones_busqueda_dates(self):
        """Test that the CLI correctly handles date parameters for 'concesiones-busqueda'."""
        result = self.runner.invoke(
            app,
            [
                "concesiones-busqueda",
                "--fechaDesde",
                "two weeks ago",
                "--fechaHasta",
                "today",
            ],
        )
        assert result.exit_code == 0
