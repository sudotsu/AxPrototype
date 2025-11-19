"""
Micro Q&A helpers for inter-role clarification.
"""

from typing import Tuple
from pathlib import Path
from axp.utils.llm import call_llm
from axp.utils.errors import append_session_error


def run_micro_qa(
    session_id: str,
    detected_domain: str,
    asker: str,
    responder: str,
    context: str,
    base_dir
) -> Tuple[bool, str, str]:
    """
    Run micro Q&A between roles.

    Args:
        session_id: Session identifier
        detected_domain: Domain name
        asker: Role asking question
        responder: Role answering question
        context: Context text for Q&A
        base_dir: Base directory for error logging

    Returns:
        Tuple of (success, question, answer)
    """
    try:
        question = call_llm(
            f"Micro-QA ({asker} asking {responder})",
            context + f"\nAsk ONE clarifying question for the {responder}. If none needed, reply with NONE.",
            temperature=0.35
        )
    except Exception as exc:
        append_session_error(session_id, detected_domain, f"QA-{asker}", exc, base_dir)
        return False, "", ""
    if question.strip().upper().startswith("NONE"):
        return False, "", ""
    try:
        answer = call_llm(
            f"Micro-QA ({responder} answering {asker})",
            context + f"\nQuestion: {question}\nProvide a short, direct answer.",
            temperature=0.2
        )
    except Exception as exc:
        append_session_error(session_id, detected_domain, f"QA-{responder}", exc, base_dir)
        return False, question, ""
    return True, question.strip(), answer.strip()

