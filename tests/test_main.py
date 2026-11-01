"""Tests for main.py: number formatting, team files, and every part of the report.

Before this audit main.py (about 570 lines, where the numbers of the report are
produced) had no tests at all. Each ``part_*`` function is run here with its output
directories redirected to a temporary folder, and the macros it writes are compared
with independent exact arithmetic (``math.comb``, ``fractions``).
"""

import json
import math
import re
import shutil
import sys
from fractions import Fraction

import pytest

import main

TEAM_NIAS = ["100496704", "100523129", "100534604", "100599060"]  # N = 107


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def macro_dict(macros):
    out = {}
    for line in macros.lines[1:]:
        m = re.fullmatch(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}", line)
        assert m, f"malformed macro line: {line!r}"
        out[m.group(1)] = m.group(2)
    return out


def body(text):
    m = re.fullmatch(r"\\ensuremath\{(.*)\}", text)
    return m.group(1) if m else text


def num(text):
    """Float value of a macro such as ``\\ensuremath{1.96\\times10^{-6}}``."""
    b = body(text)
    m = re.fullmatch(r"(-?[\d.]+)\\times10\^\{(-?\d+)\}", b)
    return float(m.group(1)) * 10 ** int(m.group(2)) if m else float(b)


def log10_of(text):
    """log10 of the value (works for 10^-871, which underflows as a float)."""
    b = body(text)
    m = re.fullmatch(r"(-?[\d.]+)\\times10\^\{(-?\d+)\}", b)
    assert m, b
    return math.log10(float(m.group(1))) + int(m.group(2))


@pytest.fixture
def tmp_dirs(monkeypatch, tmp_path):
    for name in ("FIG", "TAB", "DATA"):
        d = tmp_path / name.lower()
        d.mkdir()
        monkeypatch.setattr(main, name, d)
    monkeypatch.setattr(main, "REPORT", tmp_path)
    return tmp_path


# --------------------------------------------------------------------------- #
# sci / sci_log10 / MacroWriter
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "x, expected",
    [
        (0, "0"),
        (1.96286e-6, r"1.96\times10^{-6}"),
        (1.243e31, r"1.24\times10^{31}"),
        (0.0766, "0.0766"),
        (12.345, "12.3"),
        (999.96, "1000"),
        (9.9996e-5, r"1.00\times10^{-4}"),  # mantissa rounds up to 10 -> renormalised
        (-1.59e-22, r"-1.59\times10^{-22}"),
        (-9.9996e-5, r"-1.00\times10^{-4}"),  # regression: used to give -10.00\times10^{-5}
        (-9.9996e-23, r"-1.00\times10^{-22}"),
        (-0.0123, "-0.0123"),
        (float("inf"), r"\infty"),
    ],
)
def test_sci(x, expected):
    assert main.sci(x) == expected


def test_sci_digits():
    assert main.sci(1.23456e10, 5) == r"1.2346\times10^{10}"
    assert main.sci(1.5e-9, 1) == r"2\times10^{-9}"


def test_sci_log10():
    assert main.sci_log10(-871.0) == r"1.00\times10^{-871}"
    assert main.sci_log10(20.697) == r"4.98\times10^{20}"
    assert main.sci_log10(2.99999) == r"1.00\times10^{3}"  # rounds up to 10 -> renormalised


def test_macrowriter(tmp_path):
    w = main.MacroWriter()
    w.add("Nval", "107")
    w.add("NisOdd", "odd", math_mode=False)
    path = tmp_path / "results.tex"
    w.write(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("% Auto-generated")
    assert r"\newcommand{\Nval}{\ensuremath{107}}" in lines
    assert r"\newcommand{\NisOdd}{odd}" in lines


# --------------------------------------------------------------------------- #
# team files
# --------------------------------------------------------------------------- #


def test_load_team_missing_file(tmp_path):
    assert main.load_team(tmp_path / "nope.json") == {"team_name": "Team", "members": []}


def test_team_nias_ignores_placeholders():
    team = {"members": [{"nia": "100496704"}, {"nia": ""}, {"nia": "TBD"}, {}, {"nia": 100523129}]}
    assert main.team_nias(team) == ["100496704", 100523129]


def test_team_json_in_repo_is_valid():
    team = main.load_team(main.ROOT / "team.json")
    assert len(main.team_nias(team)) == 4
    assert sorted(main.team_nias(team)) == sorted(TEAM_NIAS)


def test_write_authors(tmp_path):
    team = {
        "team_name": "Group X",
        "members": [{"name": "Ana Pérez", "nia": "100000001", "github": "anaperez"}],
    }
    path = tmp_path / "authors.tex"
    main.write_authors(team, path)
    text = path.read_text(encoding="utf-8")
    assert "Group X" in text and "Ana Pérez" in text and "100000001" in text
    assert r"\texttt{@anaperez}" in text


# --------------------------------------------------------------------------- #
# Part 1: enumeration table for N = 7
# --------------------------------------------------------------------------- #


def test_part_enumeration(tmp_dirs):
    w = main.MacroWriter()
    main.part_enumeration(w)
    assert macro_dict(w)["NsevenTotal"] == r"\ensuremath{128}"
    rows = (main.TAB / "n7_summary.tex").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 8
    counts = [int(r.split("&")[3]) for r in rows]
    assert counts == [1, 7, 21, 35, 35, 21, 7, 1]  # Pascal row of N = 7
    # listed from 7 heads down to 0 heads, as in the lab handout's Table 1
    assert rows[0].startswith(r"7 & 0 & \texttt{HHHHHHH}")
    assert rows[-1].startswith(r"0 & 7 & \texttt{TTTTTTT}")
    full = (main.TAB / "n7_full.tex").read_text(encoding="utf-8")
    outcomes = re.findall(r"\b[HT]{7}\b", full)
    assert len(outcomes) == 128 == len(set(outcomes))  # all 128 listed, no duplicates


# --------------------------------------------------------------------------- #
# Part 2: benchmark post-processing (synthetic timings: the timing run itself is long)
# --------------------------------------------------------------------------- #


def _synthetic_benchmark(c_gen=300e-9, c_vec=4e-9):
    rec = lambda ns, c: [  # noqa: E731
        {"n": n, "t_mean": c * 2.0**n, "t_std": 0.01 * c * 2.0**n, "mem_peak_mb": 5.0} for n in ns
    ]
    return {
        "workers": 16,
        "time_limit_s": 300.0,
        "generator": rec(range(16, 27), c_gen),
        "vectorized": rec(range(26, 36), c_vec),
        "verified": {"n": 36, "t": 99.0, "correct": True},
        "verified_runs": [{"n": 36, "t": 99.0, "correct": True}],
    }


def test_part_benchmark_placeholder_without_data(tmp_dirs):
    w = main.MacroWriter()
    main.part_benchmark(w, None)
    assert "run main.py --benchmark" in macro_dict(w)["NmaxGen"]
    assert "Run" in (main.TAB / "benchmark.tex").read_text(encoding="utf-8")


def test_part_benchmark_with_data(tmp_dirs):
    w = main.MacroWriter()
    main.part_benchmark(w, _synthetic_benchmark())
    m = macro_dict(w)
    # exact doubling law t = c 2^N  ->  N_max = log2(300 / c), slope 1, cost c
    assert num(m["NmaxGen"]) == pytest.approx(math.log2(300 / 300e-9), abs=0.05)
    assert num(m["NmaxVec"]) == pytest.approx(math.log2(300 / 4e-9), abs=0.05)
    assert num(m["SlopeGen"]) == pytest.approx(1.0, abs=1e-3)
    assert num(m["CostGen"]) == pytest.approx(300.0, rel=1e-2)  # ns per state
    assert num(m["CostVec"]) == pytest.approx(4.0, rel=1e-2)
    assert m["NverifyVal"] == r"\ensuremath{36}" and num(m["TverifyVal"]) == 99
    table = (main.TAB / "benchmark.tex").read_text(encoding="utf-8")
    assert table.count(r"\\") >= 6 and "(1 run)" in table
    assert (main.FIG / "fig_benchmark.pdf").stat().st_size > 1000


def test_fits_matches_theory():
    f = main._fits(_synthetic_benchmark(c_gen=2e-7, c_vec=5e-9))
    assert f["generator"]["c"] == pytest.approx(2e-7, rel=1e-9)
    assert f["vectorized"]["n_limit"] == pytest.approx(math.log2(300 / 5e-9), abs=1e-6)


# --------------------------------------------------------------------------- #
# Part 3: distributions N = 20, 50, 80, 100 and the Monte Carlo check
# --------------------------------------------------------------------------- #


def test_part_distributions(tmp_dirs):
    w = main.MacroWriter()
    main.part_distributions(w)
    m = macro_dict(w)
    assert num(m["OmegaPeakHundred"]) == pytest.approx(math.comb(100, 50), rel=1e-3)
    assert num(m["OmegaPeakTwenty"]) == pytest.approx(math.comb(20, 10), rel=1e-3)
    assert num(m["PPeakHundred"]) == pytest.approx(math.comb(100, 50) / 2**100, abs=5e-5)
    assert (num(m["LimTotal"]), num(m["LimFact"]), num(m["LimCentral"])) == (1024, 171, 1030)
    # Monte Carlo agrees with the exact distribution (chi2 / dof ~ 1)
    assert 0.4 < num(m["MCchi"]) / num(m["MCdof"]) < 1.8
    assert num(m["MCmean"]) == pytest.approx(50.0, abs=0.1)
    for f in ("fig_distributions.pdf", "fig_simulation.pdf"):
        assert (main.FIG / f).stat().st_size > 1000


# --------------------------------------------------------------------------- #
# Part 4: probabilities and entropy for the team's N (the numbers of Table 3)
# --------------------------------------------------------------------------- #


def test_part_probabilities_team_n107_against_exact(tmp_dirs):
    w = main.MacroWriter()
    main.part_probabilities(w, TEAM_NIAS)
    m = macro_dict(w)
    n, h = 107, 53
    P = lambda k: Fraction(math.comb(n, k), 2**n)  # noqa: E731
    S = lambda k: math.log(math.comb(n, k))  # noqa: E731

    # N, M and the parity note
    assert (num(m["Mval"]), num(m["Nval"]), num(m["Nhalf"])) == (7, 107, 53)
    assert num(m["Mexact"]) == pytest.approx(7.26, abs=1e-9)  # harmonic mean
    assert m["NisOdd"] == "odd" and "odd" in m["HalfNote"]

    # questions 1-4
    assert num(m["PthirtyHeads"]) == pytest.approx(float(P(30)), rel=6e-3)
    assert num(m["PhalfHeads"]) == pytest.approx(float(P(h)), rel=1e-3)
    assert num(m["PtenHeads"]) == pytest.approx(float(sum(P(k) for k in range(43, 64))), rel=1e-3)
    assert num(m["PtwentyTails"]) == pytest.approx(float(sum(P(k) for k in range(34, 75))), rel=1e-5)

    # questions 5-7: handout definition Delta S(k1 k2) = S(k1) - S(k2)
    for tag, (k1, k2) in {"A": (78, 53), "B": (63, 53), "C": (53, 20)}.items():
        assert (num(m[f"dS{tag}from"]), num(m[f"dS{tag}to"])) == (k1, k2)
        assert num(m[f"dS{tag}"]) == pytest.approx(S(k1) - S(k2), abs=1e-3)
        assert num(m[f"dS{tag}SI"]) == pytest.approx(main.th.K_B * (S(k1) - S(k2)), rel=6e-3)
        assert num(m[f"dS{tag}ratio"]) == pytest.approx(
            math.comb(n, k1) / math.comb(n, k2), rel=6e-3
        )
    assert num(m["dSA"]) < 0 and num(m["dSB"]) < 0 and num(m["dSC"]) > 0  # sign convention

    # question 8: mean waiting time for exactly 8 heads
    assert log10_of(m["WaitEightS"]) == pytest.approx(math.log10(2**n / math.comb(n, 8)), abs=3e-3)
    years = 365.25 * 24 * 3600
    assert log10_of(m["WaitEightYears"]) == pytest.approx(
        math.log10(2**n / math.comb(n, 8) / years), abs=3e-3
    )

    # question 9: N/2 against N/2 +- 10
    assert (num(m["MPlus"]), num(m["MMinus"])) == (63, 43)
    assert num(m["RatioPlus"]) == pytest.approx(math.comb(n, 53) / math.comb(n, 63), rel=6e-3)
    assert num(m["RatioMinus"]) == pytest.approx(math.comb(n, 53) / math.comb(n, 43), rel=6e-3)

    assert (main.FIG / "fig_probabilities.pdf").stat().st_size > 1000


def test_part_probabilities_even_n(tmp_dirs):
    w = main.MacroWriter()
    main.part_probabilities(w, ["100000010"])  # last two digits 10 -> M = 10, N = 110
    m = macro_dict(w)
    assert (num(m["Nval"]), num(m["Nhalf"])) == (110, 55)
    assert m["NisOdd"] == "even" and "even" in m["HalfNote"]
    assert num(m["PhalfHeads"]) == pytest.approx(math.comb(110, 55) / 2**110, rel=1e-3)


def test_part_probabilities_rejects_nia_ending_in_00(tmp_dirs):
    with pytest.raises(ValueError, match="undefined"):
        main.part_probabilities(main.MacroWriter(), ["100000100", "100000011"])


# --------------------------------------------------------------------------- #
# Part 5: thermodynamic limit N ~ 1e23 (analytic formulas, no log-gamma)
# --------------------------------------------------------------------------- #


def test_part_thermo_limit(tmp_dirs):
    w = main.MacroWriter()
    main.part_thermo_limit(w)
    m = macro_dict(w)
    big = 1e23
    assert num(m["TLwidth"]) == pytest.approx(1 / math.sqrt(big), rel=6e-3)  # 3.16e-12
    assert num(m["TLsigma"]) == pytest.approx(math.sqrt(big) / 2, rel=6e-3)  # 1.58e11
    assert log10_of(m["TLPhalf"]) == pytest.approx(-0.5 * math.log10(math.pi * big / 2), abs=3e-3)
    # |Delta S| for k/N = 0.501 -> 0.5:  N [ln 2 - H(0.501)]  ~ 2 N d^2 with d = 1e-3
    d = 1e-3
    x = 0.5 + d
    exact_ds = big * (math.log(2) + x * math.log(x) + (1 - x) * math.log(1 - x))
    assert num(m["TLdSkB"]) == pytest.approx(exact_ds, rel=6e-3)
    assert num(m["TLdSSI"]) == pytest.approx(main.th.K_B * exact_ds, rel=6e-3)
    assert num(m["TLdSkB"]) > 0  # printed as a magnitude
    # 1e-10 deviation = 63 sigma; Gaussian tail 2 Phi(-z) ~ 2 exp(-z^2/2) / (z sqrt(2 pi))
    z = 2e-10 * math.sqrt(big)
    assert num(m["TLz"]) == round(z)
    tail = (math.log(2) - z**2 / 2 - math.log(z * math.sqrt(2 * math.pi))) / math.log(10)
    assert log10_of(m["TLtail"]) == pytest.approx(tail, abs=0.02)
    # P(exactly 8 heads) = 10^(-N log10(2) + O(log N)): only the leading digits are meaningful
    mm = re.fullmatch(r"\\ensuremath\{10\^\{(-?[\d.]+)\\times10\^\{(\d+)\}\}\}", m["TLPeight"])
    assert mm
    assert float(mm.group(1)) * 10 ** int(mm.group(2)) == pytest.approx(-big * math.log10(2), rel=6e-3)
    assert 0 < num(m["GaussErrHundred"]) < 1  # percent: Gaussian vs exact peak at N = 100
    assert (main.FIG / "fig_thermo_limit.pdf").stat().st_size > 1000


# --------------------------------------------------------------------------- #
# Whole program
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def full_run(tmp_path_factory):
    """Run main.main() once with the repository's own team.json and benchmark.json."""
    real_root, real_report = main.ROOT, main.REPORT
    out = tmp_path_factory.mktemp("full_run")
    report = out / "report"
    (report / "data").mkdir(parents=True)
    shutil.copy(real_root / "team.json", out / "team.json")
    bench = real_report / "data" / "benchmark.json"
    if bench.exists():
        shutil.copy(bench, report / "data" / "benchmark.json")
    mp = pytest.MonkeyPatch()
    for name, val in {
        "ROOT": out,
        "REPORT": report,
        "FIG": report / "figures",
        "TAB": report / "tables",
        "DATA": report / "data",
    }.items():
        mp.setattr(main, name, val)
    mp.setattr(sys, "argv", ["main.py"])
    try:
        main.main()
        yield report
    finally:
        mp.undo()


def test_main_writes_every_output(full_run):
    for f in ("fig_distributions", "fig_probabilities", "fig_simulation", "fig_thermo_limit"):
        assert (full_run / "figures" / f"{f}.pdf").stat().st_size > 1000
    for f in ("n7_summary.tex", "n7_full.tex", "benchmark.tex"):
        assert (full_run / "tables" / f).exists()
    assert (full_run / "authors.tex").exists()
    assert (full_run / "results.tex").exists()


def test_results_tex_macro_names_are_valid_and_unique(full_run):
    names = re.findall(
        r"\\newcommand\{\\([^}]*)\}", (full_run / "results.tex").read_text(encoding="utf-8")
    )
    assert len(names) > 60
    assert all(re.fullmatch(r"[A-Za-z]+", n) for n in names), "LaTeX macro names must be letters"
    assert len(names) == len(set(names)), "a duplicated name makes LaTeX fail"


def test_committed_results_tex_is_up_to_date(full_run):
    """results.tex in the repo must be what main.py produces from team.json today.

    This catches the classic mistake of editing team.json (or the code) and forgetting to
    re-run ``python main.py``. Monte-Carlo macros (MC*) are excluded: they depend on the
    NumPy version's random stream.
    """
    keep = lambda t: "\n".join(  # noqa: E731
        ln for ln in t.splitlines() if not re.match(r"\\newcommand\{\\MC", ln)
    )
    fresh = (full_run / "results.tex").read_text(encoding="utf-8")
    committed = (main.REPORT / "results.tex").read_text(encoding="utf-8")
    assert keep(fresh) == keep(committed), "report/results.tex is stale: run `python main.py`"


def test_main_nias_override_and_errors(tmp_path, monkeypatch):
    for name, sub in (("FIG", "f"), ("TAB", "t"), ("DATA", "d")):
        monkeypatch.setattr(main, name, tmp_path / sub)
    monkeypatch.setattr(main, "REPORT", tmp_path)
    monkeypatch.setattr(main, "ROOT", tmp_path)
    team = tmp_path / "team.json"
    team.write_text(json.dumps({"team_name": "T", "members": []}), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["main.py", "--team", str(team)])
    with pytest.raises(SystemExit):  # no NIAs anywhere
        main.main()

    monkeypatch.setattr(
        sys, "argv", ["main.py", "--team", str(team), "--nias", "100000010", "100000011"]
    )
    main.main()  # harmonic mean 10.476 -> M = 10 -> N = 110
    text = (tmp_path / "results.tex").read_text(encoding="utf-8")
    assert r"\newcommand{\Nval}{\ensuremath{110}}" in text


# --------------------------------------------------------------------------- #
# run_benchmark orchestration (the real timing study takes minutes: heavy parts are stubbed)
# --------------------------------------------------------------------------- #


def _stub_benchmark(monkeypatch, tmp_dirs, clock):
    import numpy as np

    data = _synthetic_benchmark()
    calls = {"verified_n": []}

    def fake_benchmark(n_values, method="vectorized", repeats=3, workers=None):
        return data[method]

    def fake_count(n, workers=1, **kw):
        calls["verified_n"].append(n)
        return np.array([math.comb(n, k) for k in range(n + 1)], dtype=np.int64)

    monkeypatch.setattr(main.ms, "benchmark", fake_benchmark)
    monkeypatch.setattr(main.ms, "count_macrostates_vectorized", fake_count)
    ticks = iter(clock)
    monkeypatch.setattr(main.time, "perf_counter", lambda: next(ticks))
    return calls


def test_run_benchmark_without_verification(monkeypatch, tmp_dirs):
    _stub_benchmark(monkeypatch, tmp_dirs, clock=[])
    data = main.run_benchmark(verify_nmax=False)
    assert set(data) == {"workers", "time_limit_s", "generator", "vectorized"}
    saved = json.loads((main.DATA / "benchmark.json").read_text(encoding="utf-8"))
    assert saved["time_limit_s"] == 300.0 and len(saved["generator"]) == 11


def test_run_benchmark_verification_steps_down_when_over_time_limit(monkeypatch, tmp_dirs):
    # N_max from the synthetic timings is 36.1 -> first try N = 36 takes 400 s (> 300 s limit),
    # so the code must step down to N = 35, which takes 100 s and is accepted.
    calls = _stub_benchmark(monkeypatch, tmp_dirs, clock=[0.0, 400.0, 0.0, 100.0])
    data = main.run_benchmark(verify_nmax=True)
    assert calls["verified_n"] == [36, 35]
    assert [r["n"] for r in data["verified_runs"]] == [36, 35]
    assert data["verified"]["n"] == 35 and data["verified"]["t"] == 100.0
    assert all(r["correct"] for r in data["verified_runs"])


def test_main_warns_about_members_without_nia(tmp_path, monkeypatch, capsys):
    for name, sub in (("FIG", "f"), ("TAB", "t"), ("DATA", "d")):
        monkeypatch.setattr(main, name, tmp_path / sub)
    monkeypatch.setattr(main, "REPORT", tmp_path)
    monkeypatch.setattr(main, "ROOT", tmp_path)
    team = tmp_path / "team.json"
    team.write_text(
        json.dumps({"team_name": "T", "members": [{"nia": "100000010"}, {"name": "No NIA yet"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["main.py", "--team", str(team)])
    main.main()
    assert "WARNING: 1 member(s)" in capsys.readouterr().out
