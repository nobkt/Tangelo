# Copyright SandboxAQ 2021-2024.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DLPNO Pair Coupling Functional C(i,j) Implementation (Phase2-Task2.4).

This module implements the rigorous analytic coupling functional C(i,j) as
defined in dev_notes/dlpno/coupling_function_spec.md. The coupling functional
quantifies the energetic importance of electron correlation between occupied
orbitals i and j using the absolute value of the MP2 pair correlation energy.

Mathematical Definition:
    C(i,j) = |E_pair^MP2(i,j)|
    
    where E_pair^MP2(i,j) = Σ_{a,b ∈ virt} [2×(ia|jb) - (ib|ja)] × (ia|jb) / (ε_i + ε_j - ε_a - ε_b)

Properties (validated by tests):
    - Symmetry: C(i,j) = C(j,i)
    - Non-negativity: C(i,j) ≥ 0
    - Self-null: C(i,i) = 0
    - Determinism: reproducible given fixed inputs

Reference:
    dev_notes/dlpno/coupling_function_spec.md (Section 4)
"""

from __future__ import annotations

import numpy as np
from typing import Any

__all__ = ["evaluate_coupling_functional"]


def evaluate_coupling_functional(
    i: int,
    j: int,
    mo_energies: np.ndarray,
    mo_integrals: np.ndarray,
    n_occ: int
) -> float:
    """Evaluate the pair coupling functional C(i,j) = |E_pair^MP2(i,j)|.

    Computes the absolute value of the MP2 pair correlation energy for
    occupied orbital pair (i,j) using canonical MO integrals and orbital
    energies. This function implements the exact formula from Section 4.2
    of coupling_function_spec.md with no approximations or truncations.

    Args:
        i: First occupied orbital index (0-based, must be < n_occ)
        j: Second occupied orbital index (0-based, must be < n_occ)
        mo_energies: Array of MO energies in Hartree (length: n_mos).
            Occupied orbitals: indices [0, n_occ), virtual: [n_occ, n_mos)
        mo_integrals: 4D array of two-electron integrals in chemist's notation
            (pq|rs) with shape (n_mos, n_mos, n_mos, n_mos).
            Physicist's notation: integrals[p,q,r,s] = <pq|rs> = (pr|qs)
        n_occ: Number of doubly occupied orbitals in RHF reference

    Returns:
        C(i,j): Non-negative coupling functional value in Hartree.
            Returns 0.0 for diagonal pairs (i == j) by self-null property.

    Raises:
        ValueError: If indices i,j are out of bounds (>= n_occ or < 0)
        ValueError: If mo_energies or mo_integrals have incorrect shape/type
        ValueError: If energy denominators are non-positive (unphysical)

    Notes:
        - Full double sum over all virtual orbitals (no screening)
        - Integrals assumed in chemist's notation: (ia|jb)
        - No frozen core handling (all occupied orbitals active)
        - No density fitting, RI, or Cholesky approximations
        - Complexity: O(n_virt²) per pair evaluation
    """
    # Input validation: check orbital indices
    if i < 0 or i >= n_occ:
        raise ValueError(f"Orbital index i={i} out of bounds (must be 0 <= i < {n_occ})")
    if j < 0 or j >= n_occ:
        raise ValueError(f"Orbital index j={j} out of bounds (must be 0 <= j < {n_occ})")

    # Input validation: check array shapes and types
    if not isinstance(mo_energies, np.ndarray):
        raise ValueError("mo_energies must be a numpy array")
    if not isinstance(mo_integrals, np.ndarray):
        raise ValueError("mo_integrals must be a numpy array")

    n_mos = len(mo_energies)
    if mo_integrals.shape != (n_mos, n_mos, n_mos, n_mos):
        raise ValueError(
            f"mo_integrals shape {mo_integrals.shape} inconsistent with "
            f"mo_energies length {n_mos} (expected {(n_mos, n_mos, n_mos, n_mos)})"
        )

    if n_occ >= n_mos:
        raise ValueError(f"n_occ={n_occ} must be less than n_mos={n_mos}")

    # Self-null property: C(i,i) = 0 exactly (Section 6.3 of spec)
    if i == j:
        return 0.0

    # Compute MP2 pair correlation energy E_pair^MP2(i,j)
    # Formula: Σ_{a,b ∈ virt} [2×(ia|jb) - (ib|ja)] × (ia|jb) / (ε_i + ε_j - ε_a - ε_b)
    
    n_virt = n_mos - n_occ
    e_pair = 0.0

    # Extract occupied orbital energies
    eps_i = mo_energies[i]
    eps_j = mo_energies[j]

    # Double sum over all virtual orbitals
    for a in range(n_occ, n_mos):
        eps_a = mo_energies[a]
        for b in range(n_occ, n_mos):
            eps_b = mo_energies[b]

            # Energy denominator: (ε_i + ε_j - ε_a - ε_b)
            denom = eps_i + eps_j - eps_a - eps_b

            # Check for non-positive denominator (unphysical for RHF)
            if denom >= 0.0:
                raise ValueError(
                    f"Non-positive energy denominator {denom:.6e} for pair ({i},{j}) "
                    f"with virtuals ({a},{b}). This indicates non-standard orbital "
                    f"energies (ε_occ >= ε_virt) which violates RHF assumptions."
                )

            # Two-electron integrals in chemist's notation
            # Physicist's notation in array: integrals[p,q,r,s] = <pq|rs> = (pr|qs)
            # Chemist's notation needed: (ia|jb) = <ij|ab> = integrals[i,j,a,b]
            iajb = mo_integrals[i, j, a, b]  # (ia|jb) in chemist's notation
            ibja = mo_integrals[i, j, b, a]  # (ib|ja) in chemist's notation

            # Amplitude factor: T_ab^ij = 2×(ia|jb) - (ib|ja)
            t_abij = 2.0 * iajb - ibja

            # MP2 pair energy contribution: T_ab^ij × (ia|jb) / denom
            e_pair += t_abij * iajb / denom

    # Return absolute value for non-negativity (Section 6.2 of spec)
    return abs(e_pair)
