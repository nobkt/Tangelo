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

"""Contract tests for DLPNO Phase1 specification baseline.

Spec §6: Contract Testing

These tests validate the structural integrity of the Phase1 specification:
- Threshold configuration structure and types
- JSON Schema validity for log schema
- EnergyAssembler guard behavior
- SPEC_VERSION accessibility and value
"""

import json
import os
import pytest
import yaml
from pathlib import Path


class TestSpecContract:
    """Test suite for DLPNO Phase1 specification contracts."""
    
    @classmethod
    def setup_class(cls):
        """Locate spec files relative to repository root."""
        # Find repository root (contains setup.py)
        cls.repo_root = Path(__file__).parent.parent
        cls.spec_dir = cls.repo_root / "spec"
        
        # Verify spec directory exists
        assert cls.spec_dir.exists(), f"Spec directory not found: {cls.spec_dir}"
    
    def test_spec_version_import(self):
        """Test SPEC_VERSION constant is accessible.
        
        Spec §6.1: SPEC_VERSION Accessibility
        """
        from tangelo.dlpno.spec_version import SPEC_VERSION
        assert SPEC_VERSION == "0.1.0", f"Expected SPEC_VERSION='0.1.0', got '{SPEC_VERSION}'"
    
    def test_thresholds_yaml_structure(self):
        """Test thresholds.yaml has required keys and correct types.
        
        Spec §6.1: Threshold Integrity
        """
        thresholds_path = self.spec_dir / "thresholds.yaml"
        assert thresholds_path.exists(), f"thresholds.yaml not found: {thresholds_path}"
        
        with open(thresholds_path, 'r') as f:
            thresholds = yaml.safe_load(f)
        
        # Required threshold keys
        required_keys = [
            "T_CutPairs",
            "T_CutPNO",
            "T_CutDO",
            "T_CutResid",
            "MaxIter_CCSD",
            "DIIS_Start",
            "DIIS_Keep",
            "PNO_TAU_SEQUENCE",
            "PAIR_TAU_SEQUENCE",
            "ENERGY_ABS_TOL",
            "ENERGY_REL_TOL",
            "DEFAULT_RANDOM_SEED",
        ]
        
        for key in required_keys:
            assert key in thresholds, f"Missing required threshold key: {key}"
        
        # Validate numeric types for scalar thresholds
        scalar_floats = ["T_CutPairs", "T_CutPNO", "T_CutDO", "T_CutResid", 
                        "ENERGY_ABS_TOL", "ENERGY_REL_TOL"]
        for key in scalar_floats:
            value = thresholds[key]["value"]
            assert isinstance(value, (int, float)), f"{key} value must be numeric, got {type(value)}"
            assert value > 0, f"{key} value must be positive, got {value}"
        
        # Validate integer types
        scalar_ints = ["MaxIter_CCSD", "DIIS_Start", "DIIS_Keep", "DEFAULT_RANDOM_SEED"]
        for key in scalar_ints:
            value = thresholds[key]["value"]
            assert isinstance(value, int), f"{key} value must be integer, got {type(value)}"
            assert value >= 0, f"{key} value must be non-negative, got {value}"
        
        # Validate threshold sequences
        pno_seq = thresholds["PNO_TAU_SEQUENCE"]["values"]
        pair_seq = thresholds["PAIR_TAU_SEQUENCE"]["values"]
        
        assert isinstance(pno_seq, list), "PNO_TAU_SEQUENCE values must be list"
        assert isinstance(pair_seq, list), "PAIR_TAU_SEQUENCE values must be list"
        assert len(pno_seq) > 0, "PNO_TAU_SEQUENCE must not be empty"
        assert len(pair_seq) > 0, "PAIR_TAU_SEQUENCE must not be empty"
    
    def test_thresholds_monotonicity(self):
        """Test that threshold sequences are strictly decreasing.
        
        Spec §11: Threshold Monotonicity Constraints
        """
        thresholds_path = self.spec_dir / "thresholds.yaml"
        with open(thresholds_path, 'r') as f:
            thresholds = yaml.safe_load(f)
        
        # Check PNO sequence monotonicity
        pno_seq = thresholds["PNO_TAU_SEQUENCE"]["values"]
        for i in range(len(pno_seq) - 1):
            assert pno_seq[i] > pno_seq[i+1], \
                f"PNO_TAU_SEQUENCE not strictly decreasing: {pno_seq[i]} <= {pno_seq[i+1]}"
        
        # Check PAIR sequence monotonicity
        pair_seq = thresholds["PAIR_TAU_SEQUENCE"]["values"]
        for i in range(len(pair_seq) - 1):
            assert pair_seq[i] > pair_seq[i+1], \
                f"PAIR_TAU_SEQUENCE not strictly decreasing: {pair_seq[i]} <= {pair_seq[i+1]}"
    
    def test_log_schema_json_validity(self):
        """Test log_schema.json is valid JSON Schema.
        
        Spec §6.1: Schema Compliance
        """
        schema_path = self.spec_dir / "log_schema.json"
        assert schema_path.exists(), f"log_schema.json not found: {schema_path}"
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Verify it's a valid JSON Schema structure
        assert "$schema" in schema, "Missing $schema field"
        assert "title" in schema, "Missing title field"
        assert "type" in schema, "Missing type field"
        assert schema["type"] == "object", "Root type must be 'object'"
        assert "required" in schema, "Missing required field"
        assert "properties" in schema, "Missing properties field"
        
        # Verify required fields are present
        required_fields = [
            "run_uuid",
            "spec_version",
            "git_hash",
            "thresholds",
            "system",
            "molecule",
            "stage",
            "timestamp_start"
        ]
        for field in required_fields:
            assert field in schema["required"], f"Required field '{field}' not in schema"
            assert field in schema["properties"], f"Required field '{field}' not in properties"
    
    def test_log_schema_validates_example(self):
        """Test that a synthetic log example validates against schema.
        
        Spec §6.1: Schema Compliance
        Spec §9.1: Required Metadata Fields
        """
        schema_path = self.spec_dir / "log_schema.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Construct minimal synthetic log
        synthetic_log = {
            "run_uuid": "12345678-1234-1234-1234-123456789abc",
            "spec_version": "0.1.0",
            "git_hash": "9acef4ed7a6334f4bf3c47148cd64a13dbeac652",
            "thresholds": {
                "T_CutPairs": 1.0e-4,
                "T_CutPNO": 1.0e-7,
                "T_CutDO": 5.0e-3,
                "T_CutResid": 1.0e-7,
                "MaxIter_CCSD": 50,
                "DIIS_Start": 2,
                "DIIS_Keep": 8
            },
            "system": {
                "molecule_name": "H2O",
                "basis_set": "cc-pVDZ",
                "charge": 0,
                "spin_multiplicity": 1
            },
            "molecule": {
                "geometry": [
                    ["O", 0.0, 0.0, 0.0],
                    ["H", 0.0, 0.757, 0.587],
                    ["H", 0.0, -0.757, 0.587]
                ],
                "n_electrons": 10,
                "n_atoms": 3,
                "geometry_units": "angstrom"
            },
            "stage": "initialization",
            "timestamp_start": "2025-01-01T00:00:00Z"
        }
        
        # Validate using jsonschema library if available, otherwise basic check
        try:
            import jsonschema
            jsonschema.validate(instance=synthetic_log, schema=schema)
        except ImportError:
            # If jsonschema not available, just verify structure matches
            for required_field in schema["required"]:
                assert required_field in synthetic_log, \
                    f"Synthetic log missing required field: {required_field}"
    
    def test_energy_assembler_guard_mp2(self):
        """Test EnergyAssembler raises IncompletePipelineError for MP2 energy.
        
        Spec §5.1: IncompletePipelineError
        Spec §2.2: Pipeline Completeness Conditions
        """
        from tangelo.dlpno.energy_assembler import EnergyAssembler, IncompletePipelineError
        
        assembler = EnergyAssembler(scf_energy=-75.0)
        
        # Verify all flags are False initially
        assert all(not flag for flag in assembler.pipeline_flags.values()), \
            "All pipeline flags should be False in Phase1"
        
        # Attempt to get MP2 energy should raise
        with pytest.raises(IncompletePipelineError) as exc_info:
            assembler.get_mp2_energy(mode="FULL")
        
        assert "pipeline incomplete" in str(exc_info.value).lower()
    
    def test_energy_assembler_guard_ccsd(self):
        """Test EnergyAssembler raises IncompletePipelineError for CCSD energy.
        
        Spec §5.1: IncompletePipelineError
        """
        from tangelo.dlpno.energy_assembler import EnergyAssembler, IncompletePipelineError
        
        assembler = EnergyAssembler(scf_energy=-75.0)
        
        with pytest.raises(IncompletePipelineError) as exc_info:
            assembler.get_ccsd_energy(mode="FULL")
        
        assert "pipeline incomplete" in str(exc_info.value).lower()
    
    def test_energy_assembler_guard_ccsd_t(self):
        """Test EnergyAssembler raises IncompletePipelineError for CCSD(T) energy.
        
        Spec §5.1: IncompletePipelineError
        """
        from tangelo.dlpno.energy_assembler import EnergyAssembler, IncompletePipelineError
        
        assembler = EnergyAssembler(scf_energy=-75.0)
        
        with pytest.raises(IncompletePipelineError) as exc_info:
            assembler.get_ccsd_t_energy(mode="FULL")
        
        assert "pipeline incomplete" in str(exc_info.value).lower()
    
    def test_energy_assembler_guard_correlation(self):
        """Test EnergyAssembler raises IncompletePipelineError for correlation energy.
        
        Spec §5.1: IncompletePipelineError
        """
        from tangelo.dlpno.energy_assembler import EnergyAssembler, IncompletePipelineError
        
        assembler = EnergyAssembler(scf_energy=-75.0)
        
        for level in ["MP2", "CCSD", "CCSD(T)"]:
            with pytest.raises(IncompletePipelineError) as exc_info:
                assembler.get_correlation_energy(level=level, mode="FULL")
            
            assert "pipeline incomplete" in str(exc_info.value).lower()
    
    def test_validation_matrix_exists(self):
        """Test validation_matrix.md exists and has content.
        
        Spec §6.2: Validation Matrix
        """
        matrix_path = self.spec_dir / "validation_matrix.md"
        assert matrix_path.exists(), f"validation_matrix.md not found: {matrix_path}"
        
        with open(matrix_path, 'r') as f:
            content = f.read()
        
        # Verify it mentions all phases (Phase1 through Phase10)
        for phase_num in range(1, 11):
            assert f"Phase{phase_num}" in content, \
                f"validation_matrix.md must mention Phase{phase_num}"
        
        # Verify table structure keywords present
        assert "Verification Method" in content, "Missing 'Verification Method' column"
        assert "Acceptance Criteria" in content, "Missing 'Acceptance Criteria' column"
    
    def test_spec_md_exists(self):
        """Test spec.md exists and has all required sections.
        
        Spec §1-§13: Full specification document
        """
        spec_path = self.spec_dir / "spec.md"
        assert spec_path.exists(), f"spec.md not found: {spec_path}"
        
        with open(spec_path, 'r') as f:
            content = f.read()
        
        # Verify key sections exist
        required_sections = [
            "§1. Scope and Purpose",
            "§2. Pipeline Architecture",
            "§3. Terminology and Definitions",
            "§4. Invariants and Determinism Rules",
            "§5. Error Classes",
            "§6. Contract Testing",
            "§7. Accuracy Targets",
            "§8. Phase List and Deliverables",
            "§9. Log Schema and Metadata",
            "§10. Spec Version and Change Control",
        ]
        
        for section in required_sections:
            assert section in content, f"spec.md missing required section: {section}"
        
        # Verify version is mentioned
        assert "0.1.0" in content, "spec.md must mention version 0.1.0"
    
    def test_error_classes_defined(self):
        """Test that error classes are defined and importable.
        
        Spec §5: Error Classes
        """
        from tangelo.dlpno.energy_assembler import IncompletePipelineError, SpecContractError
        
        # Verify they are Exception subclasses
        assert issubclass(IncompletePipelineError, Exception)
        assert issubclass(SpecContractError, Exception)
        
        # Verify they can be instantiated
        exc1 = IncompletePipelineError("test message")
        exc2 = SpecContractError("test message")
        
        assert str(exc1) == "test message"
        assert str(exc2) == "test message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
