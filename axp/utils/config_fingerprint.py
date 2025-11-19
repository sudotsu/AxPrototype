"""
Config fingerprint computation for AxProtocol.

Computes SHA256 hash of all protocol configuration files to enable
drift detection and audit trail verification.
"""

import hashlib
import json
from pathlib import Path
from typing import List, Tuple


def compute_config_hash(base_dir: Path) -> str:
    """
    Compute SHA256 hash of all protocol config files.

    Includes:
    - Governance coupling (config/governance_coupling.json)
    - Role shapes (config/role_shapes.json)
    - TAES weights (config/taes_weights.json)
    - All directive markdown files (protocol/*.md)

    Files are sorted alphabetically by path for consistent hashing.
    Missing files are included as "[MISSING: filename]" to ensure
    hash changes when files are added/removed.

    Args:
        base_dir: Base directory for finding config files

    Returns:
        SHA256 hash as hex string (prefixed with "sha256:")
    """
    config_files: List[Tuple[str, str]] = []

    # Core governance config files
    core_configs = [
        "config/governance_coupling.json",
        "config/role_shapes.json",
        "config/taes_weights.json",
    ]

    # Directive markdown files
    directive_files = [
        "protocol/AxProtocol_v2.4_D0_CHANGE_CONTROL.md",
        "protocol/AxProtocol_v2.4_CORE_DIRECTIVES.md",
        "protocol/AxProtocol_v2.4_WARROOM_ADDENDUM.md",
        "protocol/AxProtocol_v2.4_AUTHORITY_LAYER.md",
        "protocol/AxProtocol_v2.4_TAES_EVALUATION.md",
        "protocol/AxProtocol_v2.4_REDTEAM_LAYER.md",
    ]

    all_files = core_configs + directive_files

    # Read all files (or mark as missing)
    for file_path_str in sorted(all_files):  # Sort for consistent hashing
        file_path = base_dir / file_path_str

        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf8")
                # Normalize JSON files (sort keys) for consistent hashing
                if file_path.suffix == ".json":
                    try:
                        data = json.loads(content)
                        content = json.dumps(data, sort_keys=True)
                    except json.JSONDecodeError:
                        # Invalid JSON - hash as-is
                        pass
                config_files.append((file_path_str, content))
            except Exception:
                # File exists but can't read - treat as missing
                config_files.append((file_path_str, f"[ERROR: {file_path_str}]"))
        else:
            # File missing - include marker to ensure hash changes when added
            config_files.append((file_path_str, f"[MISSING: {file_path_str}]"))

    # Create deterministic string: sorted file paths + contents
    # Format: "path1\ncontent1\n---\npath2\ncontent2\n---\n..."
    hash_input = "\n---\n".join([f"{path}\n{content}" for path, content in config_files])

    # Compute SHA256 hash
    hash_bytes = hashlib.sha256(hash_input.encode("utf8")).digest()
    hash_hex = hash_bytes.hex()

    return f"sha256:{hash_hex}"


def get_config_files_list(base_dir: Path) -> List[str]:
    """
    Get list of config files included in fingerprint.

    Args:
        base_dir: Base directory

    Returns:
        List of file paths (relative to base_dir)
    """
    return sorted([
        "config/governance_coupling.json",
        "config/role_shapes.json",
        "config/taes_weights.json",
        "protocol/AxProtocol_v2.4_D0_CHANGE_CONTROL.md",
        "protocol/AxProtocol_v2.4_CORE_DIRECTIVES.md",
        "protocol/AxProtocol_v2.4_WARROOM_ADDENDUM.md",
        "protocol/AxProtocol_v2.4_AUTHORITY_LAYER.md",
        "protocol/AxProtocol_v2.4_TAES_EVALUATION.md",
        "protocol/AxProtocol_v2.4_REDTEAM_LAYER.md",
    ])

