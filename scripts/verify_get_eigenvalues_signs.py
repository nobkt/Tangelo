#!/usr/bin/env python3
"""
verify_get_eigenvalues_signs.py

検証目的:
  tangelo.toolboxes.operators.z2_tapering.get_eigenvalues が返す配列が
  常に {+1, -1} のみで構成されることをランダムケースで確認する。

背景:
  np.product -> np.prod 置換後も理論的制約 (Z2 tapering の各対称性固有値は ±1) が
  維持されているかを確認するため。

成功条件:
  すべてのランダムケースで戻り値要素が ±1 のみ。
失敗条件:
  ±1 以外の値が検出 / 例外発生。

使用方法:
  PYTHONPATH=. python scripts/verify_get_eigenvalues_signs.py
"""

from __future__ import annotations
import sys
import numpy as np

from tangelo.toolboxes.operators.z2_tapering import get_eigenvalues
from tangelo.toolboxes.qubit_mappings.statevector_mapping import get_vector

RNG = np.random.default_rng(12345)

def run_single_case(case_id: int,
                    n_qubits: int,
                    n_electrons: int,
                    spin: int,
                    mapping: str,
                    up_then_down: bool,
                    n_sym_rows: int):
    # 対称性行列をランダム生成: shape=(n_sym_rows, 2*n_qubits)
    symmetries = RNG.integers(0, 2, size=(n_sym_rows, 2 * n_qubits), dtype=np.int8).astype(bool)

    try:
        eig = get_eigenvalues(symmetries,
                              n_qubits=n_qubits,
                              n_electrons=n_electrons,
                              spin=spin,
                              mapping=mapping,
                              up_then_down=up_then_down)
    except Exception as e:
        return False, f"[CASE {case_id}] EXCEPTION: {e}"

    if eig.size != n_sym_rows:
        return False, f"[CASE {case_id}] SIZE MISMATCH expected={n_sym_rows} got={eig.size}"

    unique_vals = np.unique(eig)
    # 許容集合
    allowed = {-1, 1}
    if not set(unique_vals.tolist()).issubset(allowed):
        return False, f"[CASE {case_id}] INVALID VALUES: unique={unique_vals}"

    return True, f"[CASE {case_id}] OK (unique={unique_vals})"


def main():
    cases = []
    # (n_qubits, electron_fraction, spin_candidates)
    config = [
        (4, 0.5, [0, 1]),
        (6, 0.5, [0]),
        (6, 0.33, [0]),
        (8, 0.25, [0, 2]),
    ]

    case_id = 0
    for (nq, frac, spins) in config:
        max_elec = nq  # （化学的制約より多いのは無意味だが簡易化）
        ne_guess = max(1, int(round(max_elec * frac)))
        # 電子数は偶数でスピン (Sz) に整合するように多少調整（過度な厳密性は不要）
        if ne_guess % 2 == 1:
            ne_guess = min(max_elec, ne_guess + 1)

        for spin in spins:
            for n_sym in [1, 2, 3, 5]:
                for utd in [True, False]:
                    case_id += 1
                    cases.append((case_id, nq, ne_guess, spin, "jw", utd, n_sym))

    all_ok = True
    messages = []
    for cid, nq, ne, spin, mapping, utd, n_sym in cases:
        ok, msg = run_single_case(cid, nq, ne, spin, mapping, utd, n_sym)
        messages.append(msg)
        if not ok:
            all_ok = False

    for m in messages:
        print(m)

    if all_ok:
        print("SUCCESS: All eigenvalue sets confined to {+1, -1}.")
        return 0
    else:
        print("FAIL: One or more cases produced invalid eigenvalues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())