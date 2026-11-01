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


def test_float_overflow_limits_are_exact():
    lim = cb.float_overflow_limits()
    fmax = int(cb.FLOAT_MAX)
    # smallest N such that the quantity exceeds the largest double
    assert 2 ** lim["total_states"] > fmax >= 2 ** (lim["total_states"] - 1)
    assert math.factorial(lim["factorial"]) > fmax >= math.factorial(lim["factorial"] - 1)
    n = lim["central_binomial"]
    assert math.comb(n, n // 2) > fmax >= math.comb(n - 1, (n - 1) // 2)
    assert (lim["total_states"], lim["factorial"], lim["central_binomial"]) == (1024, 171, 1030)


def test_binom_float_edges():
    assert cb.binom_float(10, -1) == 0.0
    assert cb.binom_float(10, 11) == 0.0
    assert cb.binom_float(10, 0) == 1.0
    assert cb.binom_float(10, 10) == 1.0
    assert cb.binom_float(60, 30) == pytest.approx(math.comb(60, 30), rel=1e-12)


def test_log_binom_out_of_range_is_minus_infinity():
    # Omega = 0 -> ln Omega = -inf -> P = 0 (no exception, no nan)
    with np.errstate(all="ignore"):
        assert cb.log_binom(107, -1) == -np.inf
        assert cb.log_binom(107, 108) == -np.inf


def test_log_binom_row_and_vector_input():
    row = cb.log_binom_row(12)
    assert row.shape == (13,)
    assert np.allclose(np.exp(row), [math.comb(12, k) for k in range(13)], rtol=1e-12)
    ks = np.array([0, 5, 12])
    assert np.allclose(cb.log_binom(12, ks), np.log([1, math.comb(12, 5), 1]))
    assert isinstance(cb.log_binom(12, 5), float)


@pytest.mark.parametrize("e", [4, 6, 8, 10])
def test_log_prob_central_peak_is_reliable_up_to_1e10(e):
    """ln P(N/2) against Stirling's formula, absolute error < 1e-4 up to N = 1e10."""
    n = 10.0**e
    stirling = -0.5 * math.log(math.pi * n / 2) - 1 / (4 * n)
    assert cb.log_binom(n, n / 2) - n * math.log(2) == pytest.approx(stirling, abs=1e-4)


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN LIMITATION (docs/AUDIT.md, finding F2): log-gamma subtracts numbers ~ N ln N, "
    "so ln P(N/2) is meaningless for N >~ 1e15. The report uses the analytic Stirling form there.",
)
def test_log_binom_not_reliable_at_1e23():
    n = 1e23
    assert cb.log_binom(n, n / 2) - n * math.log(2) == pytest.approx(
        -0.5 * math.log(math.pi * n / 2), abs=1e-3
    )


def test_log_binom_huge_n_leading_term_only():
    # What the old test really verified: only the dominant term N ln 2 (relative 1e-12).
    # It says nothing about the O(ln N) correction, hence the tests above.
    n = 1e23
    assert cb.log_binom(n, n / 2) == pytest.approx(n * math.log(2), rel=1e-12)
