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

from tangelo.dlpno.config import (
    PNO_TAU_SEQUENCE_DEFAULT,
    PAIR_TAU_SEQUENCE_DEFAULT,
    ENERGY_ABS_TOL_DEFAULT,
    ENERGY_REL_TOL_DEFAULT,
    MAX_EXTRAP_POINTS,
    DEFAULT_RANDOM_SEED,
    validate_monotonic
)


class ConfigTest(unittest.TestCase):
    """Test configuration parameters and validation."""
    
    def test_default_constants(self):
        """Test that default constants are properly defined."""
        self.assertEqual(len(PNO_TAU_SEQUENCE_DEFAULT), 5)
        self.assertEqual(PNO_TAU_SEQUENCE_DEFAULT[0], 1.0e-4)
        self.assertEqual(PNO_TAU_SEQUENCE_DEFAULT[-1], 2.5e-5)
        
        self.assertEqual(len(PAIR_TAU_SEQUENCE_DEFAULT), 3)
        self.assertEqual(PAIR_TAU_SEQUENCE_DEFAULT[0], 1.0e-6)
        self.assertEqual(PAIR_TAU_SEQUENCE_DEFAULT[-1], 2.0e-7)
        
        self.assertEqual(ENERGY_ABS_TOL_DEFAULT, 1.0e-6)
        self.assertEqual(ENERGY_REL_TOL_DEFAULT, 5.0e-7)
        self.assertEqual(MAX_EXTRAP_POINTS, 3)
        self.assertEqual(DEFAULT_RANDOM_SEED, 20250101)
    
    def test_validate_monotonic_decreasing(self):
        """Test validation of strictly decreasing sequences."""
        # Valid sequences
        self.assertTrue(validate_monotonic([1.0, 0.5, 0.1]))
        self.assertTrue(validate_monotonic([10.0, 5.0, 1.0, 0.1]))
        self.assertTrue(validate_monotonic([1.0]))  # Single element
        self.assertTrue(validate_monotonic([]))  # Empty
        
        # Invalid sequences
        self.assertFalse(validate_monotonic([1.0, 1.0, 0.5]))  # Equal values
        self.assertFalse(validate_monotonic([1.0, 0.5, 0.7]))  # Increasing
        self.assertFalse(validate_monotonic([0.1, 0.5, 1.0]))  # Fully increasing
    
    def test_default_sequences_are_monotonic(self):
        """Test that default sequences are strictly decreasing."""
        self.assertTrue(validate_monotonic(PNO_TAU_SEQUENCE_DEFAULT))
        self.assertTrue(validate_monotonic(PAIR_TAU_SEQUENCE_DEFAULT))


if __name__ == '__main__':
    unittest.main()
