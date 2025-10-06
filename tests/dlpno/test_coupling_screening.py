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

"""Pair screening and error handling tests for coupling functional (Phase2-Task2.5).

Tests:
- Threshold behavior in build_pair_set
- Error handling for invalid inputs
"""

import unittest
import numpy as np

from tangelo import SecondQuantizedMolecule
from tangelo.dlpno.coupling import evaluate_coupling_functional
from tangelo.dlpno.pairs import build_pair_set


class CouplingScreeningTest(unittest.TestCase):
    """Test suite for pair screening behavior."""

    @classmethod
    def setUpClass(cls):
        """Set up test molecule for reuse."""
        cls.xyz_h2o = """
        O  0.0000  0.0000  0.1173
        H  0.0000  0.7572 -0.4692
        H  0.0000 -0.7572 -0.4692
        """
        cls.mol_h2o = SecondQuantizedMolecule(
            cls.xyz_h2o, q=0, spin=0, basis='sto-3g'
        )
        cls.mo_energies_h2o = np.array(cls.mol_h2o.mo_energies)
        _, _, cls.mo_integrals_h2o = cls.mol_h2o.get_full_space_integrals()
        cls.n_occ_h2o = cls.mol_h2o.n_electrons // 2

    def test_threshold_zero(self):
        """Test that threshold=0.0 retains all pairs."""
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

    def test_threshold_high(self):
        """Test that high threshold retains no pairs."""
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

    def test_threshold_intermediate(self):
        """Test intermediate threshold retains subset of pairs."""
        # Test with moderate threshold
        pairs_subset = build_pair_set(
            self.mol_h2o,
            threshold=1e-3,
            mo_energies=self.mo_energies_h2o,
            mo_integrals=self.mo_integrals_h2o
        )
        
        n_occ = self.n_occ_h2o
        max_pairs = n_occ * (n_occ - 1) // 2
        
        # Should retain some but not all pairs
        self.assertGreater(len(pairs_subset), 0, msg="Should retain some pairs")
        self.assertLess(len(pairs_subset), max_pairs, msg="Should not retain all pairs")
        
        # Verify all retained pairs satisfy threshold
        for i, j in pairs_subset:
            c_ij = evaluate_coupling_functional(
                i, j, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
            )
            self.assertGreaterEqual(
                c_ij, 1e-3,
                msg=f"Pair ({i},{j}) with C={c_ij:.6e} below threshold 1e-3"
            )

    def test_error_negative_threshold(self):
        """Test that negative threshold raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            build_pair_set(self.mol_h2o, threshold=-1.0)
        self.assertIn("non-negative", str(cm.exception).lower())

    def test_error_invalid_indices(self):
        """Test error raised for out-of-bounds orbital indices."""
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
        """Test error raised for invalid mo_energies/mo_integrals types."""
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
        """Test error raised for inconsistent array shapes."""
        n_occ = self.n_occ_h2o
        
        # Create integrals with wrong shape
        wrong_integrals = np.zeros((3, 3, 3, 3))
        
        with self.assertRaises(ValueError) as cm:
            evaluate_coupling_functional(
                0, 1, self.mo_energies_h2o, wrong_integrals, n_occ
            )
        self.assertIn("inconsistent", str(cm.exception).lower())

    def test_error_missing_attributes(self):
        """Test build_pair_set error handling for missing data."""
        # Create object without required attributes
        class InvalidWavefunction:
            pass
        
        invalid_wfn = InvalidWavefunction()
        with self.assertRaises(ValueError) as cm:
            build_pair_set(invalid_wfn, threshold=0.0)
        self.assertIn("mo_energies", str(cm.exception).lower())


if __name__ == '__main__':
    unittest.main()
