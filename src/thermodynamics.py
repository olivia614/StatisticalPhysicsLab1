"""Probabilities, Boltzmann entropy and the thermodynamic limit for N coins.

For N unbiased coins every microstate has probability 2**-N, so the
probability of the macrostate with k heads is

    P(N, k) = Omega(N, k) / 2**N,

and its Boltzmann entropy is S = k_B ln Omega(N, k). All quantities are
computed in log-space to avoid overflow.

Convention: when N is odd, "N/2 heads" means floor(N/2) heads.
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from scipy.special import logsumexp

from .combinatorics import log_binom

K_B = 1.380649e-23  # Boltzmann constant, J/K (exact, SI 2019)
SECONDS_PER_YEAR = 365.25 * 24 * 3600
AGE_OF_UNIVERSE_S = 13.787e9 * SECONDS_PER_YEAR  # Planck 2018


# --------------------------------------------------------------------------- #
# System size from the team's NIAs
# --------------------------------------------------------------------------- #


def harmonic_mean(values: Iterable[int]) -> float:
    """Harmonic mean n / sum(1/x_i) of strictly positive numbers."""
    vals = list(values)
    if not vals:
        raise ValueError("at least one value is required")
    if any(v <= 0 for v in vals):
        raise ValueError(
            "the harmonic mean is undefined when a value is 0 "
            "(a NIA ending in 00); ask the instructor how to proceed"
        )
    return len(vals) / sum(1.0 / v for v in vals)


def m_from_nias(nias: Iterable[int | str]) -> int:
    """M = harmonic mean of the last two digits of each NIA, rounded.

    The lab handout (First_Practice, updated version) defines M as the
    *harmonic* average of the last two digits of the team members' NIAs.

    Parameters
    ----------
    nias : iterable of int or str
        Student identifiers, e.g. ``[100523129, 100512345]``.

    Returns
    -------
    int
        M rounded to the nearest integer (halves round up).
    """
    digits = [int(str(nia).strip()) % 100 for nia in nias]
    return math.floor(harmonic_mean(digits) + 0.5)


def system_size(nias: Iterable[int | str]) -> int:
    """N = 100 + M."""
    return 100 + m_from_nias(nias)


def half(n: int) -> int:
    """The 'N/2' macrostate (floor for odd N)."""
    return n // 2


# --------------------------------------------------------------------------- #
# Probabilities
# --------------------------------------------------------------------------- #


def log_prob(n: float, k: np.ndarray | float) -> np.ndarray | float:
    """ln P(N, k) = ln Omega(N, k) - N ln 2."""
    return log_binom(n, k) - n * math.log(2.0)


def prob(n: float, k: np.ndarray | float) -> np.ndarray | float:
    """P(N, k) = Omega(N, k) / 2**N."""
    return np.exp(log_prob(n, k))


def prob_range(n: int, k_lo: int, k_hi: int) -> float:
    """Probability that the number of heads lies in ``[k_lo, k_hi]`` (inclusive).

    Uses log-sum-exp so it is accurate even when individual terms underflow.
    """
    k_lo, k_hi = max(0, k_lo), min(n, k_hi)
    if k_lo > k_hi:
        return 0.0
    ks = np.arange(k_lo, k_hi + 1)
    return float(np.exp(logsumexp(log_prob(n, ks))))


def prob_tails_range(n: int, t_lo: int, t_hi: int) -> float:
    """Probability that the number of tails lies in ``[t_lo, t_hi]``.

    Tails = N - heads, so this is ``prob_range(n, n - t_hi, n - t_lo)``.
    """
    return prob_range(n, n - t_hi, n - t_lo)


def likelihood_ratio(n: int, k1: int, k2: int) -> float:
    """P(N, k1) / P(N, k2) = Omega(N, k1) / Omega(N, k2)."""
    return float(np.exp(log_binom(n, k1) - log_binom(n, k2)))


# --------------------------------------------------------------------------- #
# Entropy
# --------------------------------------------------------------------------- #


def entropy(n: float, k: float) -> float:
    """S / k_B = ln Omega(N, k) (dimensionless)."""
    return float(log_binom(n, k))


def entropy_change(n: float, k1: float, k2: float) -> float:
    """Delta S_{k1 k2} / k_B = S(k1)/k_B - S(k2)/k_B = ln [Omega(N, k1) / Omega(N, k2)].

    This is the definition of the lab handout: Delta S_{k1 k2} = S(k1) - S(k2).
    It is positive when k1 has more microstates (more disorder) than k2 and
    negative otherwise.
    """
    return float(log_binom(n, k1) - log_binom(n, k2))


def entropy_change_si(n: float, k1: float, k2: float) -> float:
    """Delta S_{k1 k2} = S(k1) - S(k2) in J/K."""
    return K_B * entropy_change(n, k1, k2)


# --------------------------------------------------------------------------- #
# Waiting times
# --------------------------------------------------------------------------- #


def expected_wait_seconds(n: int, k: int, toss_rate_hz: float = 1.0) -> float:
    """Mean waiting time to observe exactly k heads when tossing N coins.

    Each toss is a Bernoulli trial with success probability P(N, k), so the
    number of tosses until the first success is geometric with mean 1 / P.

    Returns
    -------
    float
        Expected time in seconds (``inf`` if it exceeds float range).
    """
    lp = log_prob(n, k)
    with np.errstate(over="ignore"):
        return float(np.exp(-lp) / toss_rate_hz)


def log10_expected_wait_seconds(n: int, k: int, toss_rate_hz: float = 1.0) -> float:
    """log10 of :func:`expected_wait_seconds`; safe for any N."""
    return float(-log_prob(n, k) / math.log(10) - math.log10(toss_rate_hz))


# --------------------------------------------------------------------------- #
# Thermodynamic limit
# --------------------------------------------------------------------------- #


def gaussian_approx(n: float, k: np.ndarray | float) -> np.ndarray | float:
    """Gaussian (de Moivre-Laplace) approximation of P(N, k).

    Mean N/2, variance N/4: P ~ sqrt(2 / (pi N)) exp(-2 (k - N/2)**2 / N).
    """
    k = np.asarray(k, dtype=float)
    out = np.sqrt(2.0 / (math.pi * n)) * np.exp(-2.0 * (k - n / 2.0) ** 2 / n)
    return out if out.ndim else float(out)


def relative_width(n: float) -> float:
    """sigma / mu = (sqrt(N)/2) / (N/2) = 1 / sqrt(N)."""
    return 1.0 / math.sqrt(n)


def log10_prob_fraction(n: float, x: float) -> float:
    """log10 P(N, k = x N) using Stirling: ln P ~ N [H(x) - ln 2] (leading order).

    H(x) = -x ln x - (1 - x) ln(1 - x) is the mixing entropy per coin.
    Useful for N ~ 1e23 where even the exponent is astronomically large.

    Only the leading order is kept (the prefactor -1/2 ln(2 pi N x (1-x)) is
    dropped), so use it for *differences* between two fractions x. On its own it
    is wrong by that prefactor: at x = 1/2 it returns 0 instead of
    -1/2 log10(pi N / 2).
    """
    if x in (0.0, 1.0):
        h = 0.0
    else:
        h = -x * math.log(x) - (1 - x) * math.log(1 - x)
    return n * (h - math.log(2.0)) / math.log(10)


# --------------------------------------------------------------------------- #
# Monte Carlo simulation of repeated tosses
# --------------------------------------------------------------------------- #


def simulate_tosses(
    n: int, trials: int, rng: np.random.Generator | None = None
) -> np.ndarray:
    """Toss N fair coins ``trials`` times and histogram the number of heads.

    Returns
    -------
    numpy.ndarray
        ``counts[k]`` = number of trials with k heads, shape ``(n + 1,)``.
    """
    rng = np.random.default_rng() if rng is None else rng
    heads = rng.binomial(1, 0.5, size=(trials, n)).sum(axis=1)
    return np.bincount(heads, minlength=n + 1)
