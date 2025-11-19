# Timestamp: 2025-10-27 04:40:28 UTC
# Hash: b2cc2ba8ebf4afcbc80ff40b87d6f7807e77cd161dd4172cf8642c142822ac42
"""
AxProtocol Immutable Audit Ledger (IAL) — Directive 22
Append-only database for all state mutations.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

LEDGER_DB = Path("logs/ledger/audit_ledger.db")
LEDGER_DB.parent.mkdir(parents=True, exist_ok=True)

def init_ledger():
    """Create ledger table if not exists."""
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT,
            agent_id TEXT NOT NULL,
            role_name TEXT,
            directive INTEGER,
            action TEXT NOT NULL,
            delta TEXT,
            input_hash TEXT,
            output_hash TEXT,
            op_auth_present INTEGER DEFAULT 0,
            previous_hash TEXT,
            current_hash TEXT,
            config_hash TEXT
        )
    """)

    # Migration: Add config_hash column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE audit_log ADD COLUMN config_hash TEXT")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()
    conn.close()


def log_execution(
    session_id: str,
    agent_id: str,
    role_name: str,
    action: str,
    input_text: str = "",
    output_text: str = "",
    directive: Optional[int] = None,
    delta: Optional[dict] = None,
    op_auth_present: bool = False,
    config_hash: Optional[str] = None
):
    """
    Append entry to immutable ledger.
    Returns entry ID and hash.
    """
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()

    timestamp = datetime.utcnow().isoformat()
    input_hash = hashlib.sha256(input_text.encode()).hexdigest()[:12] if input_text else ""
    output_hash = hashlib.sha256(output_text.encode()).hexdigest()[:12] if output_text else ""
    delta_json = json.dumps(delta) if delta else ""

    # Get previous hash for chain integrity
    cursor.execute("SELECT current_hash FROM audit_log ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    previous_hash = row[0] if row else "genesis"

    # Compute current hash
    hash_input = f"{timestamp}|{agent_id}|{action}|{output_hash}|{previous_hash}"
    current_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    cursor.execute("""
        INSERT INTO audit_log (
            timestamp, session_id, agent_id, role_name, directive, action,
            delta, input_hash, output_hash, op_auth_present, previous_hash, current_hash, config_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, session_id, agent_id, role_name, directive, action,
        delta_json, input_hash, output_hash, int(op_auth_present), previous_hash, current_hash, config_hash
    ))

    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": entry_id, "hash": current_hash}


def get_last_n_entries(n: int = 5) -> list:
    """Retrieve last N ledger entries (for snapshots)."""
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM audit_log ORDER BY id DESC LIMIT ?
    """, (n,))

    rows = cursor.fetchall()
    conn.close()

    columns = [
        "id", "timestamp", "session_id", "agent_id", "role_name", "directive",
        "action", "delta", "input_hash", "output_hash", "op_auth_present",
        "previous_hash", "current_hash", "config_hash"
    ]

    return [dict(zip(columns, row)) for row in rows]


def verify_hash_chain() -> dict:
    """Verify ledger integrity (hash chain)."""
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT id, timestamp, agent_id, action, output_hash, previous_hash, current_hash FROM audit_log ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"valid": True, "entries": 0}

    broken = []

    for i, row in enumerate(rows):
        entry_id, timestamp, agent_id, action, output_hash, previous_hash, current_hash = row

        # Compute expected hash
        expected_prev = "genesis" if i == 0 else rows[i-1][6]
        hash_input = f"{timestamp}|{agent_id}|{action}|{output_hash}|{expected_prev}"
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        if current_hash != expected_hash:
            broken.append({
                "id": entry_id,
                "expected": expected_hash,
                "actual": current_hash
            })

    return {
        "valid": len(broken) == 0,
        "entries": len(rows),
        "broken": broken
    }


# Initialize on import
init_ledger()


if __name__ == "__main__":
    # Test
    log_execution(
        session_id="test-001",
        agent_id="strategist-01",
        role_name="Strategist",
        action="generate_strategy",
        output_text="Sample strategy output",
        directive=15
    )

    print("✅ Logged test entry")

    entries = get_last_n_entries(3)
    print(f"\nLast 3 entries:")
    for e in entries:
        print(f"  [{e['id']}] {e['role_name']} → {e['action']}")

    integrity = verify_hash_chain()
    print(f"\nHash chain integrity: {'✅ VALID' if integrity['valid'] else '❌ BROKEN'}")
    print(f"Entries checked: {integrity['entries']}")