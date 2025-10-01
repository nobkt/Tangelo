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

import unittest

from tangelo.dlpno.structures import (
    OrbitalSpace,
    PNOParameters,
    ConvergenceCriteria,
    ConvergenceRecord,
    default_pno_parameters
)


class StructuresEmptyTest(unittest.TestCase):
    """Test basic instantiation of data structures."""
    
    def test_orbital_space_creation(self):
        """Test OrbitalSpace can be instantiated."""
        space = OrbitalSpace()
        self.assertIsNone(space.occupied_indices)
        self.assertIsNone(space.virtual_indices)
        self.assertIsNone(space.localization_method)
        self.assertIsNone(space.lmo_coeff)
    
    def test_pno_parameters_creation(self):
        """Test PNOParameters can be instantiated."""
        params = PNOParameters(
            pno_tau_sequence=[1e-4, 1e-5],
            pair_tau_sequence=[1e-6, 1e-7],
            energy_abs_tol=1e-6,
            energy_rel_tol=1e-7,
            max_extrap_points=3
        )
        self.assertEqual(len(params.pno_tau_sequence), 2)
        self.assertEqual(len(params.pair_tau_sequence), 2)
    
    def test_convergence_criteria_creation(self):
        """Test ConvergenceCriteria can be instantiated."""
        criteria = ConvergenceCriteria(
            energy_abs_tol=1e-6,
            energy_rel_tol=1e-7
        )
        self.assertEqual(criteria.energy_abs_tol, 1e-6)
        self.assertEqual(criteria.energy_rel_tol, 1e-7)
        self.assertIsNone(criteria.max_iterations)
    
    def test_convergence_record_creation(self):
        """Test ConvergenceRecord can be instantiated."""
        record = ConvergenceRecord(
            iteration=1,
            energy=-100.0,
            residual_norm=1e-5,
            converged=False
        )
        self.assertEqual(record.iteration, 1)
        self.assertEqual(record.energy, -100.0)
        self.assertEqual(record.residual_norm, 1e-5)
        self.assertFalse(record.converged)
    
    def test_default_pno_parameters(self):
        """Test default_pno_parameters function."""
        params = default_pno_parameters()
        self.assertIsInstance(params, PNOParameters)
        self.assertEqual(len(params.pno_tau_sequence), 5)
        self.assertEqual(len(params.pair_tau_sequence), 3)
        self.assertEqual(params.max_extrap_points, 3)


if __name__ == '__main__':
    unittest.main()
