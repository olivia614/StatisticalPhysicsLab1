import math

import numpy as np
import pytest

from src import combinatorics as cb


@pytest.mark.parametrize("n", [0, 1, 5, 20, 100, 129, 500, 1000])
def test_exact_matches_math_comb(n):
    for k in range(n + 1):
        assert cb.binom_exact(n, k) == math.comb(n, k)


def test_exact_out_of_range():
    assert cb.binom_exact(5, -1) == 0
    assert cb.binom_exact(5, 6) == 0


@pytest.mark.parametrize("n", [10, 50, 100, 199, 1000])
def test_log_binom_against_exact(n):
    ks = np.arange(n + 1)
    exact_logs = np.array([math.log(math.comb(n, int(k))) for k in ks])
    assert np.allclose(cb.log_binom(n, ks), exact_logs, rtol=1e-12, atol=1e-9)


def test_log_binom_symmetry():
    ks = np.arange(101)
    row = cb.log_binom_row(100)
    assert np.allclose(row, row[::-1])
    assert np.argmax(row) == 50


@pytest.mark.parametrize("n", [1, 7, 30, 100])
def test_multiplicities_sum_to_two_power_n(n):
    assert sum(cb.multiplicity_row(n)) == 2**n
    assert cb.multiplicity_row(n) == [math.comb(n, k) for k in range(n + 1)]


def test_slide_value_n100():
    # Peak of the distribution shown on slide 10 of the lab presentation
    assert cb.binom_exact(100, 50) == pytest.approx(1.0089134454556419e29, rel=1e-15)


def test_float_binomial_overflows():
    assert math.isinf(cb.binom_float(2000, 1000))
    assert cb.binom_float(100, 50) == pytest.approx(math.comb(100, 50), rel=1e-12)


def test_float_overflow_limits():
    lim = cb.float_overflow_limits()
    assert lim["total_states"] == 1024
    assert lim["factorial"] == 171  # 170! ~ 7.3e306 is the largest finite double
    assert 1020 < lim["central_binomial"] < 1035


def test_log_binom_huge_n():
    # Stirling check at N = 1e23: ln C(N, N/2) ~ N ln 2 - 0.5 ln(pi N / 2)
    n = 1e23
    expected = n * math.log(2) - 0.5 * math.log(math.pi * n / 2)
    assert cb.log_binom(n, n / 2) == pytest.approx(expected, rel=1e-12)
