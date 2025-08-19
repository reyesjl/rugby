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
    print("\n==============================")
    print(f"  Pipeline Configuration Loaded from: {config_path}")
    print("==============================")
    video_config = VideoProcessingConfig(config.get('video_processing', {}))
    print("\n--- Video Sources ---")
    for ix, src in enumerate(video_config.video_sources.sources):
        print(f"  Source [{ix+1}]:")
        print(f"    Type         : {src.source_type.value}")
        print(f"    Path         : {src.path}")
        print(f"    Watch Patterns: {', '.join(src.watch_patterns) if src.watch_patterns else 'None'}")

    print("\n--- Conversion Settings ---")
    ffmpeg = video_config.conversion_config.ffmpeg
    print(f"  Video Codec   : {ffmpeg.video_codec}")
    print(f"  CRF           : {ffmpeg.crf}")
    print(f"  Preset        : {ffmpeg.preset}")
    print(f"  Audio Codec   : {ffmpeg.audio_codec}")
    print(f"  Audio Bitrate : {ffmpeg.audio_bitrate}")
    print(f"  Parallel Jobs : {video_config.conversion_config.parallel_workers}")

    print("\n--- Indexing Settings ---")
    idx = video_config.indexing_config
    print(f"  AI Provider   : {idx.ai_provider}")
    print(f"  Model         : {idx.model}")
    print(f"  Batch Size    : {idx.batch_size}")
    pm = idx.prompt_model
    if pm.system or pm.user or pm.instructions or pm.examples:
        print("  Prompt Model:")
        if pm.system:
            print("    System:      ", pm.system.replace('\n', '\n      '))
        if pm.user:
            print("    User:        ", pm.user.replace('\n', '\n      '))
        if pm.instructions:
            print("    Instructions:", pm.instructions.replace('\n', '\n      '))
        if pm.examples:
            print("    Examples:")
            for ex in pm.examples:
                print(f"      - user: {ex.get('user', '')}")
                print(f"        assistant: {ex.get('assistant', '')}")
    else:
        print("  Prompt Model  : (none)")
    print("==============================\n")

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