# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Additional CLI coverage for version, status, and help paths."""

from core import cli


def test_cli_version(caplog):
    caplog.set_level("INFO")
    rc = cli.main(["--version"])
    # main returns 0 for version path
    assert rc == 0
    # Verify log contains version info
    logs = "\n".join(rec.message for rec in caplog.records)
    assert "version" in logs.lower()


def test_cli_status(caplog):
    caplog.set_level("INFO")
    rc = cli.main(["--status"])
    assert rc == 0
    logs = "\n".join(rec.message for rec in caplog.records)
    assert "status" in logs.lower()


def test_cli_no_args_prints_help(capsys):
    rc = cli.main([])
    captured = capsys.readouterr()
    assert rc == 1
    assert "usage:" in captured.out.lower()
