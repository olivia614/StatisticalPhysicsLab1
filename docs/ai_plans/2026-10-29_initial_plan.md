# Plan: Statistical Physics Lab 1 (coins) — full project + AI log

## Context
The repo holds only stubs: `environment.yml`, an empty `AI_STATEMENT.md`, a placeholder `main.py`, and a template `report/main.tex`. The updated guide (`guide/Lab_Project.pdf`) sets the required deliverables. Slides 8–16 of the old deck (`guide/Practice 1 - Coins ...pdf`) list the physics questions the report has to answer. The output is a modular Python package with pytest tests, generated vector figures, a filled-in LaTeX report, and a complete AI usage log (Phase 3, 10% of the grade).

Decisions already made by the user:
- Build the full project.
- M is a parameter supplied through the NIAs; no NIAs are hard-coded.
- M is the **arithmetic** mean of the last two NIA digits, rounded to an integer.
- Full AI log plus a report appendix.

## Step 0 — keep the plan as a record
Copy this plan verbatim to `docs/ai_plans/2026-10-29_initial_plan.md` in the repo before writing any code. The first AI_STATEMENT.md entry links to it as the planning prompt and output, including the clarifying questions and the user's answers (full project, M as a parameter, arithmetic mean, full log).

## Repository layout (from the guide, Phase 4)
```
environment.yml        (fix: matplotlib>=3.7)
AI_STATEMENT.md        (full per-prompt log)
.gitignore             (Python + LaTeX aux files)
team.json              (NIAs, names, GitHub handles; placeholders until the team fills them in)
src/__init__.py
src/microstates.py     enumeration
src/combinatorics.py   exact + log-space binomials
src/thermodynamics.py  probabilities, entropy, waiting times, M/N
tests/test_microstates.py
tests/test_combinatorics.py
tests/test_thermodynamics.py
notebooks/exploration.ipynb  (short; reuses src/ for plots)
report/main.tex, report/results.tex (auto-generated), report/figures/*.pdf
main.py                CLI orchestrator
```

## Modules (typed functions with NumPy-style docstrings)
**src/microstates.py**
- `iter_microstates(n) -> Iterator[int]`: generator over `range(1 << n)`.
- `to_string(state, n) -> str` (H/T); `count_heads(state) -> int` via `int.bit_count()`.
- `macrostate_table(n) -> dict[int, list[str]]`: N=7 listing, all 128 outcomes.
- `count_macrostates_enumeration(n) -> np.ndarray`: pure-generator histogram.
- `count_macrostates_vectorized(n, chunk_bits=24)`: chunked NumPy popcount over integer blocks, with memory bounded per chunk. This is the fast path for the 5-minute N_max (extra-credit item).
- `benchmark(n_values, repeats=3) -> list[dict]`: wall time (mean ± std) and peak RAM via `tracemalloc`.

**src/combinatorics.py**
- `binom_exact(n, k)`: Python big-int product formula from Hint 2, ∏ (N+1−i)/i.
- `log_binom(n, k)`: `scipy.special.gammaln` (guide eq. 1); vectorised over k.
- `log_binom_row(n) -> np.ndarray`, `multiplicity_row(n)`.
- `float_overflow_limit()`: smallest N where `float(2**N)` / `C(N, N/2)` overflow. This answers question 5 ("max N and why").

**src/thermodynamics.py**
- `m_from_nias(nias) -> int` (arithmetic mean of `nia % 100`, rounded); `system_size(nias) -> int` (100+M).
- `log_prob(n, k)`, `prob(n, k)`, `prob_range(n, k_lo, k_hi)` using log-sum-exp.
- `entropy_change(n, k1, k2) -> float` (ΔS/k_B = ln Ω₁/Ω₂) and the value in J/K.
- `expected_wait_seconds(n, k)` = 2^N / Ω(N,k) (question 8), also given in years.
- `likelihood_ratio(n, k1, k2)` (question 9).
- `gaussian_approx(n, k)`, `relative_width(n)` = 1/√N (questions 6 and 11).
- `simulate_tosses(n, trials, rng)`: Monte Carlo histogram. The slides' objective calls for a simulation of repeated tossing, compared against the exact distribution.
- If N is odd, N/2 means ⌊N/2⌋. The report says so explicitly.

## main.py
`python main.py [--nias 100xxxxxx ...] [--benchmark] [--max-time 300]`
1. Prints the N=7 table and writes `report/figures/` plus table rows into `results.tex`.
2. Benchmarks enumeration over N=10…N_max and fits log₂(t) against N to extrapolate to 300 s. Writes `fig_benchmark.pdf`. The full run is behind `--benchmark` so the default run is fast for the live defense.
3. Plots Ω(N,k) and P_k for N=20, 50, 80, 100 (`fig_distributions.pdf`, linear + normalised k/N panel), with an MC overlay (`fig_simulation.pdf`).
4. Computes questions 1–9 for N=100+M and writes LaTeX macros (`\Nval`, `\Mval`, `\PthirtyHeads`, …) to `report/results.tex`. The report `\input`s that file, so numbers update automatically once the NIAs are set.
5. Plots the thermodynamic-limit figure: P vs k/N for N = 10², 10⁴, 10⁶ (Gaussian), showing the 1/√N narrowing (`fig_thermo_limit.pdf`).

All figures are vector `.pdf` files saved with matplotlib to `report/figures/`, with labelled axes and units.

## Tests (pytest)
- Enumeration histogram == `math.comb` for N≤16; generator and vectorized paths agree; N=7 table sums to 128 and matches Pascal row.
- `exp(log_binom)` vs `math.comb` to rel 1e-12 for N≤1000; symmetry; Σ Ω = 2^N.
- Probabilities sum to 1; `prob_range` symmetric heads/tails (question 4); ΔS sign and zero at k1=k2; `m_from_nias` on known input; wait-time formula sanity.

## Report (report/main.tex, ≈5 pp body, ≤8, appendix excluded)
Keep the template's structure and fix its issues: stray quote marks around `\texttt`, the `AI-STATEMENT` name, the fabricated performance numbers, and the "harmonic" wording. Use `\input{results}` for all numbers. Every slide question gets an answer:
- §3.1 N=7 table (all 128 listed in appendix or grouped counts in body).
- §3.2 questions 2–3: measured N_max, the timing/RAM table (mean ± std), the benchmark figure, and why larger N fails (2^N time, memory if stored, int64 bit limit).
- §3.3 question 4: distributions figure. Question 5: limits of exact float vs big-int vs log-space.
- §3.4 questions 6 and 11: Stirling → Gaussian derivation and σ/μ = 1/√N at 10²³.
- §4 questions 1–9: results table (P for 30 heads, N/2, ±10 heads, ±20 tails; ΔS/k_B and ΔS in J/K for the three pairs; waiting time for 8 heads; likelihood ratios). Question 10: Second Law discussion. Question 11: the N→∞ answers.
- Appendix A: AI statement summary + link. Appendix B: key code excerpts (bitwise loop, log-space).
- Author block and repository URL (`https://github.com/olivia614/StatisticalPhysicsLab1`) pulled from `team.json` placeholders.

## AI_STATEMENT.md
- Header: tools used (Claude Code, Opus 5.5), policy reference (guide Phase 3), and a note on the old slides' "AIs are banned" footnote: the updated 2026/27 guide supersedes it.
- One entry per prompt in this session: verbatim user prompt, what Claude generated (files/functions), human modifications (blank field for the team), and verification (which tests, what was checked by hand).
- Section "AI failures & fixes" (required by the guide), e.g. naive `list(range(1<<N))` memory blow-up replaced by chunked generator.
- Blank template entry for teammates' ChatGPT/Copilot queries.

## Not done without asking
No commits or pushes. Code stays in the working tree on `feature/latex-report`. Splitting it onto `feature/core-code` for PR review is suggested.

## Verification
1. `conda activate statphys_lab1` (env exists) → `pytest -q` passes.
2. `python main.py --nias <placeholder>` runs in a few seconds and creates `report/figures/*.pdf` + `report/results.tex`.
3. `python main.py --benchmark` reports N_max within 300 s.
4. Spot-check: for N=100, P(50)=0.0795892 (matches slide 12 peak ≈0.08) and Ω(100,50)≈1.009e29 (slide 10).
5. LaTeX: `pdflatex` is not installed locally. Compile on Overleaf or install MiKTeX, and check page count ≤ 8.
