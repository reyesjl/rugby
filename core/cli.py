"""Rugby CLI entry point."""

import argparse
import sys
from typing import Optional
from core.pipeline_models import VideoProcessingConfig
from core.pipeline_runner import PipelineRunner


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
        "--version",
        action="store_true",
        help="Show rugby-cli version and exit",
    )
    return parser


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    print("rugby-cli version 0.1.0")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show pipeline status."""
    print("🏉 Rugby Pipeline Status: Ready")
    print("✅ All packages initialized")
    return 0

def load_yaml(config_path: str) -> None:
    """Load YAML configuration file."""
    import yaml
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    video_config = VideoProcessingConfig(config.get('video_processing', {}))
    #print(video_config)
    pipeline_runner = PipelineRunner(video_config)
    pipeline_runner.run()

def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        print("rugby-cli version 0.1.0")
        return 0

    if not getattr(args, "config", None):
        parser.print_help()
        return 1

    load_yaml(args.config)
    return 0


if __name__ == "__main__":
    sys.exit(main())