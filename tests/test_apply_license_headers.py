"""Tests for ops.apply_license_headers helpers and iterator."""

from pathlib import Path

from ops.apply_license_headers import (
    PY_HEADER,
    SH_HEADER,
    apply_header_to_text,
    has_header,
    iter_files,
)


def test_has_header_detects_header():
    assert has_header(PY_HEADER + "print('x')\n")
    assert has_header(SH_HEADER + "echo x\n")


def test_apply_header_preserves_shebang_py():
    text = "#!/usr/bin/env python3\nprint('hi')\n"
    out = apply_header_to_text(Path("x.py"), text)
    assert out.startswith("#!/usr/bin/env python3\n")
    assert PY_HEADER in out


def test_apply_header_preserves_shebang_sh():
    text = "#!/usr/bin/env bash\necho hi\n"
    out = apply_header_to_text(Path("x.sh"), text)
    assert out.startswith("#!/usr/bin/env bash\n")
    assert SH_HEADER in out


def test_apply_header_plain_py():
    text = "print('hi')\n"
    out = apply_header_to_text(Path("x.py"), text)
    assert out.startswith(PY_HEADER)


def test_iter_files_filters_exts_and_skips_dirs(tmp_path):
    # Create a small tree
    (tmp_path / ".git").mkdir()
    (tmp_path / "htmlcov").mkdir()
    (tmp_path / "a.py").write_text("print(1)\n")
    (tmp_path / "b.txt").write_text("hello\n")
    (tmp_path / "c.sh").write_text("echo hi\n")

    files = list(iter_files(tmp_path, {".py", ".sh"}))
    names = {Path(f).name for f in files}
    assert "a.py" in names
    assert "c.sh" in names
    assert "b.txt" not in names
