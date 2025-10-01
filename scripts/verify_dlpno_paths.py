#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script for tangelo.dlpno.paths module.

Checks:
  1. Import side-effect silence.
  2. pair_key ordering (i>j swapped).
  3. Formatting: zero-padding to 4 digits for typical ranges.
  4. Handling of large indices (>=10000) => zero-padding rule naturally exceeded.
  5. Edge cases: i==j, negative indices (current code behavior documented, not failed unless unsafe).
  6. pair_cache_dir and run_iteration_dir path joins correctness.
  7. Determinism on repeated calls.

Exit code 0 on success, 1 on any critical failure.
Non-fatal observations (e.g. i==j allowed) are noted but not failing unless they pose correctness risk.

Usage:
    python scripts/verify_dlpno_paths.py
    python scripts/verify_dlpno_paths.py --verbose
    python scripts/verify_dlpno_paths.py --json-out verify_paths.json
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import re
import sys
from typing import Any, Dict, List

SUMMARY: Dict[str, Any] = {
    "module_import": False,
    "side_effect_stdout": "",
    "side_effect_stderr": "",
    "pair_key_tests": {},
    "edge_cases": {},
    "cache_dir_tests": {},
    "iteration_dir_tests": {},
    "determinism": {},
    "overall_pass": False,
    "fail_reasons": [],
}

FAIL = SUMMARY["fail_reasons"]

PAIR_REGEX_4 = re.compile(r"^pair_\d{4}_\d{4}$")


def fail(msg: str):
    FAIL.append(msg)


def import_module():
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        try:
            paths = importlib.import_module("tangelo.dlpno.paths")
            SUMMARY["module_import"] = True
        except Exception as exc:
            fail(f"Import failure: {exc}")
            return None
    SUMMARY["side_effect_stdout"] = buf_out.getvalue()
    SUMMARY["side_effect_stderr"] = buf_err.getvalue()
    if SUMMARY["side_effect_stdout"].strip():
        fail("Unexpected stdout during import.")
    if SUMMARY["side_effect_stderr"].strip():
        fail("Unexpected stderr during import.")
    return paths


def test_pair_key(paths):
    pk = getattr(paths, "pair_key", None)
    if pk is None:
        fail("pair_key not found.")
        return

    cases = [
        (0, 1, "pair_0000_0001"),
        (1, 0, "pair_0000_0001"),  # order normalization
        (15, 7, "pair_0007_0015"),
        (7, 15, "pair_0007_0015"),
        (123, 1234, "pair_0123_1234"),
    ]
    results = {}

    for i, j, expected in cases:
        got = pk(i, j)
        ok = (got == expected)
        results[f"{i},{j}"] = {"expected": expected, "actual": got, "pass": ok}
        if not ok:
            fail(f"pair_key({i},{j}) -> {got}, expected {expected}")

    # Large index case
    large = pk(12345, 3)
    # Expect zero-pad at least 4; if index len > 4, full number appears
    large_ok = large.startswith("pair_0003_12345")
    results["large_case"] = {"value": large, "pass": large_ok}
    if not large_ok:
        fail(f"Large index formatting unexpected: {large}")

    # Pattern check on standard-sized results
    pattern_fail = False
    for k, info in results.items():
        if k == "large_case":
            continue
        if info["pass"] and not PAIR_REGEX_4.match(info["actual"]):
            pattern_fail = True
    if pattern_fail:
        fail("Some pair_key outputs did not match 4-digit zero-padding pattern for small indices.")

    SUMMARY["pair_key_tests"] = results


def test_edge_cases(paths):
    pk = getattr(paths, "pair_key", None)
    edge_info = {}
    # i == j
    same = pk(5, 5)
    edge_info["i_equals_j"] = same
    # Negative indices
    neg = pk(-2, 4)
    edge_info["negative_mixed"] = neg
    # Document if negative passes (we do not fail unless it breaks format expectation)
    if "pair_" not in neg:
        fail("Negative index formatting invalid.")
    # Very large both sides
    huge = pk(99999, 100000)
    edge_info["huge"] = huge

    SUMMARY["edge_cases"] = edge_info
    # Policy decision: not failing i==j yet; future logic may forbid identical pairs.


def test_cache_dirs(paths):
    pcd = getattr(paths, "pair_cache_dir", None)
    pk = getattr(paths, "pair_key", None)
    if pcd is None or pk is None:
        fail("pair_cache_dir or pair_key missing.")
        return
    base = "cache_root"
    key = pk(2, 9)
    path = pcd(base, 2, 9)
    expected_suffix = os.path.join(base, key).replace("\\", "/")
    normalized = path.replace("\\", "/")
    pass_ok = normalized.endswith(expected_suffix)
    SUMMARY["cache_dir_tests"] = {
        "base": base,
        "pair": (2, 9),
        "value": path,
        "expected_suffix": expected_suffix,
        "pass": pass_ok
    }
    if not pass_ok:
        fail(f"pair_cache_dir path mismatch: {path} (expected suffix {expected_suffix})")


def test_iteration_dir(paths):
    rid = getattr(paths, "run_iteration_dir", None)
    if rid is None:
        fail("run_iteration_dir missing.")
        return
    base = "run_root"
    values = {}
    for it in [0, 1, 9, 10, 123]:
        p = rid(base, it).replace("\\", "/")
        expected = f"{base}/iter_{it:03d}"
        ok = (p == expected)
        values[it] = {"expected": expected, "actual": p, "pass": ok}
        if not ok:
            fail(f"run_iteration_dir({it}) -> {p}, expected {expected}")
    SUMMARY["iteration_dir_tests"] = values


def test_determinism(paths):
    pk = paths.pair_key
    snapshots = [pk(8, 2), pk(2, 8), pk(8, 2)]
    deterministic = snapshots[0] == snapshots[1] == snapshots[2]
    SUMMARY["determinism"] = {
        "snapshots": snapshots,
        "pair_key_deterministic": deterministic
    }
    if not deterministic:
        fail("pair_key non-deterministic results detected.")


def main():
    parser = argparse.ArgumentParser(description="Verify DLPNO paths utilities.")
    parser.add_argument("--json-out", type=str, default=None, help="Write JSON result.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    args = parser.parse_args()

    paths = import_module()
    if paths:
        test_pair_key(paths)
        test_edge_cases(paths)
        test_cache_dirs(paths)
        test_iteration_dir(paths)
        test_determinism(paths)

    SUMMARY["overall_pass"] = len(FAIL) == 0

    if args.verbose:
        print("=== DLPNO PATHS VERIFICATION REPORT ===")
        for k, v in SUMMARY.items():
            print(f"{k}: {v}")
        print("=======================================")
    else:
        status = "PASS" if SUMMARY["overall_pass"] else "FAIL"
        print(f"[paths] Verification {status}. Fail reasons: {FAIL}")

    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(SUMMARY, f, indent=2)
        except Exception as exc:
            print(f"Could not write JSON summary: {exc}", file=sys.stderr)

    sys.exit(0 if SUMMARY["overall_pass"] else 1)


if __name__ == "__main__":
    main()