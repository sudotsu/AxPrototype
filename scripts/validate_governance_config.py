"""
Validate governance coupling config.

Usage:
  python scripts/validate_governance_config.py config/governance_coupling.json

Schema (minimal):
{
  "write_governance_to_ledger": true,            # optional, boolean
  "signals": {                                   # required object
    "D3": {"mode": "hard", "iv_max": 0.68, "ird_min": 0.55},
    "SECRETS": {"mode": "soft"}
  }
}

Rules:
- mode: "hard" or "soft" (default to hard if omitted; warn)
- iv_max, ird_min: optional floats in [0,1] if present
- Unknown top-level keys are ignored with info note
- Exits non-zero on structural errors
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

OK = 0
ERR = 1

def validate(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf8"))
    except Exception as e:
        print(f"ERROR: Failed to read/parse JSON: {e}")
        return ERR

    if not isinstance(data, dict):
        print("ERROR: Top-level must be an object with 'signals'")
        return ERR

    signals = data.get("signals", None)
    if not isinstance(signals, dict):
        print("ERROR: Missing or invalid 'signals' object")
        return ERR

    if "write_governance_to_ledger" in data and not isinstance(data["write_governance_to_ledger"], bool):
        print("ERROR: 'write_governance_to_ledger' must be boolean if present")
        return ERR

    def _valid_range(x):
        try:
            xf = float(x)
            return 0.0 <= xf <= 1.0
        except Exception:
            return False

    bad = 0
    for sig, spec in signals.items():
        if not isinstance(spec, dict):
            print(f"ERROR: Signal '{sig}' -> expected object")
            bad += 1
            continue
        mode = spec.get("mode", "hard")
        if mode not in ("hard", "soft"):
            print(f"ERROR: Signal '{sig}' -> mode must be 'hard' or 'soft' (got {mode})")
            bad += 1
        if "iv_max" in spec and not _valid_range(spec["iv_max"]):
            print(f"ERROR: Signal '{sig}' -> iv_max must be a float in [0,1]")
            bad += 1
        if "ird_min" in spec and not _valid_range(spec["ird_min"]):
            print(f"ERROR: Signal '{sig}' -> ird_min must be a float in [0,1]")
            bad += 1

    if bad:
        print(f"\nFAILED: {bad} issue(s) found in 'signals'")
        return ERR

    print("OK: governance_coupling.json is valid")
    return OK

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return ERR
    path = Path(argv[1])
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return ERR
    return validate(path)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

