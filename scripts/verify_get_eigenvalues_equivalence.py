#!/usr/bin/env python3
"""
verify_get_eigenvalues_equivalence.py

検証目的:
  np.product -> np.prod 置換により get_eigenvalues の数値結果が変化していないことを確認する。

検証方法:
  1. 代表的な複数ケースで get_eigenvalues を実行
  2. (-2 * each_qubit + 1) の行ごとの手動積(逐次乗算) で再計算
  3. 両者が全て一致するか (絶対差 0) を確認

成功条件:
  全テストケースで "OK" 表示、終了コード 0

失敗条件:
  差分が検出されたケースを列挙し終了コード 1
"""

from __future__ import annotations
import sys
import numpy as np

# Tangelo のパスを明示的に追加したい場合は環境によっては以下を使う
# import pathlib, os
# sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tangelo.toolboxes.operators.z2_tapering import get_eigenvalues  # 現行実装 (np.prod 利用)

def manual_product(each_qubit_row: np.ndarray) -> int:
    # (-2 * each_qubit + 1) を要素毎に掛け合わせる “旧挙動” 再現
    # each_qubit_row は bool (True/False) なので -2*bool + 1 => {True:-1, False:1}
    factors = (-2 * each_qubit_row.astype(int) + 1).astype(int)
    acc = 1
    for f in factors:
        acc *= f
    return acc

def recompute_reference(symmetries, n_qubits, n_electrons, spin, mapping, up_then_down):
    """
    get_eigenvalues 内部計算を再現して “np.prod” を使わないルートでの期待値を得る。
    """
    # get_eigenvalues 内部と同じベクトル構築
    from tangelo.toolboxes.qubit_mappings.statevector_mapping import get_vector
    psi_init = get_vector(n_qubits, n_electrons, mapping, up_then_down, spin)

    if len(symmetries.shape) == 1:
        sym = np.reshape(symmetries, (-1, len(symmetries)))
    else:
        sym = symmetries

    each_qubit = np.einsum("ij,j->ij", sym[:, n_qubits:].astype(bool), psi_init)

    # 行ごとに手動積
    manual = np.array([manual_product(row) for row in each_qubit])
    return manual

def run_case(case_id, symmetries, n_qubits, n_electrons, spin, mapping, up_then_down):
    try:
        eig_prod = get_eigenvalues(symmetries, n_qubits, n_electrons, spin, mapping, up_then_down)
        eig_manual = recompute_reference(symmetries, n_qubits, n_electrons, spin, mapping, up_then_down)
    except Exception as e:
        print(f"[CASE {case_id}] ERROR: Exception during evaluation: {e}")
        return False

    if eig_prod.shape != eig_manual.shape:
        print(f"[CASE {case_id}] FAIL: Shape mismatch prod={eig_prod.shape} manual={eig_manual.shape}")
        return False

    if not np.array_equal(eig_prod, eig_manual):
        diff_idx = np.where(eig_prod != eig_manual)[0]
        print(f"[CASE {case_id}] FAIL: Value mismatch at indices {diff_idx}, prod={eig_prod[diff_idx]}, manual={eig_manual[diff_idx]}")
        return False

    print(f"[CASE {case_id}] OK")
    return True

def main():
    # テストケース設計:
    # - 小さい系 (4 qubits)
    # - ランダム対称性行列複数
    # - 単一行パターン
    rng = np.random.default_rng(42)

    cases = []

    # Case 1: 単一対称性 (1 行)
    sym1 = np.zeros(8, dtype=bool)  # 2N = 8 for N=4
    sym1[4] = True  # Zパートの1ビットだけ True
    cases.append(("SingleSym", sym1, 4, 2, 0, "jw", True))

    # Case 2: 3 行ランダム (N=4)
    sym2 = rng.integers(0, 2, size=(3, 8), dtype=np.int8).astype(bool)
    cases.append(("Random3", sym2, 4, 2, 0, "jw", True))

    # Case 3: N=6, 2 行ランダム
    sym3 = rng.integers(0, 2, size=(2, 12), dtype=np.int8).astype(bool)
    cases.append(("N6Random2", sym3, 6, 4, 0, "jw", False))

    # Case 4: 既知パターン (全 False と全 True 混合)
    sym4 = np.vstack([
        np.zeros(8, dtype=bool),
        np.ones(8, dtype=bool)
    ])
    cases.append(("AllFalseAllTrue", sym4, 4, 2, 0, "jw", True))

    # Case 5: スピン指定変更 (spin=1)
    sym5 = rng.integers(0, 2, size=(2, 8), dtype=np.int8).astype(bool)
    cases.append(("Spin1", sym5, 4, 2, 1, "jw", True))

    all_ok = True
    for cid, sym, nq, ne, spin, mapping, utd in cases:
        ok = run_case(cid, sym, nq, ne, spin, mapping, utd)
        all_ok = all_ok and ok

    if not all_ok:
        print("FAIL: At least one case diverged.")
        return 1

    print("SUCCESS: All cases match (np.prod replacement is behaviorally identical).")
    return 0

if __name__ == "__main__":
    sys.exit(main())