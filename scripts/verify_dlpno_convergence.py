#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script for tangelo.dlpno.convergence module.

Checks:
  1. Import side-effect silence (stdout/stderr空).
  2. ConvergenceMonitor 基本動作:
       - 初期 is_converged False
       - energy / residual の逐次 update で収束成立
       - absolute と relative 双方の条件評価
  3. None / NaN / inf の扱い:
       - NaN / inf は無視（収束成立させない）想定（math.isfinite 利用前提）
  4. iteration 順序: 逆行 (大→小) を与えた場合の振る舞い（現仕様は許容 → 記録順だけ保持）
  5. 複数連続収束後 update の安定性（converged 状態維持）
  6. ConvergenceRecord 内容フィールド一貫性
  7. JSON サマリ + exit code (0 pass / 1 fail)

Usage:
    python scripts/verify_dlpno_convergence.py
    python scripts/verify_dlpno_convergence.py --verbose
    python scripts/verify_dlpno_convergence.py --json-out verify_convergence.json
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import math
import sys
from typing import Any, Dict, List

SUMMARY: Dict[str, Any] = {
    "module_import": False,
    "side_effect_stdout": "",
    "side_effect_stderr": "",
    "basic_flow": {},
    "abs_vs_rel": {},
    "nan_inf_handling": {},
    "iteration_order": {},
    "post_convergence_stability": {},
    "records_schema": {},
    "overall_pass": False,
    "fail_reasons": [],
}

def fail(reason: str):
    SUMMARY["fail_reasons"].append(reason)

def import_module():
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        try:
            structures = importlib.import_module("tangelo.dlpno.structures")
            convergence = importlib.import_module("tangelo.dlpno.convergence")
            SUMMARY["module_import"] = True
        except Exception as exc:  # noqa
            fail(f"Import failure: {exc}")
            return None, None
    SUMMARY["side_effect_stdout"] = buf_out.getvalue()
    SUMMARY["side_effect_stderr"] = buf_err.getvalue()
    if SUMMARY["side_effect_stdout"].strip():
        fail("Unexpected stdout on import.")
    if SUMMARY["side_effect_stderr"].strip():
        fail("Unexpected stderr on import.")
    return structures, convergence

def check_basic_flow(structures, convergence):
    ConvergenceCriteria = getattr(structures, "ConvergenceCriteria", None)
    ConvergenceRecord = getattr(structures, "ConvergenceRecord", None)
    ConvergenceMonitor = getattr(convergence, "ConvergenceMonitor", None)

    if not all([ConvergenceCriteria, ConvergenceRecord, ConvergenceMonitor]):
        fail("Required classes missing.")
        return

    criteria = ConvergenceCriteria(energy_abs_tol=1e-6, energy_rel_tol=5e-7, max_iterations=20)
    monitor = ConvergenceMonitor(criteria)

    if monitor.is_converged():
        fail("Monitor should not be converged initially.")

    # iteration 0: coarse
    r0 = monitor.update(iteration=0, energy=-75.0, residual_norm=1e-2)
    # iteration 1: improvement but not converged yet
    r1 = monitor.update(iteration=1, energy=-75.123456, residual_norm=2e-6)
    # iteration 2: refine (residual below threshold, energy change small)
    r2 = monitor.update(iteration=2, energy=-75.123457, residual_norm=5e-7)

    # Evaluate transitions
    basic_pass = (not r0.converged) and (not r1.converged) and r2.converged and monitor.is_converged()
    SUMMARY["basic_flow"] = {
        "r0": r0.__dict__,
        "r1": r1.__dict__,
        "r2": r2.__dict__,
        "final_is_converged": monitor.is_converged(),
        "pass": basic_pass
    }
    if not basic_pass:
        fail("Basic convergence flow did not behave as expected.")

def check_abs_vs_rel(structures, convergence):
    ConvergenceCriteria = structures.ConvergenceCriteria
    ConvergenceMonitor = convergence.ConvergenceMonitor

    # Construct a case where absolute diff passes but relative diff maybe not
    criteria = ConvergenceCriteria(energy_abs_tol=1e-6, energy_rel_tol=1e-9)
    monitor = ConvergenceMonitor(criteria)

    # Use moderately sized energy so relative condition is strict
    e_prev = -100.000000
    monitor.update(0, e_prev, 1e-3)
    e_next = e_prev + 5e-7  # abs diff 5e-7 < 1e-6 (abs ok), relative diff = 5e-7 / 100 ~ 5e-9 > 1e-9? actually 5e-9 > 1e-9 -> relative fails
    r1 = monitor.update(1, e_next, 5e-7)
    abs_only = r1.converged

    # Now second update with even smaller change to satisfy relative
    e_next2 = e_next + 5e-10  # relative diff ~ 5e-12 < 1e-9
    r2 = monitor.update(2, e_next2, 5e-8)
    rel_pass = r2.converged

    SUMMARY["abs_vs_rel"] = {
        "first_abs_only_converged": abs_only,
        "second_rel_converged": rel_pass,
    }
    # Expectation: first should NOT converge (strict: both criteria & residual) -> abs_only False
    # second should converge -> rel_pass True
    if abs_only:
        fail("Converged on absolute criteria alone (should require relative & residual).")
    if not rel_pass:
        fail("Failed to converge when both absolute & relative criteria should be satisfied.")

def check_nan_inf(structures, convergence):
    ConvergenceCriteria = structures.ConvergenceCriteria
    ConvergenceMonitor = convergence.ConvergenceMonitor
    criteria = ConvergenceCriteria(1e-6, 5e-7)
    monitor = ConvergenceMonitor(criteria)

    # Valid first update
    monitor.update(0, -1.0, 1e-3)
    # NaN energy
    r_nan = monitor.update(1, float("nan"), 1e-4)
    # inf residual
    r_inf = monitor.update(2, -1.000001, float("inf"))
    # Large but finite
    r_ok = monitor.update(3, -1.000002, 9e-7)

    # Expect that nan/inf cases do not prematurely converge
    premature = any(r.converged for r in [r_nan, r_inf])
    SUMMARY["nan_inf_handling"] = {
        "nan_record": r_nan.__dict__,
        "inf_record": r_inf.__dict__,
        "post_record": r_ok.__dict__,
        "premature_convergence": premature
    }
    if premature:
        fail("NaN/inf caused premature convergence.")

def check_iteration_order(structures, convergence):
    ConvergenceCriteria = structures.ConvergenceCriteria
    ConvergenceMonitor = convergence.ConvergenceMonitor
    criteria = ConvergenceCriteria(1e-6, 5e-7)
    monitor = ConvergenceMonitor(criteria)

    monitor.update(5, -10.0, 1e-2)
    monitor.update(3, -10.5, 1e-3)  # out-of-order iteration index
    order = [r.iteration for r in monitor.records]
    SUMMARY["iteration_order"] = {"stored_order": order}
    # Not failing: current spec does not forbid; but record for potential future validation.

def check_post_convergence(st, convergence):
    ConvergenceCriteria = st.ConvergenceCriteria
    ConvergenceMonitor = convergence.ConvergenceMonitor
    criteria = ConvergenceCriteria(1e-6, 5e-7, max_iterations=10)
    monitor = ConvergenceMonitor(criteria)
    monitor.update(0, -50.0, 1e-3)
    monitor.update(1, -50.000001, 8e-7)
    monitor.update(2, -50.000002, 4e-7)  # expect convergence here
    converged_iter = any(r.converged for r in monitor.records)
    # additional updates after convergence
    post = monitor.update(3, -50.0000025, 3e-7)
    SUMMARY["post_convergence_stability"] = {
        "converged_iter_found": converged_iter,
        "post_update_converged_flag": post.converged,
        "monitor_is_converged": monitor.is_converged()
    }
    if not converged_iter or not monitor.is_converged():
        fail("Monitor failed to remain converged after achieving convergence.")

def check_records_schema(convergence, structures):
    ConvergenceMonitor = convergence.ConvergenceMonitor
    ConvergenceCriteria = structures.ConvergenceCriteria
    monitor = ConvergenceMonitor(ConvergenceCriteria(1e-6, 5e-7))
    monitor.update(0, -1.0, 1e-2)
    monitor.update(1, -1.1, 9e-7)
    schema_ok = True
    fields = {"iteration", "energy", "residual_norm", "converged"}
    for rec in monitor.records:
        missing = fields - set(rec.__dict__.keys())
        if missing:
            schema_ok = False
            fail(f"ConvergenceRecord missing fields: {missing}")
        if not isinstance(rec.iteration, int):
            schema_ok = False
            fail("iteration not int.")
    SUMMARY["records_schema"] = {"schema_ok": schema_ok, "count": len(monitor.records)}

def main():
    parser = argparse.ArgumentParser(description="Verify DLPNO convergence monitor.")
    parser.add_argument("--json-out", type=str, default=None, help="Write JSON summary.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    args = parser.parse_args()

    structures, convergence = import_module()
    if structures and convergence:
        check_basic_flow(structures, convergence)
        check_abs_vs_rel(structures, convergence)
        check_nan_inf(structures, convergence)
        check_iteration_order(structures, convergence)
        check_post_convergence(structures, convergence)
        check_records_schema(convergence, structures)

    SUMMARY["overall_pass"] = len(SUMMARY["fail_reasons"]) == 0

    if args.verbose:
        print("=== DLPNO CONVERGENCE VERIFICATION REPORT ===")
        for k, v in SUMMARY.items():
            if k in {"side_effect_stdout", "side_effect_stderr"} and not v:
                continue
            print(f"{k}: {v}")
        print("=============================================")
    else:
        status = "PASS" if SUMMARY["overall_pass"] else "FAIL"
        print(f"[convergence] Verification {status}. Fail reasons: {SUMMARY['fail_reasons']}")

    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(SUMMARY, f, indent=2)
        except Exception as exc:  # noqa
            print(f"Could not write JSON summary: {exc}", file=sys.stderr)

    sys.exit(0 if SUMMARY["overall_pass"] else 1)

if __name__ == "__main__":
    main()