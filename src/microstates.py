"""Enumeration of the microstates of N two-state coins.

A microstate of N coins is encoded as an N-bit integer: bit i = 1 means coin i
shows heads (H), bit i = 0 means tails (T). The integers 0 ... 2**N - 1 (i.e.
``range(1 << N)``) are therefore in one-to-one correspondence with the 2**N
microstates, and the macrostate (number of heads k) is the population count
(number of set bits) of that integer.
"""

from __future__ import annotations

import os
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor
from typing import Iterator

import numpy as np

# --------------------------------------------------------------------------- #
# Basic encoding
# --------------------------------------------------------------------------- #


def iter_microstates(n: int) -> Iterator[int]:
    """Yield every microstate of ``n`` coins as an integer in ``[0, 2**n)``.

    A generator is used so that the 2**n states are never stored in memory at
    the same time: memory use is O(1) regardless of ``n``.

    Parameters
    ----------
    n : int
        Number of coins (``n >= 0``).

    Yields
    ------
    int
        Bit-encoded microstate.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    state = 0
    total = 1 << n
    while state < total:
        yield state
        state += 1


def count_heads(state: int) -> int:
    """Return the number of heads (set bits) in a bit-encoded microstate."""
    return state.bit_count()


def to_string(state: int, n: int) -> str:
    """Render a microstate as an H/T string, most significant coin first.

    Parameters
    ----------
    state : int
        Bit-encoded microstate.
    n : int
        Number of coins (string length).

    Returns
    -------
    str
        e.g. ``to_string(0b1010, 4) == "HTHT"``.
    """
    return "".join("H" if (state >> (n - 1 - i)) & 1 else "T" for i in range(n))


def macrostate_table(n: int) -> dict[int, list[str]]:
    """List all microstates grouped by macrostate (number of heads).

    Intended for small ``n`` (the report uses ``n = 7``, 128 outcomes).

    Returns
    -------
    dict[int, list[str]]
        Maps k (heads) to the list of H/T strings with exactly k heads,
        ordered from k = n down to k = 0.
    """
    table: dict[int, list[str]] = {k: [] for k in range(n, -1, -1)}
    for state in iter_microstates(n):
        table[count_heads(state)].append(to_string(state, n))
    return table


# --------------------------------------------------------------------------- #
# Histogram of macrostates by full enumeration
# --------------------------------------------------------------------------- #


def count_macrostates_enumeration(n: int) -> np.ndarray:
    """Histogram of heads over all 2**n microstates, pure-Python generator.

    This is the reference (slow, O(2**n) Python operations, O(n) memory)
    implementation.

    Returns
    -------
    numpy.ndarray
        ``counts[k]`` = number of microstates with k heads, shape ``(n + 1,)``.
    """
    counts = [0] * (n + 1)
    for state in iter_microstates(n):
        counts[state.bit_count()] += 1
    return np.array(counts, dtype=object if n > 62 else np.int64)


def _popcount(arr: np.ndarray) -> np.ndarray:
    """Vectorised population count of a uint64 array."""
    if hasattr(np, "bitwise_count"):  # NumPy >= 2.0
        return np.bitwise_count(arr)
    # SWAR fallback for NumPy 1.x
    x = arr.astype(np.uint64, copy=True)
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return ((x * np.uint64(0x0101010101010101)) >> np.uint64(56)).astype(np.uint8)


def _count_block_range(n: int, chunk_bits: int, first: int, last: int) -> np.ndarray:
    """Histogram of heads for the blocks ``first .. last - 1`` of size 2**chunk_bits.

    Every microstate in those blocks is generated and its popcount evaluated:
    no combinatorial shortcut is used.
    """
    counts = np.zeros(n + 1, dtype=np.int64)
    size = 1 << chunk_bits
    offsets = np.arange(size, dtype=np.uint64)
    for block in range(first, last):
        states = offsets + np.uint64(block << chunk_bits)
        counts += np.bincount(_popcount(states), minlength=n + 1)[: n + 1]
    return counts


def count_macrostates_vectorized(
    n: int,
    chunk_bits: int = 22,
    workers: int = 1,
    pool: ProcessPoolExecutor | None = None,
) -> np.ndarray:
    """Histogram of heads over all 2**n microstates using chunked NumPy.

    The state space ``[0, 2**n)`` is split into blocks of ``2**chunk_bits``
    consecutive integers. Each block is materialised as a uint64 array, its
    popcounts are computed in C and accumulated with ``bincount``. Peak memory
    is therefore ~ ``9 * 2**chunk_bits`` bytes per worker, independent of n.

    Parameters
    ----------
    n : int
        Number of coins, ``0 <= n <= 63``.
    chunk_bits : int
        log2 of the block size.
    workers : int
        Number of processes. Blocks are divided evenly among them.
    pool : ProcessPoolExecutor, optional
        Reuse an existing pool (avoids ~seconds of process start-up on
        Windows when timing many runs). Must have ``workers`` processes.

    Returns
    -------
    numpy.ndarray
        ``counts[k]`` for k = 0..n (int64).
    """
    if not 0 <= n <= 63:
        raise ValueError("vectorised enumeration supports 0 <= n <= 63")
    chunk_bits = min(chunk_bits, n)
    n_blocks = 1 << (n - chunk_bits)
    workers = max(1, min(workers, n_blocks))
    if workers == 1:
        return _count_block_range(n, chunk_bits, 0, n_blocks)

    bounds = [n_blocks * i // workers for i in range(workers + 1)]
    own_pool = pool is None
    if own_pool:
        pool = ProcessPoolExecutor(max_workers=workers)
    try:
        futures = [
            pool.submit(_count_block_range, n, chunk_bits, bounds[i], bounds[i + 1])
            for i in range(workers)
        ]
        return sum((f.result() for f in futures), np.zeros(n + 1, dtype=np.int64))
    finally:
        if own_pool:
            pool.shutdown()


# --------------------------------------------------------------------------- #
# Benchmarking
# --------------------------------------------------------------------------- #


def benchmark(
    n_values: list[int],
    method: str = "vectorized",
    repeats: int = 3,
    workers: int | None = None,
) -> list[dict[str, float]]:
    """Measure wall-clock time and peak traced memory of full enumeration.

    Parameters
    ----------
    n_values : list[int]
        System sizes to time.
    method : {"generator", "vectorized"}
        Which enumeration routine to time.
    repeats : int
        Number of repetitions per N; mean and sample standard deviation are
        reported as the measurement and its uncertainty.
    workers : int, optional
        Processes for the vectorised method (default: all CPU cores).

    Returns
    -------
    list[dict]
        One record per N with keys ``n, states, t_mean, t_std, mem_peak_mb``.
        ``mem_peak_mb`` is the peak memory traced by ``tracemalloc`` for one
        block of work (one process).

    Notes
    -----
    Timing and memory are measured in separate runs: ``tracemalloc`` slows
    pure-Python loops several-fold and would bias the timings.
    """
    if workers is None:
        workers = os.cpu_count() or 1
    pool = None
    if method == "generator":
        run = lambda n: count_macrostates_enumeration(n)  # noqa: E731
        probe = lambda n: count_macrostates_enumeration(min(n, 16))  # noqa: E731
    elif method == "vectorized":
        if workers > 1:
            pool = ProcessPoolExecutor(max_workers=workers)
            count_macrostates_vectorized(20, workers=workers, pool=pool)  # warm up
        run = lambda n: count_macrostates_vectorized(n, workers=workers, pool=pool)  # noqa: E731
        # worker memory is invisible to tracemalloc: trace one block in-process
        probe = lambda n: _count_block_range(n, min(22, n), 0, 1)  # noqa: E731
    else:
        raise ValueError(f"unknown method {method!r}")
    try:
        return _benchmark_loop(n_values, run, probe, repeats)
    finally:
        if pool is not None:
            pool.shutdown()


def _benchmark_loop(n_values, run, probe, repeats) -> list[dict[str, float]]:
    results = []
    for n in n_values:
        times = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            run(n)
            times.append(time.perf_counter() - t0)
        tracemalloc.start()
        probe(n)
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        arr = np.array(times)
        results.append(
            {
                "n": n,
                "states": float(2**n),
                "t_mean": float(arr.mean()),
                "t_std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
                "mem_peak_mb": peak / 2**20,
            }
        )
    return results


def extrapolate_n_max(
    n_values: np.ndarray, t_values: np.ndarray, t_limit: float = 300.0
) -> tuple[float, float, float]:
    """Fit ``log2 t = a + b N`` and return the N at which ``t = t_limit``.

    Returns
    -------
    (n_at_limit, a, b) : tuple[float, float, float]
        Slope ``b`` should be close to 1 for O(2**N) scaling.
    """
    # Closed-form ordinary least squares (avoids a LAPACK dependency)
    # Note: with noisy timings over a short range of N the free slope is poorly
    # constrained; see per_state_cost for the robust fixed-slope estimate.
    x = np.asarray(n_values, dtype=float)
    y = np.log2(np.asarray(t_values, dtype=float))
    b = float(np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2))
    a = float(y.mean() - b * x.mean())
    return (np.log2(t_limit) - a) / b, a, b


def per_state_cost(
    n_values: np.ndarray, t_values: np.ndarray, t_limit: float = 300.0
) -> tuple[float, float]:
    """Robust N_max estimate assuming the theoretical scaling t = c * 2**N.

    The cost per microstate ``c`` is the median of ``t / 2**N`` (insensitive
    to individual runs slowed by background load).

    Returns
    -------
    (n_at_limit, c) : tuple[float, float]
        ``n_at_limit = log2(t_limit / c)``; ``c`` in seconds per microstate.
    """
    n = np.asarray(n_values, dtype=float)
    t = np.asarray(t_values, dtype=float)
    c = float(np.median(t / 2.0**n))
    return float(np.log2(t_limit / c)), c
