#!/usr/bin/env python3
"""
Animus CLI: simple command-line wrapper for index management tasks.

Subcommands:
  - index rebuild         Rebuild master index to animus/data (MP4 preferred)
  - index mp4-only        Filter current index to MP4-only (backs up full index)
  - index update-to-mp4   Update Tuesday session MPG references to MP4 where available

Examples:
  python scripts/animus_cli.py index rebuild \
      --include-folders tuesday_session_08_06_2025_mp4

  python scripts/animus_cli.py index mp4-only
  python scripts/animus_cli.py index update-to-mp4
"""
import argparse
import os
import sys

# Allow importing sibling scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from build_searchable_index import build_master_index  # noqa: E402
from create_mp4_only_index import create_mp4_only_index  # noqa: E402
from update_index_to_mp4 import update_index_to_mp4  # noqa: E402


def cmd_index_rebuild(args: argparse.Namespace) -> int:
    include = args.include_folders or None
    output = args.output or os.path.join('animus', 'data', 'master_video_index.json')
    index = build_master_index(
        base_summaries_dir=args.summaries,
        base_transcripts_dir=args.transcripts,
        output_path=output,
        include_folders=include,
        prefer_mp4=not args.no_prefer_mp4,
    )
    print(f"✅ Rebuilt index with {len(index)} entries → {output}")
    return 0


def cmd_index_mp4_only(args: argparse.Namespace) -> int:
    index_path = args.index or os.path.join('animus', 'data', 'master_video_index.json')
    create_mp4_only_index(index_path=index_path)
    return 0


def cmd_index_update_to_mp4(args: argparse.Namespace) -> int:
    index_path = args.index or os.path.join('animus', 'data', 'master_video_index.json')
    ok = update_index_to_mp4(index_file=index_path)
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Animus CLI')
    sub = p.add_subparsers(dest='command', required=True)

    # index group
    p_index = sub.add_parser('index', help='Index management commands')
    sub_index = p_index.add_subparsers(dest='index_cmd', required=True)

    # index rebuild
    p_rebuild = sub_index.add_parser('rebuild', help='Rebuild master index (MP4 preferred)')
    p_rebuild.add_argument('--summaries', default='./summaries', help='Summaries base dir')
    p_rebuild.add_argument('--transcripts', default='./transcripts', help='Transcripts base dir')
    p_rebuild.add_argument('--output', default=os.path.join('animus', 'data', 'master_video_index.json'), help='Output index path')
    p_rebuild.add_argument('--include-folders', nargs='+', help='List of folders to include')
    p_rebuild.add_argument('--no-prefer-mp4', action='store_true', help='Do not prefer MP4 when available')
    p_rebuild.set_defaults(func=cmd_index_rebuild)

    # index mp4-only
    p_mp4 = sub_index.add_parser('mp4-only', help='Filter current index to MP4-only (backs up full index)')
    p_mp4.add_argument('--index', default=os.path.join('animus', 'data', 'master_video_index.json'), help='Index file path')
    p_mp4.set_defaults(func=cmd_index_mp4_only)

    # index update-to-mp4
    p_upd = sub_index.add_parser('update-to-mp4', help='Update Tuesday session MPG → MP4 where available')
    p_upd.add_argument('--index', default=os.path.join('animus', 'data', 'master_video_index.json'), help='Index file path')
    p_upd.set_defaults(func=cmd_index_update_to_mp4)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
