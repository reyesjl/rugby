# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Ensure update_headers skips files that cannot be read without crashing."""

from pathlib import Path

from ops.apply_license_headers import update_headers


def test_update_headers_skips_unreadable_file(tmp_path, monkeypatch):
    f = tmp_path / "bad.py"
    f.write_text("print('x')\n", encoding="utf-8")

    # Simulate read_text raising for this specific file
    original_read_text = Path.read_text

    def flaky_read_text(self, *args, **kwargs):
        if self == f:
            raise OSError("boom")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", flaky_read_text)

    changed = update_headers(tmp_path)
    # Should not crash; other files none so changed==0
    assert isinstance(changed, int)
