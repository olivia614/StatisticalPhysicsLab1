import math

import numpy as np
import pytest

from src import thermodynamics as th


def test_m_from_nias_harmonic_mean():
    # last two digits 29, 45, 12, 70 -> harmonic mean 25.92 -> 26
    assert th.m_from_nias([100523129, 100000045, "100000012", 100000070]) == 26
    assert th.m_from_nias([100000010, 100000011]) == 10  # 10.476 rounds down
    assert th.system_size([100000050]) == 150  # one value: harmonic mean = the value


def test_m_from_nias_team():
    # team NIAs: last two digits 04, 29, 04, 60 -> harmonic mean 7.26 -> M = 7, N = 107
    nias = [100496704, 100523129, 100534604, 100599060]
    assert th.harmonic_mean([4, 29, 4, 60]) == pytest.approx(7.2575599583)
    assert th.m_from_nias(nias) == 7
    assert th.system_size(nias) == 107


def test_harmonic_mean_not_above_arithmetic_mean():
    digits = [4, 29, 4, 60]
    assert th.harmonic_mean(digits) < sum(digits) / len(digits)


def test_m_from_nias_zero_digit_is_undefined():
    with pytest.raises(ValueError):
        th.m_from_nias([100000100, 100000011])  # a NIA ending in 00


def test_m_from_nias_empty():
    with pytest.raises(ValueError):
        th.m_from_nias([])


@pytest.mark.parametrize("n", [20, 101, 129, 199])
def test_probabilities_normalised(n):
    assert th.prob_range(n, 0, n) == pytest.approx(1.0, rel=1e-12)
    assert np.sum(th.prob(n, np.arange(n + 1))) == pytest.approx(1.0, rel=1e-12)


def test_prob_matches_exact_fraction():
    n = 129
    for k in (8, 30, 64):
        assert th.prob(n, k) == pytest.approx(math.comb(n, k) / 2**n, rel=1e-12)


def test_n100_peak_matches_slide():
    assert th.prob(100, 50) == pytest.approx(0.0795892373871787, rel=1e-12)


def test_heads_tails_range_symmetry():
    n = 131
    h = th.half(n)
    # for odd N the tails window is the mirror of the heads window
    assert th.prob_tails_range(n, h - 20, h + 20) == pytest.approx(
        th.prob_range(n, n - (h + 20), n - (h - 20))
    )
    n = 130
    h = th.half(n)
    assert th.prob_tails_range(n, h - 20, h + 20) == pytest.approx(
        th.prob_range(n, h - 20, h + 20)
    )


def test_entropy_change_properties():
    # handout definition: Delta S_{k1 k2} = S(k1) - S(k2)
    n = 129
    h = th.half(n)
    assert th.entropy_change(n, h, h) == 0.0
    assert th.entropy_change(n, h + 25, h) < 0  # k1 less disordered than k2 (question 5)
    assert th.entropy_change(n, h + 10, h) < 0  # question 6
    assert th.entropy_change(n, h, 20) > 0  # k1 = N/2 is the most disordered (question 7)
    exact = math.log(math.comb(n, h + 25) / math.comb(n, h))
    assert th.entropy_change(n, h + 25, h) == pytest.approx(exact, rel=1e-12)
    assert th.entropy_change_si(n, h + 25, h) == pytest.approx(th.K_B * exact)


def test_entropy_change_is_antisymmetric_and_equals_entropy_difference():
    n = 107
    assert th.entropy_change(n, 63, 53) == pytest.approx(-th.entropy_change(n, 53, 63))
    assert th.entropy_change(n, 63, 53) == pytest.approx(th.entropy(n, 63) - th.entropy(n, 53))


def test_wait_time_is_inverse_probability():
    n = 129
    assert th.expected_wait_seconds(n, 8) == pytest.approx(2**n / math.comb(n, 8), rel=1e-12)
    assert th.log10_expected_wait_seconds(n, 8) == pytest.approx(
        math.log10(2**n / math.comb(n, 8)), rel=1e-12
    )


def test_likelihood_ratio():
    assert th.likelihood_ratio(100, 50, 40) == pytest.approx(
        math.comb(100, 50) / math.comb(100, 40), rel=1e-12
    )


def test_gaussian_approaches_binomial():
    n = 10_000
    ks = np.arange(4900, 5101)
    rel_err = np.abs(th.gaussian_approx(n, ks) / th.prob(n, ks) - 1)
    assert rel_err.max() < 1e-2


def test_relative_width():
    assert th.relative_width(1e23) == pytest.approx(10**-11.5)


def test_simulation_consistent_with_exact():
    rng = np.random.default_rng(1)
    n, trials = 50, 200_000
    counts = th.simulate_tosses(n, trials, rng)
    assert counts.sum() == trials
    k = np.arange(n + 1)
    mean = (k * counts).sum() / trials
    var = (k**2 * counts).sum() / trials - mean**2
    assert mean == pytest.approx(n / 2, abs=0.05)
    assert var == pytest.approx(n / 4, rel=0.03)  # binomial variance N/4
    # whole distribution, not only the mean: chi-square against the exact P_k
    expected = trials * th.prob(n, k)
    use = expected >= 10
    chi2 = float(np.sum((counts[use] - expected[use]) ** 2 / expected[use]))
    dof = int(use.sum()) - 1
    assert chi2 < dof + 5 * math.sqrt(2 * dof)  # within 5 sigma of the chi-square mean


def test_simulation_without_rng_and_shape():
    counts = th.simulate_tosses(10, 500)
    assert counts.shape == (11,) and counts.sum() == 500


# --------------------------------------------------------------------------- #
# Audit additions: independent (exact-fraction) checks of every quantity in the report
# --------------------------------------------------------------------------- #


def _exact_p(n, k):
    from fractions import Fraction

    return Fraction(math.comb(n, k), 2**n)


def test_harmonic_mean_known_values():
    assert th.harmonic_mean([1, 2, 4]) == pytest.approx(12 / 7)
    assert th.harmonic_mean([5]) == 5
    assert th.harmonic_mean([8, 8, 8]) == pytest.approx(8)
    with pytest.raises(ValueError):
        th.harmonic_mean([3, 0])
    with pytest.raises(ValueError):
        th.harmonic_mean([3, -1])


def test_system_size_and_half():
    assert th.half(107) == 53 and th.half(110) == 55
    assert th.system_size([100000010]) == 110  # one NIA ending in 10 -> M = 10
    assert th.prob(107, 53) == pytest.approx(th.prob(107, 54), rel=1e-12)  # tie for odd N


def test_team_question_values_n107_exact():
    """Every number of questions 1-9 for N = 107 against exact rational arithmetic."""
    n, h = 107, 53
    assert th.prob(n, 30) == pytest.approx(float(_exact_p(n, 30)), rel=1e-12)
    assert th.prob(n, h) == pytest.approx(float(_exact_p(n, h)), rel=1e-12)
    heads = sum(_exact_p(n, k) for k in range(h - 10, h + 11))
    assert th.prob_range(n, h - 10, h + 10) == pytest.approx(float(heads), rel=1e-12)
    # question 4: tails in [h-20, h+20]  <=>  heads in [n-(h+20), n-(h-20)] = [34, 74]
    tails = sum(_exact_p(n, k) for k in range(34, 75))
    assert th.prob_tails_range(n, h - 20, h + 20) == pytest.approx(float(tails), rel=1e-12)
    # questions 5-7: Delta S(k1 k2) = ln Omega(k1) - ln Omega(k2)
    for k1, k2 in ((h + 25, h), (h + 10, h), (h, 20)):
        exact = math.log(math.comb(n, k1)) - math.log(math.comb(n, k2))
        assert th.entropy_change(n, k1, k2) == pytest.approx(exact, rel=1e-12)
        assert th.entropy_change_si(n, k1, k2) == pytest.approx(th.K_B * exact, rel=1e-12)
    # question 8
    assert th.log10_expected_wait_seconds(n, 8) == pytest.approx(
        math.log10(2**n / math.comb(n, 8)), rel=1e-12
    )
    # question 9
    assert th.likelihood_ratio(n, h, h + 10) == pytest.approx(
        math.comb(n, h) / math.comb(n, h + 10), rel=1e-12
    )


def test_entropy_values_and_units():
    assert th.entropy(107, 53) == pytest.approx(math.log(math.comb(107, 53)), rel=1e-12)
    assert th.entropy(107, 0) == pytest.approx(0.0, abs=1e-12)  # one microstate: S = 0
    assert th.K_B == 1.380649e-23  # exact SI-2019 value


def test_prob_range_clipping_and_empty():
    assert th.prob_range(10, -5, 20) == pytest.approx(1.0)  # clipped to [0, N]
    assert th.prob_range(10, 8, 3) == 0.0  # empty window
    assert th.prob_range(10, 11, 20) == 0.0  # entirely outside
    assert th.prob_range(10, 5, 5) == pytest.approx(th.prob(10, 5))


def test_prob_tails_range_uses_heads_equals_n_minus_tails():
    # asymmetric window: 0..3 tails of 10 coins == 7..10 heads
    n = 10
    assert th.prob_tails_range(n, 0, 3) == pytest.approx(
        float(sum(_exact_p(n, k) for k in range(7, 11))), rel=1e-12
    )


def test_wait_time_overflow_is_handled():
    # P(5000, 8) ~ 1e-1500: 1/P overflows a double, the log10 version must not
    assert th.expected_wait_seconds(5000, 8) == math.inf
    assert th.log10_expected_wait_seconds(5000, 8) == pytest.approx(
        5000 * math.log10(2) - math.log10(math.comb(5000, 8)), rel=1e-9
    )


def test_wait_time_toss_rate():
    assert th.expected_wait_seconds(10, 3, toss_rate_hz=10.0) == pytest.approx(
        2**10 / math.comb(10, 3) / 10.0
    )


def test_gaussian_peak_and_scalar_type():
    assert isinstance(th.gaussian_approx(100, 50), float)
    # P(N/2) -> sqrt(2/(pi N)); this is the formula behind the report's N = 1e23 numbers
    n = 1e23
    assert th.gaussian_approx(n, n / 2) == pytest.approx(math.sqrt(2 / (math.pi * n)), rel=1e-12)
    assert -0.5 * math.log10(math.pi * n / 2) == pytest.approx(
        math.log10(th.gaussian_approx(n, n / 2)), abs=1e-9
    )
    # sum of the Gaussian over k ~ 1 (normalisation)
    ks = np.arange(4000, 6001)
    assert th.gaussian_approx(10_000, ks).sum() == pytest.approx(1.0, abs=1e-3)


def test_log10_prob_fraction_edges_and_differences():
    assert th.log10_prob_fraction(100, 0.0) == pytest.approx(-100 * math.log10(2))
    assert th.log10_prob_fraction(100, 1.0) == pytest.approx(-100 * math.log10(2))
    # Leading order only: on its own it is wrong by the prefactor, but *differences* are right.
    n = 1e5
    approx = th.log10_prob_fraction(n, 0.6) - th.log10_prob_fraction(n, 0.5)
    exact = (th.log_prob(n, 0.6 * n) - th.log_prob(n, 0.5 * n)) / math.log(10)
    assert approx == pytest.approx(exact, rel=1e-3)
    assert th.log10_prob_fraction(n, 0.5) == 0.0  # documented caveat


def test_fixed_offset_entropy_change_small_n_against_exact():
    # Delta S ~ -2 d^2 / N for a fixed offset d (used in the report for N -> infinity)
    n, d = 10_000, 10
    exact = math.log(math.comb(n, n // 2 + d) / math.comb(n, n // 2))
    assert th.entropy_change(n, n // 2 + d, n // 2) == pytest.approx(exact, rel=1e-6)
    assert exact == pytest.approx(-2 * d**2 / n, rel=1e-2)


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN LIMITATION (docs/AUDIT.md, finding F2): entropy differences from log-gamma "
    "are lost to rounding for N >~ 1e9; the true value here is -2 d^2/N = -2e-9.",
)
def test_entropy_change_fixed_offset_huge_n_not_reliable():
    n, d = 1e11, 10
    assert th.entropy_change(n, n / 2 + d, n / 2) == pytest.approx(-2 * d**2 / n, rel=0.1)


@pytest.mark.parametrize("n", [10, 107, 110])
def test_tails_window_equals_heads_window_for_a_fair_coin(n):
    """Omega(N, k) = Omega(N, N-k), so P(tails in [a,b]) = P(heads in [a,b]) for any N.

    This is why question 4 gives the same number whether the window is read as tails or
    heads, and why replacing ``prob_range(n, n - t_hi, n - t_lo)`` by
    ``prob_range(n, t_lo, t_hi)`` is an *equivalent* change that no test can detect
    (found by the mutation analysis in docs/AUDIT.md).
    """
    for a, b in ((0, 3), (n // 2 - 20, n // 2 + 20), (2, n - 2)):
        assert th.prob_tails_range(n, a, b) == pytest.approx(th.prob_range(n, a, b), rel=1e-12)
