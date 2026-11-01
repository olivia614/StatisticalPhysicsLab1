"""Binomial coefficients Omega(N, k) = N! / (k! (N - k)!).

Three evaluations are provided:

* ``binom_exact``  - arbitrary-precision Python integers using the product
  formula prod_{i=1}^{k} (N + 1 - i) / i (no factorials are formed).
* ``binom_float``  - the same product in IEEE-754 double precision; overflows
  once Omega exceeds ~1.8e308.
* ``log_binom``    - ln Omega via the log-gamma function (guide eq. 1); never
  overflows and is vectorised over k. Caveat: it subtracts three numbers of
  size ~ N ln N, so its *absolute* error is ~ 1e-16 N ln N. That is harmless
  for ln Omega itself, but it ruins differences such as ln P = ln Omega - N ln 2
  and Delta S once N is larger than ~1e10 (see docs/AUDIT.md).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import gammaln

FLOAT_MAX = np.finfo(np.float64).max


def binom_exact(n: int, k: int) -> int:
    """Exact binomial coefficient with Python big integers.

    Uses the multiplicative formula; after step i the running value equals
    C(n - k + i, i), so the integer division is always exact.
    """
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    result = 1
    for i in range(1, k + 1):
        result = result * (n + 1 - i) // i
    return result


def binom_float(n: int, k: int) -> float:
    """Binomial coefficient in double precision (may overflow to ``inf``)."""
    if k < 0 or k > n:
        return 0.0
    k = min(k, n - k)
    result = 1.0
    with np.errstate(over="ignore"):
        for i in range(1, k + 1):
            result = float(np.float64(result) * (n + 1 - i) / i)
    return result


def log_binom(n: float, k: np.ndarray | float) -> np.ndarray | float:
    """Natural log of the binomial coefficient via log-gamma.

    ln Omega(N, k) = ln Gamma(N + 1) - ln Gamma(k + 1) - ln Gamma(N - k + 1)

    Parameters
    ----------
    n : float
        Number of coins. ln Omega never overflows, but differences of ln Omega
        (probabilities, entropy changes) are reliable only for N <~ 1e10.
        For N ~ 1e23 use the Stirling/Gaussian expressions in
        ``thermodynamics.py`` instead.
    k : array_like
        Number(s) of heads, ``0 <= k <= n``.
    """
    k = np.asarray(k, dtype=float)
    out = gammaln(n + 1.0) - gammaln(k + 1.0) - gammaln(n - k + 1.0)
    return out if out.ndim else float(out)


def log_binom_row(n: int) -> np.ndarray:
    """ln Omega(n, k) for k = 0..n."""
    return log_binom(n, np.arange(n + 1))


def multiplicity_row(n: int) -> list[int]:
    """Exact Omega(n, k) for k = 0..n using the Pascal recurrence on big ints."""
    row = [1]
    for _ in range(n):
        row = [1] + [row[j] + row[j + 1] for j in range(len(row) - 1)] + [1]
    return row


def float_overflow_limits() -> dict[str, int]:
    """Smallest N for which double-precision evaluation fails.

    Returns
    -------
    dict
        ``"total_states"``: smallest N with 2**N > float max (2**N -> inf).
        ``"central_binomial"``: smallest N with C(N, N//2) > float max.
        ``"factorial"``: smallest N with N! > float max (naive N!/(k!(N-k)!)).
    """
    # Compared with exact integers: log-space comparisons are ambiguous at the edge
    fmax = int(FLOAT_MAX)
    limits: dict[str, int] = {}
    n = 1
    while 2**n <= fmax:
        n += 1
    limits["total_states"] = n
    n = 1
    while math.factorial(n) <= fmax:
        n += 1
    limits["factorial"] = n
    n = 1
    while math.comb(n, n // 2) <= fmax:
        n += 1
    limits["central_binomial"] = n
    return limits
