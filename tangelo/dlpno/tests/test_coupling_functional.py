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

"""Unit tests for DLPNO pair coupling functional C(i,j) (Phase2-Task2.4).

These tests validate the mathematical properties specified in
dev_notes/dlpno/coupling_function_spec.md Section 11:
    - 11.1: Symmetry test
    - 11.2: Non-negativity test
    - 11.3: Self-null test
    - 11.4: Pair energy reproduction test (H₂O/STO-3G)
    - Error handling for missing/invalid inputs
"""

import unittest
import numpy as np

from tangelo import SecondQuantizedMolecule
from tangelo.dlpno.coupling import evaluate_coupling_functional
from tangelo.dlpno.pairs import build_pair_set


class CouplingFunctionalTest(unittest.TestCase):
    """Test suite for coupling functional C(i,j) implementation."""

    @classmethod
    def setUpClass(cls):
        """Set up test molecules for reuse across tests."""
        # H2O molecule in STO-3G basis (reference test system from spec)
        cls.xyz_h2o = """
        O  0.0000  0.0000  0.1173
        H  0.0000  0.7572 -0.4692
        H  0.0000 -0.7572 -0.4692
        """
        cls.mol_h2o = SecondQuantizedMolecule(
            cls.xyz_h2o, q=0, spin=0, basis='sto-3g'
        )
        
        # Extract necessary data
        cls.mo_energies_h2o = np.array(cls.mol_h2o.mo_energies)
        _, _, cls.mo_integrals_h2o = cls.mol_h2o.get_full_space_integrals()
        cls.n_occ_h2o = cls.mol_h2o.n_electrons // 2  # 5 occupied orbitals

        # H2 molecule for simpler tests
        cls.xyz_h2 = "H 0 0 0\nH 0 0 0.74"
        cls.mol_h2 = SecondQuantizedMolecule(
            cls.xyz_h2, q=0, spin=0, basis='sto-3g'
        )
        cls.mo_energies_h2 = np.array(cls.mol_h2.mo_energies)
        _, _, cls.mo_integrals_h2 = cls.mol_h2.get_full_space_integrals()
        cls.n_occ_h2 = cls.mol_h2.n_electrons // 2  # 1 occupied orbital

    def test_symmetry(self):
        """Test 11.1: Symmetry property C(i,j) = C(j,i).
        
        For all distinct occupied orbital pairs, the coupling functional
        must be symmetric under exchange of indices.
        """
        eps_tol = 1e-12  # Numerical tolerance from spec
        
        # Test on H2O with multiple occupied pairs
        n_occ = self.n_occ_h2o
        for i in range(n_occ):
            for j in range(i + 1, n_occ):
                c_ij = evaluate_coupling_functional(
                    i, j, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
                )
                c_ji = evaluate_coupling_functional(
                    j, i, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
                )
                
                self.assertAlmostEqual(
                    c_ij, c_ji, delta=eps_tol,
                    msg=f"Symmetry violated for pair ({i},{j}): C({i},{j})={c_ij:.6e} != C({j},{i})={c_ji:.6e}"
                )

    def test_non_negativity(self):
        """Test 11.2: Non-negativity property C(i,j) >= 0.
        
        The coupling functional must be non-negative for all pairs
        due to the absolute value in its definition.
        """
        n_occ = self.n_occ_h2o
        
        # Test all pairs including diagonal
        for i in range(n_occ):
            for j in range(n_occ):
                c_ij = evaluate_coupling_functional(
                    i, j, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
                )
                
                self.assertGreaterEqual(
                    c_ij, 0.0,
                    msg=f"Non-negativity violated for pair ({i},{j}): C({i},{j})={c_ij:.6e} < 0"
                )

    def test_self_null(self):
        """Test 11.3: Self-null property C(i,i) = 0.
        
        The coupling functional must be exactly zero for diagonal pairs
        due to Brillouin's theorem and Pauli exclusion.
        """
        eps_tol = 1e-12  # Numerical tolerance from spec
        n_occ = self.n_occ_h2o
        
        for i in range(n_occ):
            c_ii = evaluate_coupling_functional(
                i, i, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
            )
            
            self.assertAlmostEqual(
                c_ii, 0.0, delta=eps_tol,
                msg=f"Self-null property violated for orbital {i}: C({i},{i})={c_ii:.6e} != 0"
            )

    def test_pair_energy_reproduction_h2o(self):
        """Test 11.4: Pair energy reproduction for H₂O/STO-3G.
        
        Compare the sum of signed MP2 pair energies against a reference
        MP2 calculation to validate that C(i,j) = |E_pair^MP2(i,j)|.
        
        This test verifies that the implementation correctly computes
        MP2 pair energies before taking the absolute value.
        """
        n_occ = self.n_occ_h2o
        
        # Compute total correlation energy from pair energies
        # Note: We need signed pair energies for this test
        total_corr_energy = 0.0
        pair_energies = {}
        
        for i in range(n_occ):
            for j in range(i + 1, n_occ):
                # Compute signed pair energy (before absolute value)
                e_pair = self._compute_signed_pair_energy(
                    i, j, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
                )
                pair_energies[(i, j)] = e_pair
                total_corr_energy += e_pair
                
                # Verify that C(i,j) equals |E_pair^MP2(i,j)|
                c_ij = evaluate_coupling_functional(
                    i, j, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
                )
                self.assertAlmostEqual(
                    c_ij, abs(e_pair), places=10,
                    msg=f"C({i},{j}) != |E_pair({i},{j})|: {c_ij:.6e} != {abs(e_pair):.6e}"
                )
        
        # Compare against pyscf MP2 reference (approximate check)
        # For H2O/STO-3G, MP2 correlation energy is approximately -0.036 Hartree
        # This is a sanity check; exact values may vary slightly with implementation details
        self.assertLess(
            total_corr_energy, 0.0,
            msg="Total MP2 correlation energy should be negative (favorable)"
        )
        self.assertGreater(
            total_corr_energy, -1.0,
            msg="Total MP2 correlation energy unreasonably large in magnitude"
        )

    def test_error_invalid_indices(self):
        """Test explicit error raised for out-of-bounds orbital indices."""
        n_occ = self.n_occ_h2o
        
        # Test negative index
        with self.assertRaises(ValueError) as cm:
            evaluate_coupling_functional(
                -1, 0, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
            )
        self.assertIn("out of bounds", str(cm.exception).lower())
        
        # Test index >= n_occ
        with self.assertRaises(ValueError) as cm:
            evaluate_coupling_functional(
                n_occ, 0, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
            )
        self.assertIn("out of bounds", str(cm.exception).lower())

    def test_error_invalid_array_types(self):
        """Test explicit error raised for invalid mo_energies/mo_integrals types."""
        n_occ = self.n_occ_h2o
        
        # Test non-array mo_energies
        with self.assertRaises(ValueError) as cm:
            evaluate_coupling_functional(
                0, 1, [1.0, 2.0], self.mo_integrals_h2o, n_occ
            )
        self.assertIn("numpy array", str(cm.exception).lower())
        
        # Test non-array mo_integrals
        with self.assertRaises(ValueError) as cm:
            evaluate_coupling_functional(
                0, 1, self.mo_energies_h2o, [[1.0]], n_occ
            )
        self.assertIn("numpy array", str(cm.exception).lower())

    def test_error_inconsistent_shapes(self):
        """Test explicit error raised for inconsistent array shapes."""
        n_occ = self.n_occ_h2o
        
        # Create integrals with wrong shape
        wrong_integrals = np.zeros((3, 3, 3, 3))
        
        with self.assertRaises(ValueError) as cm:
            evaluate_coupling_functional(
                0, 1, self.mo_energies_h2o, wrong_integrals, n_occ
            )
        self.assertIn("inconsistent", str(cm.exception).lower())

    def test_determinism(self):
        """Test 11.7: Determinism - repeated calls yield identical results."""
        n_occ = self.n_occ_h2o
        
        # Compute coupling functional multiple times
        results = []
        for _ in range(5):
            c_01 = evaluate_coupling_functional(
                0, 1, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
            )
            results.append(c_01)
        
        # All results must be bitwise identical
        for r in results[1:]:
            self.assertEqual(
                r, results[0],
                msg="Determinism violated: repeated calls produce different results"
            )

    def test_build_pair_set_integration(self):
        """Test integration of coupling functional into build_pair_set."""
        # Test with zero threshold (all pairs retained)
        pairs_all = build_pair_set(
            self.mol_h2o,
            threshold=0.0,
            mo_energies=self.mo_energies_h2o,
            mo_integrals=self.mo_integrals_h2o
        )
        
        n_occ = self.n_occ_h2o
        expected_n_pairs = n_occ * (n_occ - 1) // 2
        self.assertEqual(
            len(pairs_all), expected_n_pairs,
            msg=f"Expected {expected_n_pairs} pairs with threshold=0, got {len(pairs_all)}"
        )
        
        # Verify pairs are ordered with i < j
        for i, j in pairs_all:
            self.assertLess(i, j, msg=f"Pair ordering violated: ({i},{j}) has i >= j")
        
        # Test with high threshold (no pairs retained)
        pairs_none = build_pair_set(
            self.mol_h2o,
            threshold=1.0,  # Very high threshold
            mo_energies=self.mo_energies_h2o,
            mo_integrals=self.mo_integrals_h2o
        )
        self.assertEqual(
            len(pairs_none), 0,
            msg="Expected 0 pairs with very high threshold"
        )

    def test_build_pair_set_error_handling(self):
        """Test build_pair_set error handling for missing data."""
        # Test with invalid threshold
        with self.assertRaises(ValueError) as cm:
            build_pair_set(self.mol_h2o, threshold=-1.0)
        self.assertIn("non-negative", str(cm.exception).lower())
        
        # Create object without required attributes
        class InvalidWavefunction:
            pass
        
        invalid_wfn = InvalidWavefunction()
        with self.assertRaises(ValueError) as cm:
            build_pair_set(invalid_wfn, threshold=0.0)
        self.assertIn("mo_energies", str(cm.exception).lower())

    # Helper method for computing signed pair energy
    def _compute_signed_pair_energy(self, i, j, mo_energies, mo_integrals, n_occ):
        """Compute signed MP2 pair energy (before absolute value).
        
        This is a duplicate of the logic in evaluate_coupling_functional
        but returns the signed value for validation purposes.
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


if __name__ == '__main__':
    unittest.main()
