# Audit & Test report — AI-generated logic

**Date:** 2026-10-31 · **Branch:** `feature/harmonic-mean-and-entropy-sign` · **Requirement:** Lab_Project, "Audit & Test:
all AI-generated logic must be backed by unit tests".

**Result in one paragraph.** Before the audit, `src/` had 81% line coverage and `main.py` (the file that
produces every number of the report) had none. Now `src/` has **100%** and `main.py` **99%**, with **147 tests**
(145 checks + 2 `xfail` tests that document known limitations). The audit found **one error in the report**
(a false claim about the numerical range of the log-gamma formula), **one bug in the code** (`sci()` with negative
numbers), **three weak or misleading tests**, and **one decision that the team must take** (the convention for odd N).
Findings are listed in section 2, and what is still open in section 5.

How to reproduce: `python -m pytest -q` (about 15 s). Coverage needs the optional package `pytest-cov`
(`pip install pytest-cov`, not in `environment.yml` on purpose): `python -m pytest -q --cov=src --cov=main
--cov-report=term-missing`.

---

## 1. Method

1. **Inventory and coverage.** Every function of `src/` and `main.py` was listed and compared with the tests that
   exercise it (coverage + reading each test).
2. **Critical reading** of the code and of the tests: edge cases, claims made in docstrings, in the report and in
   `docs/REVIEW_GUIDE.md`, and whether each test could fail if the code were wrong.
3. **Numerical experiments** to check each suspicion before calling it an error.
4. **New tests.** Each one compares the code with an *independent* reference (`math.comb`, `fractions.Fraction`,
   closed formulas), never with the code itself.
5. **Mutation analysis.** 11 bugs were injected one at a time and the whole suite was run (section 4).

## 2. Findings

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| **F1** | Medium | `sci()` (number formatting for the report) is wrong for negative numbers just below a power of ten: `sci(-9.9996e-5)` gave `-10.00\times10^{-5}`. It matters since the ΔS fix made several results negative. | **Fixed** (`abs` in the renormalisation test) + 12 test cases |
| **F2** | **High (report)** | The report said the log-gamma formula "has no limit at all: the unit tests evaluate it at N = 10²³, where it agrees with Stirling's formula to 10⁻¹²". That is false for probabilities: the agreement is only for the dominant term N ln 2 (≈ 7·10²²), the correction −½ ln(πN/2) ≈ −27 is lost. At N = 10²³ the code returns ln P(N/2) = 2·10⁸ instead of −26.7, `log_binom(1e23, 8)` returns 0 instead of 413, and an entropy difference of −0.2 k_B comes out as 0. See the measurements below. | **Report, docstrings and review guide corrected.** Code unchanged (the report already uses the analytic Stirling/Gaussian formulas at N = 10²³). Two `xfail(strict)` tests document the limit |
| **F3** | Medium | `test_popcount_fallback_matches` did not test the fallback: on NumPy ≥ 2 `_popcount` calls `np.bitwise_count`, so the SWAR code for NumPy 1.x (lines 117–121) never ran. A teammate with NumPy 1.x would run untested code. | **Fixed**: the test removes `np.bitwise_count` to force the fallback; also covers extreme values (2⁶³, 2⁶⁴−1) and the full enumeration |
| **F4** | Medium | `test_log_binom_huge_n` used `rel=1e-12` on a value of 7·10²², i.e. it accepted errors of 7·10¹⁰ while the term it claimed to check is 27. It is the test behind F2. | **Replaced** by tests of ln P with an absolute tolerance, for N up to 10¹⁰ |
| **F5** | Low | `test_simulation_consistent_with_exact` checked only the mean. `test_heads_tails_range_symmetry` compared a formula with itself. | **Strengthened**: variance + χ² of the whole distribution; independent exact-fraction check of the tails/heads windows |
| **F6** | Medium | `main.py` (363 statements: all report numbers, figures, tables, team files) had **no tests**. This is how the arithmetic-mean and ΔS-sign errors went unnoticed. | **35 new tests** (`tests/test_main.py`), including a check that the committed `report/results.tex` is not stale |
| **F7** | **Decision** | **Odd N.** With N = 107, "N/2" is 53.5. The code takes ⌊N/2⌋ = 53, so "N/2 ± 10" is k = 43…63 (21 values), P = 0.9572. A window symmetric about 53.5 would be k = 44…63 (20 values), P = 0.9473. By the symmetry Ω(N,k) = Ω(N,N−k), 43…63 and 44…64 give the same number. | **Not changed.** The report states the convention. Ask the professor which one they expect |
| F8 | Low | `log10_prob_fraction` keeps only the leading order of Stirling: alone it returns 0 at x = 1/2 (true value −½ log₁₀(πN/2) = −11.6 at N = 10²³). The code uses it only for *differences*, which is correct. | Docstring warning + test of both facts |
| F9 | Low | `write_authors` does not escape LaTeX special characters (`& % # _ $`). A name or team name containing one would break the compilation. GitHub handles cannot contain them. | **Not changed** (recommendation R3) |
| F10 | Info | `simulate_tosses` builds a `trials × N` int64 matrix (80 MB for 10⁵ × 100). Simulating each coin is more faithful to the physics than `binomial(N, ½)`. | Not changed |
| F11 | Info | The timing study (`run_benchmark`) cannot be unit-tested in seconds: it takes minutes and its numbers depend on the machine. Its logic (data layout, stepping N down when over 5 min) is now tested with stubs. The report's N_max ≈ 36 was measured on one teammate's 16-thread laptop. | Re-measure on the laptop used in the defence |
| F12 | Info | The memory column for the generator is measured at N = 16 (`probe = …enumeration(min(n, 16))`). That is fine because the generator is O(1), and a test now checks that peak memory does not grow with N. | Test added |

### F2 in numbers (`ln P(N/2)` from log-gamma against Stirling's formula)

| N | absolute error | usable? |
|---|----------------|---------|
| 10⁴ | 1·10⁻¹³ | yes |
| 10⁶ | 7·10⁻¹⁰ | yes |
| 10⁸ | 2·10⁻⁷ | yes |
| **10¹⁰** | **2·10⁻⁵** | **yes (the limit we claim)** |
| 10¹² | 2·10⁻³ | marginal |
| 10¹⁴ | 0.19 | no |
| 10¹⁵ | 3.8 | no |
| 10¹⁶ | 54 | garbage (the result is even positive) |

For a fixed offset d = 10 the entropy difference ΔS ≈ −2d²/N is already lost at N = 10⁹ (computed −1.9·10⁻⁶, true
−2.0·10⁻⁷). **Why:** `gammaln(N+1) − gammaln(k+1) − gammaln(N−k+1)` subtracts three numbers of size N ln N, each
with relative rounding error 10⁻¹⁶, so the absolute error is about 10⁻¹⁶ N ln N, independent of how small the
difference is.

**Consequence for the practice question "maximum N for the distribution".** Honest answer: in double precision
ln Ω never overflows, but probabilities and entropy differences are reliable up to N ≈ 10¹⁰; beyond that one must
use the asymptotic (Stirling/Gaussian) expressions, which is what the report does for N ~ 10²³. The values quoted
for N = 10²³ in the report (σ, relative width, 63σ, P(8 heads) = 10^(−3.01·10²²), |ΔS| = 2·10¹⁷ k_B) do not depend on
the failing routine, and `tests/test_main.py::test_part_thermo_limit` checks them against closed formulas.

## 3. Coverage and tests before / after

| Module | Coverage before | Coverage after | What was missing |
|--------|-----------------|----------------|------------------|
| `src/combinatorics.py` | 98% | **100%** | `binom_float` out of range; exactness of the three overflow limits |
| `src/microstates.py` | 65% | **100%** | SWAR fallback (F3); `benchmark` and `_benchmark_loop`; input validation |
| `src/thermodynamics.py` | 92% | **100%** | empty/clipped ranges; `simulate_tosses` without rng; `log10_prob_fraction` edges |
| `main.py` | 0% (not imported) | **99%** | everything; only the `--benchmark` call and the `__main__` guard are not executed |
| **Tests** | 72 | **147** (145 + 2 `xfail`) | |

### Which test backs which logic

| Logic | Independent reference | Tests |
|-------|-----------------------|-------|
| Bit encoding, generator, N = 7 table | `math.comb`, `str.count` | `test_microstates.py` (generator, `to_string`, `macrostate_table` is a partition of all 2ᴺ states) |
| Vectorised/multiprocess enumeration, popcount | `int.bit_count`, `math.comb` | `test_microstates.py` (incl. forced fallback, N < chunk, invalid N) |
| Benchmark and N_max estimators | closed form t = c·2ᴺ | `test_microstates.py` (`benchmark*`, `extrapolate`, `per_state_cost`); `test_main.py` (`_fits`, `part_benchmark`, `run_benchmark`) |
| Ω(N,k): exact, float, log-gamma, Pascal row, overflow limits | `math.comb`, `math.factorial` | `test_combinatorics.py` |
| M (harmonic mean), N, N/2 | hand values (7.26 → 7 → N = 107) | `test_thermodynamics.py`, `test_main.py::test_part_probabilities_*` |
| Questions 1–9 for N = 107 | `fractions.Fraction`, `math.comb` | `test_thermodynamics.py::test_team_question_values_n107_exact`, `test_main.py::test_part_probabilities_team_n107_against_exact` |
| ΔS sign convention | handout: ΔS(k₁k₂) ≡ S(k₁) − S(k₂) | `test_entropy_change_*` |
| Waiting time, overflow-safe | `2**n / math.comb` | `test_wait_time_*` |
| Gaussian / thermodynamic limit | closed formulas (√(2/πN), 63σ, 2N d²) | `test_gaussian_*`, `test_main.py::test_part_thermo_limit` |
| Monte Carlo | exact distribution, χ², variance N/4 | `test_simulation_*`, `test_main.py::test_part_distributions` |
| Report numbers are the ones main.py produces | fresh run vs committed file | `test_committed_results_tex_is_up_to_date` |

### Tests that check the handout, not the code

Tests written by the same author, from the same reading of the handout, cannot detect a misreading. The session-1
suite (68 tests) passed with the arithmetic mean and with the reversed ΔS sign. The following tests therefore encode
the handout's own wording, and **a teammate should re-read the handout against this table before submission**:

| Handout says | Encoded in |
|--------------|------------|
| M = harmonic average of the last two digits of the NIAs; N = 100 + M | `test_m_from_nias_team` (M = 7, N = 107) |
| ΔS(k₁k₂) ≡ S(k₁) − S(k₂) | `test_entropy_change_properties` (signs for questions 5–7) |
| k_B = 1.380649·10⁻²³ J/K | `test_entropy_values_and_units` |
| Waiting time for 8 heads at one toss per second | `test_wait_time_toss_rate`, `test_part_probabilities_*` |
| Question 4 is about *tails* in [N/2 − 20, N/2 + 20] | `test_prob_tails_range_uses_heads_equals_n_minus_tails` |

## 4. Mutation analysis

Each bug was injected alone and the full suite run. **10 of 10 real bugs were detected.**

| Injected bug | Detected by |
|--------------|-------------|
| ΔS sign reversed (the original error) | `test_part_probabilities_team_n107_against_exact` |
| Arithmetic instead of harmonic mean (the original error) | same |
| `sci()` negative-number bug (F1) | `test_sci[-9.9996e-05…]` |
| Question 9 with M ± 10 (negative number of heads) | `test_part_probabilities_team_n107_against_exact` |
| k₁ and k₂ swapped in question 5 | same |
| N/2 rounded up instead of down | same |
| Waiting time multiplied instead of divided by the toss rate | `test_wait_time_toss_rate` |
| Error in the SWAR popcount (shift 56 → 55) | `test_popcount_swar_fallback_is_really_executed` |
| Generator omits the last microstate | `test_part_enumeration` and `test_generator_yields_all_states_once` |
| Wrong exact binomial formula | `test_exact_matches_math_comb` |
| *Tails window not converted to heads* (`prob_range(n, t_lo, t_hi)` instead of `prob_range(n, n−t_hi, n−t_lo)`) | **not detectable: it is an equivalent change.** By the symmetry Ω(N,k) = Ω(N,N−k) both give the same number for a fair coin, which `test_tails_window_equals_heads_window_for_a_fair_coin` documents |

## 5. What is still open

**Decisions for the team / professor**
1. Convention for odd N (F7). Currently ⌊N/2⌋ = 53.
2. Reading of question 9 ("M ± 10"): implemented as N/2 ± 10 because M − 10 = −3 is impossible.
3. Which document governs AI use (see the open issue in `AI_STATEMENT.md`).
4. Rounding of M (7.26 → 7) and what to do with a NIA ending in 00 (the code raises an error).

**Recommended improvements, not applied** (each is optional and would need to be understood for the defence)
- **R1. Numerically stable ln P for huge N.** Use ln P = −N·D(x) − ½ ln(2πN x(1−x)), with
  D(x) = ½[(1+u)·log1p(u) + (1−u)·log1p(−u)], u = 2x − 1 (a power series for small u), and
  ln C(N,k) = k ln N + Σ log1p(−i/N) − ln k! for fixed k. Only worth it if the professor expects numbers for
  N ≫ 10¹⁰ from the code and not from the analytic formulas. The two `xfail(strict)` tests would then start to pass
  and pytest would ask you to remove the `xfail`.
- **R2. Continuous integration.** A GitHub Actions workflow that runs `pytest` on every Pull Request would make the
  "tests in green before merging" requirement automatic.
- **R3. Escape LaTeX in `write_authors`** (F9).
- **R4. Re-run the timing study** on the defence laptop (`python main.py --benchmark --verify-nmax`, about 15 min) and
  decide which machine's numbers go in the report (F11).

## 6. Limits of this audit

- The figures were checked for existence and size only, not visually. Open `report/main.pdf` and look at them.
- LaTeX rendering is not unit-tested; the report compiles (two `pdflatex` passes, no errors) but its prose was not
  re-derived.
- The timing numbers depend on the machine and are not reproducible by a test.
- The audit was done by an AI assistant (see `AI_STATEMENT.md`, session 2). The team must still re-derive the formulas
  by hand and run the suite on its own laptops.
