# /ops/sync_bridge.py
# AxProtocol v2.3 — Bridge Synchronization Utility (Git-Automated)
# Purpose: keep /ops/Bridge.md aligned with latest commits and tag updates automatically.

# Timestamp: 2025-10-27 02:43:19 UTC
# Hash: 9e4c5c89a1ee4254c4c5b038045f8a579ee87de29d7d3ff4791a4c5089ad490d
import os
import subprocess
import datetime
import hashlib
import re

BRIDGE_PATH = os.path.join(os.path.dirname(__file__), "Bridge.md")
LEDGER_PATH = os.path.join(os.path.dirname(__file__), "../logs/ledger/bridge_sync.csv")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_last_commit():
    """Return latest commit hash and message."""
    result = subprocess.run(
        ["git", "-C", REPO_ROOT, "log", "-1", "--pretty=%H||%s"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None, "No commit found"
    commit_hash, message = result.stdout.strip().split("||", 1)
    return commit_hash, message

def detect_update_tag(message):
    """Infer update type from commit message."""
    match = re.search(r"#UPDATE:(BUILD|MARKET|CORE)", message, re.IGNORECASE)
    return match.group(0).upper() if match else "#UPDATE:BUILD"

def compute_checksum(file_path):
    """Compute SHA256 checksum for Bridge.md."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]

def append_to_bridge(commit_hash, tag, message):
    """Append update summary to Bridge.md Change Log."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    checksum = compute_checksum(BRIDGE_PATH)
    entry = f"| {timestamp} | {tag} | {message.strip()} | `{commit_hash[:7]}` |\n"

    with open(BRIDGE_PATH, "r+", encoding="utf-8") as f:
        content = f.readlines()
        insert_index = next(
            (i for i, line in enumerate(content) if line.strip().startswith("| Date |")), None
        )
        if insert_index is not None:
            content.insert(insert_index + 2, entry)
        f.seek(0)
        f.writelines(content)

    subprocess.run(["git", "-C", REPO_ROOT, "add", BRIDGE_PATH])
    subprocess.run(["git", "-C", REPO_ROOT, "commit", "-m", f"Bridge sync {tag} {commit_hash[:7]}"])
    subprocess.run(["git", "-C", REPO_ROOT, "push"])

    print(f"[SYNC] Bridge updated → {tag} ({commit_hash[:7]}) | checksum {checksum}")

def log_to_ledger(commit_hash, tag, message):
    """Write minimal ledger record."""
    timestamp = datetime.datetime.utcnow().isoformat()
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(f"{timestamp},{commit_hash},{tag},{message.strip()}\n")

def main():
    commit_hash, message = get_last_commit()
    if not commit_hash:
        print("[ERROR] No Git history detected.")
        return
    tag = detect_update_tag(message)
    append_to_bridge(commit_hash, tag, message)
    log_to_ledger(commit_hash, tag, message)

if __name__ == "__main__":
    main()
