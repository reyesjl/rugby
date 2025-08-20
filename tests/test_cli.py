# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Tests for the core CLI functionality."""

import os

# from core.pipeline_models import VideoProcessingConfig
import tempfile

import yaml

from core.cli import main


def test_main_with_config():
    """Test main function with --config argument and a valid YAML file."""
    sample_config: dict = {
        "video_processing": {"sources": [], "conversion": {}, "indexing": {}}
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(sample_config, tmp)
        tmp_path = tmp.name
    try:
        result = main(["--config", tmp_path])
        assert result is None or result == 0
    finally:
        os.remove(tmp_path)
