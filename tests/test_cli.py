"""Tests for the core CLI functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cli import main, cmd_version, cmd_status


def test_version_command():
    """Test the version command."""
    result = cmd_version(None)  # type: ignore
    assert result == 0


def test_status_command():
    """Test the status command."""
    result = cmd_status(None)  # type: ignore  
    assert result == 0


def test_main_no_args():
    """Test main function with no arguments shows help."""
    result = main([])
    assert result == 1


def test_main_version():
    """Test main function with version command."""
    result = main(["version"])
    assert result == 0


def test_main_status():
    """Test main function with status command."""
    result = main(["status"])
    assert result == 0