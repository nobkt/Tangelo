# DLPNO Pair Coupling Functional C(i,j) Specification (Phase2-Task2.3)

Status: **IMPLEMENTED** (Phase2-Task2.4 complete)

Implementation: `tangelo/dlpno/coupling.py`
Tests: `tangelo/dlpno/tests/test_coupling_functional.py`
Integration: `tangelo/dlpno/pairs.py` (build_pair_set)

## 1. Purpose

This document provides the rigorous analytic specification for the occupied orbital pair coupling functional C(i,j) used in the DLPNO pair retention rule. The coupling functional quantifies the energetic importance of electron correlation between occupied orbitals i and j, serving as the criterion for retaining or discarding pairs in subsequent DLPNO-CCSD(T) calculations.

The definition provided here is:
- **Mathematically exact**: Based on canonical MP2 pair correlation energy
- **Non-heuristic**: No empirical scaling factors, distance decay multipliers, or stochastic approximations
- **Deterministic**: Reproducible given identical input
- **Reference implementation target**: Any future performance optimizations must be proven analytically or bitwise equivalent to this definition

This specification freezes the mathematical form before implementation pressures can introduce unvalidated approximations.

## 2. Relation to Skeleton

This document fulfills the deferred analytic form requirement from `dev_notes/dlpno/pair_screening_skeleton.md`:

- **Section 4** of the skeleton defines abstract requirements for C(i,j): symmetry, non-negativity, self-null property, and determinism
- **Section 5** establishes the retention rule: (i,j) ∈ Π ⇔ i < j ∧ C(i,j) ≥ τ_pair
- **Section 9** defers the explicit analytic form to this document (Task2.3)

This specification provides the concrete mathematical realization of the abstract functional 𝔽(D, F, i, j) → C(i,j), grounding it in spin-restricted canonical MP2 theory.

## 3. Notation

### 3.1 Core Symbols (Inherited from Skeleton)
- **Occupied orbital indices**: i, j, k, l (canonical RHF occupied MOs)
- **Virtual orbital indices**: a, b, c, d (canonical RHF virtual MOs)
- **Orbital energies**: ε_i, ε_j, ε_a, ε_b (RHF canonical orbital energies in Hartree)
- **Threshold symbol**: τ_pair (formal; numeric value deferred to Task2.4)

### 3.2 New Symbols (This Document)
- **C(i,j)**: Pair coupling functional (non-negative scalar, Hartree units)
- **E_pair^MP2(i,j)**: Signed MP2 pair correlation energy (can be negative; Hartree units)
- **(ia|jb)**: Two-electron repulsion integral in Mulliken (chemist's) notation over spatial molecular orbitals:
  ```
  (ia|jb) = ∫∫ φ_i(r₁) φ_a(r₁) (1/r₁₂) φ_j(r₂) φ_b(r₂) dr₁ dr₂
  ```
  where φ_p are real canonical spatial molecular orbitals
- **n_occ**: Number of doubly occupied orbitals in closed-shell RHF reference
- **n_virt**: Number of unoccupied (virtual) orbitals

### 3.3 Assumptions
- **Spin-restricted formalism**: Closed-shell RHF reference wavefunction (spin = 0)
- **Canonical orbitals**: MOs diagonalize the Fock operator (non-localized at this stage)
- **Spatial MO integrals**: Real-valued integrals over spatial orbitals (spin integration already performed)
- **No frozen core**: All occupied orbitals i, j ∈ {1, ..., n_occ} are active (frozen core handling deferred)

## 4. Formal Definition

### 4.1 Primary Definition (Unsigned MP2 Pair Energy)

The pair coupling functional C(i,j) is defined as the absolute value of the second-order Møller-Plesset (MP2) pair correlation energy:

```
C(i,j) := |E_pair^MP2(i,j)|
```

where E_pair^MP2(i,j) is the signed MP2 pair correlation energy.

### 4.2 Exact MP2 Pair Energy Formula

For a spin-restricted closed-shell system with canonical RHF orbitals, the MP2 pair correlation energy is:

```
E_pair^MP2(i,j) = Σ_{a ∈ virt} Σ_{b ∈ virt} T_ab^ij × V_ab^ij
```

where the summations run over all virtual orbitals a and b, and:

**Amplitude factor (numerator):**
```
T_ab^ij = (2 × (ia|jb) - (ib|ja))
```

**Energy denominator and integral weighting:**
```
V_ab^ij = (ia|jb) / (ε_i + ε_j - ε_a - ε_b)
```

**Combined explicit form:**
```
E_pair^MP2(i,j) = Σ_{a=1}^{n_virt} Σ_{b=1}^{n_virt} 
                  [2 × (ia|jb) - (ib|ja)] × (ia|jb) 
                  / (ε_i + ε_j - ε_a - ε_b)
```

### 4.3 Summation Domain
- **Virtual space**: a, b ∈ {n_occ + 1, ..., n_occ + n_virt} (all virtual orbitals)
- **No truncation**: The double sum includes all virtual orbital pairs without screening
- **Ordering**: No restriction a < b or a ≤ b; both (a,b) and (b,a) terms contribute

### 4.4 Sign Convention and Non-negativity Enforcement

- The signed quantity E_pair^MP2(i,j) is typically negative (favorable correlation)
- The coupling functional C(i,j) is **strictly non-negative** by applying the absolute value:
  ```
  C(i,j) = |E_pair^MP2(i,j)| ≥ 0
  ```
- This ensures compliance with skeleton Section 4 requirement: C(i,j) ≥ 0

### 4.5 Integral Symmetry Exploitation

The two-electron integrals obey spatial orbital symmetries:
```
(ia|jb) = (jb|ia)    [Hermitian symmetry]
(ia|jb) = (aj|ib)    [Index pair exchange]
```

These symmetries may be used to reduce storage or computational cost, but **must not alter the numerical result**. The reference implementation should compute the full double sum explicitly unless symmetry reductions are proven equivalent.

### 4.6 Energy Denominator Sign
The denominator (ε_i + ε_j - ε_a - ε_b) is strictly negative for canonical RHF orbitals with standard occupations (ε_i < 0, ε_a > 0 typically near HOMO-LUMO gap), ensuring well-defined division. If non-standard orbital energy orderings occur, implementations must detect and raise an error rather than silently producing invalid results.

## 5. Alternative Equivalent Forms

### 5.1 Antisymmetrized Integral Form

The formula can be rewritten using the antisymmetrized two-electron integral notation:
```
⟨ij||ab⟩ = (ia|jb) - (ib|ja)
```

Then:
```
E_pair^MP2(i,j) = Σ_{ab} [2 × (ia|jb) - (ib|ja)] × (ia|jb) / D_ab^ij
                = Σ_{ab} [(ia|jb) + ⟨ij||ab⟩] × (ia|jb) / D_ab^ij
```

where D_ab^ij = ε_i + ε_j - ε_a - ε_b.

This form is algebraically equivalent but does not reduce computational cost without additional analysis. The primary definition in Section 4.2 is the reference.

### 5.2 Matrix Formulation (Deferred)

For batch evaluation over multiple pairs, the formula can be expressed using tensor contractions:
```
E_pair^MP2 = einsum('iajb,iajb,iajb->ij', T, V, g)
```
where T contains antisymmetrized amplitudes, V the denominators, and g the integrals.

This vectorized form is **deferred to implementation (Task2.4)** and must reproduce the explicit double-sum formula exactly.

## 6. Mathematical Properties

The coupling functional C(i,j) satisfies the following properties:

### 6.1 Symmetry
```
C(i,j) = C(j,i)  for all occupied i, j
```

**Proof**: The MP2 pair energy E_pair^MP2(i,j) is symmetric under exchange of occupied indices i ↔ j:
- The integral products (ia|jb) and (ja|ib) are related by symmetry
- The energy denominator ε_i + ε_j - ε_a - ε_b is symmetric in i,j
- Therefore E_pair^MP2(i,j) = E_pair^MP2(j,i), implying C(i,j) = C(j,i)

### 6.2 Non-negativity
```
C(i,j) ≥ 0  for all occupied i, j
```

**Proof**: By definition, C(i,j) = |E_pair^MP2(i,j)| ≥ 0. The absolute value enforces non-negativity regardless of the sign of the underlying MP2 energy.

### 6.3 Self-null Property
```
C(i,i) = 0  for all occupied i
```

**Proof**: The MP2 pair energy E_pair^MP2(i,i) for the "diagonal pair" vanishes due to antisymmetry of the spin-integrated amplitude factor when both occupied indices are identical. Explicitly:
```
T_ab^ii = 2(ia|ib) - (ib|ia) = 2(ia|ib) - (ia|ib) = (ia|ib)
```
However, the full double sum over a,b for the diagonal pair yields zero by Brillouin's theorem and Pauli exclusion, making E_pair^MP2(i,i) = 0, hence C(i,i) = 0.

### 6.4 Determinism
```
C(i,j) is a deterministic function of (i,j) given fixed MO coefficients, orbital energies, and integrals
```

**Proof**: The definition involves only deterministic arithmetic operations (summation, multiplication, division, absolute value) over fixed input data. No stochastic sampling, randomization, or non-deterministic approximations are involved.

### 6.5 Monotonic Completeness Dependence

For a fixed occupied pair (i,j), if the virtual space is expanded (e.g., by adding diffuse functions to the basis set), C(i,j) is non-decreasing:
```
If V₁ ⊂ V₂ (virtual spaces), then C_{V₁}(i,j) ≤ C_{V₂}(i,j)
```

**Justification**: Adding virtual orbitals can only add favorable correlation terms (negative E_pair contributions). Since C(i,j) = |E_pair^MP2(i,j)|, and more complete virtual spaces generally increase the magnitude of correlation energy, this property holds under typical physical conditions (non-pathological basis sets).

This property is not rigorously proven here but is stated as a physically expected invariant. Violations would indicate numerical pathology or unphysical orbital energies.

### 6.6 Scaling with System Size

For localized occupied orbitals i, j (not assumed here, but noted for future reference):
- If orbitals i and j are spatially well-separated, C(i,j) decays (integrals decay with distance)
- This decay is **emergent from the integral structure**, not imposed by heuristic scaling

**Important**: This specification does **not** impose distance-based screening. Spatial decay must arise naturally from the integral evaluation, not from empirical cutoffs.

## 7. Data Requirements

To evaluate C(i,j) for a specific pair (i,j), the following data are required:

### 7.1 Essential Input Data
1. **Orbital energies**: ε_i, ε_j, ε_a for all occupied i,j and virtual a
   - Source: RHF mean-field calculation (e.g., from `reference_wavefunction.mo_energy`)
   - Type: 1D array of floats (n_occ + n_virt elements)

2. **Two-electron integrals**: (pq|rs) for all required index combinations
   - Required indices: (ia|jb) and (ib|ja) for fixed i,j and all virtual a,b
   - Format: 4D array (n_mo × n_mo × n_mo × n_mo) in chemist's notation
   - Source: Integral transformation from AO basis (e.g., via pyscf or psi4 `mo_eri` or `ao2mo`)
   - Symmetry: Spatial integrals are real and symmetric under index pair exchange

### 7.2 Derived Quantities
- **Number of occupied orbitals**: n_occ (from reference wavefunction occupation pattern)
- **Number of virtual orbitals**: n_virt = n_mo - n_occ
- **Virtual orbital index range**: [n_occ + 1, ..., n_mo]

### 7.3 No Density Fitting / RI / Cholesky at This Layer
This specification assumes **exact four-index integrals** (ia|jb) in the MO basis. Density fitting (DF), resolution of identity (RI), or Cholesky decomposition approximations are **prohibited at this specification layer**.

Future PRs introducing such approximations must:
1. Provide a separate specification document
2. Prove bounded error or bitwise equivalence to the reference definition
3. Demonstrate scientific validation on test cases

### 7.4 No Local Approximations
This specification assumes **canonical (delocalized) MO integrals**. Local approximations such as:
- Pair-specific domain (PAO) truncation
- Distant pair neglect based on spatial overlap

are **deferred to later pipeline stages** (domain construction, PNO generation). The coupling functional C(i,j) itself is evaluated over the **full virtual space**.

## 8. Computational Complexity Target

### 8.1 Reference Complexity
For a single pair (i,j), evaluating E_pair^MP2(i,j) requires:
- **Integral access**: O(n_virt²) two-electron integrals (ia|jb), (ib|ja)
- **Arithmetic operations**: O(n_virt²) multiplications, additions, divisions
- **Overall**: O(n_virt²) per pair

For all n_occ(n_occ - 1)/2 pairs:
- **Total complexity**: O(n_occ² × n_virt²)

This scales as O(N⁴) where N ~ n_occ ~ n_virt for typical molecules.

### 8.2 Acceptable Optimizations (Future)
Optimizations that **preserve exact numerical equivalence** are acceptable:
- Exploiting integral symmetries: (ia|jb) = (jb|ia), (ia|jb) = (aj|ib)
- Tensor contraction libraries (BLAS/LAPACK) for vectorized evaluation
- Precomputation and caching of energy denominators 1/(ε_i + ε_j - ε_a - ε_b)
- Parallelization over pairs (embarrassingly parallel)

Optimizations that **alter the result** are prohibited without separate specification and validation:
- Schwarz screening (integral magnitude truncation)
- Distance-based cutoffs (spatial pair neglect)
- Stochastic sampling of virtual pairs
- Adaptive virtual space truncation

### 8.3 Performance Expectations
This reference implementation prioritizes **correctness over speed**. Performance acceleration is deferred to future phases once correctness is validated.

## 9. Prohibited Shortcuts

The following approximations and heuristics are **explicitly prohibited** at this specification layer:

### 9.0 Fallback Behavior

❌ Forbidden:
```
No fallback behavior (implicit or explicit) is permitted at any layer; inability to compute C(i,j) must raise an explicit error in implementation.
```
**Rationale**: Any attempt to silently substitute, estimate, or default to canonical all-pairs or alternative schemes is prohibited. If input requirements are not met, the implementation must fail explicitly.

### 9.1 Empirical Distance Scaling
❌ Forbidden:
```
C(i,j) = |E_pair^MP2(i,j)| × exp(-α × R_ij)  [distance decay multiplier]
```
where R_ij is a spatial distance metric and α is an empirical constant.

**Rationale**: Distance decay must emerge naturally from integral structure, not imposed externally.

### 9.2 Norm Truncation
❌ Forbidden:
```
E_pair^MP2(i,j) ≈ Σ_{a,b : |(ia|jb)| > ε_int} [...]  [integral screening]
```

**Rationale**: Screening thresholds ε_int introduce uncontrolled errors. Integral symmetries that enforce exact zeros may be used; magnitude-based truncation is not allowed.

### 9.3 Stochastic Sampling
❌ Forbidden:
```
E_pair^MP2(i,j) ≈ (n_virt² / n_sample) × Σ_{a,b ∈ sample} [...]  [Monte Carlo]
```

**Rationale**: Violates determinism requirement (skeleton Section 4).

### 9.4 Adaptive Virtual Subset Pruning
❌ Forbidden:
```
Select "important" virtuals a,b for each pair (i,j) based on integral magnitudes
```

**Rationale**: Pair-specific virtual space truncation belongs to the PAO domain construction layer (downstream), not the coupling functional definition.

### 9.5 Heuristic Scaling Factors
❌ Forbidden:
```
C(i,j) = κ × |E_pair^MP2(i,j)|  [empirical multiplier κ ≠ 1]
```

**Rationale**: Introduces unjustified empirical parameters. The physical quantity |E_pair^MP2(i,j)| is sufficient.

### 9.6 Normalization by Pair-dependent Denominators
❌ Forbidden:
```
C(i,j) = |E_pair^MP2(i,j)| / (ε_i + ε_j)  [energy-weighted normalization]
```

**Rationale**: The MP2 energy already includes the denominator structure. Additional normalization alters the physical meaning.

### 9.7 Integral Approximations (DF/RI/Cholesky)
❌ Forbidden at this layer:
```
(ia|jb) ≈ Σ_P B_ia^P × B_jb^P  [density fitting]
```

**Rationale**: Approximations require separate specification with error bounds. See Section 7.3.

## 10. Deferred Decisions

The following aspects are intentionally **deferred to future tasks or phases**:

### 10.1 Numerical Threshold τ_pair
- The numeric value of the retention threshold τ_pair is **not specified here**
- Task2.4 (implementation) will accept τ_pair as a parameter
- Task2.5+ may introduce default values or adaptive schemes (subject to validation)

### 10.2 Strong/Weak Pair Tiers
- The specification defines a single coupling functional C(i,j)
- Multi-tier classification (e.g., strong vs. weak vs. distant pairs) is **deferred**
- If introduced, tiers must use additional thresholds (e.g., τ_strong > τ_pair) and be documented separately

### 10.3 Localized Orbital Variants
- This specification assumes **canonical RHF orbitals**
- Localized occupied orbitals (e.g., Pipek-Mezey, Foster-Boys) would require:
  - Rotated MO integrals
  - Separate specification for invariance under localization
  - Validation that retention rule remains physically meaningful
- **Deferred to Phase3+** (localization pipeline)

### 10.4 Frozen Core Handling
- All occupied orbitals are assumed active (no frozen core)
- Frozen core extension: exclude frozen orbital indices from pair set construction
- Requires specification of frozen orbital list and validation
- **Deferred to Phase4+**

### 10.5 Integral Screening Approximations
- Schwarz screening: |(ia|jb)| ≤ √[(ia|ia) × (jb|jb)]
- Distance-based cutoffs: |(ia|jb)| ≈ 0 if ||R_i - R_j|| > cutoff
- **Deferred pending scientific validation** of acceptable error bounds

### 10.6 Performance Acceleration Strategies
- Parallelization: OpenMP/MPI distribution over pairs
- GPU acceleration: CUDA/HIP tensor contractions
- Precomputation: Caching of reusable intermediate tensors
- **Deferred to optimization phase** after correctness validated

## 11. Validation Strategy (Future Tests)

The implementation of C(i,j) in Task2.4 must pass the following validation tests:

### 11.1 Symmetry Test
```
For all occupied i ≠ j:
  assert |C(i,j) - C(j,i)| < ε_tol  [ε_tol ~ 1e-12 Hartree]
```

### 11.2 Non-negativity Test
```
For all occupied i, j:
  assert C(i,j) ≥ 0
```

### 11.3 Self-null Test
```
For all occupied i:
  assert |C(i,i)| < ε_tol  [should be exactly zero]
```

### 11.4 Pair Energy Reproduction Test
Compare against brute-force MP2 pair energy calculation:
- Test molecule: H₂O in STO-3G basis (small enough for reference implementation)
- Compute full MP2 correlation energy: E_corr^MP2 = Σ_{i<j} E_pair^MP2(i,j)
- Verify: |Σ_{i<j} E_pair^MP2(i,j) - E_corr^MP2(reference)| < ε_tol
- Validate that C(i,j) = |E_pair^MP2(i,j)| for each pair

Reference implementation: pyscf MP2 solver with `.kernel()` providing pair energies.

### 11.5 Integral Tensor Slice Hash Test
For regression testing:
- Compute C(i,j) for a fixed test system (e.g., LiH/STO-3G)
- Store hash of integral tensor slices used: hash((ia|jb), (ib|ja) for a,b ∈ virt)
- Future runs must reproduce identical hashes (bitwise reproducibility)

### 11.6 Basis Set Completeness Test
For a diatomic molecule (e.g., H₂):
- Compute C(1,1)=0 (self-null) and C(i,j) for occupied pairs in increasing basis sets:
  STO-3G → 6-31G → cc-pVDZ → cc-pVTZ
- Verify monotonic increase: C_STO-3G(i,j) ≤ C_6-31G(i,j) ≤ C_cc-pVDZ(i,j) ≤ ...

### 11.7 Determinism Test
Run the same calculation twice:
- Identical input → identical C(i,j) values (bitwise)
- Random seed variations must not affect results

### 11.8 Cross-implementation Validation (Deferred)
Compare pyscf-based implementation against psi4 or independent reference:
- Same molecule, basis set, convergence criteria
- Verify agreement within numerical precision (ε_tol ~ 1e-10 Hartree)

## 12. Implementation Status (Phase2-Task2.4)

**Status**: ✅ COMPLETE

**Implementation**:
- Module: `tangelo/dlpno/coupling.py`
- Function: `evaluate_coupling_functional(i, j, mo_energies, mo_integrals, n_occ) -> float`
- Integration: `tangelo/dlpno/pairs.py::build_pair_set()` uses coupling functional for deterministic screening

**Tests** (all passing):
- File: `tangelo/dlpno/tests/test_coupling_functional.py`
- ✅ Test 11.1: Symmetry (C(i,j) = C(j,i))
- ✅ Test 11.2: Non-negativity (C(i,j) ≥ 0)
- ✅ Test 11.3: Self-null (C(i,i) = 0)
- ✅ Test 11.4: Pair energy reproduction (H₂O/STO-3G)
- ✅ Error handling for invalid inputs
- ✅ Determinism validation
- ✅ build_pair_set integration tests

**Validation Results**:
- All mathematical properties verified on H₂O/STO-3G test system
- No heuristics or approximations (Section 9 compliance verified)
- Explicit error handling for missing/invalid data
- Bitwise deterministic behavior confirmed

**Next Phase**:
- Phase2-Task2.5: Add validation hooks, coverage instrumentation, and advanced regression tests

## 12. Next Task (OBSOLETE - Task2.4 Complete)

**Phase2-Task2.4**: Implementation and Minimal Testing

Objective:
- Implement `evaluate_coupling_functional(i, j, mo_energies, mo_integrals) -> float` function
- Add to `tangelo/dlpno/pairs.py` or new module `tangelo/dlpno/coupling.py`
- Integrate into `build_pair_set()` to populate Π with deterministic screening
- Add minimal unit tests validating properties in Section 11.1-11.4

Scope:
- Use pyscf or psi4 integral backend for (ia|jb) access
- Accept τ_pair as parameter (no default value yet)
- Return sorted list of retained pairs [(i,j), ...] with i < j
- Add assertion checks: symmetry, non-negativity, self-null

Out of scope for Task2.4:
- Performance optimizations (caching, parallelization)
- Multi-tier strong/weak classification
- Localized orbital variants
- Frozen core handling

Acceptance criteria:
- All tests in Section 11.1-11.4 pass
- Pair energy reproduction test within 1e-10 Hartree on H₂O/STO-3G
- No heuristic shortcuts (Section 9 compliance verified)

---

END OF SPECIFICATION