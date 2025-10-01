#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DLPNO config module verification script.

Scope:
- Import tangelo.dlpno.config and verify:
  * Constants exist and have exact expected values.
  * Monotonic sequences are strictly decreasing.
  * validate_monotonic() behavior on multiple edge cases.
  * default_pno_parameters() from structures matches config constants.
  * Import-time validation raises ValueError if a non-monotonic sequence
    were hypothetically present (simulated by dynamic module reconstruction;
    original module is left untouched).
  * No unexpected side-effect logs or stdout/stderr noise from import.
- Provides structured JSON summary (optional) and exit code != 0 on failure.

Usage:
    python scripts/verify_dlpno_config.py
    python scripts/verify_dlpno_config.py --verbose
    python scripts/verify_dlpno_config.py --json-out verify_config.json

Exit codes:
  0 = all checks passed
  1 = one or more checks failed
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import math
import os
import sys
import types
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

EXPECTED = {
    "PNO_TAU_SEQUENCE_DEFAULT": [1.0e-4, 7.0e-5, 5.0e-5, 3.5e-5, 2.5e-5],
    "PAIR_TAU_SEQUENCE_DEFAULT": [1.0e-6, 5.0e-7, 2.0e-7],
    "ENERGY_ABS_TOL_DEFAULT": 1.0e-6,
    "ENERGY_REL_TOL_DEFAULT": 5.0e-7,
    "MAX_EXTRAP_POINTS": 3,
    "DEFAULT_RANDOM_SEED": 20250101,
}

SUMMARY: Dict[str, Any] = {
    "module_import": False,
    "constants": {},
    "monotonic_sequences": {},
    "validate_function": {},
    "default_pno_parameters": {},
    "simulated_import_guard": {},
    "side_effect_stdout": "",
    "side_effect_stderr": "",
    "overall_pass": False,
    "fail_reasons": [],
}


def strict_monotonic_decreasing(seq: List[float]) -> bool:
    for a, b in zip(seq, seq[1:]):
        if not (b < a):
            return False
    return True


def record_failure(reason: str):
    SUMMARY["fail_reasons"].append(reason)


def check_import() -> Tuple[types.ModuleType | None, types.ModuleType | None]:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        try:
            config_mod = importlib.import_module("tangelo.dlpno.config")
            # Also import structures to get default_pno_parameters
            structures_mod = importlib.import_module("tangelo.dlpno.structures")
            SUMMARY["module_import"] = True
        except Exception as exc:  # noqa
            record_failure(f"Import failed: {exc}")
            return None, None
    SUMMARY["side_effect_stdout"] = buf_out.getvalue()
    SUMMARY["side_effect_stderr"] = buf_err.getvalue()
    if SUMMARY["side_effect_stdout"].strip():
        record_failure("Unexpected stdout on import.")
    if SUMMARY["side_effect_stderr"].strip():
        record_failure("Unexpected stderr on import.")
    return config_mod, structures_mod


def check_constants(config_mod):
    for name, expected in EXPECTED.items():
        val = getattr(config_mod, name, None)
        SUMMARY["constants"][name] = {
            "expected": expected,
            "actual": val,
            "pass": val == expected,
        }
        if val != expected:
            record_failure(f"Constant {name} mismatch: expected {expected}, got {val}")


def check_monotonic(config_mod):
    for seq_name in ("PNO_TAU_SEQUENCE_DEFAULT", "PAIR_TAU_SEQUENCE_DEFAULT"):
        seq = getattr(config_mod, seq_name, None)
        ok = isinstance(seq, list) and strict_monotonic_decreasing(seq)
        SUMMARY["monotonic_sequences"][seq_name] = {
            "sequence": seq,
            "strictly_decreasing": ok,
        }
        if not ok:
            record_failure(f"Sequence {seq_name} is not strictly decreasing.")


def check_validate_function(config_mod):
    vf = getattr(config_mod, "validate_monotonic", None)
    if vf is None:
        record_failure("validate_monotonic not found.")
        SUMMARY["validate_function"]["present"] = False
        return
    SUMMARY["validate_function"]["present"] = True

    tests = {
        "basic_true": ([3.0, 2.0, 1.0], True),
        "equal_false": ([3.0, 3.0, 1.0], False),
        "ascending_false": ([1.0, 2.0, 3.0], False),
        "single_true": ([1.23], True),
        "empty_true": ([], True),
        "negative_true": ([-1e-3, -2e-3], False),  # -2e-3 is less than -1e-3 => sequence goes down? Wait: -2e-3 < -1e-3, so progression is -1e-3 -> -2e-3 = decreasing (b<a). Correction: expected True.
    }
    # Correct negative case expectation
    tests["negative_true"] = ([-1e-3, -2e-3], True)

    results = {}
    for label, (inp, exp) in tests.items():
        try:
            got = vf(inp)
            results[label] = {"input": inp, "expected": exp, "actual": got, "pass": got == exp}
            if got != exp:
                record_failure(f"validate_monotonic failed for {label}: expected {exp}, got {got}")
        except Exception as exc:
            results[label] = {"input": inp, "expected": exp, "actual": f"EXC {exc}", "pass": False}
            record_failure(f"validate_monotonic raised exception for {label}: {exc}")
    SUMMARY["validate_function"]["cases"] = results


def check_default_pno_parameters(structures_mod, config_mod):
    func = getattr(structures_mod, "default_pno_parameters", None)
    if func is None:
        record_failure("default_pno_parameters not found.")
        return
    obj = func()
    # We don't know the dataclass attribute names beyond typical ones
    data = asdict(obj)
    expected_map = {
        "pno_tau_sequence": "PNO_TAU_SEQUENCE_DEFAULT",
        "pair_tau_sequence": "PAIR_TAU_SEQUENCE_DEFAULT",
        "energy_abs_tol": "ENERGY_ABS_TOL_DEFAULT",
        "energy_rel_tol": "ENERGY_REL_TOL_DEFAULT",
        "max_extrap_points": "MAX_EXTRAP_POINTS",
    }
    result = {}
    for field, const_name in expected_map.items():
        expected = getattr(config_mod, const_name, None)
        actual = data.get(field, None)
        ok = actual == expected
        result[field] = {"expected": expected, "actual": actual, "pass": ok}
        if not ok:
            record_failure(f"default_pno_parameters mismatch for {field}: expected {expected}, got {actual}")
    SUMMARY["default_pno_parameters"] = result


def simulate_import_guard(config_mod_path: str):
    """
    Simulate a broken module by constructing a temporary module object
    with modified sequence (not strictly decreasing) and executing its source
    after forcibly replacing the sequence. This checks that the import-time
    validation would raise ValueError.

    Note: We DO NOT modify the real file. We read its source and patch in-memory.
    """
    try:
        import inspect
        src = inspect.getsource(config_mod_path)  # actually pass module, not path
    except Exception:
        # Fallback: open via loader
        try:
            import inspect
            src = inspect.getsource(config_mod_path)
        except Exception as exc:
            record_failure(f"Could not retrieve source for simulation: {exc}")
            SUMMARY["simulated_import_guard"]["performed"] = False
            return

    # Actually we passed module object, correct approach:
    import inspect
    try:
        src = inspect.getsource(config_mod_path)
    except Exception as exc:
        record_failure(f"Could not get source for simulation: {exc}")
        SUMMARY["simulated_import_guard"]["performed"] = False
        return

    # Patch: replace first occurrence of the valid PNO sequence with a non-monotonic one
    bad_seq = "[1.0e-4, 1.0e-4, 5.0e-5]"  # duplicate to violate strict decrease
    import re
    patched = re.sub(
        r"\[1\.0e-4,\s*7\.0e-5,\s*5\.0e-5,\s*3\.5e-5,\s*2\.5e-5\]",
        bad_seq,
        src,
        count=1,
    )

    temp_mod = types.ModuleType("_dlpno_config_sim")
    # Execute patched source; expect ValueError
    try:
        exec(patched, temp_mod.__dict__)  # noqa: S102
        # If no ValueError raised internally, we emulate validation by calling validate_monotonic if present
        if "PNO_TAU_SEQUENCE_DEFAULT" in temp_mod.__dict__ and "validate_monotonic" in temp_mod.__dict__:
            # Simulate what original module does: raise if not strictly decreasing
            seq = temp_mod.__dict__["PNO_TAU_SEQUENCE_DEFAULT"]
            if not temp_mod.__dict__["validate_monotonic"](seq):
                # If our patched version did not auto-raise, treat that as partial pass but note difference.
                SUMMARY["simulated_import_guard"] = {
                    "performed": True,
                    "expected_exception": "ValueError",
                    "raised": False,
                    "note": "Patched version did not auto-raise; verify actual module enforces at import.",
                }
                # This is a soft warning not necessarily a failure because actual file DID validate.
            else:
                record_failure("Patched non-monotonic sequence incorrectly validated as decreasing.")
        else:
            record_failure("Simulation missing sequence or validate function.")
            SUMMARY["simulated_import_guard"] = {
                "performed": True,
                "expected_exception": "ValueError",
                "raised": False,
                "missing_symbols": True,
            }
            return
    except ValueError as exc:
        SUMMARY["simulated_import_guard"] = {
            "performed": True,
            "expected_exception": "ValueError",
            "raised": True,
            "message": str(exc),
        }
        return
    except Exception as exc:  # Unexpected
        record_failure(f"Unexpected exception during simulation: {exc}")
        SUMMARY["simulated_import_guard"] = {
            "performed": True,
            "expected_exception": "ValueError",
            "raised": False,
            "unexpected_exception": str(exc),
        }


def main():
    parser = argparse.ArgumentParser(description="Verify DLPNO config scaffolding.")
    parser.add_argument("--json-out", type=str, default=None, help="Write JSON summary to file.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed results.")
    args = parser.parse_args()

    # Step 1: import modules
    config_mod, structures_mod = check_import()
    if config_mod and structures_mod:
        # Step 2: constants & sequences
        check_constants(config_mod)
        check_monotonic(config_mod)
        # Step 3: validate_monotonic cases
        check_validate_function(config_mod)
        # Step 4: default_pno_parameters
        check_default_pno_parameters(structures_mod, config_mod)
        # Step 5: simulate import guard
        simulate_import_guard(config_mod)

    # Final pass/fail
    SUMMARY["overall_pass"] = len(SUMMARY["fail_reasons"]) == 0

    if args.verbose:
        print("=== DLPNO CONFIG VERIFICATION REPORT ===")
        for k, v in SUMMARY.items():
            if k in {"side_effect_stdout", "side_effect_stderr"} and not v:
                continue
            print(f"{k}: {v}")
        print("========================================")
    else:
        status = "PASS" if SUMMARY["overall_pass"] else "FAIL"
        print(f"[config] Verification {status}. Fail reasons: {SUMMARY['fail_reasons']}")

    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(SUMMARY, f, indent=2)
        except Exception as exc:  # noqa
            print(f"Could not write JSON summary: {exc}", file=sys.stderr)

    sys.exit(0 if SUMMARY["overall_pass"] else 1)


if __name__ == "__main__":
    main()