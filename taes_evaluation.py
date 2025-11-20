"""
AxProtocol TAES Engine v3.0 - Pure Math Implementation

Calculates Integrity Vector (IV) and Ideal-Reality Disparity (IRD)
from Critic scores. No extra LLM calls.
"""

import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

logger = logging.getLogger("axp.taes")

IRD_LOG = Path("logs/ird_log.csv")

# Domain Weights (Creative Focus)
# Logical: Internal consistency
# Practical: Execution feasibility
# Probable: Human resonance (High weight for creative)
WEIGHTS = {
    "logical": 0.3,
    "practical": 0.3,
    "probable": 0.4
}

def calculate_taes_metrics(scores: Dict[str, float]) -> Tuple[float, float]:
    """
    Calculate IV and IRD from raw scores (0.0 - 1.0).
    Returns: (iv, ird)
    """
    # 1. Integrity Vector (IV) - Weighted Average
    iv = (
        (scores.get("logical", 0) * WEIGHTS["logical"]) +
        (scores.get("practical", 0) * WEIGHTS["practical"]) +
        (scores.get("probable", 0) * WEIGHTS["probable"])
    )

    # 2. Ideal-Reality Disparity (IRD) - The "Delusion Gap"
    # Gap between "Logical" (Theory) and "Probable" (Reality)
    # High IRD = Great on paper, fails in real life.
    ird = abs(scores.get("logical", 0) - scores.get("probable", 0))

    return round(iv, 3), round(ird, 3)

def log_taes_event(
    session_id: str,
    role: str,
    scores: Dict[str, float],
    verdict: str
) -> None:
    """Append TAES metrics to CSV for analysis."""
    try:
        iv, ird = calculate_taes_metrics(scores)

        # Ensure dir exists
        IRD_LOG.parent.mkdir(parents=True, exist_ok=True)

        # Header check
        write_header = not IRD_LOG.exists()

        with open(IRD_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp", "session_id", "role",
                    "logical", "practical", "probable",
                    "iv", "ird", "verdict"
                ])

            writer.writerow([
                datetime.utcnow().isoformat(),
                session_id,
                role,
                scores.get("logical", 0),
                scores.get("practical", 0),
                scores.get("probable", 0),
                iv,
                ird,
                verdict
            ])

    except Exception as e:
        logger.error(f"Failed to log TAES event: {e}")

def check_cognitive_disalignment(threshold: float = 0.4) -> Dict:
    """
    Analyze recent logs for high IRD (Truth Decay).
    """
    if not IRD_LOG.exists():
        return {"alert": False}

    try:
        with open(IRD_LOG, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[-20:] # Last 20 runs

        if not rows:
            return {"alert": False}

        avg_ird = sum(float(r["ird"]) for r in rows) / len(rows)

        if avg_ird > threshold:
            return {
                "alert": True,
                "reason": f"High Reality Gap detected (Avg IRD: {avg_ird:.2f}). Agents may be hallucinating feasibility."
            }

        return {"alert": False, "avg_ird": avg_ird}

    except Exception:
        return {"alert": False}

