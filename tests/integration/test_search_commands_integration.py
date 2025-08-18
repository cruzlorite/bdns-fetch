# -*- coding: utf-8 -*-
"""
Integration tests for search commands with complex parameters.
These tests make real API calls to the BDNS API.
"""

import pytest
import json
from datetime import datetime

from bdns.api.commands.ayudasestado_busqueda import ayudasestado_busqueda
from bdns.api.commands.concesiones_busqueda import concesiones_busqueda
from bdns.api.commands.convocatorias_busqueda import convocatorias_busqueda
from bdns.api.commands.minimis_busqueda import minimis_busqueda
from bdns.api.commands.partidospoliticos_busqueda import partidospoliticos_busqueda
from bdns.api.commands.grandesbeneficiarios_busqueda import (
    grandesbeneficiarios_busqueda,
)
from bdns.api.commands.sanciones_busqueda import sanciones_busqueda
from bdns.api.types import TipoAdministracion


@pytest.mark.integration
class TestSearchCommandsIntegration:
    """Integration tests for search commands."""

    def test_ayudasestado_busqueda_basic(self, get_test_context, cleanup_test_file):
        """Test ayudasestado_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("ayudasestado_busqueda.csv")

        try:
            # Act - Test with basic parameters only (no free text)
            ayudasestado_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2020, 1, 1),
                fechaHasta=datetime(2020, 12, 31),
                tipoAdministracion=TipoAdministracion.C,
            )

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

            print(f"✅ Success: Retrieved {len(data)} ayudas estado search results")
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")

        finally:
            cleanup_test_file(output_path)

    def test_concesiones_busqueda_basic(self, get_test_context, cleanup_test_file):
        """Test concesiones_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("concesiones_busqueda.csv")

        try:
            # Act - Test with basic parameters (try broader date range and different administration)
            concesiones_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2023, 1, 1),
                fechaHasta=datetime(2024, 12, 31),
                tipoAdministracion=TipoAdministracion.C,  # Try Autonomous Communities instead
            )

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

            print(f"✅ Success: Retrieved {len(data)} concesiones search results")
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")

        finally:
            cleanup_test_file(output_path)

    def test_convocatorias_busqueda_basic(self, get_test_context, cleanup_test_file):
        """Test convocatorias_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("convocatorias_busqueda.csv")

        try:
            # Act - Test with basic parameters
            convocatorias_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2020, 1, 1),
                fechaHasta=datetime(2020, 12, 31),
                tipoAdministracion=TipoAdministracion.L,
            )

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

            print(f"✅ Success: Retrieved {len(data)} convocatorias search results")
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")

        finally:
            cleanup_test_file(output_path)

    def test_minimis_busqueda_basic(self, get_test_context, cleanup_test_file):
        """Test minimis_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("minimis_busqueda.csv")

        try:
            # Act - Test with basic parameters
            minimis_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2020, 1, 1),
                fechaHasta=datetime(2020, 12, 31),
                tipoAdministracion=TipoAdministracion.C,
            )

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

            print(f"✅ Success: Retrieved {len(data)} minimis search results")
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")

        finally:
            cleanup_test_file(output_path)

    def test_partidospoliticos_busqueda_basic(
        self, get_test_context, cleanup_test_file
    ):
        """Test partidospoliticos_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("partidospoliticos_busqueda.csv")

        try:
            # Act - Test with basic parameters (broader date range)
            partidospoliticos_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2022, 1, 1),
                fechaHasta=datetime(2024, 12, 31)
            )

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
                f"✅ Success: Retrieved {len(data)} partidos politicos search results"
            )
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")

        finally:
            cleanup_test_file(output_path)

    def test_grandesbeneficiarios_busqueda_basic(
        self, get_test_context, cleanup_test_file
    ):
        """Test grandesbeneficiarios_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("grandesbeneficiarios_busqueda.csv")

        try:
            # Act - Test with basic parameters (using a common year)
            grandesbeneficiarios_busqueda(
                ctx, anio="2023", pageSize=5, num_pages=1, from_page=0
            )

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
                f"✅ Success: Retrieved {len(data)} grandes beneficiarios search results"
            )
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")

        finally:
            cleanup_test_file(output_path)

    def test_sanciones_busqueda_basic(self, get_test_context, cleanup_test_file):
        """Test sanciones_busqueda command with basic parameters."""
        # Arrange
        ctx, output_path = get_test_context("sanciones_busqueda.csv")

        try:
            # Act - Test with basic parameters (broader date range and different administration)
            sanciones_busqueda(
                ctx,
                vpd="GE",
                pageSize=5,
                num_pages=1,
                from_page=0,
                fechaDesde=datetime(2022, 1, 1),
                fechaHasta=datetime(2024, 12, 31),
                tipoAdministracion=TipoAdministracion.A,  # Try State administration
            )

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

            print(f"✅ Success: Retrieved {len(data)} sanciones search results")
            if len(data) > 0:
                # Print available fields for debugging
                print(f"Available fields: {list(data[0].keys())}")
                # Use a field that likely exists
                sample_field = list(data[0].keys())[0] if data[0] else "No data"
                print(f"Sample field '{sample_field}': {data[0].get(sample_field, 'N/A')}")

        finally:
            cleanup_test_file(output_path)
