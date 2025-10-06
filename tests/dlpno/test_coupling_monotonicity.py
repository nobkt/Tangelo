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

"""Monotonicity tests for coupling functional basis expansion (Phase2-Task2.5).

Tests weak monotonic increase of C(i,j) with virtual space expansion:
- STO-3G vs 6-31G on H2O
- Warns but does not fail if tiny floating point drift occurs
"""

import unittest
import numpy as np

from tangelo import SecondQuantizedMolecule
from tangelo.dlpno.coupling import evaluate_coupling_functional


class CouplingMonotonicityTest(unittest.TestCase):
    """Test suite for basis set expansion monotonicity."""

    def test_basis_expansion_h2o(self):
        """Test weak monotonic increase: STO-3G vs 6-31G on H2O.
        
        Larger basis sets should generally produce equal or larger C(i,j)
        values due to increased virtual space flexibility. Small violations
        due to floating point effects trigger warnings but not failures.
        """
        xyz_h2o = """
        O  0.0000  0.0000  0.1173
        H  0.0000  0.7572 -0.4692
        H  0.0000 -0.7572 -0.4692
        """
        
        # Compute with STO-3G
        mol_sto3g = SecondQuantizedMolecule(xyz_h2o, q=0, spin=0, basis='sto-3g')
        mo_energies_sto3g = np.array(mol_sto3g.mo_energies)
        _, _, mo_integrals_sto3g = mol_sto3g.get_full_space_integrals()
        n_occ_sto3g = mol_sto3g.n_electrons // 2
        
        # Compute with 6-31G
        mol_631g = SecondQuantizedMolecule(xyz_h2o, q=0, spin=0, basis='6-31g')
        mo_energies_631g = np.array(mol_631g.mo_energies)
        _, _, mo_integrals_631g = mol_631g.get_full_space_integrals()
        n_occ_631g = mol_631g.n_electrons // 2
        
        # Should have same number of occupied orbitals
        self.assertEqual(n_occ_sto3g, n_occ_631g, 
                         msg="Number of occupied orbitals should be basis-independent")
        
        n_occ = n_occ_sto3g
        
        # Compare C(i,j) for all pairs
        violations = []
        eps_drift = 1e-9  # Allow tiny floating point drift
        
        for i in range(n_occ):
            for j in range(i + 1, n_occ):
                c_sto3g = evaluate_coupling_functional(
                    i, j, mo_energies_sto3g, mo_integrals_sto3g, n_occ
                )
                c_631g = evaluate_coupling_functional(
                    i, j, mo_energies_631g, mo_integrals_631g, n_occ
                )
                
                # Check weak monotonicity: C(6-31G) >= C(STO-3G) - eps_drift
                if c_631g < c_sto3g - eps_drift:
                    violation_amount = c_sto3g - c_631g
                    violations.append({
                        'pair': (i, j),
                        'c_sto3g': c_sto3g,
                        'c_631g': c_631g,
                        'violation': violation_amount
                    })
        
        # Report violations as warnings (print) but don't fail test
        if violations:
            print(f"\nWARNING: {len(violations)} weak monotonicity violations detected:")
            for v in violations[:5]:  # Show first 5
                print(f"  Pair {v['pair']}: STO-3G={v['c_sto3g']:.6e}, "
                      f"6-31G={v['c_631g']:.6e}, diff={v['violation']:.6e}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
            
            # Only fail if violations are large (not just floating point noise)
            max_violation = max(v['violation'] for v in violations)
            if max_violation > 1e-6:
                self.fail(f"Large monotonicity violation detected: {max_violation:.6e}")
        else:
            print("\n✓ Weak monotonic increase confirmed for all pairs (STO-3G → 6-31G)")

    def test_virtual_space_increase(self):
        """Verify that larger basis sets have more virtual orbitals."""
        xyz_h2o = """
        O  0.0000  0.0000  0.1173
        H  0.0000  0.7572 -0.4692
        H  0.0000 -0.7572 -0.4692
        """
        
        mol_sto3g = SecondQuantizedMolecule(xyz_h2o, q=0, spin=0, basis='sto-3g')
        mol_631g = SecondQuantizedMolecule(xyz_h2o, q=0, spin=0, basis='6-31g')
        
        n_occ_sto3g = mol_sto3g.n_electrons // 2
        n_occ_631g = mol_631g.n_electrons // 2
        
        n_virt_sto3g = len(mol_sto3g.mo_energies) - n_occ_sto3g
        n_virt_631g = len(mol_631g.mo_energies) - n_occ_631g
        
        self.assertGreater(
            n_virt_631g, n_virt_sto3g,
            msg=f"6-31G should have more virtuals than STO-3G: "
                f"{n_virt_631g} vs {n_virt_sto3g}"
        )
        
        print(f"\nVirtual space sizes: STO-3G={n_virt_sto3g}, 6-31G={n_virt_631g}")


if __name__ == '__main__':
    unittest.main()
