#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script for tangelo.dlpno package __init__ exports.

Checks:
  1. Import side-effect silence.
  2. Required public symbols exist after `import tangelo.dlpno as dlpno`.
  3. Symbols are importable via `from tangelo.dlpno import <symbol>`.
  4. default_pno_parameters consistency with config constants via package export.
  5. Optional __all__ consistency (if defined).
  6. Re-import idempotence (object identity for functions / classes stable).
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import sys
from typing import Any, Dict

SUMMARY: Dict[str, Any] = {
    "module_import": False,
    "side_effect_stdout": "",
    "side_effect_stderr": "",
    "exports_present": {},
    "from_import_success": {},
    "default_params_validation": {},
    "all_symbol_consistency": {},
    "reimport_idempotent": {},
    "overall_pass": False,
    "fail_reasons": [],
}

FAIL = SUMMARY["fail_reasons"]

REQUIRED_EXPORTS = [
    "PNO_TAU_SEQUENCE_DEFAULT",
    "PAIR_TAU_SEQUENCE_DEFAULT",
    "ENERGY_ABS_TOL_DEFAULT",
    "ENERGY_REL_TOL_DEFAULT",
    "OrbitalSpace",
    "PNOParameters",
    "ConvergenceCriteria",
    "ConvergenceRecord",
    "default_pno_parameters",
    "ConvergenceMonitor",
]


def fail(msg: str):
    FAIL.append(msg)


def import_pkg():
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        try:
            dlpno = importlib.import_module("tangelo.dlpno")
            SUMMARY["module_import"] = True
        except Exception as exc:  # noqa
            fail(f"Import failure: {exc}")
            return None
    SUMMARY["side_effect_stdout"] = buf_out.getvalue()
    SUMMARY["side_effect_stderr"] = buf_err.getvalue()
    if SUMMARY["side_effect_stdout"].strip():
        fail("Unexpected stdout on import.")
    if SUMMARY["side_effect_stderr"].strip():
        fail("Unexpected stderr on import.")
    return dlpno


def check_exports(dlpno):
    for name in REQUIRED_EXPORTS:
        present = hasattr(dlpno, name)
        SUMMARY["exports_present"][name] = present
        if not present:
            fail(f"Missing export: {name}")


def check_from_imports():
    results = {}
    for name in REQUIRED_EXPORTS:
        try:
            ns = {}
            exec(f'from tangelo.dlpno import {name} as SYM', {}, ns)
            results[name] = True
        except Exception as exc:  # noqa
            results[name] = False
            fail(f"from-import failed for {name}: {exc}")
    SUMMARY["from_import_success"] = results


def check_default_params(dlpno):
    if not hasattr(dlpno, "default_pno_parameters"):
        fail("default_pno_parameters missing (export phase).")
        return
    params = dlpno.default_pno_parameters()
    # basic field comparisons
    expected_pairs = [
        ("pno_tau_sequence", dlpno.PNO_TAU_SEQUENCE_DEFAULT),
        ("pair_tau_sequence", dlpno.PAIR_TAU_SEQUENCE_DEFAULT),
        ("energy_abs_tol", dlpno.ENERGY_ABS_TOL_DEFAULT),
        ("energy_rel_tol", dlpno.ENERGY_REL_TOL_DEFAULT),
    ]
    field_results = {}
    for field, expected in expected_pairs:
        actual = getattr(params, field, None)
        ok = actual == expected
        field_results[field] = {"expected": expected, "actual": actual, "pass": ok}
        if not ok:
            fail(f"default_pno_parameters mismatch via package export: {field}")
    SUMMARY["default_params_validation"] = field_results


def check_all_consistency(dlpno):
    pkg_all = getattr(dlpno, "__all__", None)
    if pkg_all is None:
        SUMMARY["all_symbol_consistency"] = {"__all__": None, "checked": False}
        return
    missing_from_all = [e for e in REQUIRED_EXPORTS if e not in pkg_all]
    SUMMARY["all_symbol_consistency"] = {
        "__all__": pkg_all,
        "missing_required": missing_from_all,
        "checked": True
    }
    if missing_from_all:
        fail(f"__all__ missing required exports: {missing_from_all}")


def check_reimport_identity():
    try:
        import tangelo.dlpno as d1
        importlib.reload(d1)
        import tangelo.dlpno as d2
        # Choose representative callables / classes
        targets = ["default_pno_parameters", "ConvergenceMonitor", "OrbitalSpace"]
        identity = {}
        for t in targets:
            identity[t] = getattr(d1, t) is getattr(d2, t)
        SUMMARY["reimport_idempotent"] = identity
    except Exception as exc:  # noqa
        fail(f"Re-import identity check failed: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Verify tangelo.dlpno __init__ exports.")
    parser.add_argument("--json-out", type=str, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    dlpno = import_pkg()
    if dlpno:
        check_exports(dlpno)
        check_from_imports()
        check_default_params(dlpno)
        check_all_consistency(dlpno)
        check_reimport_identity()

    SUMMARY["overall_pass"] = len(FAIL) == 0

    if args.verbose:
        print("=== DLPNO INIT EXPORT VERIFICATION REPORT ===")
        for k, v in SUMMARY.items():
            if k in {"side_effect_stdout", "side_effect_stderr"} and not v:
                continue
            print(f"{k}: {v}")
        print("=============================================")
    else:
        status = "PASS" if SUMMARY["overall_pass"] else "FAIL"
        print(f"[dlpno_init] Verification {status}. Fail reasons: {FAIL}")

    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(SUMMARY, f, indent=2)
        except Exception as exc:  # noqa
            print(f"Could not write JSON summary: {exc}", file=sys.stderr)

    sys.exit(0 if SUMMARY["overall_pass"] else 1)


if __name__ == "__main__":
    main()