import math

import numpy as np
import pytest

from src import microstates as ms


def test_generator_yields_all_states_once():
    states = list(ms.iter_microstates(5))
    assert states == list(range(32))


def test_generator_rejects_negative():
    with pytest.raises(ValueError):
        list(ms.iter_microstates(-1))


def test_to_string_and_count_heads():
    assert ms.to_string(0b1010, 4) == "HTHT"
    assert ms.to_string(0, 3) == "TTT"
    assert ms.count_heads(0b1011) == 3


def test_macrostate_table_n7():
    table = ms.macrostate_table(7)
    assert sum(len(v) for v in table.values()) == 128
    for k, outcomes in table.items():
        assert len(outcomes) == math.comb(7, k)
        assert all(s.count("H") == k for s in outcomes)
        assert len(set(outcomes)) == len(outcomes)  # no duplicates


@pytest.mark.parametrize("n", range(0, 17))
def test_enumeration_matches_binomial(n):
    counts = ms.count_macrostates_enumeration(n)
    assert list(counts) == [math.comb(n, k) for k in range(n + 1)]


@pytest.mark.parametrize("n", [0, 1, 7, 12, 20])
def test_vectorized_matches_generator(n):
    v = ms.count_macrostates_vectorized(n, chunk_bits=8)
    assert list(v) == [math.comb(n, k) for k in range(n + 1)]


def test_vectorized_multiprocess():
    v = ms.count_macrostates_vectorized(18, chunk_bits=10, workers=2)
    assert list(v) == [math.comb(18, k) for k in range(19)]


def test_popcount_fallback_matches():
    arr = np.arange(1 << 12, dtype=np.uint64)
    expected = np.array([int(x).bit_count() for x in arr])
    assert np.array_equal(ms._popcount(arr), expected)


def test_extrapolate_n_max_exact_doubling():
    n = np.arange(10, 20)
    t = 1e-3 * 2.0 ** (n - 10)
    n_max, _, slope = ms.extrapolate_n_max(n, t, t_limit=1e-3 * 2.0**15)
    assert slope == pytest.approx(1.0)
    assert n_max == pytest.approx(25.0)


def test_per_state_cost_ignores_outlier():
    n = np.array([30, 31, 32, 33])
    t = 2e-9 * 2.0**n
    t[2] *= 0.3  # one anomalously fast run
    n_max, c = ms.per_state_cost(n, t, t_limit=2e-9 * 2.0**36)
    assert c == pytest.approx(2e-9, rel=0.5)
    assert 35.5 < n_max < 37
