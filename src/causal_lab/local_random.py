"""Parameter-keyed random streams for the registered local-structure study."""
import hashlib
import json

import numpy as np


def identity(seed, fit, phase, family, dimension, count, repeat, parameter=None):
    values = ["local-v1", int(seed), int(fit), phase, family, int(dimension),
              int(count), int(repeat), parameter]
    return hashlib.sha256(json.dumps(values, separators=(",", ":"), ensure_ascii=True,
                                     allow_nan=False).encode("ascii")).hexdigest()


def rng_for(seed, fit, phase, family, dimension, count, repeat, parameter=None):
    return np.random.Generator(np.random.PCG64(int(identity(
        seed, fit, phase, family, dimension, count, repeat, parameter), 16)))
