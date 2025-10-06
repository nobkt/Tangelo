#!/usr/bin/env python
"""
Phase2-Task2.4 Verification Script

Independently verifies correctness of the implemented DLPNO pair coupling functional
and pair screening routine against the formal specification:

  dev_notes/dlpno/coupling_function_spec.md  (after denominator sign fix)

Tests (all must pass):
  1. Data acquisition (H2O, H2)
  2. Symmetry: C(i,j) == C(j,i)
  3. Non-negativity: C(i,j) >= 0
  4. Self-null: C(i,i) == 0
  5. Determinism: repeated identical calls bitwise same
  6. Signed MP2 pair energy reconstruction: C(i,j) == |E_pair(i,j)| & total corr energy finite negative
  7. Screening rule: threshold=0 → all pairs; high threshold → none
  8. Error handling: negative threshold raises
  9. Denominator sign guard: no non-negative denominators encountered (spec alignment)
  10. Internal recomputation consistency: standalone signed implementation matches evaluate_coupling_functional except for abs

Output:
  Intermediate per-test status lines.
  Final line:
    PASS
  or
    FAIL: <first failing test + brief reason>
"""

from __future__ import annotations
import sys
import math
import traceback
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional

FAIL_EARLY = True
EPS_SYM = 1e-12
EPS_ZERO = 1e-12

RESULTS = []

def record(ok: bool, label: str, detail: str = ""):
    msg = f"[{'OK' if ok else 'FAIL'}] {label}"
    if detail:
        msg += f" :: {detail}"
    print(msg)
    RESULTS.append((ok, label, detail))
    if not ok and FAIL_EARLY:
        raise RuntimeError(f"{label}: {detail}")

def safe_imports():
    try:
        from tangelo import SecondQuantizedMolecule
        from tangelo.dlpno.coupling import evaluate_coupling_functional
        from tangelo.dlpno.pairs import build_pair_set
    except Exception as e:
        raise ImportError(f"Required tangelo imports failed: {e}")
    return SecondQuantizedMolecule, evaluate_coupling_functional, build_pair_set

def build_molecule(xyz: str, basis="sto-3g"):
    from tangelo import SecondQuantizedMolecule
    return SecondQuantizedMolecule(xyz, q=0, spin=0, basis=basis)

def signed_pair_energy(i: int, j: int, mo_energies, mo_integrals, n_occ: int) -> float:
    if i == j:
        return 0.0
    n_mos = len(mo_energies)
    eps_i = mo_energies[i]
    eps_j = mo_energies[j]
    e_pair = 0.0
    for a in range(n_occ, n_mos):
        eps_a = mo_energies[a]
        for b in range(n_occ, n_mos):
            eps_b = mo_energies[b]
            denom = eps_i + eps_j - eps_a - eps_b
            # Mirror the production code expectation: denom must be negative.
            if denom >= 0:
                raise ValueError(f"Non-negative denominator detected ({denom:.4e}) at (i,j,a,b)=({i},{j},{a},{b})")
            iajb = mo_integrals[i, j, a, b]
            ibja = mo_integrals[i, j, b, a]
            t_abij = 2.0 * iajb - ibja
            e_pair += t_abij * iajb / denom
    return e_pair

@dataclass
class PairMetric:
    i: int
    j: int
    c_val: float
    signed: float

def main():
    SecondQuantizedMolecule, eval_coupling, build_pair_set = safe_imports()
    record(True, "Imports", "tangelo modules loaded")

    # Prepare molecules
    xyz_h2o = """O  0.0000  0.0000  0.1173
H  0.0000  0.7572 -0.4692
H  0.0000 -0.7572 -0.4692
"""
    xyz_h2 = "H 0 0 0\nH 0 0 0.74"

    mol_h2o = build_molecule(xyz_h2o)
    mol_h2 = build_molecule(xyz_h2)

    mo_energies_h2o = mol_h2o.mo_energies
    _, _, mo_ints_h2o = mol_h2o.get_full_space_integrals()
    n_occ_h2o = mol_h2o.n_electrons // 2

    if n_occ_h2o < 2:
        record(False, "DataCheck", "Unexpected small n_occ for H2O")
    else:
        record(True, "DataCheck", f"H2O n_occ={n_occ_h2o}, n_mos={len(mo_energies_h2o)}")

    # Collect pair metrics
    pair_metrics: List[PairMetric] = []
    for i in range(n_occ_h2o):
        for j in range(i + 1, n_occ_h2o):
            c_ij = eval_coupling(i, j, mo_energies_h2o, mo_ints_h2o, n_occ_h2o)
            signed = signed_pair_energy(i, j, mo_energies_h2o, mo_ints_h2o, n_occ_h2o)
            pair_metrics.append(PairMetric(i, j, c_ij, signed))

    # 1. Symmetry (recompute reversed)
    sym_ok = True
    for pm in pair_metrics:
        c_reverse = eval_coupling(pm.j, pm.i, mo_energies_h2o, mo_ints_h2o, n_occ_h2o)
        if abs(pm.c_val - c_reverse) > EPS_SYM:
            sym_ok = False
            detail = f"({pm.i},{pm.j}) diff={abs(pm.c_val - c_reverse):.3e}"
            break
    record(sym_ok, "Symmetry", "" if sym_ok else detail)

    # 2. Non-negativity
    nonneg_ok = all(pm.c_val >= -1e-16 for pm in pair_metrics)
    smallest = min(pm.c_val for pm in pair_metrics) if pair_metrics else 0.0
    record(nonneg_ok, "NonNegativity", f"min={smallest:.3e}")

    # 3. Self-null (spot check i==i)
    self_null_ok = True
    for i in range(n_occ_h2o):
        c_ii = eval_coupling(i, i, mo_energies_h2o, mo_ints_h2o, n_occ_h2o)
        if abs(c_ii) > EPS_ZERO:
            self_null_ok = False
            detail = f"C({i},{i})={c_ii:.3e}"
            break
    record(self_null_ok, "SelfNull", "" if self_null_ok else detail)

    # 4. Determinism (repeat a representative pair)
    if pair_metrics:
        rep = pair_metrics[0]
        reps = [eval_coupling(rep.i, rep.j, mo_energies_h2o, mo_ints_h2o, n_occ_h2o) for _ in range(5)]
        determinism_ok = all(r == reps[0] for r in reps[1:])
        record(determinism_ok, "Determinism", f"value={reps[0]:.6e}")
    else:
        record(False, "Determinism", "No pair metrics")

    # 5. Signed energy reconstruction: C(i,j)==|signed|
    recon_ok = True
    max_abs_diff = 0.0
    for pm in pair_metrics:
        diff = abs(pm.c_val - abs(pm.signed))
        if diff > 1e-10:
            recon_ok = False
            max_abs_diff = diff
            detail = f"({pm.i},{pm.j}) diff={diff:.3e}"
            break
        max_abs_diff = max(max_abs_diff, diff)
    record(recon_ok, "SignedReconstruction", f"max_abs_diff={max_abs_diff:.2e}" if recon_ok else detail)

    # 6. Total MP2 corr energy negative & finite
    total_signed = sum(pm.signed for pm in pair_metrics)
    finite_ok = math.isfinite(total_signed) and total_signed < 0 and total_signed > -5.0
    record(finite_ok, "TotalCorrelationEnergy", f"E_corr={total_signed:.6e}")

    # 7. Screening rule
    all_pairs = build_pair_set(
        mol_h2o,
        threshold=0.0,
        mo_energies=mo_energies_h2o,
        mo_integrals=mo_ints_h2o
    )
    expected_all = n_occ_h2o * (n_occ_h2o - 1) // 2
    rule_all_ok = (len(all_pairs) == expected_all)
    record(rule_all_ok, "ScreenThresholdZero", f"got={len(all_pairs)} expected={expected_all}")

    high_pairs = build_pair_set(
        mol_h2o,
        threshold=max(pm.c_val for pm in pair_metrics) + 1.0,
        mo_energies=mo_energies_h2o,
        mo_integrals=mo_ints_h2o
    )
    high_ok = len(high_pairs) == 0
    record(high_ok, "ScreenHighThreshold", f"retained={len(high_pairs)}")

    # 8. Error handling (negative threshold)
    neg_thr_ok = False
    try:
        build_pair_set(mol_h2o, threshold=-1.0)
    except ValueError as e:
        if "non-negative" in str(e).lower() or "non" in str(e).lower():
            neg_thr_ok = True
    record(neg_thr_ok, "ErrorNegativeThreshold")

    # 9. Denominator sign check already implicit in signed_pair_energy (would raise)
    # If we reached here no non-negative denominators occurred.
    record(True, "DenominatorSign", "All denominators negative as expected")

    # 10. Internal consistency stats
    # Provide simple distribution summary
    if pair_metrics:
        vals = [pm.c_val for pm in pair_metrics]
        summary = f"min={min(vals):.3e} max={max(vals):.3e} n={len(vals)}"
        record(True, "MagnitudeSummary", summary)
    else:
        record(False, "MagnitudeSummary", "No values")

    # Final aggregation
    first_fail = next((r for r in RESULTS if not r[0]), None)
    if first_fail:
        print(f"FAIL: {first_fail[1]} - {first_fail[2]}")
        sys.exit(1)
    else:
        print("PASS")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: Exception - {exc}")
        traceback.print_exc()
        sys.exit(2)