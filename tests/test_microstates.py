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


def test_popcount_matches_bit_count():
    arr = np.arange(1 << 12, dtype=np.uint64)
    expected = np.array([int(x).bit_count() for x in arr])
    assert np.array_equal(ms._popcount(arr), expected)


def test_popcount_swar_fallback_is_really_executed(monkeypatch):
    """The NumPy 1.x fallback must be tested explicitly.

    On NumPy >= 2 ``_popcount`` calls ``np.bitwise_count`` and never reaches the
    SWAR code, so the old version of this test did not exercise it (0% coverage
    of those lines). Here ``np.bitwise_count`` is removed to force the fallback.
    """
    monkeypatch.delattr(np, "bitwise_count", raising=False)
    assert not hasattr(np, "bitwise_count")
    arr = np.concatenate(
        [
            np.arange(1 << 12, dtype=np.uint64),
            np.array([2**63, 2**64 - 1, 0xAAAAAAAAAAAAAAAA, 0x5555555555555555], dtype=np.uint64),
        ]
    )
    expected = np.array([int(x).bit_count() for x in arr])
    assert np.array_equal(ms._popcount(arr), expected)


def test_vectorized_uses_fallback_too(monkeypatch):
    monkeypatch.delattr(np, "bitwise_count", raising=False)
    v = ms.count_macrostates_vectorized(14, chunk_bits=6)
    assert list(v) == [math.comb(14, k) for k in range(15)]


@pytest.mark.parametrize("bad_n", [-1, 64, 100])
def test_vectorized_rejects_out_of_range_n(bad_n):
    with pytest.raises(ValueError):
        ms.count_macrostates_vectorized(bad_n)


def test_vectorized_n_smaller_than_chunk():
    # chunk_bits is clipped to n; the histogram must still be exact
    assert list(ms.count_macrostates_vectorized(3, chunk_bits=22)) == [1, 3, 3, 1]


def test_enumeration_n0_and_n1():
    assert list(ms.iter_microstates(0)) == [0]
    assert list(ms.count_macrostates_enumeration(0)) == [1]
    assert list(ms.count_macrostates_enumeration(1)) == [1, 1]


def test_count_heads_and_string_convention():
    assert ms.count_heads(0b1011) == 3
    # most significant bit first: 6 = 0b110 -> "HHT"
    assert ms.to_string(6, 3) == "HHT"
    assert ms.to_string(0, 4) == "TTTT"
    assert ms.to_string(0b1010, 4) == "HTHT"


def test_macrostate_table_is_a_partition_of_all_states():
    n = 7
    table = ms.macrostate_table(n)
    everything = [s for outcomes in table.values() for s in outcomes]
    assert len(everything) == len(set(everything)) == 2**n
    assert all(len(s) == n and set(s) <= {"H", "T"} for s in everything)
    for k, outcomes in table.items():
        assert all(s.count("H") == k for s in outcomes)


# --------------------------------------------------------------------------- #
# benchmark() and its helpers (tiny sizes, only the plumbing is checked)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "method, kwargs",
    [("generator", {}), ("vectorized", {"workers": 1}), ("vectorized", {"workers": 2})],
)
def test_benchmark_records(method, kwargs):
    rec = ms.benchmark([8, 10], method=method, repeats=2, **kwargs)
    assert [r["n"] for r in rec] == [8, 10]
    for r in rec:
        assert set(r) == {"n", "states", "t_mean", "t_std", "mem_peak_mb"}
        assert r["states"] == 2.0 ** r["n"]
        assert r["t_mean"] > 0 and r["t_std"] >= 0 and r["mem_peak_mb"] >= 0


def test_benchmark_single_repeat_has_zero_std():
    rec = ms.benchmark([8], method="generator", repeats=1)
    assert rec[0]["t_std"] == 0.0


def test_benchmark_unknown_method():
    with pytest.raises(ValueError):
        ms.benchmark([8], method="gpu")


def test_generator_memory_does_not_grow_with_n():
    # the claim of the report: O(1) memory for the generator
    import tracemalloc

    def peak(n):
        tracemalloc.start()
        for _ in ms.iter_microstates(n):
            pass
        p = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        return p

    assert peak(18) < 10_000  # bytes, independent of the 2**18 states produced


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
