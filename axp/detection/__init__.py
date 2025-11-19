"""
AxProtocol Governance Detection Module

Signal detection for sycophancy, contradictions, ambiguity, etc.
"""

from .signals import (
    detect_sycophancy,
    detect_contradiction,
    detect_ambiguity_in_objective,
    unresolved_ambiguity,
    detect_wants_praise,
    precedence_inversion,
    overconfidence_no_evidence,
)

__all__ = [
    'detect_sycophancy',
    'detect_contradiction',
    'detect_ambiguity_in_objective',
    'unresolved_ambiguity',
    'detect_wants_praise',
    'precedence_inversion',
    'overconfidence_no_evidence',
]

