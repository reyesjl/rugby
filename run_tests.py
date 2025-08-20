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
import os
import sys
import tempfile


class TestResult:
    """Test result container."""

    def __init__(self, name: str, passed: bool, error: str = ""):
        self.name = name
        self.passed = passed
        self.error = error


def discover_tests(test_dir: str = "tests") -> list[str]:
    """Discover test files in the test directory."""
    test_files = []

    if not os.path.exists(test_dir):
        return test_files

    for filename in os.listdir(test_dir):
        if filename.startswith("test_") and filename.endswith(".py"):
            test_files.append(os.path.join(test_dir, filename))

    return sorted(test_files)


def run_test_file(test_file: str) -> list[TestResult]:
    """Run all tests in a test file."""
    results = []

    # Import the test module
    spec = importlib.util.spec_from_file_location("test_module", test_file)
    if spec is None or spec.loader is None:
        results.append(TestResult(test_file, False, "Could not load test file"))
        return results

    test_module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(test_module)
    except Exception as e:
        results.append(TestResult(test_file, False, str(e)))
        return results

    # Find and run test functions
    for name in dir(test_module):
        if name.startswith("test_"):
            test_func = getattr(test_module, name)
            if callable(test_func):
                sig = inspect.signature(test_func)
                params = sig.parameters
                try:
                    if "tmp_path" in params:
                        with tempfile.TemporaryDirectory() as tmpdirname:
                            import pathlib

                            tmp_path = pathlib.Path(tmpdirname)
                            test_func(tmp_path=tmp_path)
                    else:
                        test_func()
                    results.append(TestResult(f"{test_file}::{name}", True))
                except Exception as e:
                    results.append(TestResult(f"{test_file}::{name}", False, str(e)))
    return results


def main() -> int:
    """Main test runner entry point."""
    print("🏉 Rugby Pipeline Test Runner")
    print("=" * 50)

    # Set up Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Discover tests
    test_files = discover_tests()

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
