# DLPNO-CCSD(T) Formal Specification

**Version:** 0.1.0  
**Status:** Baseline (Phase1)  
**Last Updated:** 2025-01-01

---

## §1. Scope and Purpose

This specification defines the contractual baseline for the DLPNO-CCSD(T) (Domain-based Local Pair Natural Orbital Coupled Cluster with Singles, Doubles, and perturbative Triples) implementation in Tangelo.

### 1.1 Objectives
- Establish immutable vocabulary and invariants for subsequent implementation phases (Phase2–Phase10)
- Define pipeline stages, data flow, and completeness conditions
- Specify determinism rules, error classes, and accuracy targets
- Prevent rework by freezing structural contracts before algorithmic kernel development

### 1.2 Out of Scope
- Algorithmic implementations (reserved for Phase2–Phase10)
- Performance optimization strategies
- Threshold value tuning (beyond placeholder defaults)
- Canonical reference computation scripts

---

## §2. Pipeline Architecture

### 2.1 Pipeline Stages

The DLPNO-CCSD(T) pipeline consists of the following sequential stages:

1. **Localization** (Phase2): Transform canonical MOs to localized MOs (LMOs)
2. **Pair Detection** (Phase3): Identify significant electron pairs and construct domains
3. **MP2 Pair Densities** (Phase4): Compute MP2 pair correlation densities
4. **PNO Construction** (Phase4): Generate and truncate pair natural orbitals
5. **MP2 Validation** (Phase5): Verify local MP2 energy vs canonical reference
6. **CCSD Iteration** (Phase6): Solve CCSD amplitude equations in local basis
7. **CCSD Validation** (Phase7): Benchmark CCSD accuracy
8. **Triples Correction** (Phase8): Compute (T) perturbative triples contribution
9. **Energy Assembly** (Phases 4–8): Aggregate correlation energy components
10. **Threshold Profiling** (Phase9): Finalize threshold sequences
11. **Reproducibility** (Phase10): Ensure deterministic results and metadata completeness

### 2.2 Pipeline Completeness Conditions

An energy calculation is **complete** if and only if all of the following flags are true:

```python
pipeline_flags = {
    "localization_complete": bool,
    "pairs_detected": bool,
    "pno_constructed": bool,
    "mp2_converged": bool,
    "ccsd_converged": bool,
    "triples_computed": bool,
}
```

**Phase1 Status:** All flags default to `False`. No partial energy emission is permitted until explicitly enabled in future phases.

---

## §3. Terminology and Definitions

### 3.1 Orbital Spaces
- **Canonical MOs:** Molecular orbitals from self-consistent field (SCF) calculation
- **Localized MOs (LMOs):** Spatially localized orbitals via Boys, Pipek–Mezey, or similar
- **Pair Natural Orbitals (PNOs):** Truncated natural orbitals of pair correlation density
- **Projected Atomic Orbitals (PAOs):** Virtual space basis for domain construction

### 3.2 Pairs and Domains
- **Pair (i,j):** Electron pair formed by occupied orbitals i and j (i < j always)
- **Domain [ij]:** Reduced orbital subspace for pair (i,j) after truncation
- **Strong Pair:** Pair with estimated correlation energy exceeding T_CutPairs
- **Weak Pair:** Pair below T_CutPairs threshold (treated with MP2 or neglected)

### 3.3 Thresholds (see spec/thresholds.yaml)
- **T_CutPairs:** Pair energy cutoff for strong/weak classification
- **T_CutPNO:** PNO truncation threshold (eigenvalue-based)
- **T_CutDO:** Distant orbital removal threshold
- **T_CutResid:** Residual norm convergence threshold for CCSD
- **MaxIter_CCSD:** Maximum CCSD iterations
- **DIIS_Start:** Iteration to enable DIIS extrapolation
- **DIIS_Keep:** Number of DIIS vectors to retain

---

## §4. Invariants and Determinism Rules

### 4.1 Pair Ordering Invariant
**Rule:** Pairs are always indexed with i < j.  
**Rationale:** Eliminates ambiguity in pair key generation and storage.  
**Implementation:** `pair_key(i, j)` function enforces i < j via swap if needed.

### 4.2 Localization Ordering Determinism (Phase2)
**Placeholder:** Localization algorithm must produce deterministic orbital ordering given:
- Fixed input geometry and basis
- Fixed random seed (DEFAULT_RANDOM_SEED)
- Specified localization method (Boys, Pipek–Mezey, etc.)

### 4.3 PNO Eigenvalue Sorting (Phase4)
**Rule:** PNO eigenvalues sorted in descending order.  
**Tie-breaking:** If eigenvalues are numerically equal (within tolerance), sort by MO index (ascending).  
**Rationale:** Ensures reproducible truncation decisions.

### 4.4 DIIS Determinism (Phase6)
**Placeholder:** DIIS extrapolation must use fixed vector ordering and orthogonalization procedure.  
**Future Work:** Specify QR vs Gram–Schmidt choice and numerical tolerance.

### 4.5 Floating-Point Reproducibility
**Requirement:** All matrix operations must produce bitwise-identical results given:
- Same compiler and BLAS/LAPACK version
- Same random seed
- Same threshold values
- Same input geometry and basis

---

## §5. Error Classes

### 5.1 IncompletePipelineError
**Raised when:** User attempts to retrieve final energy before pipeline completion.  
**Spec Reference:** §2.2 (Pipeline Completeness Conditions)  
**Phase1 Behavior:** Always raised by EnergyAssembler (no partial energies allowed).

### 5.2 SpecContractError
**Reserved for:** Future CI contract violations (e.g., monotonic threshold violation, schema mismatch).  
**Spec Reference:** §6 (Contract Testing)  
**Phase1 Behavior:** Not yet raised; defined for forward compatibility.

### 5.3 Future Error Classes (Placeholders)
- **ConvergenceFailureError:** CCSD/MP2 fails to converge within MaxIter
- **ThresholdViolationError:** User-provided threshold violates monotonicity
- **LocalizationError:** Localization algorithm fails or produces non-orthogonal orbitals

---

## §6. Contract Testing

### 6.1 Test Categories
1. **Threshold Integrity:** Validate thresholds.yaml structure, types, monotonicity constraints
2. **Schema Compliance:** Ensure log_schema.json is valid JSON Schema draft 2020-12
3. **Assembler Guard:** Verify EnergyAssembler raises IncompletePipelineError in all FULL modes
4. **SPEC_VERSION Accessibility:** Confirm `from tangelo.dlpno.spec_version import SPEC_VERSION` succeeds

### 6.2 Validation Matrix
See `spec/validation_matrix.md` for detailed phase-by-phase verification table.

---

## §7. Accuracy Targets

### 7.1 MP2 Accuracy (Phase5)
**Target:** Local MP2 within 0.1 kcal/mol of canonical MP2 (default thresholds)  
**Benchmark Systems:** H₂O, N₂, small peptides

### 7.2 CCSD Accuracy (Phase7)
**Target:** Local CCSD within 0.5 kcal/mol of canonical CCSD (default thresholds)  
**Benchmark Systems:** H₂O, N₂, ethene

### 7.3 CCSD(T) Accuracy (Phase8)
**Target:** Local CCSD(T) within 1.0 kcal/mol of canonical CCSD(T) (default thresholds)  
**Benchmark Systems:** H₂O, benzene, alanine tripeptide

### 7.4 Reproducibility Tolerance
**Target:** Bitwise-identical energies across repeated runs on same platform  
**Fallback:** Numerical agreement within 1.0e-10 Eh for cross-platform validation

---

## §8. Phase List and Deliverables

| Phase | Deliverable | Spec Reference |
|-------|-------------|----------------|
| Phase1 | Formal spec, thresholds, schema, assembler guard | §1–§7 |
| Phase2 | Deterministic localization integration | §4.2 |
| Phase3 | Pair detection and domain builder | §3.2 |
| Phase4 | MP2 pair density and PNO truncation | §3.1, §4.3 |
| Phase5 | Local MP2 validation | §7.1 |
| Phase6 | CCSD kernel | §4.4 |
| Phase7 | CCSD accuracy benchmarking | §7.2 |
| Phase8 | (T) triples module | §7.3 |
| Phase9 | Threshold profiles freeze | §3.3 |
| Phase10 | Reproducibility and release prep | §7.4 |

---

## §9. Log Schema and Metadata

### 9.1 Required Metadata Fields
See `spec/log_schema.json` for full JSON Schema definition. Minimum required fields:

- `run_uuid`: Unique identifier for this calculation run
- `spec_version`: Version of this specification (0.1.0)
- `git_hash`: Git commit hash of Tangelo codebase
- `thresholds`: Dictionary of threshold values used
- `system`: System identifier (molecule name, basis set, etc.)
- `molecule`: Molecular geometry and charge/spin state
- `stage`: Current pipeline stage (localization, pair_detection, etc.)
- `timestamp_start`: ISO 8601 timestamp of calculation start

### 9.2 Log Validation
All production runs MUST emit logs conforming to log_schema.json.  
CI pipeline SHALL validate log schema compliance (Phase10).

---

## §10. Spec Version and Change Control

### 10.1 Versioning Scheme
**Format:** MAJOR.MINOR.PATCH (Semantic Versioning)  
- **MAJOR:** Breaking changes to pipeline architecture or invariants
- **MINOR:** Backward-compatible additions (new phases, optional features)
- **PATCH:** Bug fixes, clarifications, non-breaking updates

### 10.2 Current Version
**SPEC_VERSION = "0.1.0"** (Phase1 baseline)

### 10.3 Modification Procedure
1. All spec changes require PR with "SPEC CHANGE" label
2. PR description MUST reference affected spec sections (§X.Y)
3. Increment SPEC_VERSION constant in `tangelo/dlpno/spec_version.py`
4. Update `spec/spec.md` "Last Updated" timestamp
5. Add migration notes in CHANGELOG (if breaking change)

---

## §11. Appendix: Threshold Monotonicity Constraints

**Constraint:** Threshold sequences MUST be strictly decreasing (monotonic).  
**Rationale:** Enables systematic extrapolation to complete basis set (CBS) limit.  
**Validation:** Import-time check in `tangelo/dlpno/config.py` raises on violation.

Example:
```python
PNO_TAU_SEQUENCE_DEFAULT = [1.0e-4, 7.0e-5, 5.0e-5, 3.5e-5, 2.5e-5]  # Valid
PAIR_TAU_SEQUENCE_DEFAULT = [1.0e-6, 5.0e-7, 2.0e-7]  # Valid
```

---

## §12. Appendix: Coordinate System Conventions

**Placeholder for Phase2:** Define coordinate system origin, axis orientation, and symmetry handling conventions for localization algorithms.

---

## §13. References

- Neese, F., Wennmohs, F., Hansen, A. (2009). "Efficient and accurate local approximations to coupled-electron pair approaches: An attempt to revive the pair natural orbital method." *J. Chem. Phys.* 130, 114108.
- Riplinger, C., Neese, F. (2013). "An efficient and near linear scaling pair natural orbital based local coupled cluster method." *J. Chem. Phys.* 138, 034106.
- Internal Issue Tracker: https://github.com/nobkt/Tangelo/issues/1

---

**END OF SPECIFICATION v0.1.0**
