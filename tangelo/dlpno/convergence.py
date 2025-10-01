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

"""Convergence monitoring for DLPNO-CCSD(T) calculations."""

import math

from tangelo.dlpno.structures import ConvergenceCriteria, ConvergenceRecord


class ConvergenceMonitor:
    """Monitor convergence of iterative calculations.
    
    Attributes:
        criteria: Convergence criteria for the calculation
    """
    
    def __init__(self, criteria: ConvergenceCriteria):
        """Initialize convergence monitor.
        
        Args:
            criteria: Convergence criteria to use
        """
        self.criteria = criteria
        self._records: list[ConvergenceRecord] = []
        self._converged = False
    
    def update(self, iteration: int, energy: float | None, residual_norm: float | None) -> ConvergenceRecord:
        """Update convergence monitor with new iteration data.
        
        Args:
            iteration: Current iteration number
            energy: Energy value for this iteration
            residual_norm: Residual norm for this iteration
            
        Returns:
            ConvergenceRecord: Record with convergence status
        """
        converged = False
        
        # Check convergence only after at least 1 iteration and if values are finite
        if iteration > 0 and len(self._records) > 0:
            prev_record = self._records[-1]
            
            # Check if both energy and residual meet criteria
            energy_converged = False
            residual_converged = False
            
            if energy is not None and math.isfinite(energy):
                if prev_record.energy is not None and math.isfinite(prev_record.energy):
                    energy_diff = abs(energy - prev_record.energy)
                    abs_tol_met = energy_diff < self.criteria.energy_abs_tol
                    
                    # Relative tolerance check (avoid division by zero)
                    if abs(prev_record.energy) > 1e-12:
                        rel_tol_met = energy_diff / abs(prev_record.energy) < self.criteria.energy_rel_tol
                    else:
                        rel_tol_met = abs_tol_met
                    
                    energy_converged = abs_tol_met and rel_tol_met
            
            if residual_norm is not None and math.isfinite(residual_norm):
                # Residual convergence uses absolute tolerance
                residual_converged = residual_norm < self.criteria.energy_abs_tol
            
            # Both must converge
            converged = energy_converged and residual_converged
        
        record = ConvergenceRecord(
            iteration=iteration,
            energy=energy,
            residual_norm=residual_norm,
            converged=converged
        )
        
        self._records.append(record)
        
        if converged:
            self._converged = True
        
        return record
    
    def is_converged(self) -> bool:
        """Check if calculation has converged.
        
        Returns:
            bool: True if converged, False otherwise
        """
        return self._converged
    
    @property
    def records(self) -> list[ConvergenceRecord]:
        """Get list of convergence records.
        
        Returns:
            list[ConvergenceRecord]: All convergence records
        """
        return self._records.copy()
