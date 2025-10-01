# DLPNO-CCSD(T) Validation Matrix

**Spec Version:** 0.1.0  
**Purpose:** Map each implementation phase to verification methods and acceptance criteria

---

## Validation Matrix

| Phase | Component | Verification Method | Artifact | Acceptance Criteria |
|-------|-----------|---------------------|----------|---------------------|
| **Phase1** | Formal Specification | Manual review + contract tests | `spec/spec.md`, `spec/thresholds.yaml`, `spec/log_schema.json` | All spec sections complete; thresholds.yaml parseable with required keys; log_schema.json valid JSON Schema draft 2020-12 |
| **Phase1** | Spec Version Constant | Import test | `tangelo/dlpno/spec_version.py` | `from tangelo.dlpno.spec_version import SPEC_VERSION` succeeds; value equals "0.1.0" |
| **Phase1** | Energy Assembler Guard | Unit test | `tangelo/dlpno/energy_assembler.py` | `EnergyAssembler` raises `IncompletePipelineError` on any energy request with all pipeline flags False |
| **Phase1** | Threshold Integrity | Contract test | `tests/test_spec_contract.py` | All required threshold keys present; numeric types correct; monotonic sequences validated |
| **Phase1** | Log Schema Validation | Contract test | `tests/test_spec_contract.py` | Synthetic log example validates against schema; schema loads without errors |
| **Phase1** | PR Template | Manual review | `.github/pull_request_template.md` | Template includes spec section reference requirement and "SPEC CHANGE" checkbox |
| | | | | |
| **Phase2** | Deterministic Localization | Unit test + benchmark | Localization module | Boys/PM localization produces identical results across runs with fixed seed; orbital ordering deterministic |
| **Phase2** | Localization Accuracy | Reference comparison | Benchmark calculations | Localized orbitals match PySCF/ORCA reference (overlap matrix > 0.99) |
| **Phase2** | Orthogonality Preservation | Unit test | Localization module | Localized orbital matrix U satisfies U^T U = I within 1e-12 tolerance |
| | | | | |
| **Phase3** | Pair Detection | Unit test | Pair builder module | All pairs (i,j) with i < j generated; strong/weak classification matches threshold |
| **Phase3** | Domain Construction | Reference comparison | Benchmark systems | PAO domains match ORCA reference (>90% overlap for strong pairs) |
| **Phase3** | Pair Ordering | Unit test | Pair builder module | `pair_key(i,j)` always returns `(min(i,j), max(i,j))` |
| | | | | |
| **Phase4** | MP2 Pair Densities | Unit test + canonical ref | MP2 module | Pair densities positive semidefinite; trace equals MP2 natural occupation sum |
| **Phase4** | PNO Truncation | Unit test + reference | PNO module | Eigenvalues sorted descending; truncation at T_CutPNO threshold; tie-breaking by MO index |
| **Phase4** | Domain Completeness | Unit test | PNO module | Sum of discarded PNO occupations < T_CutPNO * n_virtual for each pair |
| | | | | |
| **Phase5** | Local MP2 Energy | Canonical reference | Benchmark calculations | Local MP2 within 0.1 kcal/mol of canonical MP2 for H₂O, N₂ (default thresholds) |
| **Phase5** | Pair Energy Sum | Unit test | MP2 module | Sum of pair MP2 energies equals total local MP2 correlation energy |
| **Phase5** | Threshold Extrapolation | Regression test | Benchmark with multiple thresholds | Energy vs 1/τ linear fit R² > 0.95 for PNO threshold sequence |
| | | | | |
| **Phase6** | CCSD Amplitudes | Unit test + canonical ref | CCSD module | Amplitude updates satisfy CCSD equations (residual < T_CutResid) |
| **Phase6** | DIIS Convergence | Unit test | CCSD module | DIIS accelerates convergence (iteration count reduced by >30% vs no DIIS) |
| **Phase6** | Amplitude Determinism | Reproducibility test | CCSD module | Amplitudes bitwise identical across runs with fixed seed and input |
| | | | | |
| **Phase7** | Local CCSD Energy | Canonical reference | Benchmark calculations | Local CCSD within 0.5 kcal/mol of canonical CCSD for H₂O, N₂, ethene (default thresholds) |
| **Phase7** | Convergence Robustness | Stress test | Difficult systems (stretched bonds) | CCSD converges within MaxIter_CCSD for 95% of test systems |
| **Phase7** | Energy Decomposition | Unit test | CCSD module | CCSD correlation energy equals sum of pair contributions + singles contribution |
| | | | | |
| **Phase8** | Triples Correction | Canonical reference | Benchmark calculations | (T) correction within 10% of canonical (T) for H₂O, benzene |
| **Phase8** | Triples Scaling | Performance test | Systems of varying size | (T) computation time scales as O(N⁴) or better (vs O(N⁷) canonical) |
| **Phase8** | Energy Assembly | Integration test | Full pipeline | Total DLPNO-CCSD(T) energy within 1.0 kcal/mol of canonical CCSD(T) |
| | | | | |
| **Phase9** | Threshold Profiles | Systematic study | 10+ systems, 3+ basis sets | Default thresholds achieve <1 kcal/mol error for 90% of test set |
| **Phase9** | Extrapolation Formula | Regression test | Multiple threshold sequences | CBS-like extrapolation reduces error by >50% vs single-point calculation |
| **Phase9** | Cost-Accuracy Tradeoff | Benchmark analysis | Timing vs accuracy plots | NormalPNO defaults provide best balance (accuracy/time ratio) |
| | | | | |
| **Phase10** | Reproducibility | Cross-platform test | Linux, macOS, Windows | Energies agree within 1e-10 Eh across platforms (same inputs) |
| **Phase10** | Log Schema Compliance | CI validation | All production runs | 100% of logs validate against spec/log_schema.json |
| **Phase10** | Documentation Completeness | Manual review | README, API docs, tutorials | All public APIs documented; tutorial covers H₂O → peptide progression |
| **Phase10** | Release Checklist | Manual review | CHANGELOG, version tags | All Phase1-9 items green; SPEC_VERSION matches release tag |

---

## Notes

1. **Acceptance criteria are binding:** Each phase PR must demonstrate all listed criteria before merge.
2. **Reference data sources:**
   - Canonical CCSD(T): PySCF, ORCA, or Gaussian calculations
   - Localization: PySCF Boys/Pipek-Mezey implementations
   - Threshold profiles: ORCA DLPNO-CCSD(T) benchmarks from Neese group publications
3. **Test data preservation:** Benchmark inputs and reference outputs archived in `tests/data/dlpno_benchmarks/`
4. **CI integration:** Phase5+ tests run nightly (expensive calculations); Phase1-4 tests run on every commit.
5. **Performance regression:** Each phase must not degrade performance of prior phases by >10%.

---

## Verification Workflow

```
┌─────────────────┐
│ Phase PR opened │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Run phase-specific tests│
│ (see Verification col)  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐    NO     ┌──────────────┐
│ All acceptance criteria ├──────────>│ Request fixes│
│ met?                    │           └──────────────┘
└────────┬────────────────┘
         │ YES
         ▼
┌─────────────────────────┐
│ Update validation_matrix│
│ status (green checkmark)│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Merge to main           │
└─────────────────────────┘
```

---

**Last Updated:** 2025-01-01  
**Spec Version:** 0.1.0
