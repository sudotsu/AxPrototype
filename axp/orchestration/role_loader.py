"""
Role loading from domain-specific files.
"""

import os
from pathlib import Path
from typing import Dict


def load_domain_roles(domain: str, base_dir: Path) -> Dict[str, str]:
    """
    Load roles for a specific domain.

    Args:
        domain: Domain name (e.g., 'marketing', 'technical', 'ops', etc.)
        base_dir: Base directory

    Returns:
        Dictionary with role contents
    """
    try:
        from load_roles import load_roles_by_pattern
        BUILD_TYPE = os.getenv("BUILD_TYPE", "stable")

        # Pass domain to role loader
        _roles = load_roles_by_pattern(BUILD_TYPE, domain)

        print(f"[OK] Loaded {domain} domain roles ({BUILD_TYPE})")
        roles_dict = {
            'strategist': _roles["strategist"]["content"],
            'analyst': _roles["analyst"]["content"],
            'producer': _roles["producer"]["content"],
            'courier': _roles["courier"]["content"],
            'critic': _roles["critic"]["content"],
        }
        # Phase 2: Add Caller role if available
        if "caller" in _roles:
            roles_dict['caller'] = _roles["caller"]["content"]
        return roles_dict
    except Exception as e:
        print(f"[WARN] Role loader not available for {domain} — using inline defaults.\n{e}")
        # Fallback to generic roles
        return {
            'caller': (
                "Role: Caller. Analyze user objective and triage: terminate trivial requests, "
                "proceed with clear objectives, or suggest optimized prompt for ambiguous ones."
            ),
            'strategist': (
                "Role: Strategist. Define positioning, 3 audiences, 3 hooks, 3-step plan. "
                "Be decisive; ground in objective. End with KPI or action (Directive 15)."
            ),
            'analyst': (
                "Role: Analyst. Pressure-test assumptions; risks->mitigations; 3 KPIs with numeric targets; "
                "A/B plan; short validation table. Prioritize 95% workable now. Score ≥85."
            ),
            'producer': (
                "Role: Producer. Create publishable assets for Nextdoor, Facebook, Craigslist (≤180 words each), "
                "3 alt headlines, 1 proof bullet. Clear CTA. Platform-specific. Score ≥85."
            ),
            'courier': (
                "Role: Courier. Build D1–D7 schedule (times + channels), DM plan, KPI tracker, "
                "3 fallback moves if leads < target by Day 3. Score ≥85."
            ),
            'critic': (
                "Role: Critic. Audit for compliance, clarity, proof, CTA power, local tone. "
                "List 'Issue->Fix' pairs, give five 0–100 ratings + average. If <85, revise once, re-score."
            ),
        }

