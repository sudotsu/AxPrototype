"""
AxProtocol Sentinel API
-----------------------
FastAPI application for independent ledger verification.
Production-ready with proper error handling and logging.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from verify_ledger import verify_all, verify_session_log

logger = logging.getLogger("axprotocol.sentinel")

# Configurable paths (defaults for Docker, override via env)
REPORTS_DIR = Path(os.getenv("AXP_REPORTS_DIR", "/audit/reports"))
LEDGER_DIR = os.getenv("AXP_LEDGER_DIR", "/audit/ledger")
SESSIONS_DIR = os.getenv("AXP_SESSIONS_DIR", "/audit/logs/sessions")  # Phase 1: Session log verification
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AxProtocol Sentinel", version="1.0")


@app.get("/health")
def health() -> Dict[str, Any]:
    """
    Health check endpoint with ledger integrity status.

    Phase 1: Returns ledger integrity status and last valid hash.

    Returns:
        Status, timestamp, and ledger integrity information
    """
    # Phase 1: Quick integrity check
    session_log_status = verify_session_log(sessions_dir=SESSIONS_DIR)
    ledger_integrity = "PASS" if session_log_status.get("verified", False) else "FAIL"
    last_valid_hash = session_log_status.get("last_valid_hash")

    return {
        "status": "ok",
        "ts": datetime.now(timezone.utc).isoformat(),
        "ledger_dir": LEDGER_DIR,
        "sessions_dir": SESSIONS_DIR,
        "reports_dir": str(REPORTS_DIR),
        "ledger_integrity": ledger_integrity,
        "last_valid_hash": last_valid_hash,
    }


@app.get("/verify")
def verify() -> JSONResponse:
    """
    Verify ledger integrity and signatures.

    Phase 1: Enhanced to verify both signed ledger and session_log.jsonl chain.

    Returns:
        Verification report with details for both ledger systems

    Raises:
        HTTPException: If verification fails critically
    """
    try:
        # Verify signed ledger (Ed25519 signatures)
        ledger_res = verify_all(ledger_dir=LEDGER_DIR)

        # Phase 1: Verify session_log.jsonl hash chain
        session_log_res = verify_session_log(sessions_dir=SESSIONS_DIR)

        # Combine results
        combined_res = {
            "ledger_verified": ledger_res.get("verified", False),
            "session_log_verified": session_log_res.get("verified", False),
            "overall_verified": ledger_res.get("verified", False) and session_log_res.get("verified", False),
            "ledger_details": ledger_res,
            "session_log_details": session_log_res,
            "last_valid_hash": session_log_res.get("last_valid_hash"),
        }

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = REPORTS_DIR / f"sentinel_{stamp}.json"

        try:
            with open(report_path, "w", encoding="utf8") as f:
                json.dump(combined_res, f, indent=2)
            logger.info(f"Verification report written: {report_path}")
        except IOError as e:
            logger.error(f"Failed to write report: {e}")
            # Don't fail the request if report write fails

        return JSONResponse(combined_res)
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.get("/reports")
def list_reports() -> Dict[str, List[str]]:
    """
    List recent verification reports.

    Returns:
        List of report filenames (last 30)
    """
    try:
        files = sorted([
            f.name for f in REPORTS_DIR.glob("*.json")
        ], reverse=True)[:30]
        return {"reports": files}
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        return {"reports": []}
