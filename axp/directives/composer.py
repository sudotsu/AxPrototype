"""
Directive composition for role system prompts.
"""

import logging
from typing import Optional


# Usability improvement: Directive summaries for self-documentation
# D0: Change Control - Version tracking and rollback authority
# D1-14: Core Directives - Truth discipline, logic integrity, contradiction detection
# D15-19: War-Room Addendum - Objective grounding, scoring thresholds, handoffs
# D20-24: Authority Assertion Layer - Operator supremacy, CAM leases, immutable ledger
# D25-25c: TAES Evaluation - Logical/Practical/Probable scoring, IRD thresholds
# D26-28: Red-Team Layer - Falsification MAS, CV detection, structured dissent

BRIEFINGS = {
    "d0":    "Observe Change Control (D0): record kernel modifications, maintain directive parity, enforce version integrity, rollback authority reserved to Operator.",
    "core":  "Enforce AxProtocol Core (1–14): truth discipline, logic integrity, contradiction detection.",
    "add":   "Apply War-Room Addendum (15–19): objective grounding, scoring ≥85, handoff, efficiency, client-readiness.",
    "aal":   "Respect Authority Assertion (20–24): Operator supremacy, CAM lease, immutable ledger, killchain, drift monitor.",
    "taes":  "Use TAES (25–25c): weigh Logical/Practical/Probable, IRD>0.5 -> RRP.",
    "rdl":   "Red-Team Layer (26–28): falsification MAS, CV detection, residual risk, structured dissent.",
}

# Collaboration contract appended to all role system prompts to encourage
# complementary, non-duplicative artifacts with cross-role traceability.
COLLAB_CONTRACT = (
    "\nCollaboration Contract:\n"
    "- Build on prior roles; do not restate their sections.\n"
    "- Introduce new artifacts and assign stable IDs (S-1, A-1, P-1, C-1).\n"
    "- Cross-reference upstream IDs wherever applicable.\n"
    "- Prefer depth and specificity over general prose.\n"
)

# Role-specific directive loadouts + temperature to reduce cross-role mimicry
ROLE_CFG = {
    # Strategist: full CORE to enforce logic/integrity (D1–14), brief ADD
    "Strategist": {
        "include": ("d0", "core", "add"),
        "ask_full": "CORE",
        "temp": 0.30
    },
    # Analyst: full TAES (D25–25c) for IV/IRD math, brief CORE
    "Analyst": {
        "include": ("d0", "core", "taes"),
        "ask_full": "TAES",
        "temp": 0.20
    },
    # Producer: full War-Room Addendum (D15–19) for handoffs/deliverables
    "Producer": {
        "include": ("d0", "add", "core"),
        "ask_full": "ADD",
        "temp": 0.65
    },
    # Courier: full AAL (D20–24) for packaging, CAM, ledger, authority checks
    "Courier": {
        "include": ("d0", "add", "aal"),
        "ask_full": "AAL",
        "temp": 0.35
    },
    # Critic: full RDL (D26–28) + brief TAES/AAL to run falsification gate
    "Critic": {
        "include": ("d0", "core", "rdl", "taes", "aal"),
        "ask_full": "RDL",
        "temp": 0.25
    }
}


def compose_system(
    role_prompt: str,
    directives: dict,
    include=("d0", "core", "add", "aal", "taes", "rdl"),
    ask_full: Optional[str] = None
) -> str:
    """
    Compose system prompt from role + directive briefings + optional full directive content.

    Args:
        role_prompt: The role definition text
        directives: Dictionary of directive content (from load_directives)
        include: Which directive briefings to include (lowercase keys)
        ask_full: Optional directive key (uppercase) to append full text (e.g., "RDL", "TAES", "CORE")
                  Use this when agent needs complete directive details for enforcement
    """
    buf = [BRIEFINGS[k] for k in include if k in BRIEFINGS]
    if role_prompt:
        buf.insert(0, role_prompt.strip())

    # If ask_full specified, append the complete directive text
    if ask_full and ask_full.upper() in directives:
        directive_key = ask_full.upper()
        buf.append(f"\n{'═'*80}\nFULL DIRECTIVE: {directive_key}\n{'═'*80}\n{directives[directive_key]}")

    # Append collaboration contract to all roles
    buf.append(COLLAB_CONTRACT)

    # Optional debug: dump first few lines of the system prompt
    try:
        import os as _os
        if _os.getenv("DEBUG_SYS", "0") == "1":
            preview = "\n".join("\n\n".join(buf).splitlines()[:12])
            print("[DEBUG_SYS] System prompt preview:\n" + preview + "\n---")
    except Exception as e:
        # Code quality improvement: Log debug failures
        logging.getLogger("axprotocol").debug(f"Debug preview failed: {e}")

    return "\n\n".join(buf)


def system_for(role_name: str, role_prompt: str, directives: dict) -> str:
    """
    Generate system prompt for a specific role.

    Args:
        role_name: Role name (must be in ROLE_CFG)
        role_prompt: Role definition text
        directives: Dictionary of directive content

    Returns:
        Composed system prompt
    """
    cfg = ROLE_CFG[role_name]
    return compose_system(
        role_prompt,
        directives,
        include=cfg["include"],
        ask_full=cfg["ask_full"]
    )


def role_temp(role_name: str) -> float:
    """
    Get temperature setting for a role.

    Args:
        role_name: Role name

    Returns:
        Temperature value
    """
    return ROLE_CFG[role_name]["temp"]

