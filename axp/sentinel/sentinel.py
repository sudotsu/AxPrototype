"""
Sentinel CLI Auditor
--------------------
Command-line tool for verifying ledger integrity.
Production-ready with proper error handling and logging.
"""

from __future__ import annotations

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from axp.governance.ledger import get_public_key_path, verify_payload

logger = logging.getLogger("axprotocol.sentinel")

PUB_KEY_PATH = get_public_key_path()

REPORT_DIR = Path("logs/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = REPORT_DIR / "sentinel_report.json"


def verify_ledger() -> dict:
    """
    Verify ledger integrity (CLI version).

    Returns:
        Verification report dictionary
    """
    if not PUB_KEY_PATH.exists():
        logger.warning(f"Public key not found: {PUB_KEY_PATH}")
        return {"verified": False, "details": [{"error": "pubkey_not_found"}]}

    ledger_dir = Path("logs/ledger")
    if not ledger_dir.exists():
        logger.warning(f"Ledger directory not found: {ledger_dir}")
        return {"verified": False, "details": [{"error": "ledger_dir_not_found"}]}

    files = sorted(ledger_dir.glob("*.jsonl"))
    if not files:
        logger.warning("No ledger files found")
        return {"verified": False, "details": [{"error": "no_ledger_files"}]}

    results: List[dict] = []
    verified = True

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf8") as f:
                for line_no, line in enumerate(f, start=1):
                    if not line.strip():
                        continue

                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError as e:
                        verified = False
                        results.append({
                            "file": str(file_path),
                            "line": line_no,
                            "error": f"Invalid JSON: {e}"
                        })
                        continue

                    entry = rec.get("entry", {})
                    sig_hex = rec.get("sig")

                    if not entry:
                        verified = False
                        results.append({
                            "file": str(file_path),
                            "line": line_no,
                            "error": "Missing entry"
                        })
                        continue

                    # Verify hash
                    payload = json.dumps(entry, sort_keys=True).encode()
                    data = entry.get("data", {})
                    expected_hash = hashlib.sha256(
                        json.dumps(data, sort_keys=True).encode()
                    ).hexdigest()

                    if entry.get("hash") != expected_hash:
                        verified = False
                        results.append({
                            "file": str(file_path),
                            "line": line_no,
                            "error": "Hash mismatch",
                            "expected": expected_hash,
                            "actual": entry.get("hash")
                        })
                        continue

                    # Verify signature
                    if sig_hex:
                        try:
                            verify_payload(payload, sig_hex)
                        except ValueError as exc:
                            verified = False
                            results.append({
                                "file": str(file_path),
                                "line": line_no,
                                "error": f"Signature invalid: {exc}"
                            })
                    else:
                        verified = False
                        results.append({
                            "file": str(file_path),
                            "line": line_no,
                            "error": "Missing signature"
                        })
        except IOError as e:
            verified = False
            results.append({
                "file": str(file_path),
                "error": f"File read failed: {e}"
            })

    report = {
        "verified": verified,
        "details": results,
        "ledger_files": [str(f) for f in files],
        "entries_checked": len(results)
    }

    try:
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf8")
    except IOError as e:
        logger.error(f"Failed to write report: {e}")

    return report


if __name__ == "__main__":
    verify_ledger()
