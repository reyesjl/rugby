# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Smoke test ops.apply_license_headers.main to ensure it runs without errors."""

from ops import apply_license_headers as alh


def test_ops_main_smoke(monkeypatch, tmp_path, capsys):
    # Put a tiny file under a temp ROOT and monkeypatch ROOT constant
    p = tmp_path / "x.py"
    p.write_text("print('x')\n", encoding="utf-8")

    monkeypatch.setattr(alh, "ROOT", tmp_path)

    rc = alh.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "Files changed" in out
