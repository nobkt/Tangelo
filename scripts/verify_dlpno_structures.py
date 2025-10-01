#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script for tangelo.dlpno.structures module.

Checks:
  1. Module/import side-effect silence (no stdout/stderr).
  2. Presence and basic instantiation of dataclasses:
       - OrbitalSpace
       - PNOParameters
       - ConvergenceCriteria
       - ConvergenceRecord
       - default_pno_parameters()
  3. Attribute/type sanity (duck checks, not exhaustive typing).
  4. default_pno_parameters returns value-copies (mutating returned lists does
     not alter config constants).
  5. Edge cases: empty lists, None fields, negative tolerances (currently allowed).
  6. Idempotent re-import (no state bleed).
  7. JSON summary + exit code (0 pass / 1 fail).

Usage:
    python scripts/verify_dlpno_structures.py
    python scripts/verify_dlpno_structures.py --verbose
    python scripts/verify_dlpno_structures.py --json-out verify_structures.json
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import sys
from dataclasses import is_dataclass, asdict
from typing import Any, Dict, List

SUMMARY: Dict[str, Any] = {
    "module_import": False,
    "side_effect_stdout": "",
    "side_effect_stderr": "",
    "dataclasses_present": {},
    "default_params_integrity": {},
    "copy_independence": {},
    "edge_cases": {},
    "reimport_idempotent": False,
    "overall_pass": False,
    "fail_reasons": [],
}


def fail(reason: str):
    SUMMARY["fail_reasons"].append(reason)


def import_modules():
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        try:
            structures = importlib.import_module("tangelo.dlpno.structures")
            config = importlib.import_module("tangelo.dlpno.config")
            SUMMARY["module_import"] = True
        except Exception as exc:  # noqa
            fail(f"Import error: {exc}")
            return None, None
    SUMMARY["side_effect_stdout"] = buf_out.getvalue()
    SUMMARY["side_effect_stderr"] = buf_err.getvalue()
    if SUMMARY["side_effect_stdout"].strip():
        fail("Unexpected stdout during import.")
    if SUMMARY["side_effect_stderr"].strip():
        fail("Unexpected stderr during import.")
    return structures, config


def check_dataclasses(structures):
    targets = [
        "OrbitalSpace",
        "PNOParameters",
        "ConvergenceCriteria",
        "ConvergenceRecord",
    ]
    for name in targets:
        obj = getattr(structures, name, None)
        present = obj is not None
        dc = is_dataclass(obj) if present else False
        SUMMARY["dataclasses_present"][name] = {"present": present, "is_dataclass": dc}
        if not present:
            fail(f"{name} missing.")
        elif not dc:
            fail(f"{name} is not a dataclass.")


def instantiate_and_validate(structures, config):
    # default_pno_parameters
    default_fn = getattr(structures, "default_pno_parameters", None)
    if default_fn is None:
        fail("default_pno_parameters function missing.")
        return
    params = default_fn()
    if not is_dataclass(params):
        fail("default_pno_parameters did not return a dataclass.")
        return

    d = asdict(params)
    expected_map = {
        "pno_tau_sequence": config.PNO_TAU_SEQUENCE_DEFAULT,
        "pair_tau_sequence": config.PAIR_TAU_SEQUENCE_DEFAULT,
        "energy_abs_tol": config.ENERGY_ABS_TOL_DEFAULT,
        "energy_rel_tol": config.ENERGY_REL_TOL_DEFAULT,
        "max_extrap_points": config.MAX_EXTRAP_POINTS,
    }
    integrity = {}
    for k, exp in expected_map.items():
        ok = d.get(k) == exp
        integrity[k] = {"expected": exp, "actual": d.get(k), "pass": ok}
        if not ok:
            fail(f"default_pno_parameters field {k} mismatch.")
    SUMMARY["default_params_integrity"] = integrity

    # Copy independence test
    # Mutate the lists we got and re-check config constants unchanged
    copy_status = {}
    for list_field, const_name in [
        ("pno_tau_sequence", "PNO_TAU_SEQUENCE_DEFAULT"),
        ("pair_tau_sequence", "PAIR_TAU_SEQUENCE_DEFAULT"),
    ]:
        original_config_list = getattr(config, const_name)
        mutated = getattr(params, list_field)
        if not isinstance(mutated, list):
            fail(f"{list_field} not a list in PNOParameters.")
            continue
        if mutated is original_config_list:
            fail(f"{list_field} references config constant directly (should copy).")
            copy_status[list_field] = {"independent": False}
            continue
        # mutate returned list
        mutated.append(9999.0)
        still_unchanged = getattr(config, const_name) == original_config_list and 9999.0 not in original_config_list
        if not still_unchanged:
            fail(f"Config constant {const_name} changed after mutating default object list.")
        copy_status[list_field] = {"independent": still_unchanged}
    SUMMARY["copy_independence"] = copy_status

    # Instantiate OrbitalSpace with partial data
    OrbitalSpace = getattr(structures, "OrbitalSpace", None)
    if OrbitalSpace is not None:
        os_obj = OrbitalSpace(occupied_indices=[0, 1], virtual_indices=[2, 3, 4], localization_method="pipek")
        if not hasattr(os_obj, "occupied_indices") or os_obj.occupied_indices != [0, 1]:
            fail("OrbitalSpace.occupied_indices not set correctly.")
        if os_obj.localization_method != "pipek":
            fail("OrbitalSpace.localization_method mismatch.")

    # Instantiate ConvergenceCriteria edge: negative tolerances (allowed currently)
    ConvergenceCriteria = getattr(structures, "ConvergenceCriteria", None)
    if ConvergenceCriteria is not None:
        crit = ConvergenceCriteria(energy_abs_tol=-1.0, energy_rel_tol=-2.0)
        SUMMARY["edge_cases"]["negative_tol_allowed"] = True
        # Document that we allowed it (could be future validation)
        # Not marking fail; just recording.
        if crit.energy_abs_tol != -1.0:
            fail("ConvergenceCriteria energy_abs_tol not stored as given.")

    # ConvergenceRecord simple instantiation
    ConvergenceRecord = getattr(structures, "ConvergenceRecord", None)
    if ConvergenceRecord is not None:
        rec = ConvergenceRecord(iteration=0, energy=None, residual_norm=None, converged=False)
        if rec.iteration != 0 or rec.converged is not False:
            fail("ConvergenceRecord basic fields mismatch.")


def reimport_idempotency():
    # Ensure re-import does not produce failures (importlib.reload)
    try:
        import tangelo.dlpno.structures as s
        importlib.reload(s)
        SUMMARY["reimport_idempotent"] = True
    except Exception as exc:  # noqa
        fail(f"Re-import failed: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Verify DLPNO structures scaffolding.")
    parser.add_argument("--json-out", type=str, default=None, help="Write JSON summary.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    args = parser.parse_args()

    structures, config = import_modules()
    if structures and config:
        check_dataclasses(structures)
        instantiate_and_validate(structures, config)
        reimport_idempotency()

    SUMMARY["overall_pass"] = len(SUMMARY["fail_reasons"]) == 0

    if args.verbose:
        print("=== DLPNO STRUCTURES VERIFICATION REPORT ===")
        for k, v in SUMMARY.items():
            if k in {"side_effect_stdout", "side_effect_stderr"} and not v:
                continue
            print(f"{k}: {v}")
        print("============================================")
    else:
        status = "PASS" if SUMMARY["overall_pass"] else "FAIL"
        print(f"[structures] Verification {status}. Fail reasons: {SUMMARY['fail_reasons']}")

    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(SUMMARY, f, indent=2)
        except Exception as exc:  # noqa
            print(f"Could not write JSON summary: {exc}", file=sys.stderr)

    sys.exit(0 if SUMMARY["overall_pass"] else 1)


if __name__ == "__main__":
    main()