"""
Schema validators for role outputs.

Validates JSON structures for Caller, S (Strategist), A (Analyst), P (Producer),
C (Courier), and X (Critic) role outputs.
"""

from typing import Optional


def validate_Caller(data: dict) -> tuple[bool, str]:
    """
    Validate Caller output (oneOf: terminate, proceed, suggest_optimized_prompt_and_insight).

    Phase 2: Validates Caller's three possible states.
    """
    if not isinstance(data, dict):
        return False, "Caller output must be a dictionary"

    status = data.get("status")
    if status not in ["terminate", "proceed", "suggest_optimized_prompt_and_insight"]:
        return False, f"Invalid status: {status}"

    if status == "terminate":
        if "response" not in data:
            return False, "terminate status requires 'response' field"
        return True, "ok"

    if status == "proceed":
        if "payload" not in data or not isinstance(data["payload"], dict):
            return False, "proceed status requires 'payload' object"
        if "objective" not in data["payload"]:
            return False, "payload must contain 'objective' field"
        return True, "ok"

    if status == "suggest_optimized_prompt_and_insight":
        required = ["suggested_objective", "axp_insight", "user_confirmation_question"]
        for field in required:
            if field not in data:
                return False, f"suggest_optimized_prompt_and_insight requires '{field}' field"

        # Validate axp_insight structure
        insight = data.get("axp_insight", {})
        if not isinstance(insight, dict):
            return False, "axp_insight must be an object"
        if "title" not in insight or "perspectives" not in insight or "verdict" not in insight:
            return False, "axp_insight must contain 'title', 'perspectives', and 'verdict'"

        if not isinstance(insight.get("perspectives"), list):
            return False, "axp_insight.perspectives must be an array"

        return True, "ok"

    return False, "Unknown status"


def validate_S(items) -> tuple[bool, str]:
    """Validate Strategist output (S array)."""
    if not isinstance(items, list) or not items:
        return False, "S must be non-empty list"
    req = {"s_id", "title", "audience", "hooks", "three_step_plan"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "S item missing required keys"
    return True, "ok"


def validate_A(items, s_ids: set) -> tuple[bool, str]:
    """Validate Analyst output (A array) with S-ID references."""
    if not isinstance(items, list) or not items:
        return False, "A must be non-empty list"
    req = {"a_id", "s_refs", "kpi_table"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "A item missing required keys"
        if not set(it.get("s_refs", [])).issubset(s_ids):
            return False, "A item has unknown S refs"
    return True, "ok"


def validate_P(items, a_ids: set) -> tuple[bool, str]:
    """Validate Producer output (P array) with A-ID references."""
    if not isinstance(items, list) or not items:
        return False, "P must be non-empty list"
    req = {"p_id", "a_refs", "spec_type", "body"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "P item missing required keys"
        if not set(it.get("a_refs", [])).issubset(a_ids):
            return False, "P item has unknown A refs"
    return True, "ok"


def validate_C(items, p_ids: set, producer_assets: Optional[list] = None) -> tuple[bool, str]:
    """
    Validate Courier output (C array) with P-ID references.

    Args:
        items: C array to validate
        p_ids: Set of valid P-IDs (from Producer)
        producer_assets: Optional list of Producer assets for explicit validation

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(items, list) or not items:
        return False, "C must be non-empty list"
    req = {"day", "time", "channel", "p_id", "kpi_target", "owner_action"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "C row missing required keys"
        if it.get("p_id") not in p_ids:
            return False, "C row references unknown P-ID"

    # Explicit validation: Courier must only use Producer's declared assets
    if producer_assets is not None:
        used_p_ids = {row.get('p_id') for row in items}
        prod_p_ids = {asset.get('p_id') for asset in producer_assets if isinstance(asset, dict)}
        if not used_p_ids.issubset(prod_p_ids):
            missing = used_p_ids - prod_p_ids
            return False, f"Courier used undeclared assets: {missing}"

    return True, "ok"


def validate_X(items, s_ids: set, a_ids: set, p_ids: set, c_ids: set) -> tuple[bool, str]:
    """Validate Critic output (X array) with cross-references."""
    if not isinstance(items, list) or not items:
        return False, "X must be non-empty list"
    req = {"x_id", "refs", "issue", "fix", "severity", "proof_scores"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "X item missing required keys"
        refs = it.get("refs", {}) or {}
        if not isinstance(refs, dict):
            return False, "X refs must be dict"
        if not set(refs.get("s", [])).issubset(s_ids):
            return False, "X refs contain unknown S ids"
        if not set(refs.get("a", [])).issubset(a_ids):
            return False, "X refs contain unknown A ids"
        if not set(refs.get("p", [])).issubset(p_ids):
            return False, "X refs contain unknown P ids"
        if not set(refs.get("c", [])).issubset(c_ids):
            return False, "X refs contain unknown C ids"
    return True, "ok"

