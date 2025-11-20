"""
Role loading from domain-specific files.
"""

import os
from pathlib import Path
from typing import Dict

def load_domain_roles(domain: str, base_dir: Path) -> Dict[str, str]:
    """
    Load roles for the creative domain (Caller, Builder, Critic).
    """
    try:
        # Assuming you have a utility to read the files, strictly pathing here
        role_path = base_dir / "roles" / domain

        def read_role(name):
            return (role_path / f"{name}_stable.txt").read_text(encoding="utf-8")

        roles_dict = {
            'caller': read_role("caller"),
            'builder': read_role("builder"),
            'critic': read_role("critic"),
        }
        return roles_dict

    except Exception as e:
        print(f"[WARN] Role loader failed for {domain}: {e}")
        # Fallback defaults (Emergency only)
        return {
            'caller': "Role: Caller. Analyze user objective...",
            'builder': "Role: Builder. Create final artifact...",
            'critic': "Role: Critic. Evaluate and revise..."
        }
