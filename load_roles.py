# Timestamp: 2025-11-20 13:00:00 UTC

"""
AxProtocol Role Loader - Phase 2: Creative Domain Only

Loads the 3 core roles: Caller, Builder, Critic.
"""

import os
from pathlib import Path
from typing import Dict

def load_domain_roles(domain: str = "creative", base_dir: Path = Path(".")) -> Dict[str, str]:
    """
    Load the definitive 3 roles for the Creative WarRoom.

    Args:
        domain: Hardcoded to 'creative' for Phase 2.
        base_dir: Project root.

    Returns:
        Dictionary with role contents.
    """

    # Force domain to creative for this phase
    target_domain = "creative"
    role_path = base_dir / "axp" / "roles" / target_domain

    required_roles = ["caller", "builder", "critic"]
    loaded_roles = {}

    print(f"[AxProtocol] Loading roles from {role_path}...")

    for role in required_roles:
        file_path = role_path / f"{role}_stable.txt"
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Missing critical role file: {file_path}")

            content = file_path.read_text(encoding="utf-8")
            loaded_roles[role] = content
            print(f"  [OK] Loaded {role.capitalize()}")

        except Exception as e:
            print(f"  [ERR] Failed to load {role}: {e}")
            # Emergency fallback (should never happen in prod)
            loaded_roles[role] = f"System Error: Could not load {role} prompt."

    return loaded_roles
