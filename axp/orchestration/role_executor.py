"""
Role execution utilities for running roles and parsing JSON outputs.
"""

import json
from pathlib import Path
from typing import Callable, Dict, List, Tuple, Optional

from axp.utils.llm import call_llm
from axp.utils.helpers import (
    extract_json_block,
    violates_exclusions,
    strict_reprompt,
    redundancy_score,
)
from axp.utils.errors import append_session_error
from axp.directives.composer import role_temp


def run_role_json(
    role_name: str,
    sys_prompt: str,
    user_prompt: str,
    strict_prompt: str,
    example_path: Optional[Path],
    validator: Callable,
    registry: Dict,
    registry_key: str,
    shapes_cfg: Dict,
    session_id: str,
    detected_domain: str,
    prev_texts: List[str],
    redundancy_metrics: Dict,
    base_dir: Path
) -> Tuple[str, list]:
    """
    Execute a role and parse JSON output with validation and redundancy checks.

    Args:
        role_name: Role name
        sys_prompt: System prompt
        user_prompt: User prompt
        strict_prompt: Strict reprompt text
        example_path: Optional path to few-shot example
        validator: Validation function
        registry: Registry dictionary
        registry_key: Key in registry for this role's output
        shapes_cfg: Role shapes configuration
        session_id: Session identifier
        detected_domain: Domain name
        prev_texts: List of prior role outputs for redundancy checking
        redundancy_metrics: Dictionary to store redundancy scores
        base_dir: Base directory for error logging

    Returns:
        Tuple of (output_text, parsed_data)
    """
    def _call(prompt: str, temp: float) -> str:
        try:
            return call_llm(sys_prompt, prompt, temperature=temp)
        except Exception as exc:
            append_session_error(session_id, detected_domain, role_name, exc, base_dir)
            raise

    def _parse(text: str):
        if violates_exclusions(text, role_name, shapes_cfg):
            return None, "excluded"
        data = extract_json_block(text)
        if data is None:
            return None, "no_json"
        ok, msg = validator(data)
        if not ok:
            return None, msg
        return data, "ok"

    base_temp = role_temp(role_name)
    text = _call(user_prompt, base_temp)
    data, msg = _parse(text)
    if data is None:
        text = strict_reprompt(role_name, sys_prompt, strict_prompt, example_path)
        data, msg = _parse(text)
        if data is None:
            # Graceful fallback: record soft failure and continue with empty slice
            append_session_error(session_id, detected_domain, role_name, Exception(f"validation_failed: {msg}"), base_dir)
            text = "[]"
            data = []
    red = redundancy_score(text, prev_texts, n=3)
    if red > 0.6:
        text = strict_reprompt(role_name, sys_prompt, strict_prompt, example_path)
        data, msg = _parse(text)
        if data is None:
            append_session_error(session_id, detected_domain, role_name, Exception(f"redundancy_retry_failed: {msg}"), base_dir)
        else:
            red = redundancy_score(text, prev_texts, n=3)
    prev_texts.append(text)
    try:
        redundancy_metrics[role_name] = float(f"{red:.3f}")
    except Exception:
        pass
    registry[registry_key] = data or []
    return text, data

