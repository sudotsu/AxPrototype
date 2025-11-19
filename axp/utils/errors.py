"""
Error logging and debugging utilities.
"""

import os
import traceback as _tb
from pathlib import Path


def append_session_error(session_id: str, domain: str, role: str, exc: Exception, base_dir: Path):
    """
    Append error to session error log.

    Args:
        session_id: Session identifier
        domain: Domain name
        role: Role name
        exc: Exception instance
        base_dir: Base directory for logs
    """
    try:
        sess_dir = base_dir / "logs" / "sessions"
        sess_dir.mkdir(parents=True, exist_ok=True)
        path = sess_dir / f"{session_id}_errors.log"
        with open(path, "a", encoding="utf8") as f:
            f.write("[Error] Role=" + role + " Domain=" + str(domain) + "\n")
            f.write("Type: " + exc.__class__.__name__ + "\n")
            f.write("Message: " + str(exc) + "\n")
            f.write("Traceback:\n" + "".join(_tb.format_exception(type(exc), exc, exc.__traceback__)) + "\n\n")
    except Exception:
        pass


def write_sys_preview(session_id: str, role_name: str, sys: str, base_dir: Path, max_lines: int = 12) -> None:
    """
    Write system prompt preview to debug log.

    Args:
        session_id: Session identifier
        role_name: Role name
        sys: System prompt text
        base_dir: Base directory for logs
        max_lines: Maximum lines to write
    """
    try:
        if os.getenv("DEBUG_SYS", "0") != "1":
            return
        lines = "\n".join((sys or "").splitlines()[:max_lines])
        out = f"[{role_name}] System preview\n{lines}\n---\n"
        path = base_dir / "logs" / "sessions" / f"{session_id}_sys.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf8") as f:
            f.write(out)
    except Exception:
        pass

