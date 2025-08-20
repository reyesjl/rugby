#!/usr/bin/env python3
"""
Apply Biasware LLC proprietary license headers to source files.

- Preserves shebangs on scripts.
- Updates .py, .sh, and .yaml/.yml/.toml files.
- Skips files in .git, .venv, env, htmlcov, .pytest_cache.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

HEADER_LINES = [
    "Copyright (c) 2025 Biasware LLC",
    "Proprietary and Confidential. All Rights Reserved.",
    "This file is the sole property of Biasware LLC.",
    "Unauthorized use, distribution, or reverse engineering is prohibited.",
]

PY_HEADER = "\n".join([f"# {line}" for line in HEADER_LINES]) + "\n\n"
SH_HEADER = "\n".join([f"# {line}" for line in HEADER_LINES]) + "\n\n"
TXT_HEADER = "\n".join([f"# {line}" for line in HEADER_LINES]) + "\n\n"

INCLUDE_EXTS = {".py", ".sh", ".bash", ".toml", ".yaml", ".yml"}
EXCLUDE_DIRS = {".git", ".venv", "env", "htmlcov", ".pytest_cache", "__pycache__"}

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(d in parts for d in EXCLUDE_DIRS)

def has_header(text: str) -> bool:
    return "Biasware LLC" in text and "Proprietary" in text

def apply_header_to_text(path: Path, text: str) -> str:
    if has_header(text):
        return text

    if text.startswith("#!"):  # preserve shebang
        first_line, rest = text.split("\n", 1)
        header = SH_HEADER if path.suffix in {".sh", ".bash"} else PY_HEADER
        return f"{first_line}\n{header}{rest}"
    else:
        if path.suffix in {".sh", ".bash"}:
            return SH_HEADER + text
        elif path.suffix == ".py":
            return PY_HEADER + text
        else:
            return TXT_HEADER + text

def iter_files(base: Path, exts: set[str]) -> Iterable[Path]:
    for p in base.rglob("*"):
        if p.is_file() and p.suffix in exts and not should_skip(p):
            yield p

def main() -> int:
    changed = 0
    for file_path in iter_files(ROOT, INCLUDE_EXTS):
        try:
            original = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
        updated = apply_header_to_text(file_path, original)
        if updated != original:
            file_path.write_text(updated, encoding="utf-8")
            changed += 1
            print(f"Updated header: {file_path}")

    print(f"\nLicense header update complete. Files changed: {changed}")
    return 0

if __name__ == "__main__":
    sys.exit(main())