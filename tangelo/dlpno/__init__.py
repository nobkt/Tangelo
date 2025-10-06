"""DLPNO scaffolding package for Tangelo.

Re-exports configuration constants, data structures, and monitoring utilities
needed for the DLPNO-CCSD(T) implementation roadmap. Algorithmic logic is
intentionally absent at this stage.
"""

from __future__ import annotations

# Configuration constants
from .config import (
    PNO_TAU_SEQUENCE_DEFAULT,
    PAIR_TAU_SEQUENCE_DEFAULT,
    ENERGY_ABS_TOL_DEFAULT,
    ENERGY_REL_TOL_DEFAULT,
)

# Data structures & helper
from .structures import (
    OrbitalSpace,
    PNOParameters,
    ConvergenceCriteria,
    ConvergenceRecord,
    default_pno_parameters,
)

# Convergence utilities
from .convergence import ConvergenceMonitor

# Pair screening
from .pairs import build_pair_set, OccupiedPair, PairSet
from .coupling import evaluate_coupling_functional

__all__ = [
    # Config constants
    "PNO_TAU_SEQUENCE_DEFAULT",
    "PAIR_TAU_SEQUENCE_DEFAULT",
    "ENERGY_ABS_TOL_DEFAULT",
    "ENERGY_REL_TOL_DEFAULT",
    # Data & helper
    "OrbitalSpace",
    "PNOParameters",
    "ConvergenceCriteria",
    "ConvergenceRecord",
    "default_pno_parameters",
    # Monitor
    "ConvergenceMonitor",
    # Pair screening
    "build_pair_set",
    "OccupiedPair",
    "PairSet",
    "evaluate_coupling_functional",
]