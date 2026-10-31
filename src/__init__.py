"""Statistical Physics Lab 1: microstates of a system of N unbiased coins.

Modules
-------
microstates
    Bitwise enumeration of the 2**N microstates (generators and chunked NumPy).
combinatorics
    Exact (big-integer) and log-space binomial coefficients.
thermodynamics
    Probabilities, Boltzmann entropy, waiting times and the thermodynamic limit.
"""

from . import combinatorics, microstates, thermodynamics

__all__ = ["combinatorics", "microstates", "thermodynamics"]
