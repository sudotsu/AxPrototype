"""
AxProtocol Ledger Signing Layer
-------------------------------
Append-only ledger with Ed25519 signatures using PyNaCl.
Production-ready with proper error handling and input validation.
"""

from __future__ import annotations

import json
import hashlib
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("axprotocol.ledger")

try:
    from nacl.signing import SigningKey, VerifyKey
    _HAVE_NACL = True
except ImportError:  # pragma: no cover - fallback when PyNaCl unavailable
    _HAVE_NACL = False
    import hmac
    import secrets

_KEY_DIR = Path(os.path.expanduser("~/.axp_keys"))
_KEY_DIR.mkdir(parents=True, exist_ok=True)
_PRIVATE_PATH = _KEY_DIR / "private.key"
_PUBLIC_PATH = _KEY_DIR / "public.key"

# Initialize signing key (Ed25519 or HMAC fallback)
if _HAVE_NACL:
    try:
        if not _PRIVATE_PATH.exists():
            sk = SigningKey.generate()
            _PRIVATE_PATH.write_bytes(sk.encode())
            _PUBLIC_PATH.write_bytes(sk.verify_key.encode())
            logger.info("Generated new Ed25519 signing key")
        _SIGNING_KEY = SigningKey(_PRIVATE_PATH.read_bytes())
        _PUBLIC_PATH.write_bytes(_SIGNING_KEY.verify_key.encode())

        def _sign(payload: bytes) -> str:
            return _SIGNING_KEY.sign(payload).hex()

        def _verify(payload: bytes, sig_hex: str) -> None:
            verify_key = VerifyKey(_PUBLIC_PATH.read_bytes())
            verify_key.verify(payload, bytes.fromhex(sig_hex))
    except Exception as e:
        logger.error(f"Failed to initialize Ed25519 signing: {e}")
        raise RuntimeError("Cannot initialize ledger signing key") from e
else:
    try:
        if not _PRIVATE_PATH.exists():
            secret = secrets.token_bytes(32)
            _PRIVATE_PATH.write_bytes(secret)
            _PUBLIC_PATH.write_bytes(secret)
            logger.warning("Using HMAC fallback (PyNaCl unavailable)")
        _SECRET = _PRIVATE_PATH.read_bytes()
        _PUBLIC_PATH.write_bytes(_SECRET)

        def _sign(payload: bytes) -> str:
            return hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()

        def _verify(payload: bytes, sig_hex: str) -> None:
            expected = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, sig_hex):
                raise ValueError("Signature mismatch")
    except Exception as e:
        logger.error(f"Failed to initialize HMAC fallback: {e}")
        raise RuntimeError("Cannot initialize ledger signing key") from e

# Ledger directory (configurable via env)
LEDGER_DIR = Path(os.getenv("AXP_LEDGER_DIR", "logs/ledger"))
LEDGER_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_PUBLIC_KEY_PATH = LEDGER_DIR / "public.key"

# Mirror public key to ledger directory
try:
    if _HAVE_NACL:
        LEDGER_PUBLIC_KEY_PATH.write_bytes(_SIGNING_KEY.verify_key.encode())
    else:
        if not LEDGER_PUBLIC_KEY_PATH.exists():
            LEDGER_PUBLIC_KEY_PATH.write_bytes(_SECRET)
except Exception as e:
    logger.warning(f"Failed to write public key to ledger dir: {e}")


def write_ledger_entry(role: str, action: str, data: Dict[str, Any], config_hash: Optional[str] = None) -> str:
    """
    Append a signed ledger entry.

    Args:
        role: Role identifier (e.g., "Strategist", "TAES")
        action: Action name (e.g., "evaluation", "generate_strategy")
        data: Data dictionary to log
        config_hash: Optional config fingerprint hash (sha256:...)

    Returns:
        Content hash for downstream linkage

    Raises:
        ValueError: If inputs are invalid
        IOError: If ledger write fails
    """
    # Input validation (TRUTH > OBEDIENCE - fail fast on bad data)
    if not role or not isinstance(role, str):
        raise ValueError("role must be non-empty string")
    if not action or not isinstance(action, str):
        raise ValueError("action must be non-empty string")
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary")

    try:
        # Use datetime for consistency (not time.strftime)
        timestamp = datetime.now(timezone.utc).isoformat()
        data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        entry = {
            "timestamp": timestamp,
            "role": role,
            "action": action,
            "hash": data_hash,
            "data": data,
        }

        # Add config_hash if provided (for drift detection)
        if config_hash:
            entry["config_hash"] = config_hash
        payload = json.dumps(entry, sort_keys=True).encode()
        signature = _sign(payload)

        # Use date from timestamp for filename consistency
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        file_path = LEDGER_DIR / f"{date_str}.jsonl"

        # Atomic write with error handling
        try:
            with open(file_path, "a", encoding="utf8") as f:
                f.write(json.dumps({"entry": entry, "sig": signature}) + "\n")
        except IOError as e:
            logger.error(f"Failed to write ledger entry: {e}")
            raise RuntimeError(f"Ledger write failed: {e}") from e

        return entry["hash"]
    except Exception as e:
        logger.error(f"Ledger entry creation failed: {e}", exc_info=True)
        raise


def get_public_key_path() -> Path:
    """Get path to public key file."""
    return _PUBLIC_PATH


def verify_payload(payload: bytes, signature_hex: str) -> None:
    """
    Verify payload signature.

    Args:
        payload: Payload bytes to verify
        signature_hex: Hex-encoded signature

    Raises:
        ValueError: If signature is invalid or malformed
    """
    if not isinstance(payload, bytes):
        raise ValueError("payload must be bytes")
    if not isinstance(signature_hex, str):
        raise ValueError("signature_hex must be string")

    try:
        _verify(payload, signature_hex)
    except ValueError:
        raise  # Re-raise signature mismatch
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise ValueError(f"Signature verification failed: {e}") from e
