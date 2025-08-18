"""Rugby CLI entry point."""

import argparse
import sys
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="rugby-cli",
        description="Rugby video processing pipeline CLI",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version")
    version_parser.set_defaults(func=cmd_version)
    
    # Status command  
    status_parser = subparsers.add_parser("status", help="Show pipeline status")
    status_parser.set_defaults(func=cmd_status)
    
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


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if hasattr(args, "func"):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())