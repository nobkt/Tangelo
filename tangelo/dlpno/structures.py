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

"""Data structures for DLPNO-CCSD(T) calculations."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from tangelo.dlpno.config import (
    PNO_TAU_SEQUENCE_DEFAULT,
    PAIR_TAU_SEQUENCE_DEFAULT,
    ENERGY_ABS_TOL_DEFAULT,
    ENERGY_REL_TOL_DEFAULT,
    MAX_EXTRAP_POINTS
)


@dataclass
class OrbitalSpace:
    """Represents orbital space information for DLPNO calculations.
    
    Attributes:
        occupied_indices: List of occupied orbital indices
        virtual_indices: List of virtual orbital indices
        localization_method: Name of the localization method used
        lmo_coeff: Localized molecular orbital coefficients
    """
    occupied_indices: list[int] | None = None
    virtual_indices: list[int] | None = None
    localization_method: str | None = None
    lmo_coeff: 'np.ndarray | None' = None


@dataclass
class PNOParameters:
    """Parameters for PNO truncation in DLPNO calculations.
    
    Attributes:
        pno_tau_sequence: Sequence of PNO truncation thresholds
        pair_tau_sequence: Sequence of pair truncation thresholds
        energy_abs_tol: Absolute energy convergence tolerance
        energy_rel_tol: Relative energy convergence tolerance
        max_extrap_points: Maximum number of extrapolation points
    """
    pno_tau_sequence: list[float]
    pair_tau_sequence: list[float]
    energy_abs_tol: float
    energy_rel_tol: float
    max_extrap_points: int


@dataclass
class ConvergenceCriteria:
    """Convergence criteria for iterative calculations.
    
    Attributes:
        energy_abs_tol: Absolute energy convergence tolerance
        energy_rel_tol: Relative energy convergence tolerance
        max_iterations: Maximum number of iterations (optional)
    """
    energy_abs_tol: float
    energy_rel_tol: float
    max_iterations: int | None = None


@dataclass
class ConvergenceRecord:
    """Record of convergence information for a single iteration.
    
    Attributes:
        iteration: Iteration number
        energy: Energy value for this iteration
        residual_norm: Residual norm for this iteration
        converged: Whether convergence criteria are satisfied
    """
    iteration: int
    energy: float | None
    residual_norm: float | None
    converged: bool


def default_pno_parameters() -> PNOParameters:
    """Create PNOParameters with default values from config.
    
    Returns:
        PNOParameters: Parameters initialized with default constants
    """
    return PNOParameters(
        pno_tau_sequence=PNO_TAU_SEQUENCE_DEFAULT.copy(),
        pair_tau_sequence=PAIR_TAU_SEQUENCE_DEFAULT.copy(),
        energy_abs_tol=ENERGY_ABS_TOL_DEFAULT,
        energy_rel_tol=ENERGY_REL_TOL_DEFAULT,
        max_extrap_points=MAX_EXTRAP_POINTS
    )
