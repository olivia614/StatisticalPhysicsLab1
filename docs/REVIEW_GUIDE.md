# Review Guide — what was built, and what you must check and understand

**Audience:** the four team members, preparing for submission and for the live code defense.
The professor picks **one of us at random** to defend the project (guide, Phase 8). So **every
member must understand every part**, not only the part they reviewed.

Each part below has four subsections:

- **What was done**: a summary and the files to open.
- **What you must understand**: concepts you should be able to explain without notes.
- **What to review / verify**: concrete checks. Several are judgement calls the AI made that the team
  must confirm or change.
- **Likely defense questions**: practise answering them aloud.

Line references are to the state of the code on 2026-10-29.

---

## 0. Running the project (do this first, on your own laptop)

**What was done**
- `environment.yml` defines the `statphys_lab1` Conda env (only change: `matplotlib>=3.7`, as the guide asks).
- `python main.py` runs every calculation in about 5 s. It writes figures to `report/figures/`, numbers to
  `report/results.tex` and table rows to `report/tables/`.
- `python main.py --benchmark --verify-nmax` reruns the timing study (about 15 min).
- `python -m pytest -q` runs the 68 tests.

**What you must understand**
- **The MKL workaround.** `main.py` and `tests/conftest.py` set `MKL_THREADING_LAYER=SEQUENTIAL` *before*
  importing NumPy. On our Windows env, threaded MKL crashed Python (error `0xc06d007f`) inside
  `numpy.linalg`, which Matplotlib uses. You should be able to say this in one sentence.

**What to review / verify**
- [ ] **Run everything.** On **your own laptop** run: `conda env create -f environment.yml`, then
      `conda activate statphys_lab1`, then `python -m pytest -q`, then `python main.py`. The defense is
      done on your own machine, so it must work there.
- [ ] **Remove the workaround if unnecessary.** If you are on macOS or Linux and everything works, try
      without the MKL line. It should be harmless either way.

---

## 1. Repository structure and Git workflow (15% of the grade)

**What was done**
- The layout follows guide Phase 4: `src/` (3 modules), `tests/`, `notebooks/`, `report/`, `main.py`,
  `AI_STATEMENT.md`, `environment.yml`. Additional files: `team.json` (team data), `docs/` (plan and this
  guide), `.gitignore`.
- Branches:
  - `feature/latex-report`: the team's template.
  - `feature/lab1-implementation`: all code, report and AI log. Commits: `first implementation code`,
    `updated version with NIAs`.
  - `docs/review-guide`: this file, rebased on top of `feature/lab1-implementation`.
- **Not pushed yet**, and nothing is merged into `main`. `docs/ai_plans/` (the saved plan that
  `AI_STATEMENT.md` links to) is still untracked; commit it.

**What you must understand**
- Feature-branch workflow, why `main` is protected, and what a PR review is for.
- Why `report/results.tex` and `report/tables/*.tex` are **generated**. They must never be edited by
  hand; you change the code or `team.json` and rerun `main.py`.

**What to review / verify**
- [ ] **Push and open PRs.** Push `feature/lab1-implementation` and `docs/review-guide`, then open PRs into
      `main`. **Each PR must be approved by a teammate other
      than the author.**
- [ ] **Spread the contributions.** The rubric rewards "active contributions from **all** team members".
      Make sure everyone has real commits: fixing `team.json`, filling in the AI log, reviewing,
      improving figures, and so on.
- [ ] **Decide on `guide/`.** It contains the course PDFs and is untracked. We recommend **not**
      committing it (copyright, size).
- [ ] **Tag the release.** At the end, tag `v1.0` on `main` (guide Phase 7).

**Likely defense questions**
- "Show me your commit history. What did *you* contribute?"
- "What happens if two of you edit the same file on different branches?"

---

## 2. Microstate enumeration (slides Q1) — `src/microstates.py`

**What was done**
- A microstate of N coins is encoded as an integer `s` in `[0, 2^N)`. Bit *i* = 1 means coin *i* is
  heads (slide "Hint 1").
- `iter_microstates(n)` (line 25) is a **generator**: it `yield`s 0, 1, …, 2^N − 1 one at a time, so it uses
  O(1) memory.
- `count_heads(state)` uses `int.bit_count()` (popcount), which gives the macrostate k directly.
- `to_string` / `macrostate_table` produce the full H/T listing for N = 7 (128 outcomes). It appears as
  Table 1 and in Appendix C of the report.

**What you must understand**
- **Why `1 << N == 2^N`.** Shifting left by N bits multiplies by 2^N.
- **The binary/coin bijection.** Each binary number of N bits is exactly one coin configuration, and the
  number of 1-bits is the number of heads.
- **Generator vs. list.** `list(range(1 << 30))` would need about 8 GB; a generator needs almost nothing.

**What to review / verify**
- [ ] **Check the listing.** Look at Appendix C: are all 128 listed, with no duplicates? Do the counts
      match Pascal's row 1, 7, 21, 35, 35, 21, 7, 1?
- [ ] **Check the string order.** `to_string` prints the **most significant bit first**, so state `6 = 110`
      becomes `HHT`. Be ready to explain the convention.
- [ ] **Read the vectorised path.** `count_macrostates_vectorized` (line 139) splits the state space into
      blocks of 2^22, popcounts each block with NumPy (`np.bitwise_count`, or the SWAR fallback
      `_popcount` for NumPy 1.x), and runs blocks in parallel processes. Make sure you can explain the
      line `states = offsets + np.uint64(block << chunk_bits)`.

**Likely defense questions**
- "Walk me through `iter_microstates`. Why `yield`?"
- "How do you get the number of heads from the integer?"
- "Is the vectorised version cheating?" Answer: no. Every one of the 2^N states is generated and
  popcounted; it is the same algorithm, run in compiled code over chunks. No binomial formula is used.

---

## 3. Benchmark and maximum N (slides Q2–Q3, the extra point) — `src/microstates.py`, `main.py`

**What was done**
- `benchmark()` (line 197) times both methods: 3 repeats each, mean ± sample standard deviation. It measures
  peak memory with `tracemalloc` in a **separate** run, because tracing slows Python loops.
- The vectorised benchmark reuses one warmed-up process pool, so process start-up (~3 s on Windows) is not
  counted.
- **N_max is estimated with `per_state_cost` (line 296).** It assumes the theoretical law t = c·2^N and takes
  c = median(t/2^N) over the four largest N. A free-slope fit (`extrapolate_n_max`) is still reported as a
  consistency check. The robust estimate was adopted because the free fit on noisy laptop timings gave
  absurd results.
- `--verify-nmax` actually runs the predicted N_max. If it takes more than 300 s, it steps down to N − 1.
- **Result on the lab laptop (16 threads):**
  - generator: c ≈ 300 ns/state, so N_max ≈ 30;
  - vectorised: c ≈ 3.8 ns/state, so N_max ≈ 36.2;
  - **N = 36 verified in 99 s** with the exact histogram.
  - An earlier, heavier-loaded run took 322 s for N = 37, slightly over the limit.

**What you must understand**
- **Why each extra coin doubles the time.** Plot log₂ t against N: the slope should be about 1.
- **Why we cannot go much further.** At about 1 ns/state, N = 40 takes about 18 min and N = 60 takes
  decades. Storing the states costs 8·2^N bytes. Writing out the listing costs N·2^N characters. The uint64
  encoding caps the vectorised method at N ≤ 63.
- **Why repeats and error bars matter.** Timings are the **only measured (experimental) quantity** in the
  project, so they are the only quantity with a statistical uncertainty.

**What to review / verify**
- [ ] **Rerun the benchmark.** Run `python main.py --benchmark --verify-nmax` on a quiet, plugged-in
      laptop. The numbers depend on the machine. Decide **which laptop's results go into the report**,
      and say so in the text.
- [ ] **Read Table 2 and Figure 1.** The vectorised N = 26–27 points have large error bars because of
      residual pool overhead. Is that acceptable, or should we drop them?
- [ ] **Decide on N = 37.** Do we want to claim it? Only if a verified run finishes in ≤ 300 s on the
      presenting laptop.
- [ ] **Check the memory column.** It is per process: about 100 MB per vectorised worker, so 16 workers
      use about 1.6 GB in total. Make sure the caption is clear.

**Likely defense questions**
- "What is your N_max, and how did you measure it?"
- "Why not just use more cores?" Each core halves the time at most, which gains about 1 coin per doubling
  of the core count; 2^N always wins.
- "Why did you fix the slope to 1 instead of fitting it?"

---

## 4. Combinatorics without overflow (slides Q4–Q5) — `src/combinatorics.py`

**What was done**
- `binom_exact(n, k)` (line 23) uses the product formula from slide "Hint 2", ∏ (N+1−i)/i, with Python big
  integers. After step i the running value equals C(N−k+i, i), so the integer division is always exact.
- `multiplicity_row(n)` builds exact rows with Pascal's rule; it is used for the plots.
- `log_binom(n, k)` (line 50) computes ln Ω = lnΓ(N+1) − lnΓ(k+1) − lnΓ(N−k+1) (guide eq. 1) with
  `scipy.special.gammaln`. It never overflows, even at N = 10²³.
- `float_overflow_limits()`, compared with exact integers, finds where double precision fails:
  - 2^N overflows at **N = 1024**;
  - a naive N! overflows at **N = 171**;
  - C(N, N/2) overflows at **N = 1030**.

**What you must understand**
- **Why dividing factorials is a bad idea.** N! overflows long before C(N, k) does.
- **What Γ is.** Γ(n+1) = n!, and lnΓ is computed directly without ever forming n!.
- **The answer to Q5 ("max N you can calculate, and why").** In floats, about 1030. With big integers there
  is no hard limit, only cost. In log-space there is no limit at all.

**What to review / verify**
- [ ] **Check one value by hand.** Ω(100, 50) ≈ 1.009 × 10²⁹, which matches slide 10.
- [ ] **Read the unit tests.** `tests/test_combinatorics.py` checks `log_binom` against `math.comb` to
      relative 10⁻¹². Read it and confirm it actually verifies what we claim.

**Likely defense questions**
- "Show me the log-space formula in the code and explain it."
- "Why does 2^N overflow at 1024 exactly?" Because the largest double is about 1.8 × 10³⁰⁸ ≈ 2¹⁰²⁴.

---

## 5. Distributions for N = 20, 50, 80, 100 and the Monte Carlo check (slides Q4, "objectives") — `main.py: part_distributions`

**What was done**
- **Figure 2** has two panels: (a) Ω(N, k) on a log scale, and (b) P_k = Ω/2^N.
- **Appendix B (Figure 5).** 100,000 simulated tosses of 100 coins (seed 2026), with Poisson error bars
  √n_k, compared with the exact curve. The result is χ² = 41.3 for 42 degrees of freedom. This covers
  the slides' "develop a computational simulation" objective.

**What you must understand**
- **Why the peak height falls while the peak multiplicity grows.** P_max ≈ √(2/πN).
- **The width.** In k the width grows as √N/2, but relative to N it shrinks as 1/√N.
- **What χ²/dof ≈ 1 means.** The simulated histogram agrees with theory within counting noise.

**What to review / verify**
- [ ] **Check the axes.** Are the labels and units clear? (k is dimensionless and P is a probability, so no
      physical units are needed. Say so if asked.)
- [ ] **Decide where the Monte Carlo goes.** It is in the appendix to save body pages. Is that what we
      want?

---

## 6. Thermodynamic limit N → 10²³ (slides Q6 and Q11) — report §3.4 and §4.4, `main.py: part_thermo_limit`

**What was done**
- **The derivation.** Stirling's formula ln N! ≈ N ln N − N + ½ ln(2πN), expanded to second order around
  N/2, gives a Gaussian with μ = N/2, σ = √N/2 and σ/μ = 1/√N (Eq. 4). At N = 100 this Gaussian is
  already within 0.25% of the exact peak.
- **At N = 10²³:**
  - σ/μ = 3.16 × 10⁻¹²;
  - a deviation of 10⁻¹⁰ in k/N is a 63σ event, with P ≈ 10⁻⁸⁷¹;
  - a 0.1% deviation is suppressed by 10^(−8.7×10¹⁶);
  - P(exactly 8 heads) = 10^(−3.01×10²²).
- **Figure 3** shows the peak in k/N narrowing for N = 10², 10⁴, 10⁶ and 10⁸.

**What you must understand**
- **Reproduce the derivation yourself on paper.** This is the "derivation of the thermodynamic limit" item
  in the Physics rubric (20%).
- **The key subtlety in §4.4.** P(N/2) itself → 0, and so does any window of **fixed** width ±10. What → 1
  is a window of fixed **relative** width ε. Many students get this wrong.
- **Leading-order Stirling.** `log10_prob_fraction` uses ln P ≈ N[H(x) − ln 2], with H the mixing entropy
  per coin.

**What to review / verify**
- [ ] **Re-derive Eq. 4 by hand.** Check the coefficient 2(k − N/2)²/N.
- [ ] **Check the Q11 bullet points.** They make three claims: fixed-k probabilities → 0 like 2^−N; fixed
      windows → 0; ΔS for a fixed offset ≈ 2δ²k_B/N → 0, while for a fixed fraction ΔS ∝ N. Do you agree
      with each, and can you justify it?

**Likely defense questions**
- "What happens to the distribution with 10²³ coins? Why does that matter for thermodynamics?"
- "Derive σ for the binomial distribution." Variance = N·p·(1 − p) = N/4.

---

## 7. Probabilities and entropy for N = 100 + M (slides Q1–Q9) — `src/thermodynamics.py`, `main.py: part_probabilities`

**What was done**
- **M and N.** `m_from_nias` gives M = **arithmetic** mean of the last two NIA digits, rounded half-up. You
  chose this on 2026-10-29: the slides say "average" and the old template said "harmonic". So N = 100 + M.
- **Our system.** NIAs 100496704, 100523129, 100534604 and 100599060 give last two digits 04, 29, 04 and 60.
  Their mean is 24.25, so **M = 24 and N = 124**.
- **Parity of N.** N = 124 is even, so N/2 = 62 is an exact macrostate. The code still handles odd N
  (N/2 → ⌊N/2⌋), and `main.py` writes the matching sentence into the report (`\HalfNote`).
- **Questions 1–4.** `prob` gives Ω/2^N in log-space. `prob_range` sums with log-sum-exp.
  `prob_tails_range` converts a tails window to a heads window (heads = N − tails).
- **Questions 5–7.** ΔS/k_B = ln Ω(k₂)/Ω(k₁), for the transition **in the order the slide lists it**
  (k₁ → k₂). It is reported in units of k_B and in J/K (k_B = 1.380649 × 10⁻²³ J/K).
- **Question 8.** The waiting time for "just 8 heads" is 1/P(N, 8) tosses (mean of a geometric
  distribution), at one toss per second. It is also given in years and in ages of the Universe.
- **Question 9.** P(N/2)/P(M ± 10), interpreted as k = M + 10 and k = M − 10 heads.
- **Figure 4.** Panel (a) shows P_k with the ±10 band and markers at 30 and M ± 10. Panel (b) shows S/k_B
  with the states used in questions 5–8.
- **Our results for N = 124.** Memorise the orders of magnitude for the defense:

  | Question | Quantity | Value |
  |---|---|---|
  | 1 | P(k = 30) | 2.46 × 10⁻⁹ |
  | 2 | P(k = 62) | 0.0715 |
  | 3 | P(52 ≤ k ≤ 72) heads | 0.9411 |
  | 4 | P(42 ≤ tails ≤ 82) | 0.999796 |
  | 5 | ΔS, 87 → 62 heads | +10.29 k_B = 1.42 × 10⁻²² J/K |
  | 6 | ΔS, 72 → 62 heads | +1.61 k_B = 2.22 × 10⁻²³ J/K |
  | 7 | ΔS, 62 → 20 heads | −30.86 k_B = −4.26 × 10⁻²² J/K |
  | 8 | Mean wait for exactly 8 heads (1 toss/s) | 1.93 × 10²⁵ s ≈ 6.1 × 10¹⁷ years |
  | 9 | P(62)/P(34), P(62)/P(14) | 4.43 × 10⁵, 1.40 × 10¹⁸ |

  These come from `report/results.tex`. If `team.json` changes, rerun `python main.py` and the values
  update everywhere.

**What you must understand**
- **Each formula, and why P = Ω/2^N.** All microstates are equally likely for fair coins.
- **Why P(N/2) is "small" (≈ 0.07) yet N/2 is the most probable state.** There are N + 1 macrostates.
- **Why the waiting time is 1/p.** Look up the geometric distribution.

**What to review / verify (judgement calls; the team must agree)**
- [ ] **Finish `team.json`.** The NIAs are done. Still to fill in: the names of members 3–4 (currently
      "Author 3", "Author 4"), the GitHub handles (`user1`, `user3`, `user4`; Olivia's is `olivia614`) and
      the team name ("Group X"). Then rerun `python main.py` so the author block updates.
- [ ] **Rounding of M.** The guide doesn't specify it. We round half-up and report the exact mean as well.
      OK?
- [ ] **Q4 tails vs. heads.** "Between N/2 − 20 and N/2 + 20 tails". With N = 124 even, the window
      42–82 tails is the same as 42–82 heads, by symmetry. Be ready to explain why the answer is identical to
      a heads window. (For an odd N the window would be slightly asymmetric in heads.)
- [ ] **Q7 sign.** ΔS for "N/2 and 20 heads" is computed as N/2 → 20, so it is **negative**. Questions 5 and
      6 are computed towards N/2, so they are positive. Is that the reading you want, or should all three
      be reported as magnitudes?
- [ ] **Q9 interpretation.** "M ± 10, the number of heads in the average of your NIAs" is read as
      k = M ± 10. Another reading would be N/2 ± 10. Decide, and if in doubt **ask the professor**.
- [ ] **Recompute one value with a calculator**, e.g. P(30) = C(N, 30)/2^N, to make sure you trust the code.

**Likely defense questions**
- "What's your N? How did you get M?"
- "Calculate the entropy change between N/2 + 10 and N/2. What does the sign mean?"
- "How long would you wait for 8 heads, and why that formula?"

---

## 8. The Second Law (slides Q10) — report §4.3

**What was done**
- The report argues that nothing contradicts the Second Law. In statistical mechanics the law is
  **probabilistic**: low-entropy states are allowed but exponentially rare, with relative weight e^(ΔS/k_B).
  For N = 124 the fluctuations are visible: about 5.9% of tosses fall outside 62 ± 10, and going from 62 to
  20 heads is "only" e^30.9 ≈ 2.5 × 10¹³ times rarer than the reverse. For N = 10²³ such fluctuations are
  never seen.

**What you must understand**
- **The difference between microscopic reversibility and macroscopic irreversibility.** This is the core of
  the "statistical interpretation of entropy" in the rubric.
- **Why "most probable macrostate" equals "equilibrium" equals "maximum entropy".**

**What to review / verify**
- [ ] **Read §4.3–4.4 critically.** Is the reasoning clear? Would you phrase it differently? **This is the
      section where the professor will probe your understanding the most.** Rewrite it in your own words
      if needed.

---

## 9. The LaTeX report (15%) — `report/main.tex`

**What was done**
- The report is built on the team's template, with all of its sections.
- Every number is a macro from `report/results.tex`, e.g. `\Nval`, `\PthirtyHeads`, `\dSA`. Table rows come
  from `report/tables/*.tex` through `\tabinput`. That macro uses the TeX primitive `\@@input`, because
  plain `\input` breaks inside `tabular`.
- The author block comes from `report/authors.tex`, which is generated from `team.json`.
- **Page count:** 9 pages. The body is pages 1–7 (the limit is "about 5, maximum 8, excluding the title
  page"). Appendices: AI statement, Monte Carlo check, N = 7 listing, code excerpts.
- The report was compiled with Tectonic (XeLaTeX engine) with no warnings. `report/main.pdf` has the
  final numbers (N = 124) but still has placeholder names in the author block.

**What to review / verify**
- [ ] **Compile it yourself.** Upload `report/` to Overleaf, or use MiKTeX/TeX Live with `pdflatex`. Check
      that it still compiles with pdfLaTeX, since only XeLaTeX has been tested.
- [ ] **Read the whole report once, start to finish, for style.** The slides ask for "clear, simple,
      objective, terse" writing. Shorten anything you find wordy.
- [ ] **Check the length.** The body is 7 pages and the target is about 5. Consider trimming §2 (workflow)
      or moving the benchmark table to an appendix.
- [ ] **Update the team details.** Replace "Group X" (`team.json → team_name`) and check the date, which is
      `\today`.
- [ ] **Check the title page.** The slides say "excluding the title page". Decide whether to add a separate
      title page (`\clearpage` after the abstract).
- [ ] **Check the figures.** Are they readable when printed? Are the fonts large enough? Every figure
      should be referenced in the text, and it is now; check that this stays true after any edits.

---

## 10. AI transparency (10%) — `AI_STATEMENT.md`, report Appendix A

**What was done**
- **Prompt log.** Every prompt sent to Claude Code in this session is logged verbatim, including the
  Spanish ones with translations, together with the AI's answers and the files it generated.
- **Verification.** The verification steps and a table of **eight problems** found while auditing the AI's
  output are recorded: an overflow edge case, the MKL crash, timing bias from `tracemalloc`, noisy
  benchmark fits, the LaTeX `\input` problem, an invented GitHub handle, an unresolvable mantissa, and the
  memory-design risk.
- **The old "AIs are banned" footnote.** The statement explains that the old slides' footnote is superseded
  by the 2026/27 guide.
- **Planning record.** The planning transcript is in `docs/ai_plans/2026-10-29_initial_plan.md`.

**What to review / verify**
- [ ] **Fill in "Human modifications".** That column of the files table is still empty. The rubric grades
      "human verification steps and auditing of AI outputs", so write what **you** checked and changed.
- [ ] **Log everything else.** Every other member must add entries for **any** AI tool they used
      (ChatGPT, Copilot, …), using the template at the end of the file. This also applies to AI used while
      editing the report.
- [ ] **Log this guide.** The request for this review guide is itself an AI query; it is listed below.
- [ ] **Be ready for the obvious question.** "Which parts did the AI write, and how do you know they are
      correct?" Answer: the tests, the hand checks and the physics cross-checks.

---

## 11. Tests — `tests/`

**What was done**
- 68 tests:
  - enumeration vs. `math.comb`;
  - generator vs. vectorised vs. multiprocess paths;
  - log-space vs. exact values up to N = 1000 and at N = 10²³;
  - normalisation, symmetry and the ΔS sign;
  - the M formula and the waiting time;
  - the robust N_max estimator with an outlier;
  - Monte Carlo consistency.

**What you must understand**
- **How to run them live** (`python -m pytest -q`) and how to explain one test of your choice.

**What to review / verify**
- [ ] **Add at least one test yourself.** For example, test `to_string` or `prob_tails_range` for another N.
      It gives you a real commit and something to talk about in the defense.

---

## Suggested split of the review work

Everyone must still read everything, but assign one owner per block.

| Owner | Parts |
|-------|-------|
| Member A | 0, 1, 11: environment, Git, PRs, tests, `v1.0` tag |
| Member B | 2, 3: enumeration and benchmark (rerun on the chosen laptop) |
| Member C | 4, 5, 6: combinatorics, distributions, thermodynamic limit (derivation on paper) |
| Member D | 7, 8, 9, 10: N = 100 + M questions, Second Law text, LaTeX polish, AI statement |

## Final checklist before submission

- [ ] `team.json` is complete. Then rerun `python main.py` and recompile the PDF.
- [ ] `python -m pytest -q` passes on at least two members' laptops.
- [ ] Judgement calls in §7 (rounding, Q7 sign, Q9 reading) are agreed or confirmed with the professor.
- [ ] Body ≤ 8 pages; every figure and table is referenced; no placeholder text remains ("Group X",
      `user1`, `100XXXXXX`).
- [ ] `AI_STATEMENT.md` is complete for **all** members.
- [ ] All PRs are merged into `main` with peer approval, and `v1.0` is tagged.
- [ ] The repository URL and the compiled PDF are submitted to Aula Global.
- [ ] Each member has rehearsed the 5–10 min defense: open VS Code, run `main.py` and `pytest`, explain
      `iter_microstates` and `log_binom`, and answer "why doesn't this violate the Second Law?".
