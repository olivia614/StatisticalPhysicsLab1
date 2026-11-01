# AI Usage Statement — Statistical Physics Lab 1

This file is required by **Phase 3 (Responsible AI Collaboration & Transparency Protocol)** of the
*Student Project Guidelines: Lab 1* (UC3M, 2026/27). It logs every AI query, what the AI produced,
what the team changed, and how the output was verified.

> **Note on the old slides.** The 2024/25 lab presentation ("Practice 1 – Coins", slide 8) says
> "AIs are banned" for the enumeration code. The updated 2026/27 project guidelines replace that
> rule. They explicitly allow AI tools as code assistants, provided their use is logged and
> audited here. The team followed the updated guidelines.

> **Open issue (added 2026-10-31).** The 2026/27 practice handout itself (*First_Practice.pdf*, "Note on
> Code Integrity") says the code must be written by the student team and prohibits code from AI tools,
> while the project guidelines (*Lab_Project.pdf*, Phase 3) allow AI as a code assistant if it is logged and
> audited. The two documents disagree. The team must ask the instructor which one applies, and until then
> every AI contribution is logged here in full.

## Tools used

| Tool | Model / version | Used by | Used for |
|------|-----------------|---------|----------|
| Claude Code (VS Code extension) | Claude Opus 5.5 (`claude-opus-5-5`) | jcantillana04 | Planning, code in `src/`, `tests/`, `main.py`, notebook, LaTeX report, this file |
| Claude chat (claude.ai) | Claude Sonnet 5.5 (`claude-sonnet-5-5`) | olivia614 (repository owner) | Planning the next steps, correcting the M/N and ΔS-sign errors, the audit and new tests (`tests/`, `docs/AUDIT.md`), updating `docs/REVIEW_GUIDE.md` and this file |

*(Add a row for every other tool a team member used, e.g. ChatGPT or GitHub Copilot.)*

---

## Session 1 — 2026-10-29 — Claude Code (jcantillana04)

Branch: `feature/lab1-implementation` (created from `feature/latex-report`).
Full approved plan: [`docs/ai_plans/2026-10-29_initial_plan.md`](docs/ai_plans/2026-10-29_initial_plan.md).

### Prompt 1.1 — task description (verbatim)

> Check the guide folder, there you will find three files, one contains the report as transcribed
> latex in the main.tex fle. The slides are the old version of the lab guide, which we use for
> reference and understanding of the problem but contains not updated requisites for the report.
> The other filie is the updated guide. Note that I will need a report of all AI usage as
> specified in the guide.

**AI output.** The AI read the three PDFs in `guide/` and the repository. It found that `src/`,
`tests/` and a working `main.py` were missing, and asked four clarifying questions:

| Question | Team answer |
|----------|-------------|
| Scope of the work | Full project (code, tests, figures, report, AI log) |
| NIAs for N = 100 + M | Make M a parameter (NIAs read from `team.json` / `--nias`) |
| Arithmetic vs. harmonic mean for M (the slides and the template disagree) | **Arithmetic** (as in the slides) |
| Detail of the AI log | Full per-prompt log plus a report appendix |

It then wrote an implementation plan (see link above).

### Prompt 1.2 (verbatim)

> Save the plan for track record and ask me again to accept this plan

**AI output.** The plan was saved to `docs/ai_plans/2026-10-29_initial_plan.md` as the first
implementation step. The plan was then approved.

### Prompt 1.3 (verbatim)

> make sure that the plan is carried out ina separate branch

**AI output.** The AI created the branch `feature/lab1-implementation`. All of the work below is on
this branch. Nothing has been committed or pushed by the AI.

### Prompt 1.4 (verbatim, in Spanish)

> como vas? estas haciendo algo?

*(Translation: "How is it going? Are you doing anything?")*

**AI output.** A progress report. While checking progress, the AI found that the second benchmark run
had extrapolated a nonsensical N_max = 49, because noisy timings at N = 33–34 flattened the fitted
slope. It stopped that run before the multi-day verification started (see the failures table).

### Prompt 1.5 (verbatim, in Spanish)

> has lanzado subagentes o lo estas haciendo tu? si has mandado subagentes revisa que no esten
> bloqueados. En caso que esten bloqueados hazlo tu

*(Translation: "Have you launched sub-agents or are you doing it yourself? If you sent sub-agents,
check they are not blocked. If they are blocked, do it yourself.")*

**AI output.** The AI confirmed that no sub-agents were used and that no stray processes were running.
It then made the N_max estimate robust (see `per_state_cost`), re-ran the benchmark and verified
N = 36 directly.

### Prompt 1.6 (verbatim)

> Now, I want you to make a separate file where you explain what you did in each part overall and
> guide us on what we should be revising and understanding in each part. Do that in a new branch.

**AI output.** The AI created the branch `docs/review-guide` (from `feature/lab1-implementation`) and
wrote [`docs/REVIEW_GUIDE.md`](docs/REVIEW_GUIDE.md). For each part of the project the guide gives a
summary of the work, the concepts to understand, the checks to make (including the AI's judgement calls
on how to read questions 4, 7 and 9), and likely defense questions.

### Prompts 1.7–1.10 — Git help (verbatim)

> I will commit it, any file I should not commit?

> I just want my teammates (from github) to be able to see the implementation, even if some parts are
> not finished, how do i do that?

> can you cjeck if the files are comitting? It is taking longer than I expected

> it wont let me write the message

**AI output.** Advice only, with no code generated:
- which files not to commit (`guide/` course PDFs, the draft `report/main.pdf`);
- the commands to commit on `feature/lab1-implementation` and push the branch, or open a draft PR;
- a diagnosis of the stalled commit: VS Code's Source Control was waiting for the message in
  `COMMIT_EDITMSG`. The AI suggested aborting and committing with `git commit -m`.

The AI attempted to stop the stalled git process. Claude Code's permission system blocked that, and the
user resolved it manually. The commits themselves were made by the user.

### Prompts 1.11–1.12 (verbatim)

> I have the NIAs: 100496704, 100523129, 100534604, 100599060. Include this everywhere a parameter was
> left as placeholder

> file is closed, and leave the names as placeholders we'll fill it manually

**AI output.**
- `team.json` now holds all four NIAs, which gives M = (29 + 04 + 04 + 60)/4 = 24.25 → 24 and
  **N = 124**. All report numbers were regenerated with `python main.py`.
- Because N is now even, the report's "N/2" sentence is generated for either parity (`\HalfNote`).
- `notebooks/exploration.ipynb` now reads N from `team.json` instead of hard-coding it.
- The report was recompiled and checked.
- Member names and GitHub handles were left as placeholders, as requested.

### Prompt 1.13 (verbatim)

> update the guide now

**AI output.** `docs/REVIEW_GUIDE.md` was updated on `docs/review-guide`:
- N = 124 / M = 24 throughout, with a quick-reference table of the question 1–9 results (checked against
  `report/results.tex`);
- notes on parity handling for even N;
- the Q4 symmetry remark and the Second Law figures for N = 124;
- the current Git and PDF status.

### Files generated in Session 1

| File | Content | Generated by AI | Human modifications |
|------|---------|-----------------|---------------------|
| `src/microstates.py` | Bit-encoded generator `iter_microstates` (`1 << N`), `bit_count` macrostates, N = 7 table, chunked/multiprocess NumPy popcount enumeration, benchmark + exponential fit | Yes | *(team to fill in)* |
| `src/combinatorics.py` | `binom_exact` (product formula, slide hint 2), `binom_float`, `log_binom` (log-gamma, guide eq. 1), Pascal row, float-overflow limits | Yes | |
| `src/thermodynamics.py` | `m_from_nias`, probabilities (log-sum-exp ranges), ΔS, waiting time, likelihood ratio, Gaussian limit, Monte Carlo tosses | Yes | |
| `tests/test_*.py`, `tests/conftest.py` | 68 pytest tests | Yes | |
| `main.py` | CLI: runs every question, writes `report/figures/*.pdf`, `report/results.tex`, `report/tables/*.tex` | Yes | |
| `report/main.tex` | Full report built on the team's template; all numbers come from `results.tex` | Yes (template by team) | |
| `notebooks/exploration.ipynb` | Small interactive checks | Yes | |
| `team.json` | Team metadata. All four NIAs were supplied by the team (prompt 1.11); names and GitHub handles of members 3–4 (and member 1's handle) are placeholders | Yes | **Names and handles to be filled in by the team** |
| `.gitignore`, `environment.yml` (`matplotlib>=3.7`) | Housekeeping | Yes | |

### Verification performed

1. **Unit tests** (`python -m pytest -q`): 68 passed. The tests compare every routine against
   independent references:
   - enumeration histograms vs. `math.comb` for N = 0 … 16 (generator) and N ≤ 20 (vectorised, 1 and 2 processes);
   - `log_binom` vs. `log(math.comb)` to relative 1e-12 for N up to 1000, and vs. Stirling at N = 1e23;
   - Σ Ω = 2^N, symmetry, normalisation of probabilities, ΔS sign conventions, waiting time = 2^N / Ω;
   - known value Ω(100, 50) = 1.0089e29 and P(100, 50) = 0.07959 (slides 10 and 12 of the presentation).
2. **Monte Carlo cross-check**: 100,000 simulated tosses of 100 coins against the exact distribution,
   χ² = 41.3 for 42 degrees of freedom.
3. **Benchmark verification run**: N = 36 (6.9×10¹⁰ microstates) was fully enumerated in 99 s on
   16 processes, and the histogram matched `math.comb` exactly (`report/data/benchmark.json`).
   An earlier run under heavier machine load took 322 s for N = 37, just over the 5-minute limit.
4. **LaTeX build**: the report compiles without errors or warnings (checked with the Tectonic engine;
   9 pages, body = pages 1–7, appendices from page 8). The rendered pages were inspected visually.
5. **To do by the team**: re-derive the formulas in Sections 3–4 of the report by hand, and check
   the physics discussion before submission.

### AI failures and how they were resolved

| Problem | Detected by | Resolution |
|---------|-------------|------------|
| `float_overflow_limits()` first compared logarithms and returned N = 1025 for overflow of 2^N. The true value is 1024: `1024·ln 2` and `ln(float max)` agree to rounding error. | `test_float_overflow_limits` | Switched to exact integer comparisons (`2**n > int(float_max)`). |
| `numpy.polyfit` and every `numpy.linalg` call (also used internally by Matplotlib) crashed Python with Windows fatal error `0xc06d007f`. The threaded MKL backend in the conda-forge environment failed to load its OpenMP runtime. | Running the tests / `main.py` | Set `MKL_THREADING_LAYER=SEQUENTIAL` before importing NumPy (`main.py`, `tests/conftest.py`). Also replaced `polyfit` with a closed-form least-squares fit. The Conda environment itself was not modified. |
| Design risk: a naive `list(range(1 << N))` or storing all microstates needs 8·2^N bytes (8 GB at N = 30). | Planning | Generators (`yield`) and fixed-size chunks of 2^22 states keep memory constant (≈ 100 MB per process). |
| The first version of `benchmark()` timed each run with `tracemalloc` active. Tracing slows pure-Python loops several-fold, so the generator timings would have been inflated. | AI self-review during the first benchmark run (run aborted) | Timing runs now execute without tracing; peak memory is measured in a separate probe run. |
| Fitting a free slope to noisy timings (other load on the laptop, thermal throttling) gave slopes far from 1 and absurd extrapolations: N_max = 49 in one run, which would have taken days to verify. Process-pool start-up (~3 s on Windows) also dominated the small-N vectorised runs. | Checking benchmark progress | Reuse one warmed-up process pool. Fit only the 4 largest N. Estimate N_max from the theoretical law t = c·2^N with c = median(t/2^N) (`per_state_cost`, unit-tested with an outlier). Cap verification at 3 coins beyond the largest timed N, and step down if a run exceeds 300 s. |
| `\input` of generated table rows inside `tabular` failed (`Misplaced \noalign`): LaTeX's `\input` is not expandable. | LaTeX compilation | Added `\tabinput`, which uses the expandable TeX primitive `\@@input`. |
| The AI first wrote an invented GitHub handle for one member in `team.json`. | AI self-review | Replaced with a placeholder. Real handles must be entered by the team. |
| The first draft printed P(k = 8) at N = 1e23 with a 23-digit exponent, which double precision cannot resolve. | AI self-review | Exponent now printed to 3 significant figures (10^(−3.01×10²²)). |

---

## Session 2 — 2026-10-31 — Claude chat, claude.ai (olivia614)

Branch: `feature/harmonic-mean-and-entropy-sign` (created from `docs/review-guide`).
The AI could only **read** the repository. It prepared the changes below in a local copy and handed the
changed files to the team member, who applies them to her own branch. The AI pushed nothing.
The team member wrote her prompts in Spanish; they are given here in English translation.

*Context.* A preliminary conversation earlier on the same day, in which the AI first read the guides and the
repository, was dropped by the team member. This entry covers the conversation that restarted afterwards.
All the changes listed below were re-done from the base branch during this conversation.

### Prompt 2.1 (translated from Spanish)

> I have been asked to do the work described in these files (one is a general explanation, another a more
> concrete example without the GitHub part, and the third is specifically what I have to do in my
> laboratory, taking the other two into account). Taking into account the GitHub repository we have already
> created, what would be the next step? Do we have to create new documents, or is the only thing left to
> improve the code?

**AI output.** No new documents are needed: the structure required by the project guidelines already exists.
The remaining work is: agree on a base branch (`docs/review-guide` and `feature/lab1-implementation` have
diverged); fix two errors in the existing code (M computed with the arithmetic instead of the harmonic mean,
giving N = 124 instead of 107, and the sign of ΔS in questions 5–7 reversed with respect to the handout);
regenerate the results and the report; fill in `team.json`; improve and understand the code each member
will defend; keep logging AI use in this file; merge through reviewed Pull Requests, tag `v1.0` and submit.
It also pointed out the contradiction between the two documents about AI-written code (see the open issue above).

### Prompt 2.2 (translated from Spanish)

> I have reviewed the different files and you are right that we have to use the harmonic mean, which is what
> they really ask for in the specific handout of this lab. And explain the sign of S to me better.

**AI output.** An explanation of the sign. The handout defines ΔS(k₁k₂) ≡ S(k₁) − S(k₂). In questions 5 and 6,
k₁ is further from N/2 than k₂ and has fewer microstates, so ΔS is negative; in question 7, k₁ = N/2 is the
most disordered macrostate, so ΔS is positive. The code computed S(k₂) − S(k₁), which only differs in sign.

### Prompt 2.3 (translated from Spanish)

> Ok, now redo the whole repository fixing these two errors everywhere it is needed, and add to the AI
> statement the conversation we have just had (since I said we were starting again). It has to be in English.
> Also, if I have missed anything I have to do now (beyond the steps you already gave me), tell me too.

**AI output.** The changes below, prepared on the local branch `feature/harmonic-mean-and-entropy-sign`:

| File | Change |
|------|--------|
| `src/thermodynamics.py` | New `harmonic_mean`; `m_from_nias` uses it (clear error if a NIA ends in 00, where it is undefined). `entropy_change(n, k1, k2)` and `entropy_change_si` now return S(k1) − S(k2), as in the handout |
| `tests/test_thermodynamics.py` | Harmonic-mean tests (team case M = 7, N = 107, zero digit); entropy-sign tests (questions 5–7) and an antisymmetry test. 72 tests in total |
| `main.py` | Harmonic mean exported; odd-N note mentions the tie between k = 53 and 54; question 9 uses N/2 ± 10; entropy differences use the handout definition; magnitude shown for the N → 10²³ entropy |
| `notebooks/exploration.ipynb` | Entropy cell uses the handout's ΔS definition (comment updated, old output cleared) |
| `report/main.tex` | Text on M (harmonic), definition ΔS(k₁k₂) ≡ S(k₁) − S(k₂) with its sign convention, entropy table and discussion, question 9 as N/2 ± 10; test count updated to 72 |
| `report/results.tex`, `report/figures/*.pdf`, `report/main.pdf` | Regenerated with `python main.py` for N = 107 and recompiled |
| `docs/REVIEW_GUIDE.md` | Section 7 and related notes updated: harmonic mean, N = 107, sign convention, new results table |
| `AI_STATEMENT.md` | This entry, the open-issue note and the new tools row. All Session 1 entries are kept |

### Prompt 2.4 — 2026-11-01 (translated from Spanish)

> Now, with the new branch in which the changes were made, do this part: "Audit & Test: All AI-generated logic
> must be backed by unit tests", and tell me if there is any error that should be changed or improved. Also
> document all of this in this new branch, and give me again a zip with this new branch and all the changes
> included.

**AI output.** An audit of the code and of the existing tests, recorded in full in
[`docs/AUDIT.md`](docs/AUDIT.md). Summary:

- **Coverage** went from 81% (`src/`) and 0% (`main.py`) to 100% and 99%; the suite went from 72 to 147 tests
  (145 checks and 2 `xfail` tests that document known limitations).
- **Errors found:** (F2) the report claimed that the log-gamma formula "has no limit at all" and agrees with
  Stirling's formula at N = 10²³; in fact probabilities and entropy differences are reliable only up to
  N ≈ 10¹⁰ (measured table in `docs/AUDIT.md`), so the report text, three docstrings and the review guide were
  corrected; (F1) `sci()` mis-formatted negative numbers just below a power of ten; (F3, F4, F5) three tests that
  did not test what they claimed (the NumPy 1.x popcount fallback was never executed, a tolerance of 10⁻¹² hid
  errors of 10¹⁰, and one test compared a formula with itself); (F6) `main.py` had no tests.
- **Decision left to the team (F7):** the convention for "N/2 ± 10" when N = 107 is odd.
- **Mutation analysis:** 11 bugs were injected (including the two errors corrected in prompt 2.3); 10 were
  detected, and the 11th turned out to be an equivalent change (tails and heads windows have the same
  probability for a fair coin).

| File | Change |
|------|--------|
| `docs/AUDIT.md` | New: method, findings F1–F12, measured precision table, coverage, test-to-logic map, mutation analysis, open decisions |
| `tests/test_main.py` | New: 35 tests of `main.py` (formatting, team files, each part of the report against exact arithmetic, whole-program run, check that `report/results.tex` is not stale) |
| `tests/test_microstates.py`, `tests/test_combinatorics.py`, `tests/test_thermodynamics.py` | Weak tests replaced (F3, F4, F5); tests added for every uncovered function and edge case; two `xfail(strict)` tests documenting F2 |
| `main.py` | `sci()` fix (F1) |
| `src/combinatorics.py`, `src/thermodynamics.py` | Docstrings only: valid numerical range of `log_binom`; `log10_prob_fraction` is leading order. No change in behaviour |
| `report/main.tex` | Corrected the log-gamma paragraph and the conclusion (F2); test count and reference to the audit |
| `docs/REVIEW_GUIDE.md` | Sections 0, 4 and 11 corrected and updated |
| `.gitignore` | Ignores `.coverage` and `htmlcov/` |

### Code optimisation of the Session 1 code

*(To be filled in by the team only if an optimisation conversation takes place. For each one: the prompt,
what the AI proposed, what was changed, and the measured effect, e.g. benchmark times before and after.
No optimisation was done in this session.)*

| Date | Prompt (summary) | AI proposal | Change made | Measured effect |
|------|------------------|-------------|-------------|-----------------|
| | | | | |

### Notes and changes by the team member

| Date | File / section | What was changed or noted | Why |
|------|----------------|---------------------------|-----|
| 2026-10-31 | Lab handout vs. code | Reviewed the handouts herself and confirmed that the harmonic mean is what this lab asks for (prompt 2.2) | To decide that M must be changed |
| 2026-10-31 | Entropy sign | Read the explanation of the sign of ΔS(k₁k₂) and confirmed she understood it before the change was made | To be able to defend it |
| | *(add your own edits here, with the file and commit)* | | |

### Verification performed by the AI

1. `python -m pytest -q`: 72 passed after prompt 2.3; **145 passed and 2 expected failures (`xfail`) after prompt 2.4**,
   with 100% line coverage of `src/` and 99% of `main.py` (`pytest --cov`).
2. The N = 107 results were recomputed independently with exact integer arithmetic (`math.comb`,
   `fractions`) and match `report/results.tex`: P(30) = 1.963e-6, P(53) = P(54) = 0.07660,
   P(43 ≤ k ≤ 63) = 0.9572, P(33 ≤ tails ≤ 73) = 0.999934, ΔS = −11.527, −1.675 and +22.371 (units of k_B),
   P(53)/P(63) = 5.34, P(53)/P(43) = 7.77, waiting time for 8 heads 10^20.70 s.
3. The report compiles (two `pdflatex` passes, 0 errors, 0 overfull boxes, 9 pages).
4. Mutation analysis of prompt 2.4: 10 of 10 real injected bugs are detected by the suite (see `docs/AUDIT.md`, section 4).
5. **To do by the team:** run everything on a personal laptop, re-derive the formulas by hand, and decide the
   judgement calls listed in `docs/REVIEW_GUIDE.md` (rounding of M, odd N, question 9).

### AI failures and how they were resolved (Session 2)

| Problem | Detected by | Resolution |
|---------|-------------|------------|
| Session 1 used the arithmetic mean for M (taken from the old slides), giving N = 124, while the updated handout and the template say harmonic (N = 107). All part-2 numbers were affected. | Comparing the code with the updated handout | `m_from_nias` fixed, tests updated, everything regenerated |
| `entropy_change` computed S(k2) − S(k1), the opposite of the handout's ΔS(k1k2) ≡ S(k1) − S(k2): the signs of questions 5–7 were reversed. The Session 1 tests checked the code against itself, not against the handout. | Re-reading the handout's definition against the code | Function, tests, report and review guide changed; the convention is now stated in the report |
| With M = 7 the reading "k = M ± 10" of question 9 gives k = −3, which is impossible. | Running the code with the new N | Question 9 read as N/2 ± 10, documented in the report and the review guide. **To be confirmed with the instructor.** |
| The entropy table wrapped its rows and one limit value was printed with a sign inside an absolute value. | Reading the compiled PDF | Ratios removed from the table; the magnitude is printed |
| Session 1 wrote, and the report stated, that the log-gamma formula "has no limit at all" and is validated at N = 10²³. The validating test used a relative tolerance of 10⁻¹² on a value of 7·10²², so it could not see the missing −27 correction. | Audit (prompt 2.4): a numerical experiment at N = 10¹⁵ and 10²³ | Report, docstrings and review guide corrected with the measured limit (N ≈ 10¹⁰); test replaced; the limit is documented by `xfail` tests. Code unchanged |
| `sci()` printed `-10.00\times10^{-5}` for −9.9996·10⁻⁵. | Audit (prompt 2.4), edge-case experiment | Fixed and tested |
| `test_popcount_fallback_matches` never executed the fallback it was named after (NumPy ≥ 2 uses `np.bitwise_count`). | Coverage report | Test rewritten to force the fallback |
| *Audit's own mistakes.* (a) A new test assumed the N = 7 table is listed from 0 to 7 heads; the code lists 7 down to 0, as in the handout. (b) One injected bug looked like an undetected gap in the tests, but it was an equivalent change. | Test run; investigating the surviving mutant | (a) The test assumption was corrected, not the code. (b) Documented in `docs/AUDIT.md` with a test of the symmetry |

---

## Template for further entries (copy for each new AI query)

```markdown
### Prompt X.Y — <date> — <tool> (<team member>)
> <prompt, verbatim>

**AI output:** <code / text produced, or the files and functions affected>
**Human modifications:** <what was changed and why>
**Verification:** <tests run, manual checks, comparison with theory>
```
