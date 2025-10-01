#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script for tangelo.dlpno.localization.adapter.

Checks:
  1. Import side-effect silence.
  2. list_supported_methods returns expected canonical list ["boys", "pipek"].
  3. get_localized_orbitals raises NotImplementedError with informative message.
  4. Case-insensitive usage decision (current spec: no guarantee; we record behavior).
  5. Misspelled method still raises NotImplementedError (record).
  6. No 'pyscf' import present in module source.
  7. JSON summary & exit code.

Exit code: 0 pass / 1 fail.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import sys
import inspect
import re
from typing import Any, Dict

SUMMARY: Dict[str, Any] = {
    "module_import": False,
    "side_effect_stdout": "",
    "side_effect_stderr": "",
    "supported_methods": {},
    "notimplemented_default": {},
    "notimplemented_boys": {},
    "case_variation": {},
    "misspelled_method": {},
    "no_pyscf_import": {},
    "overall_pass": False,
    "fail_reasons": [],
}

FAIL = SUMMARY["fail_reasons"]


def fail(msg: str):
    FAIL.append(msg)


def import_module():
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        try:
            mod = importlib.import_module("tangelo.dlpno.localization.adapter")
            SUMMARY["module_import"] = True
        except Exception as exc:
            fail(f"Import failure: {exc}")
            return None
    SUMMARY["side_effect_stdout"] = buf_out.getvalue()
    SUMMARY["side_effect_stderr"] = buf_err.getvalue()
    if SUMMARY["side_effect_stdout"].strip():
        fail("Unexpected stdout on import.")
    if SUMMARY["side_effect_stderr"].strip():
        fail("Unexpected stderr on import.")
    return mod


def check_supported_methods(mod):
    fn = getattr(mod, "list_supported_methods", None)
    if fn is None:
        fail("list_supported_methods missing.")
        return
    try:
        methods = fn()
    except Exception as exc:
        fail(f"list_supported_methods raised: {exc}")
        return
    expected = ["boys", "pipek"]
    pass_flag = methods == expected
    SUMMARY["supported_methods"] = {
        "returned": methods,
        "expected": expected,
        "pass": pass_flag
    }
    if not pass_flag:
        fail(f"Supported methods mismatch: got {methods}, expected {expected}")


def attempt_get(mod, method: str, label: str):
    fn = getattr(mod, "get_localized_orbitals", None)
    if fn is None:
        fail("get_localized_orbitals missing.")
        return
    try:
        fn(mf=None, method=method)
        fail(f"{label}: Expected NotImplementedError, got no exception.")
        SUMMARY[label] = {"raised": False}
    except NotImplementedError as exc:
        msg = str(exc)
        informative = method.lower() in msg.lower() or "localiz" in msg.lower()
        SUMMARY[label] = {
            "raised": True,
            "message_contains_method_or_hint": informative,
            "message": msg[:200]
        }
        if not informative:
            fail(f"{label}: NotImplementedError message not informative: {msg}")
    except Exception as exc:
        fail(f"{label}: Unexpected exception type {type(exc).__name__}: {exc}")
        SUMMARY[label] = {
            "raised": False,
            "unexpected_exception": str(exc)
        }


def check_notimplemented(mod):
    # default (pipek)
    attempt_get(mod, "pipek", "notimplemented_default")
    # explicitly boys
    attempt_get(mod, "boys", "notimplemented_boys")


def check_case_variation(mod):
    # If case variation differs (PIPEK), we just record outcome; no fail unless silent success
    fn = getattr(mod, "get_localized_orbitals", None)
    if fn is None:
        return
    try:
        fn(mf=None, method="PIPEK")
        fail("case_variation: expected NotImplementedError for uppercase 'PIPEK'.")
        SUMMARY["case_variation"] = {"raised": False}
    except NotImplementedError as exc:
        SUMMARY["case_variation"] = {
            "raised": True,
            "case_sensitive": True,
            "message": str(exc)[:120]
        }
    except Exception as exc:
        fail(f"case_variation: unexpected exception {exc}")
        SUMMARY["case_variation"] = {"raised": False, "unexpected": str(exc)}


def check_misspelled(mod):
    attempt_get(mod, "pyper", "misspelled_method")  # intentionally wrong


def check_no_pyscf_import(mod):
    try:
        src = inspect.getsource(mod)
    except OSError:
        # If source retrieval fails (e.g., compiled), skip with warning
        SUMMARY["no_pyscf_import"] = {"source_read": False, "pass": False}
        fail("Could not read module source for pyscf import check.")
        return
    # Look for import pyscf or from pyscf...
    pattern = re.compile(r"(^|\\n)\\s*from\\s+pyscf|(^|\\n)\\s*import\\s+pyscf")
    found = pattern.search(src) is not None
    SUMMARY["no_pyscf_import"] = {
        "source_read": True,
        "pyscf_import_found": found,
        "pass": not found
    }
    if found:
        fail("pyscf import present (should not be in placeholder).")


def main():
    parser = argparse.ArgumentParser(description="Verify DLPNO localization adapter placeholder.")
    parser.add_argument("--json-out", type=str, default=None, help="Write JSON summary.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    args = parser.parse_args()

    mod = import_module()
    if mod:
        check_supported_methods(mod)
        check_notimplemented(mod)
        check_case_variation(mod)
        check_misspelled(mod)
        check_no_pyscf_import(mod)

    SUMMARY["overall_pass"] = len(FAIL) == 0

    if args.verbose:
        print("=== DLPNO LOCALIZATION ADAPTER VERIFICATION REPORT ===")
        for k, v in SUMMARY.items():
            if k in {"side_effect_stdout", "side_effect_stderr"} and not v:
                continue
            print(f"{k}: {v}")
        print("=====================================================")
    else:
        status = "PASS" if SUMMARY["overall_pass"] else "FAIL"
        print(f"[localization_adapter] Verification {status}. Fail reasons: {FAIL}")

    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(SUMMARY, f, indent=2)
        except Exception as exc:  # noqa
            print(f"Could not write JSON summary: {exc}", file=sys.stderr)

    sys.exit(0 if SUMMARY["overall_pass"] else 1)


if __name__ == "__main__":
    main()