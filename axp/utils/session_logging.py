"""
Session logging utilities for AxProtocol execution results.
Enhanced for Phase 1: Comprehensive hash-linked session_log.jsonl entries.
"""

import csv
import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any


def extract_kpi_rows(markdown_text: str):
    """
    Extract KPI rows from markdown table.

    Args:
        markdown_text: Markdown text containing KPI table

    Returns:
        List of [kpi, target, status] tuples
    """
    pattern = r"\| *([^\|]+)\| *([^\|]+)\| *([^\|]+)\|"
    rows = re.findall(pattern, markdown_text)
    out = []
    for r in rows:
        if "KPI" in r[0] or "---" in r[0]:
            continue
        out.append([x.strip() for x in r])
    return out


def _compute_hash(data: Any) -> str:
    """
    Compute SHA256 hash of data (handles strings, dicts, etc.).

    Phase 1: Cryptographic hashing for tamper-evident chain.
    Uses SHA-256 for all hash computations.
    """
    if isinstance(data, dict):
        payload = json.dumps(data, sort_keys=True).encode('utf-8')
    elif isinstance(data, str):
        payload = data.encode('utf-8')
    else:
        payload = str(data).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def get_last_entry_hash(base_dir: Optional[Path] = None) -> Optional[str]:
    """
    Read the last entry hash from session_log.jsonl to maintain chain integrity.

    Phase 1: Enables automatic chain linking for Sentinel auditability.

    Args:
        base_dir: Base directory for logs (defaults to current working directory)

    Returns:
        Hash of the last entry, or None if no entries exist
    """
    if base_dir is None:
        base_dir = Path.cwd()

    log_file = base_dir / "logs" / "sessions" / "session_log.jsonl"

    if not log_file.exists():
        return None

    try:
        # Read last line (most efficient for append-only file)
        with open(log_file, "rb") as f:
            # Seek to end and read backwards to find last line
            try:
                f.seek(-2, 2)  # Go to second-to-last byte
                while f.read(1) != b'\n':
                    f.seek(-2, 1)  # Move back one byte
            except OSError:
                # File is too small, read from start
                f.seek(0)

            last_line = f.readline().decode('utf-8').strip()
            if not last_line:
                return None

            entry = json.loads(last_line)
            return entry.get("entry_hash")
    except (IOError, json.JSONDecodeError, KeyError):
        return None


def log_agent_entry(
    session_id: str,
    role_name: str,
    input_payload: str,
    output_payload: str,
    full_prompt: str,
    response_raw: str,
    taes_score: Optional[Dict] = None,
    directive_evaluation: Optional[Dict] = None,
    config_hash: Optional[str] = None,
    base_dir: Path = None,
    previous_entry_hash: Optional[str] = None
) -> str:
    """
    Log comprehensive agent entry to session_log.jsonl with all required hashes.

    Phase 1: Creates hash-linked entries for Sentinel auditability.

    Args:
        session_id: Session identifier
        role_name: Role name (Strategist, Analyst, etc.)
        input_payload: Input text/prompt to the agent
        output_payload: Output text from the agent
        full_prompt: Full system prompt used
        response_raw: Raw LLM response (before parsing)
        taes_score: TAES evaluation dictionary (optional)
        directive_evaluation: Directive adherence evaluation (optional)
        config_hash: Config fingerprint hash
        base_dir: Base directory for logs
        previous_entry_hash: Hash of previous entry for chain linking

    Returns:
        Hash of this entry for next entry's previous_entry_hash
    """
    if base_dir is None:
        base_dir = Path.cwd()

    log_dir = base_dir / "logs" / "sessions"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Automatically get previous entry hash if not provided
    if previous_entry_hash is None:
        previous_entry_hash = get_last_entry_hash(base_dir) or "genesis"

    # Compute all required hashes
    input_payload_hash = _compute_hash(input_payload)
    output_payload_hash = _compute_hash(output_payload)
    full_prompt_hash = _compute_hash(full_prompt)
    response_raw_hash = _compute_hash(response_raw)
    taes_score_hash = _compute_hash(taes_score) if taes_score else None
    directive_evaluation_hash = _compute_hash(directive_evaluation) if directive_evaluation else None

    # Create entry
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "session_id": session_id,
        "role_name": role_name,
        "hashes": {
            "input_payload_hash": input_payload_hash,
            "output_payload_hash": output_payload_hash,
            "full_prompt_hash": full_prompt_hash,
            "response_raw_hash": response_raw_hash,
            "taes_score_hash": taes_score_hash,
            "directive_evaluation_hash": directive_evaluation_hash,
        },
        "data": {
            "input_payload": input_payload,
            "output_payload": output_payload,
            "full_prompt": full_prompt,
            "response_raw": response_raw,
            "taes_score": taes_score,
            "directive_evaluation": directive_evaluation,
        },
        "config_hash": config_hash,
        "previous_entry_hash": previous_entry_hash,  # Already set to "genesis" if None above
    }

    # Compute entry hash (for chain linking) - includes all critical fields for tamper detection
    # Phase 1: Entry hash includes metadata, all field hashes, config_hash, and previous hash
    entry_hash = _compute_hash({
        "timestamp": entry["timestamp"],
        "session_id": entry["session_id"],
        "role_name": entry["role_name"],
        "hashes": entry["hashes"],  # All individual field hashes
        "config_hash": entry.get("config_hash"),  # Config fingerprint
        "previous_entry_hash": entry["previous_entry_hash"],  # Chain link
    })
    entry["entry_hash"] = entry_hash

    # Append to session_log.jsonl (append-only)
    log_file = log_dir / "session_log.jsonl"
    with open(log_file, "a", encoding="utf8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry_hash


def log_session(
    objective: str,
    s: str,
    a: str,
    p_rev: str,
    c_rev: str,
    crit: str,
    results: Dict,
    base_dir: Path,
    tier: str,
    model: str
) -> str:
    """
    Log session results to file and generate ROI/KPI logs.

    Args:
        objective: Campaign objective
        s: Strategist output
        a: Analyst output
        p_rev: Producer revised output
        c_rev: Courier revised output
        crit: Critic output
        results: Results dictionary with TAES data
        base_dir: Base directory for logs
        tier: Tier name (DEV, PREP, CLIENT)
        model: Model name

    Returns:
        Path to log file as string
    """
    log_dir = base_dir / "logs" / "sessions"
    log_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_dir / f"{ts}_{tier.lower()}.log"

    # Get domain from results
    domain = results.get('domain', 'unknown')

    with open(log_path, "w", encoding="utf8") as f:
        f.write(f"[Timestamp] {ts} UTC\n[Model] {model}\n[Tier] {tier}\n[Domain] {domain}\n\n")
        f.write("[Objective]\n" + objective + "\n\n")
        f.write("## STRATEGIST\n" + s + "\n\n")

        # Add TAES data
        if 'strategist' in results:
            taes = results['strategist']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## ANALYST\n" + a + "\n\n")

        if 'analyst' in results:
            taes = results['analyst']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## PRODUCER [Revised]\n" + p_rev + "\n\n")

        if 'producer_revised' in results:
            taes = results['producer_revised']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## COURIER [Revised]\n" + c_rev + "\n\n")

        if 'courier_revised' in results:
            taes = results['courier_revised']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## CRITIC\n" + crit + "\n")

    # ROI trigger detection
    if "[Tier: Immediate ROI]" in (s + a + p_rev + c_rev + crit):
        payload = {
            "trigger": "AxP_Curve_ImmediateROI",
            "timestamp": ts,
            "tier": tier,
            "model": model,
            "domain": domain,
            "objective": objective[:300],
            "summary": "Immediate ROI trigger detected in AxProtocol chain output.",
            "source": "AxProtocol War Room v2.4",
        }
        with open(log_dir / f"{ts}_{tier.lower()}_ROI.json", "w", encoding="utf8") as jf:
            json.dump(payload, jf, indent=2)

    # KPI CSV
    kpi_rows = extract_kpi_rows(c_rev)
    if kpi_rows:
        csv_path = base_dir / "logs" / "kpi_log.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        header = ["timestamp", "objective", "kpi", "target", "status"]
        exists = csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf8") as csvf:
            w = csv.writer(csvf)
            if not exists:
                w.writerow(header)
            for kpi, target, status in kpi_rows:
                w.writerow([ts, objective, kpi, target, status])

    return str(log_path)


def verify_session_log_chain(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Verify the integrity of the session_log.jsonl hash chain.

    Phase 1: Sentinel auditability - detects tampering by verifying:
    - Each entry's hash matches its computed hash
    - Each entry's previous_entry_hash matches the previous entry's entry_hash
    - Chain is unbroken from genesis to latest entry

    Args:
        base_dir: Base directory for logs (defaults to current working directory)

    Returns:
        Dictionary with verification results:
        {
            "valid": bool,
            "entries_checked": int,
            "broken_links": List[Dict],  # List of entries with broken chain links
            "invalid_hashes": List[Dict],  # List of entries with invalid entry_hash
        }
    """
    if base_dir is None:
        base_dir = Path.cwd()

    log_file = base_dir / "logs" / "sessions" / "session_log.jsonl"

    if not log_file.exists():
        return {
            "valid": True,
            "entries_checked": 0,
            "broken_links": [],
            "invalid_hashes": [],
        }

    broken_links = []
    invalid_hashes = []
    previous_hash = "genesis"

    try:
        with open(log_file, "r", encoding="utf8") as f:
            for line_num, line in enumerate(f, start=1):
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as e:
                    invalid_hashes.append({
                        "line": line_num,
                        "error": f"Invalid JSON: {e}",
                    })
                    continue

                # Verify previous_entry_hash matches previous entry's hash
                if entry.get("previous_entry_hash") != previous_hash:
                    broken_links.append({
                        "line": line_num,
                        "session_id": entry.get("session_id"),
                        "role_name": entry.get("role_name"),
                        "expected_previous_hash": previous_hash,
                        "actual_previous_hash": entry.get("previous_entry_hash"),
                    })

                # Verify entry_hash matches computed hash
                stored_hash = entry.get("entry_hash")
                if stored_hash:
                    # Recompute hash using same method as log_agent_entry
                    computed_hash = _compute_hash({
                        "timestamp": entry.get("timestamp"),
                        "session_id": entry.get("session_id"),
                        "role_name": entry.get("role_name"),
                        "hashes": entry.get("hashes", {}),
                        "config_hash": entry.get("config_hash"),
                        "previous_entry_hash": entry.get("previous_entry_hash", "genesis"),
                    })

                    if stored_hash != computed_hash:
                        invalid_hashes.append({
                            "line": line_num,
                            "session_id": entry.get("session_id"),
                            "role_name": entry.get("role_name"),
                            "expected_hash": computed_hash,
                            "actual_hash": stored_hash,
                        })

                # Update previous_hash for next iteration
                previous_hash = stored_hash or "genesis"

        return {
            "valid": len(broken_links) == 0 and len(invalid_hashes) == 0,
            "entries_checked": line_num,
            "broken_links": broken_links,
            "invalid_hashes": invalid_hashes,
        }
    except IOError as e:
        return {
            "valid": False,
            "entries_checked": 0,
            "broken_links": [],
            "invalid_hashes": [{"error": f"File read failed: {e}"}],
        }
