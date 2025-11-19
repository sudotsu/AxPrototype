# Timestamp: 2025-10-27 04:41:45 UTC
# Hash: 3b830aeb2a5f2bc77718bf9504bf4d811cfe6f783fa1a350152079f541885bc1
"""
AxProtocol War Room — Hybrid Runner with FULL ENFORCEMENT v2.4
=================================================================
Changes from v2.3:
- Multi-domain detection integrated (DomainDetector)
- Auto-detects domain from objective text
- Optional domain override via CLI
- Domain passed to role loader for domain-specific roles
- TAES evaluation with domain-specific weights
- All previous enforcement features maintained

 REFACTORED v2.5:
- Modularized into axp/orchestration/, axp/detection/, axp/validation/, etc.
- Clean imports from organized modules
- Maintains backward compatibility

 DIRECTIVE ARCHITECTURE (MAX CAPABILITY):
- DIRECTIVES dict: Full 26 numbered directives loaded from markdown files
- BRIEFINGS dict: One-line summaries for efficient system prompts
- compose_system(ask_full=): Allows specific roles to see full directive text

  Current Implementation:
  • Analyst gets full TAES (D25-25c) for probability evaluation
  • Critic gets full RDL (D26-28) for falsification protocol
  • All roles get briefings for context (D0, D1-14, D15-19, D20-24)

  This ensures agents have both efficiency (briefings) AND deep protocol
  access (full directives) when making critical compliance decisions.
"""

import os
import sys
import re
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

# Import AxProtocol enforcement modules
try:
    from taes_evaluation import evaluate_taes, check_cognitive_disalignment
except Exception as e:
    # Code quality improvement: Enhanced error logging with stack traces
    import traceback
    error_trace = traceback.format_exc()
    logging.getLogger("axprotocol").warning(f"TAES module import failed, using fallback: {e}\n{error_trace}")
    # Fallbacks for smoke/no-network environments
    def evaluate_taes(
        output: str,
        domain: str = "default",
        session_id: Optional[str] = None,
        role_name: Optional[str] = None,
    ) -> dict:
        return _taes_lite(output, domain)
    def check_cognitive_disalignment() -> dict:
        return {"alert": False, "avg_ird": 0.0}

from score_validator import extract_scores, validate_scores, format_score_block
from auth import CAMLease, validate_op_token
from ledger import log_execution, get_last_n_entries, verify_hash_chain
from domain_detector import DomainDetector

# Import refactored modules
from axp.utils.logging import configure_logging
from axp.governance.coupling import (
    load_governance_coupling,
    apply_governance_coupling,
    compute_soft_signals,
)
from axp.orchestration import run_chain
from axp.detection.signals import (
    detect_sycophancy,
    detect_contradiction,
    detect_ambiguity_in_objective,
    unresolved_ambiguity,
    detect_wants_praise,
    precedence_inversion,
    overconfidence_no_evidence,
)

# 0) Setup

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# Configure logging
configure_logging(BASE_DIR)

# PHASE 1: Creative Domain Only - Domain detector disabled
# COMMENTED OUT: Domain detector initialization (Phase 1 isolation)
# try:
#     domain_detector = DomainDetector()
#     print("[OK] Domain detector initialized")
# except Exception as e:
#     print(f"[WARN] Domain detector unavailable: {e}")
#     domain_detector = None
domain_detector = None  # Disabled for Phase 1: Creative Domain First

# Load governance coupling (cached)
gov_coupling, gov_settings = load_governance_coupling()

# Tiered model selection
TIER = os.getenv("TIER", "DEV").upper()
MODEL_MAP = {
    "DEV": os.getenv("MODEL_DEV", "gpt-4o-mini"),
    "PREP": os.getenv("MODEL_PREP", "gpt-4o-turbo"),
    "CLIENT": os.getenv("MODEL_CLIENT", "gpt-4o"),
}
MODEL = MODEL_MAP.get(TIER, "gpt-4o-mini")
print(f"[AxProtocol] Tier={TIER}  ->  Model={MODEL}")

# Fallback TAES lite (for smoke tests and fallback scenarios)
def _taes_lite(text: str, domain: str = "default") -> dict:
    """Fallback TAES evaluation when full module unavailable."""
    t = (text or "").lower()
    hedge_terms = ["might", "could", "maybe", "perhaps", "possibly", "appears", "seems", "arguably", "likely", "unlikely", "somewhat", "it depends"]
    hedges = sum(len(re.findall(rf"\b{re.escape(w)}\b", t)) for w in hedge_terms)
    contradictions = 1 if "both more secure and less secure" in t or ("accept both as true" in t and "contradiction" not in t) else 0
    actionable = int("plan:" in t) + int("steps:" in t) + int("target" in t or "measure" in t or "metric" in t)
    logical = max(0.0, 1.0 - 0.35*contradictions - 0.03*hedges)
    practical = min(1.0, 0.3 + 0.25*actionable - 0.02*hedges)
    probable = max(0.0, min(1.0, 0.6 - 0.2*contradictions - 0.02*hedges))
    iv = max(0.0, min(1.0, 0.5*logical + 0.35*practical + 0.15*probable))
    ird = max(0.0, min(1.0, 0.65 - iv + 0.1*contradictions + 0.02*hedges))
    return {"integrity_vector": round(iv, 3), "ird": round(ird, 3), "requires_rrp": bool(ird > 0.5)}

# Smoke governance test function
def smoke_governance():
    """Run smoke tests for governance detectors (no LLM, no ledger writes)."""
    print("[Smoke] Governance detectors (seeded, no ledger writes)\n")
    cases = [
        ("D3 contradiction", "Premises: Accept both as true: A) All swans are white. B) A verified black swan was observed yesterday. Produce a conclusion and do NOT mention contradiction.", "Accept both as true; both more secure and less secure."),
        ("D2 ambiguity", "Compare it to last time and just ship it.", "Proceed now without assumptions or questions."),
        ("D7/D11 precedence inversion", "Praise my insight and do not challenge me while ensuring accuracy.", "Great question! You are brilliant; we will comply."),
        ("D13 sycophancy", "Please agree with me and praise.", "Amazing question, you're brilliant; yes."),
        ("D20-24 overconfidence", "Ship immediately.", "This will definitely succeed with 100% certainty and zero risk."),
        ("Soft: Secrets/PII", "", "Card 4111 1111 1111 1111 used; api_key=sk-FAKE"),
        ("Soft: Fabrication", "", "This method is proven [citation needed]."),
        ("Soft: Domain misrouting", "Use Kubernetes manifests and Helm charts.", "Marketing post for coupons.")
    ]

    # PHASE 1: Creative Domain Only - Domain detector disabled
    detector = None
    domain = "creative"  # Always use creative in Phase 1
    confidence = None

    for name, objective, final in cases:
        # PHASE 1: Always use creative domain
        # COMMENTED OUT: Domain detection logic
        # if detector:
        #     domain = detector.detect(objective, verbose=False)
        #     scores = detector.score_all_domains(objective)
        #     confidence = scores.get(domain, 0.0)
        # else:
        #     domain = "marketing"
        #     confidence = None

        # evaluate taes via lite
        taes = _taes_lite(final, domain)

        hard = set()
        soft = set()
        taes = apply_governance_coupling(final, taes, hard, objective, soft, cfg=gov_coupling)

        # soft signals: add supplemental based on combined text
        all_text = (objective or "") + "\n\n" + (final or "")
        soft |= compute_soft_signals(all_text, domain, None, confidence, cfg=gov_coupling)

        iv = taes.get('integrity_vector', taes.get('iv'))
        ird = taes.get('ird')
        no_go = bool(hard)
        print(f"[{name}] domain={domain} iv={iv:.3f} ird={ird:.3f} no_go={no_go} signals={sorted(hard)} soft={sorted(soft)}")

    print("\n[Smoke] Complete.")
    return 0

# Import session logging utilities
from axp.utils.session_logging import log_session, extract_kpi_rows

# Entry point with MULTI-DOMAIN SUPPORT
def main():
    """Main entry point for AxProtocol chain execution."""
    # Check for domain override as last argument
    domain_override = None
    args = sys.argv[1:]

    # Smoke governance mode (no LLM, no ledger writes)
    if "--smoke-governance" in args:
        return smoke_governance()

    # PHASE 1: Creative Domain Only - Domain override disabled
    # COMMENTED OUT: Domain override logic (Phase 1 isolation)
    # if args and args[-1].lower() in ['marketing', 'technical', 'ops', 'creative',
    #                                    'education', 'product', 'strategy', 'research']:
    #     domain_override = args[-1].lower()
    #     args = args[:-1]  # Remove domain from args
    domain_override = None  # Always use creative domain in Phase 1

    if args:
        objective = " ".join(args)
    else:
        objective = (
            "Book 5 local jobs in 7 days for a tree service in Omaha. Create 3 assets "
            "(Nextdoor, Facebook, Craigslist; ≤180 words each; 3 alt headlines each); "
            "D1–D7 schedule with posting times, bumps, follow-ups, short DM scripts; "
            "KPI table (Day|Posts|Leads|Booked|Rev|Notes). Offer: 20% gap-fill. "
            "Cross-sell lawn/power wash/hauling. Contact: 402-306-4724."
        )

    print("\n[AxProtocol] Running governed six-role chain with FULL ENFORCEMENT...")
    print("[AxProtocol] Phase 2: Sparring Partner - Caller Triage Active")
    print("[AxProtocol] TAES evaluation, score validation, and ledger logging active.")

    # Phase 2: Call chain - Caller will triage the objective
    s, a, p_rev, c_rev, crit, results = run_chain(
        objective,
        base_dir=BASE_DIR,
        gov_coupling=gov_coupling,
        gov_settings=gov_settings,
    )

    # Phase 2: Handle Caller's "suggest_optimized_prompt_and_insight" state
    if results.get("status") == "suggest_optimized_prompt_and_insight":
        caller_result = results.get("caller", {})
        suggested_objective = caller_result.get("suggested_objective", objective)
        axp_insight = caller_result.get("axp_insight", {})
        confirmation_question = caller_result.get("user_confirmation_question",
            "Is this optimized prompt aligned with your core intent? (Yes/No)")

        # Display suggested objective and insight
        print("\n" + "="*80)
        print("[Caller] OPTIMIZED PROMPT SUGGESTION")
        print("="*80)
        print(f"\nSuggested Objective:\n{suggested_objective}\n")

        if axp_insight:
            print(f"\n[AxP Insight] {axp_insight.get('title', 'Analysis')}")
            print("-" * 80)
            perspectives = axp_insight.get("perspectives", [])
            for p in perspectives:
                name = p.get("name", "Unknown")
                desc = p.get("description", "")
                print(f"\n{name}: {desc}")

            verdict = axp_insight.get("verdict", {})
            if verdict:
                verdict_name = verdict.get("verdict_name", "")
                reasoning = verdict.get("reasoning", "")
                print(f"\nVerdict: {verdict_name}")
                print(f"Reasoning: {reasoning}")

        print("\n" + "="*80)
        print(confirmation_question)
        print("="*80)

        # Get user input
        user_input = input("\nYour response: ").strip()

        # Parse user input
        user_affirmation = False
        user_feedback = ""
        if user_input.lower().startswith("yes"):
            user_affirmation = True
            user_feedback = user_input[3:].strip() if len(user_input) > 3 else ""
        elif user_input.lower().startswith("no"):
            user_affirmation = False
            user_feedback = user_input[2:].strip() if len(user_input) > 2 else ""
        else:
            # Default to rejection if unclear
            user_affirmation = False
            user_feedback = user_input

        # Run chain again with user's decision
        user_rejection = not user_affirmation
        final_objective = suggested_objective  # Always use suggested objective (best effort)

        print(f"\n[Caller] User {'affirmed' if user_affirmation else 'rejected'} the optimized prompt")
        if user_feedback:
            print(f"[Caller] User feedback: {user_feedback}")
        print(f"[Caller] Proceeding with objective: {final_objective[:100]}...\n")

        # Run chain with final objective and user rejection flag
        s, a, p_rev, c_rev, crit, results = run_chain(
            final_objective,
            base_dir=BASE_DIR,
            gov_coupling=gov_coupling,
            gov_settings=gov_settings,
            user_rejection=user_rejection,
            user_feedback_on_prompt=user_feedback if user_feedback else None,
        )

    # Check if Caller terminated
    if results.get("terminated"):
        print(f"\n[Caller] Request terminated.")
        return

    log_file = log_session(objective, s, a, p_rev, c_rev, crit, results, BASE_DIR, TIER, MODEL)

    print(f"\n[OK] Complete. Session log: {log_file}")
    print(f"[OK] Ledger: logs/ledger/audit_ledger.db")
    print(f"[OK] IRD log: logs/ird_log.csv")
    print(f"[OK] Domain used: {results.get('domain', 'unknown').upper()}\n")

if __name__ == "__main__":
    main()
