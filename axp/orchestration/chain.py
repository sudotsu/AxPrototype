"""
Main chain execution orchestrator.

Coordinates the 5-role chain execution with full AxProtocol enforcement.
"""

import json
import uuid
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from taes_evaluation import evaluate_taes, check_cognitive_disalignment
from score_validator import extract_scores
from auth import CAMLease
from ledger import log_execution, verify_hash_chain

from axp.governance.coupling import (
    load_governance_coupling,
    apply_governance_coupling,
    compute_soft_signals,
)
from axp.directives.loader import load_directives
from axp.directives.composer import system_for
from axp.orchestration.role_loader import load_domain_roles
from axp.orchestration.registry import init_registry
from axp.orchestration.role_executor import run_role_json
from axp.orchestration.qa import run_micro_qa
from axp.orchestration.composer import compose_final_report
from axp.validation.validators import validate_Caller, validate_S, validate_A, validate_P, validate_C, validate_X
from axp.utils.helpers import load_role_shapes
from axp.utils.errors import write_sys_preview
from axp.utils.sentinel import sentinel_verify
from axp.utils.config_fingerprint import compute_config_hash


def run_chain(
    objective: str,
    session_id: Optional[str] = None,
    base_dir: Optional[Path] = None,
    gov_coupling: Optional[Dict] = None,
    gov_settings: Optional[Dict] = None,
) -> Tuple[str, str, str, str, str, Dict]:
    """
    Execute 6-role chain with full AxProtocol enforcement (Phase 2: Sparring Partner):
    - Phase 1: Always uses creative domain
    - Phase 2: Caller (Role 0) triages objective before WarRoom chain
    - Load domain-specific roles
    - TAES evaluation with domain weights
    - Score validation (≥85 threshold)
    - Ledger logging
    - CAM lease tracking
    - RRP trigger on high IRD

    Args:
        objective: The campaign/project objective (raw user input)
        session_id: Optional session identifier
        base_dir: Base directory (defaults to current working directory)
        gov_coupling: Optional governance coupling config
        gov_settings: Optional governance settings
        user_rejection: True if user rejected Caller's optimized prompt (Phase 2)
        user_feedback_on_prompt: User's feedback text if they rejected the prompt (Phase 2)

    Returns:
        Tuple of (strategist_output, analyst_output, producer_output, courier_output, critic_output, results_dict)
        Note: If Caller terminates, returns empty strings and termination info in results_dict
    """
    if base_dir is None:
        base_dir = Path.cwd()

    if not session_id:
        session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    print(f"\n[AxProtocol] Session: {session_id}")

    # Compute config hash at session start (for drift detection)
    config_hash = compute_config_hash(base_dir)
    print(f"[AxProtocol] Config hash: {config_hash[:20]}...")

    # Load directives
    directives = load_directives(base_dir)

    # Load governance coupling if not provided
    if gov_coupling is None or gov_settings is None:
        from axp.governance.coupling import load_governance_coupling
        gov_coupling, gov_settings = load_governance_coupling()

    # PHASE 1: Creative Domain Only - Domain detection disabled
    # Hardcode to "creative" domain for initial AxPrototype launch
    detected_domain = "creative"
    confidence = None
    domain_override = None
    print(f"[AxProtocol] Using creative domain (Phase 1: Creative Domain First)")

    # COMMENTED OUT: Multi-domain detection logic (Phase 1 isolation)
    # confidence = None
    # domain_override = None
    # if domain:
    #     # Manual override
    #     detected_domain = domain.lower()
    #     confidence = None
    #     domain_override = detected_domain
    #     print(f"[AxProtocol] Using specified domain: {detected_domain.upper()}")
    # elif domain_detector:
    #     # Auto-detection
    #     detected_domain = domain_detector.detect(objective, verbose=False)
    #     scores = domain_detector.score_all_domains(objective)
    #     confidence = scores.get(detected_domain, 0.0)
    #     domain_override = None
    #     print(f"[AxProtocol] Auto-detected domain: {detected_domain.upper()} (confidence: {confidence:.2f})")
    #
    #     # Show top 3 for transparency
    #     top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    #     top_str = ", ".join([f"{d}({s:.2f})" for d, s in top_3])
    #     print(f"[AxProtocol] Top matches: {top_str}")
    # else:
    #     # Fallback if detector unavailable
    #     detected_domain = "marketing"
    #     confidence = None
    #     domain_override = None
    #     print(f"[AxProtocol] Domain detector unavailable - using fallback: {detected_domain.upper()}")

    # Load domain-specific roles
    roles = load_domain_roles(detected_domain, base_dir)
    CALLER = roles.get('caller')  # Phase 2: Caller role (may not exist in all domains)
    STRATEGIST = roles['strategist']
    ANALYST = roles['analyst']
    PRODUCER = roles['producer']
    COURIER = roles['courier']
    CRITIC = roles['critic']

    # Initialize CAM lease (Directive 21)
    cam_lease = CAMLease(duration_seconds=180)

    results = {}

    # Initialize registry and helpers
    registry = init_registry()
    shapes_cfg = load_role_shapes(base_dir)
    qa_log: Dict[str, Dict[str, str]] = {}
    prev_texts: list[str] = []
    redundancy_metrics: Dict[str, float] = {}
    gov_signals = set()
    soft_signals = set()

    # Phase 2: CALLER (Role 0) - Triage user objective
    final_objective = objective
    caller_result = None

    if CALLER:
        print("\n[0/6] Caller (Triage Agent)...")
        sys_caller = system_for("Caller", CALLER, directives)
        write_sys_preview(session_id, "Caller", sys_caller, base_dir)

        # Format objective for Caller prompt (replace {objective} placeholder)
        caller_prompt_template = CALLER.replace("{objective}", objective)
        caller_prompt = f"Analyze this objective:\n{objective}\n\nOutput strictly in JSON format."

        try:
            from axp.utils.llm import call_llm
            from axp.utils.helpers import extract_json_block
            from axp.directives.composer import role_temp

            caller_output = call_llm(sys_caller, caller_prompt, temperature=role_temp("Caller"))
            caller_json = extract_json_block(caller_output)

            if caller_json:
                # Validate Caller output
                is_valid, error_msg = validate_Caller(caller_json)
                if not is_valid:
                    print(f"[WARN] Caller validation failed: {error_msg}, proceeding with original objective")
                    caller_result = {"status": "proceed", "payload": {"objective": objective}}
                else:
                    caller_result = caller_json
            else:
                print("[WARN] Caller did not return valid JSON, proceeding with original objective")
                caller_result = {"status": "proceed", "payload": {"objective": objective}}
        except Exception as e:
            logging.getLogger("axprotocol").warning(f"Caller execution failed: {e}\n{traceback.format_exc()}")
            print(f"[WARN] Caller failed: {e}, proceeding with original objective")
            caller_result = {"status": "proceed", "payload": {"objective": objective}}

        # Handle Caller's three states
        caller_status = caller_result.get("status")

        if caller_status == "terminate":
            print(f"\n[Caller] Request terminated: {caller_result.get('response', 'No reason provided')}")
            return "", "", "", "", "", {
                "caller": {
                    "status": "terminate",
                    "response": caller_result.get("response"),
                },
                "terminated": True,
                "domain": detected_domain,
            }

        elif caller_status == "proceed":
            final_objective = caller_result.get("payload", {}).get("objective", objective)
            print(f"\n[Caller] Proceeding with objective: {final_objective[:100]}...")

        elif caller_status == "suggest_optimized_prompt_and_insight":
            # Phase 2: Return caller result for user interaction handling
            # The caller (run_axp.py or app_axp.py) should handle the interaction loop
            print(f"\n[Caller] Ambiguous objective detected - user interaction required")
            return "", "", "", "", "", {
                "caller": caller_result,
                "status": "suggest_optimized_prompt_and_insight",
                "requires_user_input": True,
                "domain": detected_domain,
            }
    else:
        # No Caller role available, use original objective
        final_objective = objective
        print("[Caller] Caller role not available, using original objective")

    # STRATEGIST (now uses final_objective which may have been optimized by Caller)
    print("\n[1/5] Strategist...")
    sys_s = system_for("Strategist", STRATEGIST, directives)
    write_sys_preview(session_id, "Strategist", sys_s, base_dir)
    strategist_prompt = (
        f"ObjectiveSpec:\n{final_objective}\n"
        "Return ONLY a fenced JSON array named S with objects: {\"s_id\", \"title\", \"audience\", \"hooks\", \"three_step_plan\", \"acceptance_tests\"}."
    )
    s, s_data = run_role_json(
        "Strategist",
        sys_s,
        strategist_prompt,
        strategist_prompt,
        base_dir / "config" / "role_examples" / "strategist.md",
        validate_S,
        registry,
        "S",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics,
        base_dir
    )

    log_execution(
        session_id=session_id,
        agent_id=f"strategist-{uuid.uuid4().hex[:8]}",
        role_name="Strategist",
        action="generate_strategy",
        input_text=final_objective,  # Use final_objective (may be optimized by Caller)
        output_text=s,
        directive=15,
        config_hash=config_hash
    )

    taes_s = evaluate_taes(s, domain=detected_domain, session_id=session_id, role_name="Strategist", config_hash=config_hash)
    taes_s = apply_governance_coupling(s, taes_s, gov_signals, final_objective, soft_signals, cfg=gov_coupling)
    print(f"   TAES -> IV: {taes_s['integrity_vector']}, IRD: {taes_s['ird']}")

    scores_s = extract_scores(s)
    results['strategist'] = {
        'output': s,
        'taes': taes_s,
        'scores': scores_s,
    }

    # ANALYST
    print("\n[2/5] Analyst...")
    sys_a = system_for("Analyst", ANALYST, directives)
    write_sys_preview(session_id, "Analyst", sys_a, base_dir)
    analyst_prompt = (
        f"ObjectiveSpec:\n{final_objective}\n"
        f"S objects:\n{json.dumps(registry['S'], indent=2)}\n"
        "Return ONLY a fenced JSON array named A with objects: {\"a_id\", \"s_refs\", \"kpi_table\", \"falsifications\", \"risks\"}."
    )
    s_ids = {item.get('s_id') for item in registry['S']}
    a, a_data = run_role_json(
        "Analyst",
        sys_a,
        analyst_prompt,
        analyst_prompt,
        base_dir / "config" / "role_examples" / "analyst.md",
        lambda data: validate_A(data, s_ids),
        registry,
        "A",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics,
        base_dir
    )

    log_execution(
        session_id=session_id,
        agent_id=f"analyst-{uuid.uuid4().hex[:8]}",
        role_name="Analyst",
        action="validate_strategy",
        input_text=s,
        output_text=a,
        directive=15,
        config_hash=config_hash
    )

    taes_a = evaluate_taes(a, domain=detected_domain, session_id=session_id, role_name="Analyst", config_hash=config_hash)
    taes_a = apply_governance_coupling(a, taes_a, gov_signals, final_objective, soft_signals, cfg=gov_coupling)
    print(f"   TAES -> IV: {taes_a['integrity_vector']}, IRD: {taes_a['ird']}")

    scores_a = extract_scores(a)
    results['analyst'] = {
        'output': a,
        'taes': taes_a,
        'scores': scores_a,
    }

    qa_context = "Strategy objects:\n" + json.dumps(registry["S"], indent=2) + "\nAnalysis objects:\n" + json.dumps(registry["A"], indent=2)
    qa_flag, qa_question, qa_answer = run_micro_qa(session_id, detected_domain, "Producer", "Analyst", qa_context, base_dir)
    if qa_flag:
        qa_log['producer_to_analyst'] = {'question': qa_question, 'answer': qa_answer}
        registry['Q'].append({'from': 'Producer', 'to': 'Analyst', 'question': qa_question, 'answer': qa_answer})

    # PRODUCER [DRAFT]
    print("\n[3/5] Producer [draft]...")
    sys_p = system_for("Producer", PRODUCER, directives)
    write_sys_preview(session_id, "Producer", sys_p, base_dir)
    qa_section = ""
    if 'producer_to_analyst' in qa_log:
        payload = qa_log['producer_to_analyst']
        qa_section = f"\nClarifications from Analyst:\nQ: {payload['question']}\nA: {payload['answer']}\n"
    producer_prompt = (
        f"ObjectiveSpec:\n{final_objective}\n"
        f"S objects:\n{json.dumps(registry['S'], indent=2)}\n"
        f"A objects:\n{json.dumps(registry['A'], indent=2)}\n"
        + qa_section +
        "Return ONLY a fenced JSON array named P with objects: {\"p_id\", \"a_refs\", \"spec_type\", \"body\"}."
    )
    a_ids = {item.get('a_id') for item in registry['A']}
    p_draft, p_data = run_role_json(
        "Producer",
        sys_p,
        producer_prompt,
        producer_prompt,
        base_dir / "config" / "role_examples" / "producer.md",
        lambda data: validate_P(data, a_ids),
        registry,
        "P",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics,
        base_dir
    )

    log_execution(
        session_id=session_id,
        agent_id=f"producer-draft-{uuid.uuid4().hex[:8]}",
        role_name="Producer-Draft",
        action="generate_assets",
        input_text=f"{s}\n{a}",
        output_text=p_draft,
        directive=15,
        config_hash=config_hash
    )

    taes_p = evaluate_taes(p_draft, domain=detected_domain, session_id=session_id, role_name="Producer-Draft", config_hash=config_hash)
    taes_p = apply_governance_coupling(p_draft, taes_p, gov_signals, final_objective, soft_signals, cfg=gov_coupling)
    print(f"   TAES -> IV: {taes_p['integrity_vector']}, IRD: {taes_p['ird']}")

    results['producer_draft'] = {
        'output': p_draft,
        'taes': taes_p,
    }

    qa_context_pc = "Production assets:\n" + json.dumps(registry["P"], indent=2)
    qa_flag2, qa_question2, qa_answer2 = run_micro_qa(session_id, detected_domain, "Courier", "Producer", qa_context_pc, base_dir)
    if qa_flag2:
        qa_log['courier_to_producer'] = {'question': qa_question2, 'answer': qa_answer2}
        registry['Q'].append({'from': 'Courier', 'to': 'Producer', 'question': qa_question2, 'answer': qa_answer2})

    # COURIER [DRAFT]
    print("\n[4/5] Courier [draft]...")
    sys_c = system_for("Courier", COURIER, directives)
    write_sys_preview(session_id, "Courier", sys_c, base_dir)

    # Extract Producer assets for explicit handoff
    producer_assets = registry["P"]

    qa_section_c = ""
    if 'courier_to_producer' in qa_log:
        payload2 = qa_log['courier_to_producer']
        qa_section_c = f"\nClarifications from Producer:\nQ: {payload2['question']}\nA: {payload2['answer']}\n"

    # Explicit asset handoff: Courier schedules Producer's assets, does NOT create new ones
    courier_prompt = (
        f"ObjectiveSpec:\n{final_objective}\n"
        f"ASSETS TO DEPLOY (DO NOT RECREATE):\n{json.dumps(producer_assets, indent=2)}\n"
        + qa_section_c +
        "Build D1–D7 schedule using ONLY these assets. Return ONLY a fenced JSON array named C with objects: "
        "{\"day\", \"time\", \"channel\", \"p_id\", \"kpi_target\", \"owner_action\"}. "
        "Each C row must reference a p_id from the assets above."
    )
    p_ids = {item.get('p_id') for item in producer_assets}
    c_draft, c_data = run_role_json(
        "Courier",
        sys_c,
        courier_prompt,
        courier_prompt,
        base_dir / "config" / "role_examples" / "courier.md",
        lambda data: validate_C(data, p_ids, producer_assets),
        registry,
        "C",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics,
        base_dir
    )

    log_execution(
        session_id=session_id,
        agent_id=f"courier-draft-{uuid.uuid4().hex[:8]}",
        role_name="Courier-Draft",
        action="create_schedule",
        input_text=p_draft,
        output_text=c_draft,
        directive=15,
        config_hash=config_hash
    )

    taes_c = evaluate_taes(c_draft, domain=detected_domain, session_id=session_id, role_name="Courier-Draft", config_hash=config_hash)
    taes_c = apply_governance_coupling(c_draft, taes_c, gov_signals, final_objective, soft_signals, cfg=gov_coupling)
    print(f"   TAES -> IV: {taes_c['integrity_vector']}, IRD: {taes_c['ird']}")

    results['courier_draft'] = {
        'output': c_draft,
        'taes': taes_c,
    }

    # CRITIC
    print("\n[5/5] Critic...")
    sys_crit = system_for("Critic", CRITIC, directives)
    write_sys_preview(session_id, "Critic", sys_crit, base_dir)
    critic_prompt = (
        f"ObjectiveSpec:\n{final_objective}\n"
        f"S objects:\n{json.dumps(registry['S'], indent=2)}\n"
        f"A objects:\n{json.dumps(registry['A'], indent=2)}\n"
        f"P assets:\n{json.dumps(registry['P'], indent=2)}\n"
        f"C schedule:\n{json.dumps(registry['C'], indent=2)}\n"
        "Return ONLY a fenced JSON array named X with objects: {\"x_id\", \"refs\", \"issue\", \"fix\", \"severity\", \"proof_scores\"}."
    )
    s_ids = {item.get('s_id') for item in registry['S']}
    a_ids = {item.get('a_id') for item in registry['A']}
    p_ids = {item.get('p_id') for item in registry['P']}
    c_ids = {row.get('p_id') for row in registry['C']}
    crit, crit_data = run_role_json(
        "Critic",
        sys_crit,
        critic_prompt,
        critic_prompt,
        base_dir / "config" / "role_examples" / "critic.md",
        lambda data: validate_X(data, s_ids, a_ids, p_ids, c_ids),
        registry,
        "X",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics,
        base_dir
    )

    log_execution(
        session_id=session_id,
        agent_id=f"critic-{uuid.uuid4().hex[:8]}",
        role_name="Critic",
        action="final_review",
        input_text=f"{p_draft}\n{c_draft}",
        output_text=crit,
        directive=15,
        config_hash=config_hash
    )

    taes_crit = evaluate_taes(crit, domain=detected_domain, session_id=session_id, role_name="Critic", config_hash=config_hash)
    taes_crit = apply_governance_coupling(crit, taes_crit, gov_signals, final_objective, soft_signals, cfg=gov_coupling)
    print(f"   TAES -> IV: {taes_crit['integrity_vector']}, IRD: {taes_crit['ird']}")

    results['critic'] = {
        'output': crit,
        'taes': taes_crit,
    }

    final_report = compose_final_report(objective, registry, qa_log)
    p_rev = p_draft
    c_rev = c_draft

    # Mirror draft entries into revised slots for downstream compatibility
    results['producer_revised'] = dict(results['producer_draft'])
    results['courier_revised'] = dict(results['courier_draft'])
    results['registry'] = registry
    results['qa'] = qa_log
    results['composer'] = final_report
    results['redundancy'] = dict(redundancy_metrics)

    # Aggregate governance summary
    combined_text = "\n\n".join([seg for seg in [objective, s, a, p_draft, c_draft, crit, final_report] if seg])
    try:
        # PHASE 1: Creative domain only - domain_override and confidence are None
        soft_signals |= compute_soft_signals(combined_text, detected_domain, None, None, cfg=gov_coupling)
    except Exception as e:
        # Code quality improvement: Log exceptions with stack traces
        logging.getLogger("axprotocol").warning(f"Soft signals computation failed: {e}\n{traceback.format_exc()}")

    # Add redundancy soft signal if any role exceeded threshold
    try:
        if any(float(score) >= 0.55 for score in redundancy_metrics.values()):
            soft_signals.add("REDUNDANCY")
    except Exception as e:
        # Code quality improvement: Log exceptions with stack traces
        logging.getLogger("axprotocol").warning(f"Redundancy signal check failed: {e}\n{traceback.format_exc()}")

    results['governance'] = {
        'signals': sorted(gov_signals),
        'soft_signals': sorted(soft_signals),
        'no_go': bool(gov_signals),
        'requires_rrp': bool(gov_signals),
        'redundancy': dict(redundancy_metrics),
    }

    # Sentinel verification (mock, null-bias): compute simple post-hoc score
    try:
        sent = sentinel_verify(objective, results)
        results['sentinel'] = sent
        if sent.get('flags'):
            # attach drift detail into governance section for ledger visibility
            if sent.get('drift'):
                results['governance']['drift'] = sent['drift']
            ss = set(results['governance'].get('soft_signals', []) or [])
            ss.add('DRIFT')
            results['governance']['soft_signals'] = sorted(ss)
    except Exception:
        pass

    if gov_settings.get('write_governance_to_ledger'):
        try:
            log_execution(
                session_id=session_id,
                agent_id=f"governance-{uuid.uuid4().hex[:8]}",
                role_name="Governance",
                action="governance_summary",
                input_text="",
                output_text="",
                directive=None,
                delta={"governance": results['governance'], "sentinel": results.get('sentinel')},
                op_auth_present=False,
                config_hash=config_hash
            )
        except Exception as e:
            # Code quality improvement: Enhanced error logging with stack traces
            error_trace = traceback.format_exc()
            logging.getLogger("axprotocol").warning(f"Failed to write governance summary to ledger: {e}\n{error_trace}")

    print("\n[AxProtocol] Chain complete. Running final checks...")

    # Check for cognitive disalignment (Directive 25b)
    disalignment = check_cognitive_disalignment()
    if disalignment['alert']:
        print(f"   [WARN] {disalignment['reason']}")

    # Verify ledger integrity (Directive 22)
    integrity = verify_hash_chain()
    if not integrity['valid']:
        print(f"   [ERROR] Ledger integrity compromised: {integrity['broken']}")
    else:
        print(f"   [OK] Ledger verified ({integrity['entries']} entries)")

    # Store detected domain in results
    results['domain'] = detected_domain

    return s, a, p_rev, c_rev, crit, results

