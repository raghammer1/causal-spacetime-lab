"""Explicit, disjoint semantic streams for Experiment 6; no primary defaults."""
from __future__ import annotations
import hashlib
import json
import numpy as np

SEEDS = {"smoke": (61001,), "pilot": (61002,), "calibration": (61003,),
         "primary": (61101, 61201, 61301), "bootstrap": (61401,), "audit": (61501,)}


def stream_key(phase, batch, *parts):
    if phase not in SEEDS or not isinstance(batch, int) or not 0 <= batch < len(SEEDS[phase]):
        raise ValueError("an explicit known phase and valid batch are required")
    return json.dumps(["quantum-v1", phase, SEEDS[phase][batch], *parts],
                      separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def rng_for(phase, batch, *parts):
    digest = hashlib.sha256(stream_key(phase, batch, *parts).encode("ascii")).digest()
    words = np.frombuffer(digest, dtype="<u4").tolist()
    return np.random.default_rng(np.random.SeedSequence(words))
