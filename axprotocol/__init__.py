"""
AxProtocol - Self-auditing, directive-aware AI reasoning kernel

AxProtocol is a multi-role reasoning system with:
- Strategist → Analyst → Producer → Courier → Critic chain
- TAES (Truth/Alignment/Efficiency/Signal) evaluation
- Directive-based governance enforcement
- Immutable audit ledger
- Domain-specific role configurations

Public API:
    from axprotocol import run_chain
"""

__version__ = "2.4.0"

# Re-export main public API from internal axp package
from axp.orchestration import run_chain

# Re-export commonly used utilities
from axp.utils.config_fingerprint import compute_config_hash
from axp.utils.session_logging import log_session

# Re-export validators for external use
from axp.validation import validate_S, validate_A, validate_P, validate_C, validate_X

# Re-export detection functions
from axp.detection import (
    detect_sycophancy,
    detect_contradiction,
    detect_ambiguity_in_objective,
    unresolved_ambiguity,
    detect_wants_praise,
    precedence_inversion,
    overconfidence_no_evidence,
)

__all__ = [
    # Main API
    "run_chain",
    # Utilities
    "compute_config_hash",
    "log_session",
    # Validators
    "validate_S",
    "validate_A",
    "validate_P",
    "validate_C",
    "validate_X",
    # Detection
    "detect_sycophancy",
    "detect_contradiction",
    "detect_ambiguity_in_objective",
    "unresolved_ambiguity",
    "detect_wants_praise",
    "precedence_inversion",
    "overconfidence_no_evidence",
    # Version
    "__version__",
]

