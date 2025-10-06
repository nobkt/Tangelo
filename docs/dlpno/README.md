# DLPNO-CCSD(T) Scaffolding

This directory contains the initial scaffolding for a future DLPNO-CCSD(T) (Domain‑based Local Pair Natural Orbital Coupled Cluster with Singles, Doubles, and perturbative Triples) implementation in Tangelo.

> Status: Framework only. No integral handling, pair enumeration, PNO construction, CC amplitude equations, energy evaluation, or localization algorithms are implemented yet.

---

## 1. Introduction

DLPNO-CCSD(T) provides (near) linear-scaling approximations to canonical CCSD(T) by exploiting locality and truncating pair natural orbital (PNO) spaces. This scaffolding establishes a deterministic, testable foundation so that future algorithmic layers (classical and quantum‑assisted) can be added incrementally with clear convergence and reproducibility guarantees.

---

## 2. Design Goals

- **Determinism**: All default parameter sequences are explicitly enumerated; no hidden heuristics.
- **Systematic Convergence Path**: Threshold sequences (PNO / pair) enable staged refinement and controlled extrapolation.
- **Minimal Import Footprint**: No heavy dependencies (e.g. PySCF) pulled until genuinely required.
- **Separation of Concerns**: Configuration, data structures, convergence monitoring, path utilities, and logging kept orthogonal.
- **Future Quantum Integration**: Data model organized so that localized spaces / truncated subspaces can map to quantum ansatz / resource estimation workflows.
- **Testability**: Every module has a pure-Python interface with low side effects, enabling isolated unit testing.
- **Traceability**: Each architectural element linked to Issue references for evolution tracking.
- **Reproducibility**: Random seed constant surfaced (even if not yet used) to normalize future stochastic steps (e.g., screening order or randomized localization variants).

---

## 3. Module Overview

| Module | Purpose | Key Exports / Notes |
| ------ | ------- | ------------------- |
| `config.py` | Fixed deterministic threshold sequences, energy tolerances, import-time strict monotonic validation. | `PNO_TAU_SEQUENCE_DEFAULT`, `PAIR_TAU_SEQUENCE_DEFAULT`, tolerances, `validate_monotonic` |
| `structures.py` | Lightweight dataclasses representing orbital spaces, parameter bundles, convergence records. | `OrbitalSpace`, `PNOParameters`, `ConvergenceCriteria`, `ConvergenceRecord`, `default_pno_parameters` |
| `convergence.py` | Stateful but isolated convergence monitor tracking energy / residual evolution. | `ConvergenceMonitor` |
| `paths.py` | Pure string/path helpers for canonical pair keys and iteration directories. | `pair_key`, `pair_cache_dir`, `run_iteration_dir` |
| `logging_utils.py` | Local logger initialization with optional JSON formatter (no global config pollution). | `init_dlpno_logger` |
| `localization/adapter.py` | Placeholder API for orbital localization (Boys / Pipek–Mezey) with NotImplementedError. | `list_supported_methods`, `get_localized_orbitals` |
| `__init__.py` | Re-export curated public surface (no side effects). | See “Public API” below |

**Public API Surface (re-exported in `tangelo.dlpno`):**
```
PNO_TAU_SEQUENCE_DEFAULT
PAIR_TAU_SEQUENCE_DEFAULT
ENERGY_ABS_TOL_DEFAULT
ENERGY_REL_TOL_DEFAULT
OrbitalSpace
PNOParameters
ConvergenceCriteria
ConvergenceRecord
default_pno_parameters
ConvergenceMonitor
build_pair_set
OccupiedPair
PairSet
evaluate_coupling_functional
```

---

## 4. Current Scope (Implemented)

- Deterministic configuration constants with strict monotonic validation
- Dataclasses (no coupled-cluster mathematics)
- Convergence monitoring logic with absolute + relative + residual criteria
- **Pair coupling functional C(i,j) = |E_pair^MP2(i,j)| (Phase2-Task2.4)**
- **Deterministic pair screening using coupling functional**
- Path / naming helpers (pair keys, iteration directories)
- Lightweight logging initializer (plain or JSON)
- Placeholder localization adapter interface
- Unit tests covering:
  - Configuration validation & defaults
  - Dataclass instantiation & independence of default lists
  - ConvergenceMonitor basic and edge-case behavior (NaN / inf)
  - **Coupling functional properties (symmetry, non-negativity, self-null)**
  - **Pair energy reproduction (H₂O/STO-3G validation)**
  - **build_pair_set integration and error handling**
  - Path formatting and normalization
  - Logging handler non-duplication and JSON formatting
  - Localization adapter placeholder behavior
  - Package export integrity

---

## 5. Out of Scope (Explicitly NOT Implemented Yet)

- ~~Pair detection / domain construction~~ (Pair screening implemented; domain construction deferred)
- PNO generation / truncation logic
- CCSD amplitude iterations or residual evaluations
- (T) perturbative triples correction
- Integral transformation / density fitting pipelines
- Orbital localization algorithms (Boys / Pipek–Mezey integration with PySCF)
- Extrapolation strategies (beyond constant placeholders)
- Any GPU / distributed execution layers
- Quantum embedding / active-space reduction mapping

---

## 6. Future Work Roadmap

Planned incremental layers (tentative order):

1. ~~Pair list generation & domain screening primitives~~ ✅ **COMPLETE (Phase2-Task2.4)**
2. Orbital localization backend integration (PySCF) and validation
3. Virtual space partitioning & PNO construction
4. CCSD amplitude build skeleton (T1/T2 residual placeholders → full kernels)
5. Energy accumulation & incremental extrapolation harness
6. (T) correction integration (semi-canonical / localized variants)
7. Adaptive threshold refinement & automated convergence driver
8. Resource / scaling instrumentation (timings, FLOP / memory estimates)
9. Quantum mapping hooks (selection of localized active subspaces)
10. Robust I/O & checkpointing (pair caches, intermediate amplitude storage)

---

## 7. Design Notes & Rationale

- **Strict monotonic sequences** ensure unambiguous extrapolation windows.
- **Pure functions for path/key generation** avoid hidden state and simplify downstream caching layers.
- **JSON logging option** facilitates structured telemetry ingestion (future performance dashboards).
- **Placeholder localization** defers heavy imports, improving cold-start of unrelated Tangelo features.

---

## 8. Issue Traceability

Originating discussion and acceptance criteria:  
- Issue #1 (Initial DLPNO-CCSD(T) scaffolding)  
  - URL: https://github.com/nobkt/Tangelo/issues/1

Subsequent enhancements will reference this scaffold Issue in their descriptions for lineage tracking.

---

## 9. Testing & Validation

Run only DLPNO-related tests:
```
pytest -k dlpno
```

Key acceptance checks:
- Import-time validation raises on non-monotonic sequences.
- ConvergenceMonitor deterministic across repeated runs.
- No unexpected stdout/stderr on module imports.
- Logging JSON output parseable and handler count stable.
- Public API re-exports remain stable (guarded by test script).

---

## 10. Contributing Guidelines (Scaffold Phase)

When adding future logic:
- Avoid implicit heuristics; surface parameters explicitly in `config.py`.
- Extend tests concurrently with new modules (no untested growth).
- Keep localization integrations optional (lazy import patterns).
- Update this README’s Future Work and Issue Traceability sections.

---

## 11. Regression Validation (Phase2-Task2.5)

### 11.1 Reference Dataset

A reference regression dataset is maintained at `tests/data/dlpno_coupling_reference.json` containing baseline C(i,j) coupling functional values and total MP2 correlation energies for small molecules:

- **Molecules**: H2, H2O, LiH, NH3 (all in STO-3G basis)
- **Data Stored**: Upper-triangular C(i,j) values, total signed MP2 pair correlation energy, SHA256 regression hash
- **Purpose**: Protect against unintended semantic changes from future performance optimizations, refactoring, or dependency updates

### 11.2 Validation Guarantees

The test suite provides the following correctness guarantees:

1. **Value Accuracy**: Computed C(i,j) values match reference within 1e-12 Hartree tolerance
2. **Hash Integrity**: SHA256 hash of concatenated double-precision C(i,j) bytes validates bitwise reproducibility (warns on mismatch due to PySCF non-determinism)
3. **Denominator Safety**: Artificial non-positive energy denominator triggers ValueError with required error signature
4. **Seed Invariance**: Results are independent of numpy random state
5. **Basis Monotonicity**: Weak monotonic increase of C(i,j) with virtual space expansion (STO-3G → 6-31G)

### 11.3 Test Organization

Tests are organized by concern:

- `tests/dlpno/test_coupling_core.py`: Fundamental mathematical properties (symmetry, non-negativity, self-null, determinism)
- `tests/dlpno/test_coupling_regression.py`: Reference dataset comparison, hash validation, denominator safety
- `tests/dlpno/test_coupling_screening.py`: Pair screening threshold behavior, error handling
- `tests/dlpno/test_coupling_monotonicity.py`: Basis set expansion monotonicity checks

Shared utilities are in `tests/dlpno/util_coupling.py` (compute_c_matrix, compute_signed_pair_energy, load_reference_dataset).

### 11.4 Coverage Instrumentation

Coverage configuration is available in `pyproject.toml`:

```bash
# Run tests with coverage
pytest --cov=tangelo.dlpno --cov-report=term-missing

# Run only DLPNO tests with coverage
pytest tests/dlpno/ --cov=tangelo.dlpno --cov-report=html
```

Target: `tangelo/dlpno` module with branch coverage enabled.

### 11.5 Regenerating Reference Data

If algorithmic changes require updating the baseline (e.g., integral convention change):

1. Update the generation script logic
2. Regenerate reference data with the updated script
3. Verify all tests pass with new baseline
4. Document the change in commit message and spec

**Important**: Reference data updates must be deliberate and documented. Accidental changes will be caught by CI.

---

## 12. Disclaimer

This scaffold does not perform any quantum chemistry calculations yet. It is a structural and testing foundation only.

---