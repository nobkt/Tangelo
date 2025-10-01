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

"""Energy assembler for DLPNO-CCSD(T) calculations.

Spec §2.2: Pipeline Completeness Conditions
Spec §5.1: IncompletePipelineError

This module provides the EnergyAssembler class which enforces pipeline
completeness before emitting final energies, preventing partial/invalid
energy leakage.
"""

from __future__ import annotations
from typing import Dict, Optional


class IncompletePipelineError(RuntimeError):
    """Raised when attempting to retrieve energy before pipeline completion.
    
    Spec §5.1: This error is raised by EnergyAssembler when the user attempts
    to obtain a final energy value before all required pipeline stages have
    completed successfully.
    
    In Phase1, all pipeline flags default to False, so this error is always
    raised. Future phases will gradually enable pipeline stages.
    """
    pass


class SpecContractError(RuntimeError):
    """Raised on CI contract violations (reserved for future use).
    
    Spec §5.2: This error class is reserved for future contract enforcement,
    such as threshold monotonicity violations, schema mismatches, or other
    specification breaches detected at runtime or in CI.
    
    Phase1: Not yet raised; defined for forward compatibility.
    """
    pass


class EnergyAssembler:
    """Assembles final DLPNO-CCSD(T) energy from pipeline components.
    
    Spec §2.2: Pipeline Completeness Conditions
    
    This class enforces the pipeline completeness invariant: no energy may
    be emitted until all required stages are complete (or a permitted partial
    mode is explicitly requested in future phases).
    
    Phase1 Status: All pipeline flags default to False. Any attempt to retrieve
    energy raises IncompletePipelineError. This is a hard guard preventing
    accidental use of incomplete implementations.
    
    Future Phases: As pipeline stages are implemented (Phase2-Phase8), the
    corresponding flags will be set to True, gradually enabling partial and
    then full energy assembly.
    
    Attributes:
        pipeline_flags: Dictionary tracking completion status of each stage
        scf_energy: Reference SCF energy (Hartree)
        mp2_correlation: Local MP2 correlation energy (Hartree)
        ccsd_correlation: Local CCSD correlation energy (Hartree)
        triples_correction: Perturbative (T) correction (Hartree)
    """
    
    def __init__(self, scf_energy: Optional[float] = None):
        """Initialize energy assembler with SCF reference energy.
        
        Args:
            scf_energy: Reference SCF energy in Hartree (optional in Phase1)
        """
        self.scf_energy = scf_energy
        self.mp2_correlation: Optional[float] = None
        self.ccsd_correlation: Optional[float] = None
        self.triples_correction: Optional[float] = None
        
        # Spec §2.2: Pipeline completeness flags
        self.pipeline_flags: Dict[str, bool] = {
            "localization_complete": False,
            "pairs_detected": False,
            "pno_constructed": False,
            "mp2_converged": False,
            "ccsd_converged": False,
            "triples_computed": False,
        }
    
    def set_mp2_energy(self, correlation_energy: float) -> None:
        """Set MP2 correlation energy component.
        
        Args:
            correlation_energy: MP2 correlation energy in Hartree
        """
        self.mp2_correlation = correlation_energy
        # Future phases will set mp2_converged flag here
    
    def set_ccsd_energy(self, correlation_energy: float) -> None:
        """Set CCSD correlation energy component.
        
        Args:
            correlation_energy: CCSD correlation energy in Hartree
        """
        self.ccsd_correlation = correlation_energy
        # Future phases will set ccsd_converged flag here
    
    def set_triples_correction(self, correction: float) -> None:
        """Set perturbative triples correction.
        
        Args:
            correction: (T) correction in Hartree
        """
        self.triples_correction = correction
        # Future phases will set triples_computed flag here
    
    def _check_pipeline_complete(self) -> bool:
        """Check if all pipeline stages are complete.
        
        Spec §2.2: Pipeline Completeness Conditions
        
        Returns:
            True if all pipeline flags are True, False otherwise
        """
        return all(self.pipeline_flags.values())
    
    def get_mp2_energy(self, mode: str = "FULL") -> float:
        """Retrieve total MP2 energy (SCF + correlation).
        
        Spec §2.2, §5.1: Raises IncompletePipelineError in Phase1
        
        Args:
            mode: Energy mode ("FULL" requires complete pipeline)
        
        Returns:
            Total MP2 energy in Hartree
            
        Raises:
            IncompletePipelineError: If pipeline not complete in FULL mode
        """
        if mode == "FULL" and not self._check_pipeline_complete():
            raise IncompletePipelineError(
                "Cannot retrieve MP2 energy: pipeline incomplete. "
                f"Flags: {self.pipeline_flags}. "
                "Phase1: All stages unimplemented, so all flags are False. "
                "This guard prevents partial/invalid energy emission."
            )
        
        # Future phases: return self.scf_energy + self.mp2_correlation
        raise IncompletePipelineError(
            "MP2 energy assembly not yet implemented (Phase1-4). "
            "This is a hard guard preventing accidental use."
        )
    
    def get_ccsd_energy(self, mode: str = "FULL") -> float:
        """Retrieve total CCSD energy (SCF + CCSD correlation).
        
        Spec §2.2, §5.1: Raises IncompletePipelineError in Phase1
        
        Args:
            mode: Energy mode ("FULL" requires complete pipeline)
        
        Returns:
            Total CCSD energy in Hartree
            
        Raises:
            IncompletePipelineError: If pipeline not complete in FULL mode
        """
        if mode == "FULL" and not self._check_pipeline_complete():
            raise IncompletePipelineError(
                "Cannot retrieve CCSD energy: pipeline incomplete. "
                f"Flags: {self.pipeline_flags}. "
                "Phase1: All stages unimplemented, so all flags are False. "
                "This guard prevents partial/invalid energy emission."
            )
        
        # Future phases: return self.scf_energy + self.ccsd_correlation
        raise IncompletePipelineError(
            "CCSD energy assembly not yet implemented (Phase1-6). "
            "This is a hard guard preventing accidental use."
        )
    
    def get_ccsd_t_energy(self, mode: str = "FULL") -> float:
        """Retrieve total CCSD(T) energy (SCF + CCSD + (T) correction).
        
        Spec §2.2, §5.1: Raises IncompletePipelineError in Phase1
        
        Args:
            mode: Energy mode ("FULL" requires complete pipeline)
        
        Returns:
            Total CCSD(T) energy in Hartree
            
        Raises:
            IncompletePipelineError: If pipeline not complete in FULL mode
        """
        if mode == "FULL" and not self._check_pipeline_complete():
            raise IncompletePipelineError(
                "Cannot retrieve CCSD(T) energy: pipeline incomplete. "
                f"Flags: {self.pipeline_flags}. "
                "Phase1: All stages unimplemented, so all flags are False. "
                "This guard prevents partial/invalid energy emission."
            )
        
        # Future phases: return self.scf_energy + self.ccsd_correlation + self.triples_correction
        raise IncompletePipelineError(
            "CCSD(T) energy assembly not yet implemented (Phase1-8). "
            "This is a hard guard preventing accidental use."
        )
    
    def get_correlation_energy(self, level: str = "CCSD(T)", mode: str = "FULL") -> float:
        """Retrieve correlation energy at specified level.
        
        Spec §2.2, §5.1: Raises IncompletePipelineError in Phase1
        
        Args:
            level: Correlation level ("MP2", "CCSD", or "CCSD(T)")
            mode: Energy mode ("FULL" requires complete pipeline)
        
        Returns:
            Correlation energy in Hartree
            
        Raises:
            IncompletePipelineError: If pipeline not complete in FULL mode
            ValueError: If level is not recognized
        """
        if level not in ["MP2", "CCSD", "CCSD(T)"]:
            raise ValueError(f"Unknown correlation level: {level}")
        
        if mode == "FULL" and not self._check_pipeline_complete():
            raise IncompletePipelineError(
                f"Cannot retrieve {level} correlation energy: pipeline incomplete. "
                f"Flags: {self.pipeline_flags}. "
                "Phase1: All stages unimplemented, so all flags are False. "
                "This guard prevents partial/invalid energy emission."
            )
        
        # Future phases: return appropriate correlation energy component(s)
        raise IncompletePipelineError(
            f"{level} correlation energy assembly not yet implemented (Phase1). "
            "This is a hard guard preventing accidental use."
        )
