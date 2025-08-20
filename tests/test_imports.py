# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Tests for package imports."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_core_import():
    """Test that core package can be imported."""
    import core
    assert core is not None


def test_ingest_import():
    """Test that ingest package can be imported."""
    import ingest
    assert ingest is not None


def test_convert_import():
    """Test that convert package can be imported."""
    import convert
    assert convert is not None


def test_indexing_import():
    """Test that indexing package can be imported."""
    import indexing
    assert indexing is not None


def test_api_import():
    """Test that api package can be imported."""
    import api
    assert api is not None


def test_ops_import():
    """Test that ops package can be imported."""
    import ops
    assert ops is not None


def test_storage_import():
    """Test that storage package can be imported."""
    import storage
    assert storage is not None