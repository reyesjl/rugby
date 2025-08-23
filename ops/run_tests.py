#!/usr/bin/env python3
# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""
Rugby Pipeline Test Runner

A pytest-like test runner for the rugby pipeline that works without external dependencies.
"""

import importlib.util
import inspect
import io
import logging
import os
import sys
import tempfile
from types import SimpleNamespace
from typing import Any, Optional


class TestResult:
    """Test result container."""

    def __init__(self, name: str, passed: bool, error: str = "") -> None:
        self.name = name
        self.passed = passed
        self.error = error


def discover_tests(test_dir: str = "tests") -> list[str]:
    """Discover test files in the test directory."""
    test_files: list[str] = []

    if not os.path.exists(test_dir):
        return test_files

    for filename in os.listdir(test_dir):
        if filename.startswith("test_") and filename.endswith(".py"):
            test_files.append(os.path.join(test_dir, filename))

    return sorted(test_files)


def run_test_file(test_file: str) -> list[TestResult]:
    """Run all tests in a test file with minimal pytest-like fixture emulation."""
    results: list[TestResult] = []

    # Import the test module (unique module name per file for isolation)
    module_name = f"test_module_{os.path.basename(test_file).replace('.py','')}"
    spec = importlib.util.spec_from_file_location(module_name, test_file)
    if spec is None or spec.loader is None:
        results.append(TestResult(test_file, False, "Could not load test file"))
        return results
    test_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(test_module)  # type: ignore[union-attr]
    except Exception as e:  # Import/setup error aborts whole file
        results.append(TestResult(test_file, False, str(e)))
        return results

    # Helper fixture implementations -------------------------------------------------
    class _MonkeyPatch:
        def __init__(self) -> None:
            self._env: list[tuple[str, Optional[str]]] = []
            self._attrs: list[tuple[object, str, Optional[object], bool]] = []

        def setenv(self, key: str, value: str) -> None:
            self._env.append((key, os.environ.get(key)))
            os.environ[key] = value

        def setattr(self, obj: Any, name: str, value: Any) -> None:  # type: ignore[override]
            existed = hasattr(obj, name)
            original = getattr(obj, name) if existed else None
            self._attrs.append((obj, name, original, existed))
            setattr(obj, name, value)

        def undo(self) -> None:
            for obj, name, original, existed in reversed(self._attrs):
                if existed:
                    setattr(obj, name, original)
                else:
                    try:
                        delattr(obj, name)
                    except AttributeError:
                        pass
            for key, original in reversed(self._env):
                if original is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original

    class _CapSys:
        def __init__(self) -> None:
            # Use Any for stdout/stderr handles to avoid strict type mismatch under different IO implementations
            self._orig_out: Any = None  # type: ignore[assignment]
            self._orig_err: Any = None  # type: ignore[assignment]
            self._out_buf: Optional[io.StringIO] = None
            self._err_buf: Optional[io.StringIO] = None

        def start(self) -> None:
            self._orig_out, self._orig_err = sys.stdout, sys.stderr
            self._out_buf, self._err_buf = io.StringIO(), io.StringIO()
            sys.stdout, sys.stderr = self._out_buf, self._err_buf

        def stop(self) -> None:
            if self._orig_out is not None:
                sys.stdout = self._orig_out
            if self._orig_err is not None:
                sys.stderr = self._orig_err

        def readouterr(self) -> SimpleNamespace:
            return SimpleNamespace(
                out=self._out_buf.getvalue() if self._out_buf else "",
                err=self._err_buf.getvalue() if self._err_buf else "",
            )

    class _CapLog(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.records: list[logging.LogRecord] = []
            self._level_override: Optional[int] = None

        def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
            # Ensure 'message' attribute is present (mimic logging.makeLogRecord behavior)
            if not hasattr(record, "message"):
                try:
                    record.message = record.getMessage()  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover - defensive
                    record.message = record.msg  # type: ignore[attr-defined]
            self.records.append(record)

        @property
        def text(self) -> str:
            return "\n".join(self.format(r) for r in self.records)

        def clear(self) -> None:
            self.records.clear()

        def set_level(  # compatibility shim
            self, level: int | str, logger: Optional[logging.Logger] = None
        ) -> None:
            lvl = logging.getLevelName(level) if isinstance(level, str) else int(level)
            target = logger or logging.getLogger()
            target.setLevel(lvl)
            self._level_override = lvl

    # Iterate over test callables ----------------------------------------------------
    for name in dir(test_module):
        if not name.startswith("test_"):
            continue
        test_func = getattr(test_module, name)
        if not callable(test_func):
            continue
        sig = inspect.signature(test_func)
        params = sig.parameters
        # Prepare fixtures (typed)
        monkeypatch: _MonkeyPatch | None = (
            _MonkeyPatch() if "monkeypatch" in params else None
        )
        capsys: _CapSys | None = _CapSys() if "capsys" in params else None
        caplog_handler: _CapLog | None = _CapLog() if "caplog" in params else None

        kwargs: dict[str, Any] = {}
        tmp_dir_ctx: tempfile.TemporaryDirectory[str] | None = None
        if "tmp_path" in params:
            tmp_dir_ctx = tempfile.TemporaryDirectory()
            import pathlib

            kwargs["tmp_path"] = pathlib.Path(tmp_dir_ctx.name)
        if monkeypatch:
            kwargs["monkeypatch"] = monkeypatch
        if capsys:
            capsys.start()
            kwargs["capsys"] = capsys
        logger = None
        if caplog_handler:
            logger = logging.getLogger()
            logger.addHandler(caplog_handler)
            caplog_handler.setFormatter(
                logging.Formatter("%(levelname)s:%(name)s:%(message)s")
            )
            kwargs["caplog"] = caplog_handler

        try:
            test_func(**kwargs)
            results.append(TestResult(f"{test_file}::{name}", True))
        except Exception as e:  # noqa: BLE001
            results.append(TestResult(f"{test_file}::{name}", False, str(e)))
        finally:
            if capsys:
                capsys.stop()
            if caplog_handler and logger:
                logger.removeHandler(caplog_handler)
            if monkeypatch:
                monkeypatch.undo()
            if tmp_dir_ctx:
                tmp_dir_ctx.cleanup()

    return results


def main() -> int:
    """Main test runner entry point."""
    print("🏉 Rugby Pipeline Test Runner")
    print("=" * 50)

    # Set up Python path (repo root, not just ops/)
    ops_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(ops_dir)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Provide a dummy OpenAI key for tests that expect it (unless already set)
    os.environ.setdefault("OPENAI_API_KEY", "test-key")

    # Discover tests
    test_files: list[str] = discover_tests()

    if not test_files:
        print("No test files found.")
        return 0

    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file}")
    print()

    # Run tests
    all_results = []
    passed_count = 0
    failed_count = 0

    for test_file in test_files:
        print(f"Running {test_file}...")
        file_results = run_test_file(test_file)
        all_results.extend(file_results)

        for result in file_results:
            if result.passed:
                print(f"  ✅ {result.name}")
                passed_count += 1
            else:
                print(f"  ❌ {result.name}: {result.error}")
                failed_count += 1
        print()

    # Print summary
    total_tests = passed_count + failed_count
    print("=" * 50)
    print(
        f"Test Results: {passed_count} passed, {failed_count} failed, {total_tests} total"
    )

    if failed_count > 0:
        print("❌ Some tests failed")
        return 1
    else:
        print("✅ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
