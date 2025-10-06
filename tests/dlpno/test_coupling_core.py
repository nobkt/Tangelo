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

"""Core property tests for DLPNO coupling functional C(i,j) (Phase2-Task2.5).

Tests fundamental mathematical properties:
- Symmetry: C(i,j) = C(j,i)
- Non-negativity: C(i,j) >= 0
- Self-null: C(i,i) = 0
- Determinism: reproducible results
"""

import unittest
import numpy as np

from tangelo import SecondQuantizedMolecule
from tangelo.dlpno.coupling import evaluate_coupling_functional


class CouplingCoreTest(unittest.TestCase):
    """Test suite for core coupling functional properties."""

    @classmethod
    def setUpClass(cls):
        """Set up test molecules for reuse across tests."""
        # H2O molecule in STO-3G basis (reference test system)
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
        cls.n_occ_h2o = cls.mol_h2o.n_electrons // 2

        # H2 molecule for simpler tests
        cls.xyz_h2 = "H 0 0 0\nH 0 0 0.74"
        cls.mol_h2 = SecondQuantizedMolecule(
            cls.xyz_h2, q=0, spin=0, basis='sto-3g'
        )
        cls.mo_energies_h2 = np.array(cls.mol_h2.mo_energies)
        _, _, cls.mo_integrals_h2 = cls.mol_h2.get_full_space_integrals()
        cls.n_occ_h2 = cls.mol_h2.n_electrons // 2

    def test_symmetry(self):
        """Test symmetry property C(i,j) = C(j,i).
        
        For all distinct occupied orbital pairs, the coupling functional
        must be symmetric under exchange of indices.
        """
        eps_tol = 1e-12
        
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
        """Test non-negativity property C(i,j) >= 0.
        
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
        """Test self-null property C(i,i) = 0.
        
        The coupling functional must be exactly zero for diagonal pairs
        due to Brillouin's theorem and Pauli exclusion.
        """
        eps_tol = 1e-12
        n_occ = self.n_occ_h2o
        
        for i in range(n_occ):
            c_ii = evaluate_coupling_functional(
                i, i, self.mo_energies_h2o, self.mo_integrals_h2o, n_occ
            )
            
            self.assertAlmostEqual(
                c_ii, 0.0, delta=eps_tol,
                msg=f"Self-null property violated for orbital {i}: C({i},{i})={c_ii:.6e} != 0"
            )

    def test_determinism(self):
        """Test determinism - repeated calls yield identical results."""
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


if __name__ == '__main__':
    unittest.main()
