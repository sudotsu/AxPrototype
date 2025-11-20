import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Internal imports
from axp.core.engine import run_role_json
from axp.governance.taes_evaluation import calculate_taes_metrics, log_taes_event
# from axp.utils.session_logging import log_session  # Commented out until refactored

# Configure logging
logger = logging.getLogger("axp.chain")

def init_registry():
    """Initialize the session registry for the 3-Role Chain."""
    return {
        "Caller": {},
        "Builder": {},
        "Critic": {},
        "metadata": {
            "start_time": datetime.utcnow().isoformat(),
            "domain": "creative",
            "revision_count": 0
        }
    }

def execute_caller_only(
    user_prompt: str,
    base_dir: Path,
    session_id: str,
    validator_func: Any,
    shapes_config: Dict
) -> Dict:
    """
    Executes ONLY the Caller role to generate OPS (Optimized Prompt Suggestion)
    and AxP Insight. This is the 'Sparring Partner' phase.
    """
    registry = init_registry()

    # Empty placeholders for required args that aren't used in Caller phase
    prev_texts = []
    redundancy_metrics = {}

    # 1. Run Caller
    _, caller_data = run_role_json(
        role_name="Caller",
        sys_prompt_path=base_dir / "prompts" / "creative" / "caller_stable.txt",
        user_prompt=user_prompt,
        strict_prompt=None, # Caller usually doesn't need strict JSON enforcement on input
        example_path=None,
        validator=validator_func,
        registry=registry,
        registry_key="Caller",
        shapes_cfg=shapes_config,
        session_id=session_id,
        detected_domain="creative",
        prev_texts=prev_texts,
        redundancy_metrics=redundancy_metrics,
        base_dir=base_dir
    )

    return caller_data

def run_creative_chain(
    final_objective: str,
    user_context: Dict,
    config: Dict,
    base_dir: Path,
    session_id: str,
    validator_func: Any,
    shapes_config: Dict
) -> Dict:
    """
    The Engine -> Gatekeeper Loop.
    Executes Builder -> Critic.
    If Critic rejects, triggers Revision -> Builder -> Critic (Re-eval).
    """
    registry = init_registry()

    # Setup context tracking
    prev_texts = []
    redundancy_metrics = {}

    # --- PHASE 1: BUILDER (Draft 1) ---
    logger.info(">>> STARTING BUILDER (Draft 1)")

    # Inject user context (if they rejected previous attempts, etc.)
    builder_prompt = final_objective
    if user_context.get("user_feedback"):
        builder_prompt += f"\n\n[USER CONTEXT]: {user_context['user_feedback']}"

    _, builder_data = run_role_json(
        role_name="Builder",
        sys_prompt_path=base_dir / "prompts" / "creative" / "builder_stable.txt",
        user_prompt=builder_prompt,
        strict_prompt=None,
        example_path=None,
        validator=validator_func,
        registry=registry,
        registry_key="Builder",
        shapes_cfg=shapes_config,
        session_id=session_id,
        detected_domain="creative",
        prev_texts=prev_texts,
        redundancy_metrics=redundancy_metrics,
        base_dir=base_dir
    )

    # Update history for redundancy checks
    if "content" in builder_data:
        prev_texts.append(builder_data["content"])

    # --- PHASE 2: CRITIC (Eval 1) ---
    logger.info(">>> STARTING CRITIC (Eval 1)")

    _, critic_data = run_role_json(
        role_name="Critic",
        sys_prompt_path=base_dir / "prompts" / "creative" / "critic_stable.txt",
        user_prompt=json.dumps(builder_data), # Pass full Builder JSON to Critic
        strict_prompt=None,
        example_path=None,
        validator=validator_func,
        registry=registry,
        registry_key="Critic",
        shapes_cfg=shapes_config,
        session_id=session_id,
        detected_domain="creative",
        prev_texts=prev_texts,
        redundancy_metrics=redundancy_metrics,
        base_dir=base_dir
    )

    # Log initial TAES
    if "scores" in critic_data:
        log_taes_event(session_id, "Critic_1", critic_data["scores"])

    # --- PHASE 3: GOVERNANCE & REVISION LOOP ---
    # Check score. If < 85 (or threshold), trigger revision.
    taes_score = critic_data.get("taes_score", 0)

    if taes_score < 85:
        logger.info(f"!!! REVISION TRIGGERED (Score: {taes_score}) !!!")
        registry["metadata"]["revision_count"] += 1

        # Construct Revision Prompt
        revision_prompt = (
            f"ORIGINAL REQUEST: {final_objective}\n"
            f"DRAFT 1:\n{builder_data.get('content', '')}\n\n"
            f"CRITIC FEEDBACK (Score {taes_score}):\n{critic_data.get('feedback', 'No feedback provided.')}\n"
            f"INSTRUCTION: Rewrite the draft to address the feedback explicitly."
        )

        # 3a. Builder (Revision)
        _, builder_revised = run_role_json(
            role_name="Builder",
            sys_prompt_path=base_dir / "prompts" / "creative" / "builder_stable.txt",
            user_prompt=revision_prompt,
            strict_prompt=None,
            example_path=None,
            validator=validator_func,
            registry=registry,
            registry_key="Builder", # Overwrites previous Builder entry in registry (Snapshot model)
            shapes_cfg=shapes_config,
            session_id=session_id,
            detected_domain="creative",
            prev_texts=prev_texts,
            redundancy_metrics=redundancy_metrics,
            base_dir=base_dir
        )

        # Update output reference
        builder_data = builder_revised

        # 3b. Critic (Re-Eval) - CRITICAL FIX: Re-running Critic on new draft
        logger.info(">>> STARTING CRITIC (Eval 2 - Post-Revision)")
        _, critic_revised = run_role_json(
            role_name="Critic",
            sys_prompt_path=base_dir / "prompts" / "creative" / "critic_stable.txt",
            user_prompt=json.dumps(builder_data),
            strict_prompt=None,
            example_path=None,
            validator=validator_func,
            registry=registry,
            registry_key="Critic", # Overwrites previous Critic entry
            shapes_cfg=shapes_config,
            session_id=session_id,
            detected_domain="creative",
            prev_texts=prev_texts,
            redundancy_metrics=redundancy_metrics,
            base_dir=base_dir
        )

        # Update critic reference and log new TAES
        critic_data = critic_revised
        if "scores" in critic_data:
            log_taes_event(session_id, "Critic_2", critic_data["scores"])

    # --- PHASE 4: FINALIZATION ---

    # Calculate final governance metrics (IV/IRD)
    # This acts as the final gate. In future, this could block output.
    governance_status = "approved"
    if "scores" in critic_data:
        metrics = calculate_taes_metrics([critic_data["scores"]])
        # Example Gate: If IRD is too high (hallucination risk), flag it.
        if metrics["ird"] > 0.15:
            governance_status = "flagged_high_ird"

    final_output = {
        "artifact": builder_data.get("content", ""),
        "rationale": builder_data.get("rationale", ""),
        "critic_feedback": critic_data.get("feedback", ""),
        "taes_score": critic_data.get("taes_score", 0),
        "governance_status": governance_status,
        "session_id": session_id
    }

    # Legacy Logging (Commented out until signature is fixed)
    # log_session(...)

    return final_output
