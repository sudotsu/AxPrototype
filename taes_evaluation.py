"""
AxProtocol TAES Evaluation Engine v2.2
Converts reasoning outputs into measurable Logical/Practical/Probable scores.
"""

import json
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from openai import OpenAI  # pyright: ignore[reportMissingImports]
import os
import logging
import asyncio  # Performance improvement: Async support for parallel TAES evaluations

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from axp.governance.ledger import write_ledger_entry

# Adaptive weighting matrix (Directive 25a)
ADAPTIVE_MATRIX = {
    "code": {"logical": 0.6, "practical": 0.35, "probable": 0.05},
    "infrastructure": {"logical": 0.6, "practical": 0.35, "probable": 0.05},
    "ops": {"logical": 0.4, "practical": 0.45, "probable": 0.15},
    "operations": {"logical": 0.4, "practical": 0.45, "probable": 0.15},
    "process": {"logical": 0.4, "practical": 0.45, "probable": 0.15},
    "creative": {"logical": 0.35, "practical": 0.25, "probable": 0.4},
    "content": {"logical": 0.35, "practical": 0.25, "probable": 0.4},
    "marketing": {"logical": 0.3, "practical": 0.2, "probable": 0.5},
    "growth": {"logical": 0.3, "practical": 0.2, "probable": 0.5},
    "default": {"logical": 0.4, "practical": 0.4, "probable": 0.2},
}

IRD_LOG = Path("logs/ird_log.csv")
IRD_LOG.parent.mkdir(parents=True, exist_ok=True)

# Optional: load per-domain TAES weights from config with safe fallback
def _load_taes_weights() -> dict:
    base_dir = Path(__file__).parent
    candidates = []
    try:
        import os as _os
        env_path = _os.getenv("TAES_WEIGHTS_PATH")
        if env_path:
            candidates.append(Path(env_path))
    except Exception:
        pass
    candidates.append(base_dir / "config" / "taes_weights.json")
    candidates.append(base_dir / "taes_weights.json")

    loaded = {}
    found_any = False
    for p in candidates:
        try:
            if p.exists():
                found_any = True
                raw = p.read_text(encoding="utf8")
                try:
                    data = json.loads(raw)
                except Exception as e:
                    logger.warning(f"TAES weights: invalid JSON in {p}: {e}; using built-in defaults")
                    return ADAPTIVE_MATRIX
                if not isinstance(data, dict):
                    logger.warning(f"TAES weights: expected object at {p}; using built-in defaults")
                    return ADAPTIVE_MATRIX
                for dname, weights in data.items():
                    if not isinstance(weights, dict):
                        logger.warning(f"TAES weights: domain '{dname}' is not an object; skipping")
                        continue
                    l = weights.get("logical")
                    pr = weights.get("practical")
                    pb = weights.get("probable")
                    try:
                        l = float(l); pr = float(pr); pb = float(pb)
                    except Exception:
                        logger.warning(f"TAES weights: domain '{dname}' has non-numeric values; skipping")
                        continue
                    if any(v < 0 for v in (l, pr, pb)):
                        logger.warning(f"TAES weights: domain '{dname}' has negative weights; skipping")
                        continue
                    loaded[dname.lower()] = {"logical": l, "practical": pr, "probable": pb}
                break
        except Exception as e:
            logger.warning(f"TAES weights: failed reading {p}: {e}; continuing")
            continue
    if not loaded:
        if not found_any:
            logger.warning("TAES weights: config not found; using built-in defaults")
        else:
            logger.warning("TAES weights: no valid entries; using built-in defaults")
        return ADAPTIVE_MATRIX
    # Merge with built-ins; config overrides defaults
    return {**ADAPTIVE_MATRIX, **loaded}

TAES_WEIGHTS = _load_taes_weights()

def _summarize_for_taes(output: str, max_length: int = 2500) -> str:
    """
    Summarize long outputs before TAES evaluation (domain-specific improvement).
    Uses simple truncation with context preservation for now.
    """
    if len(output) <= max_length:
        return output

    # Keep first 1500 chars (context) + last 1000 chars (conclusion)
    # This preserves both opening context and final conclusions
    prefix = output[:1500]
    suffix = output[-1000:]
    return f"{prefix}\n\n[... {len(output) - 2500} characters truncated ...]\n\n{suffix}"

def evaluate_taes(
    output: str,
    domain: str = "default",
    session_id: Optional[str] = None,
    role_name: Optional[str] = None,
    model: str = "gpt-4o-mini",
    config_hash: Optional[str] = None
) -> dict:
    """
    Score output on Logical/Practical/Probable axes.
    Returns TAES verdict with IV, IRD, and RRP requirement.
    """

    # Normalize domain
    domain = domain.lower().strip()
    if domain not in TAES_WEIGHTS:
        domain = "default"

    # Get weights
    weights = TAES_WEIGHTS[domain]

    # Domain-specific improvement: Handle longer outputs by summarizing first
    evaluation_text = output if len(output) <= 2500 else _summarize_for_taes(output)

    # Construct scoring prompt
    prompt = f"""Score this output on three dimensions (0-100 scale):

**Logical**: Correctness, consistency, evidence quality, logical coherence
**Practical**: Feasibility, resource requirements, timeline realism, implementation clarity
**Probable**: Realistic human behavior, adoption likelihood, psychological plausibility

Context: This is a {domain} task.

Output to evaluate:
{evaluation_text}

Return ONLY valid JSON in this exact format:
{{"logical": <0-100>, "practical": <0-100>, "probable": <0-100>}}"""

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=150,
            messages=[
                {"role": "system", "content": "You are a TAES evaluator. Return only JSON."},
                {"role": "user", "content": prompt}
            ]
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        scores = json.loads(raw)

        # Validate scores
        for key in ["logical", "practical", "probable"]:
            if key not in scores or not (0 <= scores[key] <= 100):
                raise ValueError(f"Invalid score for {key}")

    except Exception as e:
        # Code quality improvement: Enhanced error logging with stack traces
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[TAES ERROR] Scoring failed: {e}\n{error_trace}")
        print(f"[TAES ERROR] Scoring failed: {e}")
        # Fallback scores (neutral)
        scores = {"logical": 75, "practical": 75, "probable": 75}

    # Calculate metrics
    logical_norm = scores["logical"] / 100
    practical_norm = scores["practical"] / 100
    probable_norm = scores["probable"] / 100

    # Integrity Vector (weighted mean)
    iv = (
        logical_norm * weights["logical"] +
        practical_norm * weights["practical"] +
        probable_norm * weights["probable"]
    )

    # Ideal-Reality Disparity
    ird = abs((logical_norm + practical_norm) - probable_norm)

    # Reality Reconciliation Pass required?
    requires_rrp = ird > 0.5

    result = {
        "scores": scores,
        "weights": weights,
        "domain": domain,
        "integrity_vector": round(iv, 3),
        "ird": round(ird, 3),
        "requires_rrp": requires_rrp,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "role_name": role_name,
    }

    try:
        ledger_data = {
            "domain": domain,
            "scores": scores,
            "weights": weights,
            "session_id": session_id,
            "role_name": role_name,
        }
        ledger_hash = write_ledger_entry("TAES", "evaluation", ledger_data, config_hash=config_hash)
        result["ledger_hash"] = ledger_hash
    except Exception as exc:
        logger.warning("TAES ledger logging failed: %s", exc)

    # Log to CSV
    _log_ird(result)

    return result


# Performance improvement: Async version for parallel TAES evaluations
async def evaluate_taes_async(
    output: str,
    domain: str = "default",
    session_id: Optional[str] = None,
    role_name: Optional[str] = None,
    model: str = "gpt-4o-mini",
    client: Optional[OpenAI] = None,
    config_hash: Optional[str] = None
) -> dict:
    """
    Async version of evaluate_taes for parallel batch processing.
    Use this when evaluating multiple role outputs simultaneously.
    """
    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    domain = domain.lower().strip()
    if domain not in TAES_WEIGHTS:
        domain = "default"

    weights = TAES_WEIGHTS[domain]
    evaluation_text = output if len(output) <= 2500 else _summarize_for_taes(output)

    prompt = f"""Score this output on three dimensions (0-100 scale):

**Logical**: Correctness, consistency, evidence quality, logical coherence
**Practical**: Feasibility, resource requirements, timeline realism, implementation clarity
**Probable**: Realistic human behavior, adoption likelihood, psychological plausibility

Context: This is a {domain} task.

Output to evaluate:
{evaluation_text}

Return ONLY valid JSON in this exact format:
{{"logical": <0-100>, "practical": <0-100>, "probable": <0-100>}}"""

    try:
        # Use async client if available, otherwise run in executor
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=model,
                temperature=0.2,
                max_tokens=150,
                messages=[
                    {"role": "system", "content": "You are a TAES evaluator. Return only JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        scores = json.loads(raw)

        for key in ["logical", "practical", "probable"]:
            if key not in scores or not (0 <= scores[key] <= 100):
                raise ValueError(f"Invalid score for {key}")

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[TAES ERROR] Async scoring failed: {e}\n{error_trace}")
        scores = {"logical": 75, "practical": 75, "probable": 75}

    logical_norm = scores["logical"] / 100
    practical_norm = scores["practical"] / 100
    probable_norm = scores["probable"] / 100

    iv = (
        logical_norm * weights["logical"] +
        practical_norm * weights["practical"] +
        probable_norm * weights["probable"]
    )

    ird = abs((logical_norm + practical_norm) - probable_norm)
    requires_rrp = ird > 0.5

    result = {
        "scores": scores,
        "weights": weights,
        "domain": domain,
        "integrity_vector": round(iv, 3),
        "ird": round(ird, 3),
        "requires_rrp": requires_rrp,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "role_name": role_name,
    }

    try:
        ledger_data = {
            "domain": domain,
            "scores": scores,
            "weights": weights,
            "session_id": session_id,
            "role_name": role_name,
        }
        ledger_hash = write_ledger_entry("TAES", "evaluation", ledger_data, config_hash=config_hash)
        result["ledger_hash"] = ledger_hash
    except Exception as exc:
        logger.warning("TAES ledger logging failed: %s", exc)

    _log_ird(result)
    return result


async def evaluate_taes_batch(
    outputs: List[Dict[str, str]],
    domain: str = "default",
    session_id: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> List[dict]:
    """
    Performance improvement: Evaluate multiple TAES outputs in parallel.

    Args:
        outputs: List of dicts with 'output' and 'role_name' keys
        domain: Domain for all evaluations
        session_id: Session identifier
        model: Model to use

    Returns:
        List of TAES results in same order as inputs
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tasks = [
        evaluate_taes_async(
            output['output'],
            domain=domain,
            session_id=session_id,
            role_name=output.get('role_name'),
            model=model,
            client=client
        )
        for output in outputs
    ]
    return await asyncio.gather(*tasks)


def _rotate_ird_log(max_size_mb: float = 10.0, keep_backups: int = 5):
    """
    Performance improvement: Rotate IRD log when it exceeds size limit.
    Similar to score history rotation pattern.
    """
    if not IRD_LOG.exists():
        return

    size_mb = IRD_LOG.stat().st_size / (1024 * 1024)
    if size_mb < max_size_mb:
        return

    # Rotate: move current to backup
    import shutil
    for i in range(keep_backups - 1, 0, -1):
        old_backup = IRD_LOG.parent / f"ird_log.{i}.csv"
        new_backup = IRD_LOG.parent / f"ird_log.{i+1}.csv"
        if old_backup.exists():
            shutil.move(str(old_backup), str(new_backup))

    # Move current to .1
    shutil.move(str(IRD_LOG), str(IRD_LOG.parent / "ird_log.1.csv"))
    logger.info(f"Rotated IRD log ({size_mb:.2f}MB)")

def _log_ird(result: dict):
    """Append IRD data to logs/ird_log.csv (Directive 25b)"""
    # Performance improvement: Check and rotate log if needed
    _rotate_ird_log()

    header = [
        "timestamp", "session_id", "role_name", "domain",
        "logical", "practical", "probable",
        "iv", "ird", "requires_rrp"
    ]

    row = [
        result["timestamp"],
        result.get("session_id", ""),
        result.get("role_name", ""),
        result["domain"],
        result["scores"]["logical"],
        result["scores"]["practical"],
        result["scores"]["probable"],
        result["integrity_vector"],
        result["ird"],
        result["requires_rrp"]
    ]

    file_exists = IRD_LOG.exists()

    with open(IRD_LOG, "a", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)


def check_cognitive_disalignment() -> dict:
    """
    Analyze recent IRD trends.
    Alert if monthly average > 0.4 (Directive 25b).
    """
    if not IRD_LOG.exists():
        return {"alert": False, "reason": "No IRD data"}

    try:
        with open(IRD_LOG, "r", encoding="utf8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if len(rows) < 5:
            return {"alert": False, "reason": "Insufficient data"}

        recent = rows[-30:]  # Last 30 entries
        avg_ird = sum(float(r["ird"]) for r in recent) / len(recent)

        if avg_ird > 0.4:
            return {
                "alert": True,
                "avg_ird": round(avg_ird, 3),
                "reason": "Cognitive Disalignment Alert: IRD average > 0.4"
            }

        return {"alert": False, "avg_ird": round(avg_ird, 3)}

    except Exception as e:
        return {"alert": False, "reason": f"Analysis failed: {e}"}


if __name__ == "__main__":
    # Test
    test_output = """
    The strategy positions tree services as emergency-ready 24/7 providers.
    Target audiences: homeowners with storm damage, property managers, insurance adjusters.
    Three hooks: speed (same-day), safety (licensed/insured), savings (20% gap-fill discount).
    """

    result = evaluate_taes(test_output, domain="marketing", session_id="test-001", role_name="Strategist")
    print(json.dumps(result, indent=2))
    print(f"\n✅ Logged to {IRD_LOG}")
