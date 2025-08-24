# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Rugby CLI entry point."""

import argparse
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv  # type: ignore

from core.pipeline_models import VideoProcessingConfig
from core.pipeline_runner import PipelineRunner

load_dotenv()

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="rugby-cli",
        description="Rugby video processing pipeline CLI",
    )

    parser.add_argument(
        "--config",
        required=False,
        help="Launch Provided Pipeline",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show rugby-cli version and exit",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show Rugby pipeline status and exit",
    )
    return parser


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    logger.info("rugby-cli version 0.1.0")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show pipeline status."""
    logger.info("Rugby Pipeline Status: Ready")
    logger.info("All packages initialized")
    return 0


def load_yaml(config_path: str) -> None:
    """Load YAML configuration file."""
    import yaml

    with open(config_path) as file:
        config = yaml.safe_load(file)
    video_config = VideoProcessingConfig(config.get("video_processing", {}))
    # logger.debug("Loaded config: %s", video_config)
    pipeline_runner = PipelineRunner(video_config)
    pipeline_runner.run()


def configure_logging(level: int = logging.INFO) -> None:
    """Initialize application logging."""
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


def read_log_level() -> int:
    log_level = os.getenv("LOG_LEVEL", "WARN")
    level = logging._nameToLevel.get(log_level, logging.WARN)
    if level is None or level == logging.NOTSET:
        level = logging.WARN
    return level


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configure logging for the application
    configure_logging(level=read_log_level())

    if getattr(args, "status", False):
        return cmd_status(args)

    if getattr(args, "version", False):
        return cmd_version(args)

    if not getattr(args, "config", None):
        parser.print_help()
        return 1

    load_yaml(args.config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
