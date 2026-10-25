"""Causal Spacetime Lab: transparent numerical experiments, not proof of emergent gravity."""
from .core import (
    CausalDiamond,
    sprinkle,
    causal_order,
    longest_chain_order,
    longest_chain_fast,
    inferred_duration,
    comparable_pair_fraction,
)

__all__ = [
    "CausalDiamond", "sprinkle", "causal_order", "longest_chain_order",
    "longest_chain_fast", "inferred_duration", "comparable_pair_fraction",
]
