"""Versioned, independently addressable random streams for growth research."""
from __future__ import annotations

import hashlib
import json

import numpy as np


def identity(seed, batch, phase, family, parameter, history, source_count=None, replica=None):
    """Return a stable history/operation identity; generation omits terminal N."""
    return json.dumps(["growth-v1", seed, batch, phase, family, parameter,
                       history, source_count, replica], ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def rng_for(seed, batch, phase, family, parameter, history, source_count=None, replica=None):
    key = identity(seed, batch, phase, family, parameter, history, source_count, replica)
    digest = hashlib.sha256(key.encode("ascii")).digest()
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest, "big")))
