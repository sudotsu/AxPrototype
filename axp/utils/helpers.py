"""
Miscellaneous helper functions.
"""

import re
import json
import os
from pathlib import Path
from typing import Optional


def shingles(text: str, n: int = 3) -> set:
    """
    Generate n-gram shingles from text for redundancy detection.

    Args:
        text: Input text
        n: Shingle size (default 3)

    Returns:
        Set of shingle strings
    """
    t = (text or "").lower()
    tokens = re.findall(r"[a-z0-9]+", t)
    return {" ".join(tokens[i:i+n]) for i in range(max(0, len(tokens) - n + 1))}


def redundancy_score(current: str, prior: list[str], n: int = 3) -> float:
    """
    Compute redundancy score between current text and prior texts.

    Args:
        current: Current text
        prior: List of prior texts
        n: Shingle size

    Returns:
        Redundancy score (0.0 = no overlap, 1.0 = complete overlap)
    """
    if not current or not prior:
        return 0.0
    cur = shingles(current, n)
    if not cur:
        return 0.0
    # Compare against the union of prior shingles for a conservative upper bound
    prior_union: set = set()
    for p in prior:
        prior_union |= shingles(p, n)
    if not prior_union:
        return 0.0
    inter = len(cur & prior_union)
    union = len(cur | prior_union)
    return inter / union if union else 0.0


def uniqueness_nudge(role: str) -> str:
    """
    Get role-specific prompt nudge to encourage unique outputs.

    Args:
        role: Role name

    Returns:
        Nudge text
    """
    hints = {
        "Strategist": (
            "Remove checklist/rationale overlap. Introduce distinct positioning, unique audiences/hooks,"
            " and S-ID acceptance tests not present upstream. Do NOT include specs, schedules, or audits."
        ),
        "Analyst": (
            "Eliminate narrative; present numeric KPIs, falsifications, and an A-ID map to S-IDs."
            " Do NOT include positioning/audience/hooks, schedules, or production copy."
        ),
        "Producer": (
            "Replace prose with assets/specs (P-IDs). Provide API/contracts, DDL, config tables,"
            " or copy blocks tied to A-IDs. Do NOT include schedules or audits."
        ),
        "Courier": (
            "Return only schedule tables, DM scripts, KPI tracker rows with P-ID references."
            " Do NOT restate assets or strategy."
        ),
        "Critic": (
            "Return Issue->Fix pairs with S/A/P/C references and audit tables."
            " Do NOT write new assets or schedules."
        ),
    }
    return hints.get(role, "Reduce overlap and add new, role-unique artifacts.")


def extract_json_block(text: str):
    """
    Extract JSON block from text (fenced or bare).

    Args:
        text: Text containing JSON

    Returns:
        Parsed JSON object/array or None if not found/invalid
    """
    t = text or ""
    # Try fenced JSON
    m = re.search(r"```json\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", t, re.IGNORECASE)
    if not m:
        # Try first brace/bracket
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", t)
    if not m:
        return None
    frag = m.group(1)
    try:
        return json.loads(frag)
    except Exception:
        return None


def violates_exclusions(text: str, role_name: str, shapes_cfg: dict) -> bool:
    """
    Check if text violates role exclusion rules.

    Args:
        text: Generated text
        role_name: Role name
        shapes_cfg: Role shapes configuration dict

    Returns:
        True if violations detected
    """
    if not text or not isinstance(shapes_cfg, dict):
        return False
    role_spec = shapes_cfg.get(role_name) or shapes_cfg.get(role_name.lower())
    if not isinstance(role_spec, dict):
        return False
    haystack = text.lower()
    banned = role_spec.get("banned") or []
    for phrase in banned:
        try:
            if phrase and phrase.lower() in haystack:
                return True
        except Exception:
            continue
    banned_regex = role_spec.get("banned_regex") or []
    for pattern in banned_regex:
        try:
            if pattern and re.search(pattern, text, re.IGNORECASE):
                return True
        except Exception:
            continue
    return False


def strict_reprompt(
    role: str,
    sys_prompt: str,
    base_user: str,
    fewshot_path: Optional[Path] = None,
    llm_func=None
) -> str:
    """
    Generate strict reprompt with example.

    Args:
        role: Role name
        sys_prompt: System prompt
        base_user: Base user prompt
        fewshot_path: Optional path to few-shot example
        llm_func: LLM callable (defaults to call_llm)

    Returns:
        Generated text
    """
    if llm_func is None:
        from axp.utils.llm import call_llm
        llm_func = call_llm

    demo = ""
    try:
        if fewshot_path and fewshot_path.exists():
            demo = "\n\nExample:\n" + fewshot_path.read_text(encoding="utf8")[:800]
    except Exception:
        demo = ""
    user = base_user + "\n\nSTRICT MODE: Return ONLY JSON in a single fenced block (```json ... ```)." + demo
    return llm_func(sys_prompt, user, temperature=0.2)


def load_role_shapes(base_dir: Path) -> dict:
    """
    Load role shapes configuration.

    Args:
        base_dir: Base directory

    Returns:
        Role shapes configuration dict
    """
    paths = [
        os.getenv("ROLE_SHAPES_PATH"),
        str(base_dir / "config" / "role_shapes.json"),
    ]
    for p in paths:
        try:
            if p and Path(p).exists():
                return json.loads(Path(p).read_text(encoding="utf8"))
        except Exception:
            continue
    return {}

