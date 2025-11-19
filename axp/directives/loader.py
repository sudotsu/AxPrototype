"""
Directive loading from markdown files.
"""

from functools import lru_cache
from pathlib import Path


def _read_text(path: Path) -> str:
    """Read text file or return missing indicator."""
    return path.read_text(encoding="utf8") if path.exists() else f"[Missing: {path.name}]"


@lru_cache(maxsize=1)
def load_directives(base_dir: Path):
    """
    Load directives from markdown files.
    Cached to avoid reloading on every run (performance improvement).

    Args:
        base_dir: Base directory for finding protocol files

    Returns:
        Dictionary mapping directive keys to content
    """
    # Try /protocol first (your current layout), then root as fallback
    def locate(filename: str) -> Path:
        for root in [base_dir / "protocol", base_dir]:
            p = root / filename
            if p.exists():
                return p
        # Fall back to /protocol even if missing (so missing files are obvious)
        return (base_dir / "protocol" / filename)

    files = {
        "D0":   locate("AxProtocol_v2.4_D0_CHANGE_CONTROL.md"),
        "CORE": locate("AxProtocol_v2.4_CORE_DIRECTIVES.md"),
        "ADD":  locate("AxProtocol_v2.4_WARROOM_ADDENDUM.md"),
        "AAL":  locate("AxProtocol_v2.4_AUTHORITY_LAYER.md"),
        "TAES": locate("AxProtocol_v2.4_TAES_EVALUATION.md"),
        "RDL":  locate("AxProtocol_v2.4_REDTEAM_LAYER.md"),
    }
    return {k: _read_text(v) for k, v in files.items()}

