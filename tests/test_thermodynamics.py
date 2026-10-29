import math

import numpy as np
import pytest

from src import thermodynamics as th


def test_m_from_nias_arithmetic_mean():
    # last two digits 29, 45, 12, 70 -> mean 39
    assert th.m_from_nias([100523129, 100000045, "100000012", 100000070]) == 39
    assert th.m_from_nias([100000010, 100000011]) == 11  # 10.5 rounds up
    assert th.system_size([100000050]) == 150


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
    n = 129
    h = th.half(n)
    assert th.entropy_change(n, h, h) == 0.0
    assert th.entropy_change(n, h + 25, h) > 0  # towards equilibrium
    assert th.entropy_change(n, h, 20) < 0
    exact = math.log(math.comb(n, h) / math.comb(n, h + 25))
    assert th.entropy_change(n, h + 25, h) == pytest.approx(exact, rel=1e-12)
    assert th.entropy_change_si(n, h + 25, h) == pytest.approx(th.K_B * exact)


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
    mean = (np.arange(n + 1) * counts).sum() / trials
    assert mean == pytest.approx(n / 2, abs=0.05)
