"""
Ledger Verification Utilities
-----------------------------
Shared verification logic for Sentinel auditor.
Production-ready with proper error handling and type safety.
"""

import json
import hashlib
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    _HAVE_NACL = True
except ImportError:
    _HAVE_NACL = False
    import hmac

logger = logging.getLogger("axprotocol.sentinel")

PUB_KEY_ENV = "AXP_PUBLIC_KEY"
PUB_KEY_FILE = os.environ.get(PUB_KEY_ENV, "/audit/ledger/public.key")

# Phase 1: Import session log verification from axp.utils.session_logging
# Note: Sentinel runs in separate container with its own code copy for isolation
try:
    # Add parent directories to path to import axp modules
    # Sentinel container should have its own copy of axp/ code
    base_path = Path(__file__).resolve().parents[2]
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))

    from axp.utils.session_logging import verify_session_log_chain, get_last_entry_hash
    _HAVE_SESSION_LOG_VERIFY = True
except ImportError as e:
    logger.warning(f"Session log verification unavailable: {e}")
    _HAVE_SESSION_LOG_VERIFY = False


def _verify_sig(entry: Dict[str, Any], sig_hex: str, pubkey: bytes) -> bool:
    """
    Verify signature for a ledger entry.

    Args:
        entry: Entry dictionary
        sig_hex: Hex-encoded signature
        pubkey: Public key bytes

    Returns:
        True if signature valid, False otherwise
    """
    if not _HAVE_NACL:
        # HMAC fallback verification
        try:
            secret = pubkey  # In HMAC mode, pubkey is the secret
            msg = json.dumps(entry, sort_keys=True).encode()
            expected = hmac.new(secret, msg, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, sig_hex)
        except Exception:
            return False

    try:
        msg = json.dumps(entry, sort_keys=True).encode()
        VerifyKey(pubkey).verify(msg, bytes.fromhex(sig_hex))
        return True
    except BadSignatureError:
        return False
    except Exception as e:
        logger.warning(f"Signature verification error: {e}")
        return False


def verify_all(ledger_dir: str = "/audit/ledger") -> Dict[str, Any]:
    """
    Verify all ledger files for integrity and signature validity.

    Args:
        ledger_dir: Directory containing ledger .jsonl files

    Returns:
        Verification report with status and details
    """
    ledger_path = Path(ledger_dir)
    if not ledger_path.exists():
        logger.warning(f"Ledger directory does not exist: {ledger_dir}")
        return {"verified": False, "details": [{"error": "ledger_dir_not_found", "path": ledger_dir}]}

    files = sorted(ledger_path.glob("*.jsonl"))
    if not files:
        logger.warning(f"No ledger files found in {ledger_dir}")
        return {"verified": False, "details": [{"error": "no_ledger_files"}]}

    details: List[Dict[str, Any]] = []
    verified = True
    pubkey: Optional[bytes] = None

    # Load public key
    pubkey_path = Path(PUB_KEY_FILE)
    if pubkey_path.exists():
        try:
            pubkey = pubkey_path.read_bytes()
        except IOError as e:
            logger.error(f"Failed to read public key: {e}")
            return {"verified": False, "details": [{"error": "pubkey_read_failed", "reason": str(e)}]}
    else:
        logger.warning(f"Public key not found: {PUB_KEY_FILE}")
        # Continue without signature verification if key missing

    # Verify each file
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf8") as f:
                for line_num, line in enumerate(f, start=1):
                    if not line.strip():
                        continue

                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError as e:
                        verified = False
                        details.append({
                            "file": str(file_path),
                            "line": line_num,
                            "error": "invalid_json",
                            "reason": str(e)
                        })
                        continue

                    entry = rec.get("entry", {})
                    sig = rec.get("sig")

                    # Verify hash
                    try:
                        payload_hash = hashlib.sha256(
                            json.dumps(entry, sort_keys=True).encode()
                        ).hexdigest()
                        if payload_hash != entry.get("hash"):
                            verified = False
                            details.append({
                                "file": str(file_path),
                                "line": line_num,
                                "error": "hash_mismatch",
                                "expected": payload_hash,
                                "actual": entry.get("hash")
                            })
                    except Exception as e:
                        verified = False
                        details.append({
                            "file": str(file_path),
                            "line": line_num,
                            "error": "hash_computation_failed",
                            "reason": str(e)
                        })

                    # Verify signature if key available
                    if pubkey and sig:
                        if not _verify_sig(entry, sig, pubkey):
                            verified = False
                            details.append({
                                "file": str(file_path),
                                "line": line_num,
                                "error": "sig_invalid"
                            })
        except IOError as e:
            verified = False
            details.append({
                "file": str(file_path),
                "error": "file_read_failed",
                "reason": str(e)
            })

    return {
        "verified": verified,
        "details": details,
        "files_checked": len(files),
        "entries_checked": sum(1 for _ in details if "line" in _)
    }


def verify_session_log(sessions_dir: str = "/audit/logs/sessions") -> Dict[str, Any]:
    """
    Verify session_log.jsonl hash chain integrity.

    Phase 1: Sentinel auditability - verifies cryptographic hash chain.

    Args:
        sessions_dir: Directory containing session_log.jsonl

    Returns:
        Verification report with chain integrity status
    """
    if not _HAVE_SESSION_LOG_VERIFY:
        return {
            "verified": False,
            "error": "session_log_verification_unavailable",
            "details": "Session log verification module not available"
        }

    try:
        sessions_path = Path(sessions_dir)
        # Use parent directory as base_dir for verify_session_log_chain
        base_dir = sessions_path.parent.parent if sessions_path.name == "sessions" else sessions_path.parent

        result = verify_session_log_chain(base_dir=base_dir)

        # Get last valid hash for status endpoint
        last_valid_hash = None
        if result.get("valid"):
            last_valid_hash = get_last_entry_hash(base_dir=base_dir)

        return {
            "verified": result.get("valid", False),
            "entries_checked": result.get("entries_checked", 0),
            "broken_links": result.get("broken_links", []),
            "invalid_hashes": result.get("invalid_hashes", []),
            "last_valid_hash": last_valid_hash,
        }
    except Exception as e:
        logger.error(f"Session log verification failed: {e}", exc_info=True)
        return {
            "verified": False,
            "error": "verification_exception",
            "details": str(e)
        }
