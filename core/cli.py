"""Rugby CLI entry point."""

import argparse
import sys
from typing import Optional
from core.pipeline_models import VideoProcessingConfig


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="rugby-cli",
        description="Rugby video processing pipeline CLI",
    )
    
    parser.add_argument(
        "--config",
        required=True,
        help="Launch Provided Pipeline",
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
    print("--------------")
    print(f"Loaded configuration from {config_path}")

    video_config = VideoProcessingConfig(config.get('video_processing', {}))
    print(video_config)

def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    print(args)

    if not hasattr(args, 'config'):
        parser.print_help()
        return 1

    load_yaml(args.config)

    return 0


if __name__ == "__main__":
    sys.exit(main())