# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Integration-like test for update_headers over a temp tree."""

from pathlib import Path

from ops.apply_license_headers import has_header, update_headers


def test_update_headers_changes_supported_files(tmp_path):
    (tmp_path / "a.py").write_text("print('x')\n", encoding="utf-8")
    (tmp_path / "b.sh").write_text("echo hi\n", encoding="utf-8")
    (tmp_path / "c.txt").write_text("hello\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()

    changed = update_headers(Path(tmp_path))
    # .py, .sh, and .txt via TXT_HEADER should be updated where exts included
    # TXT is not in INCLUDE_EXTS by default; expect 2 changes
    assert changed == 2

    assert has_header((tmp_path / "a.py").read_text(encoding="utf-8"))
    assert has_header((tmp_path / "b.sh").read_text(encoding="utf-8"))
    # By design, .txt is not included in INCLUDE_EXTS, so ensure it's untouched
    assert not has_header((tmp_path / "c.txt").read_text(encoding="utf-8"))
