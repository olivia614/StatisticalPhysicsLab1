import os

# See main.py: avoid threaded-MKL load failure in numpy.linalg on Windows.
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
