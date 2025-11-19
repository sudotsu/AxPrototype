# /verify/test_taes_adherence.py
"""
TAES Adherence (D25–25c) — Correctness, Determinism, and Kernel Consistency

Scope
-----
Benchmark-grade tests for the TAES evaluator and its integration with the kernel.
Targets the approved public adapters:

    from score_validator import evaluate_text
    from run_axp import run_once

We assert:
- Schema & ranges for TAES scores (logical, practical, probable, iv, ird, requires_rrp).
- Determinism under fixed seed.
- Behavioral monotonicity: a coherent, actionable passage scores better than a contradictory,
  hedged passage (IV higher, IRD lower).
- Contract rule: requires_rrp == (ird > 0.5).
- Kernel TAES consistency: kernel["taes"] roughly matches evaluate_text(kernel["final"])
  within tolerances (same evaluator or compatible pipeline).

Assumptions
-----------
- Python 3.12+, pytest installed.
- Tests run offline; no network access required.
- Seeded runs are deterministic for both adapters.
- Kernel is invokable and returns TAES block under result["taes"] per the contract.

Run
---
    pytest verify/test_taes_adherence.py -q
"""

from typing import Dict, List, Tuple, Optional
import os

import pytest

from score_validator import evaluate_text
from run_axp import run_once
from axp.governance.coupling import initialize_schema


# ---------- Constants & Fixtures ----------

SEED: int = 1337
IV_MARGIN: float = 0.05     # required advantage for coherent over contradictory
IRD_MARGIN: float = 0.05    # required improvement (lower is better) for coherent over contradictory
CONSISTENCY_TOL: float = 0.15  # kernel vs. standalone evaluator tolerance

GOOD_TEXT: str = (
    "Position: Passkeys materially reduce account takeover vs. passwords in 2025. "
    "Reasoning: They remove shared secrets, resist phishing and credential stuffing, "
    "and bind authentication to device-bound private keys. "
    "Plan: Enforce WebAuthn with platform authenticators first, roamers for privileged roles; "
    "ship progressive rollout with metrics (A2R, takeover rate), and a break-glass path. "
    "Risks: Device loss and recovery flows. Mitigation: multi-device registration, "
    "recovery with identity-proofing and time delays. Measurement: takeover rate target < 0.1%."
)

BAD_TEXT: str = (
    "We should keep passwords because change is risky, yet also adopt passkeys immediately "
    "without any plan. Passkeys are both more secure and less secure than passwords, which is fine. "
    "We will stop all breaches next week with a small banner update. Maybe, could be, perhaps. "
    "No risks are relevant but also the risks are enormous; proceed now and never mind evidence."
)


def _schema_ok(scores: Dict[str, float]) -> None:
    """
    Validate TAES schema presence and ranges.

    Args:
        scores: Dict returned by evaluate_text.

    Returns:
        None; asserts internally.
    """
    required = ["logical", "practical", "probable", "iv", "ird", "requires_rrp"]
    for k in required:
        assert k in scores, f"TAES missing key: {k}"

    # Floats in [0,1] for axes and iv; ird also expected in [0,1] (or >=0); tests allow [0,1+]
    for k in ["logical", "practical", "probable", "iv", "ird"]:
        v = float(scores[k])
        assert 0.0 <= v <= 1.0 + 1e-9, f"TAES[{k}] out of expected range: {v}"

    # requires_rrp boolean
    assert isinstance(scores["requires_rrp"], bool), "requires_rrp must be boolean"


# ---------- Tests ----------

def test_schema_and_ranges() -> None:
    """TAES returns all required keys with valid ranges."""
    scores = evaluate_text(GOOD_TEXT, seed=SEED)
    _schema_ok(scores)

    # Contract: requires_rrp == (ird > 0.5)
    ird = float(scores["ird"])
    assert scores["requires_rrp"] == (ird > 0.5), (
        "requires_rrp must be True iff IRD > 0.5"
    )


def test_determinism_with_seed() -> None:
    """Same text + same seed => identical scores."""
    s1 = evaluate_text(GOOD_TEXT, seed=SEED)
    s2 = evaluate_text(GOOD_TEXT, seed=SEED)
    assert s1 == s2, "TAES scores should be identical for same text and seed"

    # Different seed may differ; we just assert it returns valid schema.
    s3 = evaluate_text(GOOD_TEXT, seed=SEED + 1)
    _schema_ok(s3)


def test_behavior_monotonicity_coherent_beats_contradictory() -> None:
    """
    Coherent/actionable text should outperform contradictory/hedged text:
    - IV higher by at least IV_MARGIN
    - IRD lower by at least IRD_MARGIN
    """
    good = evaluate_text(GOOD_TEXT, seed=SEED)
    bad = evaluate_text(BAD_TEXT, seed=SEED)

    iv_good = float(good["iv"])
    iv_bad = float(bad["iv"])
    ird_good = float(good["ird"])
    ird_bad = float(bad["ird"])

    assert iv_good >= iv_bad + IV_MARGIN, (
        f"IV not sufficiently higher for coherent text: good={iv_good:.3f}, bad={iv_bad:.3f}"
    )
    assert ird_good <= ird_bad - IRD_MARGIN, (
        f"IRD not sufficiently lower for coherent text: good={ird_good:.3f}, bad={ird_bad:.3f}"
    )


def test_requires_rrp_boolean_relation() -> None:
    """
    Contract check independent of absolute values:
    requires_rrp must be True iff ird > 0.5.
    """
    for text in (GOOD_TEXT, BAD_TEXT):
        scores = evaluate_text(text, seed=SEED)
        ird = float(scores["ird"])
        assert scores["requires_rrp"] == (ird > 0.5), (
            f"requires_rrp boolean mismatch for IRD={ird:.3f}"
        )


def test_kernel_taes_consistency_on_final_output() -> None:
    """
    Kernel's TAES block should be broadly consistent with a fresh evaluate_text over its own
    final output. Allow tolerance since kernel may evaluate full chain vs. final only.

    We also check that detector is bypassed (no 'detector' key present).
    """
    prompt = (
        "Give a concise, testable recommendation for reducing account takeover risk in a small "
        "SaaS business. Provide a 3-step action plan with a measurable target."
    )
    result = run_once(prompt=prompt, meta={"domain": "strategy"}, seed=SEED, capture_logs=True)

    assert "taes" in result, "Kernel result missing 'taes' block"
    assert "final" in result and isinstance(result["final"], str), "Kernel result missing 'final' text"
    assert "detector" not in result, "Domain detector should be bypassed when meta.domain provided"

    kernel_scores = result["taes"]
    _schema_ok(kernel_scores)

    # Standalone evaluation on kernel's final
    eval_scores = evaluate_text(result["final"], seed=SEED)

    # Compare key aggregates with tolerances
    for k in ("iv", "ird"):
        kv = float(kernel_scores[k])
        ev = float(eval_scores[k])
        assert abs(kv - ev) <= CONSISTENCY_TOL, (
            f"Kernel TAES '{k}' deviates from evaluator beyond tolerance: "
            f"kernel={kv:.3f}, eval={ev:.3f}, tol={CONSISTENCY_TOL}"
        )

    # requires_rrp boolean relation must hold in kernel as well
    k_ird = float(kernel_scores["ird"])
    assert kernel_scores["requires_rrp"] == (k_ird > 0.5), (
        "Kernel requires_rrp must be True iff IRD > 0.5"
    )


def test_schema_load_success() -> None:
    """Schema bootstrap should succeed even if config files are missing/empty."""
    data = initialize_schema()
    assert isinstance(data, dict), "initialize_schema() must return a dict"
    # Ensure keys exist and are non-empty
    for k in ("S", "A", "C", "X"):
        assert k in data, f"Schema missing key: {k}"
        assert isinstance(data[k], dict) and len(data[k]) > 0, f"Schema section {k} not properly initialized"


# ---------- How to run & expected output (documentation only) ----------

# Command:
#     pytest verify/test_taes_adherence.py -q
#
# Expected (example):
#     .....                                                            [100%]
#
#     5 passed in 1.2s
#
# Notes:
# - Tolerances are set to keep tests robust across minor implementation differences.
# - If kernel and evaluator diverge materially, investigate pipeline differences
#   (e.g., chain-wide vs. final-only evaluation) and align or adjust CONSISTENCY_TOL.
