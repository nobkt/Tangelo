# DLPNO Pair Screening Skeleton (Phase2-Task2.1)
Status: Draft (formalism only, no numeric thresholds or implementation)

## 1. Purpose
Define the formal retention rule for occupied orbital pairs (i,j) used in the DLPNO-CCSD(T) pipeline without introducing heuristic shortcuts or empirical adjustments. This fixes notation and invariants before any API or algorithmic code is added.

## 2. Notation
- Occupied orbitals: i, j, k, l
- Canonical virtual orbitals: a, b
- Pair: (i,j) with ordering convention i < j in stored form; (i,j) ≡ (j,i)
- Retained pair set: Π
- Discarded pair set: Π̄
- Coupling functional placeholder: C(i,j)
- Threshold symbol (formal only): τ_pair (no numeric value here)
- Optional classification placeholder: τ_strong (present for future stratification if rigorously justified)
- Distance / metric placeholder: R(i,j) (not yet defined or required)

## 3. Inputs (Abstract)
- RHF reference: MO coefficients C, orbital energies ε, occupation pattern
- Access abstraction to required one-/two-electron information (details deferred)
- Precomputed matrices (Fock F, density D) as potential arguments to the coupling functional

## 4. Formal Coupling Functional Requirements
Define C(i,j) = 𝔽(D, F, i, j) subject to:
1. Symmetry: C(i,j) = C(j,i)
2. Non-negativity: C(i,j) ≥ 0
3. Self-null: C(i,i) = 0
4. Deterministic: no stochastic elements
(The explicit analytic form of 𝔽 is deferred.)

## 5. Retention Rule (Formal)
A pair is retained iff:
  (i,j) ∈ Π  ⇔  i < j ∧ C(i,j) ≥ τ_pair
All candidate pairs with i < j are evaluated exactly once. No adaptive relaxation of τ_pair is permitted.

## 6. Output
- Π: Deterministically ordered list (lexicographic by i then j) of retained pairs
- Derived metadata (later): |Π| and coverage fraction |Π| / (n_occ (n_occ - 1) / 2)

## 7. Invariants
- Symmetry by construction (only store i<j)
- Idempotence: Re-running on identical RHF input yields identical Π
- Monotonicity: Lowering τ_pair (when numerical values are later introduced) can only increase |Π|
- No hidden fallback to canonical all-pairs; inability to compute C(i,j) must raise

## 8. Prohibited
- Empirical distance scaling of C(i,j) without formal derivation
- Dynamic auto-relaxation or iterative lowering of τ_pair
- Random/stochastic sampling eliminating candidate pairs
- Silent switch to full canonical pair set without explicit user action

## 9. Deferred (Future PRs)
- Explicit analytic form of C(i,j)
- Numerical assignment of τ_pair (and possible τ_strong)
- Strong/weak tier classification policy
- Performance / spatial acceleration structures (screening indexes, neighbor lists)

## 10. Validation Hooks (Planned)
- `assert_symmetry(Π)`
- `recompute_and_diff(Π, input)` expecting zero differences
- `coverage_stats()` reporting |Π| fraction
- (Later correlation analysis) instrumentation only, not heuristic gating

## 11. Downstream Dependencies
Π feeds:
1. Domain construction per retained pair
2. PNO generation per pair domain
3. Local CCSD amplitude equation assembly scope

## 12. Next Step (Phase2-Task2.2)
Create API stub: `tangelo/dlpno/pairs.py` with function placeholder `build_pair_set(reference_wavefunction, threshold_symbol="τ_pair")` referencing this document.

END
