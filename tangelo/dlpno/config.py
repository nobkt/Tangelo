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

"""Configuration parameters for DLPNO-CCSD(T) calculations."""

# Default parameter sequences for DLPNO-CCSD(T)
PNO_TAU_SEQUENCE_DEFAULT = [1.0e-4, 7.0e-5, 5.0e-5, 3.5e-5, 2.5e-5]
PAIR_TAU_SEQUENCE_DEFAULT = [1.0e-6, 5.0e-7, 2.0e-7]

# Convergence tolerances
ENERGY_ABS_TOL_DEFAULT = 1.0e-6  # Eh
ENERGY_REL_TOL_DEFAULT = 5.0e-7

# Extrapolation parameters
MAX_EXTRAP_POINTS = 3

# Random seed for deterministic behavior
DEFAULT_RANDOM_SEED = 20250101


def validate_monotonic(seq: list[float]) -> bool:
    """Validate that a sequence is strictly decreasing.
    
    Args:
        seq: List of float values to validate
        
    Returns:
        bool: True if sequence is strictly decreasing, False otherwise
    """
    if len(seq) < 2:
        return True
    for i in range(len(seq) - 1):
        if seq[i] <= seq[i + 1]:
            return False
    return True


# Validate default sequences at import time
if not validate_monotonic(PNO_TAU_SEQUENCE_DEFAULT):
    raise ValueError("PNO_TAU_SEQUENCE_DEFAULT must be strictly decreasing")

if not validate_monotonic(PAIR_TAU_SEQUENCE_DEFAULT):
    raise ValueError("PAIR_TAU_SEQUENCE_DEFAULT must be strictly decreasing")
