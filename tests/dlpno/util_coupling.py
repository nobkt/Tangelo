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

"""Shared utilities for DLPNO coupling functional tests (Phase2-Task2.5).

This module provides common helper functions used across multiple test files:
- compute_c_matrix: Compute full upper-triangular C(i,j) matrix
- compute_signed_pair_energy: Compute signed MP2 pair energy (before abs)
- load_reference_dataset: Load regression reference data from JSON file
"""

import json
import hashlib
import numpy as np
from pathlib import Path
from tangelo.dlpno.coupling import evaluate_coupling_functional


def compute_c_matrix(mo_energies, mo_integrals, n_occ):
    """Compute full upper-triangular C(i,j) matrix for a molecule.
    
    Args:
        mo_energies: Array of MO energies in Hartree
        mo_integrals: 4D array of two-electron integrals
        n_occ: Number of doubly occupied orbitals
        
    Returns:
        List of dicts with keys 'i', 'j', 'value' for all pairs with i < j
    """
    c_values = []
    for i in range(n_occ):
        for j in range(i + 1, n_occ):
            c_ij = evaluate_coupling_functional(i, j, mo_energies, mo_integrals, n_occ)
            c_values.append({"i": int(i), "j": int(j), "value": float(c_ij)})
    return c_values


def compute_signed_pair_energy(i, j, mo_energies, mo_integrals, n_occ):
    """Compute signed MP2 pair energy (before absolute value).
    
    This duplicates the logic in evaluate_coupling_functional but returns
    the signed value for validation purposes.
    
    Args:
        i: First occupied orbital index
        j: Second occupied orbital index
        mo_energies: Array of MO energies in Hartree
        mo_integrals: 4D array of two-electron integrals
        n_occ: Number of doubly occupied orbitals
        
    Returns:
        Signed MP2 pair correlation energy in Hartree
    """
    if i == j:
        return 0.0
    
    n_mos = len(mo_energies)
    e_pair = 0.0
    
    eps_i = mo_energies[i]
    eps_j = mo_energies[j]
    
    for a in range(n_occ, n_mos):
        eps_a = mo_energies[a]
        for b in range(n_occ, n_mos):
            eps_b = mo_energies[b]
            denom = eps_i + eps_j - eps_a - eps_b
            
            iajb = mo_integrals[i, j, a, b]
            ibja = mo_integrals[i, j, b, a]
            t_abij = 2.0 * iajb - ibja
            e_pair += t_abij * iajb / denom
    
    return e_pair


def compute_regression_hash(c_values):
    """Compute SHA256 hash of concatenated C(i,j) values in lexicographic order.
    
    Args:
        c_values: List of dicts with keys 'i', 'j', 'value'
        
    Returns:
        SHA256 hash as hexadecimal string
    """
    # Sort by (i,j) to ensure deterministic ordering
    sorted_values = sorted(c_values, key=lambda x: (x['i'], x['j']))
    
    # Concatenate as double-precision bytes
    byte_data = b''
    for entry in sorted_values:
        byte_data += np.float64(entry['value']).tobytes()
    
    # Compute SHA256 hash
    return hashlib.sha256(byte_data).hexdigest()


def load_reference_dataset():
    """Load the reference regression dataset from JSON file.
    
    Returns:
        Dictionary containing the reference dataset with molecule data
        
    Raises:
        FileNotFoundError: If reference dataset file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    # Find the reference dataset file
    dataset_path = Path(__file__).parent.parent / 'data' / 'dlpno_coupling_reference.json'
    
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Reference dataset not found at {dataset_path}. "
            "Run the reference data generation script first."
        )
    
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    return dataset
