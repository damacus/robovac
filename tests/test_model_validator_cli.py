"""Tests for the standalone model validator CLI tool."""

import subprocess
import sys
import pytest
from typing import Any


class TestModelValidatorCLI:
    """Test suite for the model_validator_cli.py tool."""

    def run_cli(self, *args: Any) -> subprocess.CompletedProcess[str]:
        """Helper function to run the CLI tool as a subprocess."""
        command = [sys.executable, "-m", "custom_components.robovac.model_validator_cli"] + list(args)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result

    def test_cli_help_flag(self) -> None:
        """Test that the --help flag works and shows usage."""
        result = self.run_cli("--help")
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "validate robovac model compatibility" in result.stdout.lower()

    def test_cli_list_flag(self) -> None:
        """Test that the --list flag lists all supported models."""
        result = self.run_cli("--list")
        assert result.returncode == 0
        assert "Supported Models:" in result.stdout
        assert "T2278" in result.stdout
        assert "T2080" in result.stdout

    def test_cli_supported_model(self) -> None:
        """Test validating a supported model returns a success message."""
        result = self.run_cli("T2278")
        assert result.returncode == 0
        assert "✅ T2278 is a supported model." in result.stdout
        assert "Series: L" in result.stdout

    def test_cli_unsupported_model(self) -> None:
        """Test validating an unsupported model shows suggestions."""
        result = self.run_cli("T9999")
        assert result.returncode == 1
        assert "❌ T9999 is not a supported model." in result.stdout
        assert "Suggestions:" in result.stdout

    def test_cli_invalid_model_format(self) -> None:
        """Test validating a model with an invalid format."""
        result = self.run_cli("INVALID")
        assert result.returncode == 1
        assert "❌ INVALID is not a supported model." in result.stdout

    def test_cli_no_arguments(self) -> None:
        """Test running the CLI with no arguments shows help."""
        result = self.run_cli()
        assert result.returncode != 0  # Should fail as an argument is required
        assert "usage:" in result.stderr.lower()
