"""
Final report composition utilities.
"""

from typing import Dict


def compose_final_report(objective: str, registry: Dict, qa_log: Dict) -> str:
    """
    Compose final execution summary report.

    Args:
        objective: Original objective
        registry: Registry with role outputs
        qa_log: Q&A log

    Returns:
        Markdown-formatted report
    """
    lines = []
    lines.append("# AxProtocol Execution Summary")
    lines.append(f"Objective: {objective}")
    if registry.get("S"):
        lines.append("\n## Strategy (S)")
        for item in registry["S"]:
            lines.append(f"- {item.get('s_id')}: {item.get('title')}")
    if registry.get("A"):
        lines.append("\n## Analysis (A)")
        for item in registry["A"]:
            lines.append(f"- {item.get('a_id')} -> refs {item.get('s_refs')}")
    if registry.get("P"):
        lines.append("\n## Production Assets (P)")
        for item in registry["P"]:
            lines.append(f"- {item.get('p_id')} [{item.get('spec_type')}], refs {item.get('a_refs')}")
    if registry.get("C"):
        lines.append("\n## Courier Schedule (C)")
        for item in registry["C"]:
            lines.append(f"- {item.get('day')} {item.get('time')} via {item.get('channel')} -> {item.get('p_id')} (target {item.get('kpi_target')})")
    if registry.get("X"):
        lines.append("\n## Critic Findings (X)")
        for item in registry["X"]:
            lines.append(f"- {item.get('x_id')} severity={item.get('severity')} refs={item.get('refs')}")
    if qa_log:
        lines.append("\n## Clarifications")
        for key, payload in qa_log.items():
            lines.append(f"- {key}: Q: {payload['question']} | A: {payload['answer']}")
    return "\n".join(lines)

