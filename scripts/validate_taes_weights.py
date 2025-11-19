"""
Validate a TAES weights JSON file.

Usage:
  python scripts/validate_taes_weights.py config/taes_weights.json

Checks:
  - Top-level object of domains
  - Each domain has numeric logical/practical/probable in [0,1]
  - Sum is within [0.99, 1.01] (tolerant)
  - Reports ignored extra keys (ok)
  - Exits with non-zero status on errors
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
        print("ERROR: Top-level must be an object mapping domain -> weights")
        return ERR

    bad = 0
    for domain, weights in data.items():
        if domain.startswith("_"):
            # comment/meta key; skip
            continue
        if not isinstance(weights, dict):
            print(f"WARN: Domain '{domain}' is not an object; skipping")
            continue
        try:
            l = float(weights.get("logical"))
            p = float(weights.get("practical"))
            b = float(weights.get("probable"))
        except Exception:
            print(f"ERROR: Domain '{domain}' must have numeric logical/practical/probable")
            bad += 1
            continue
        if not (0.0 <= l <= 1.0 and 0.0 <= p <= 1.0 and 0.0 <= b <= 1.0):
            print(f"ERROR: Domain '{domain}' has weights out of [0,1]")
            bad += 1
            continue
        s = l + p + b
        if not (0.99 <= s <= 1.01):
            print(f"ERROR: Domain '{domain}' weights must sum ~1.0 (got {s:.3f})")
            bad += 1
            continue
        extras = set(weights.keys()) - {"logical","practical","probable"}
        if extras:
            print(f"INFO: Domain '{domain}' has extra keys ignored by runtime: {sorted(extras)}")

    if bad:
        print(f"\nFAILED: {bad} domain(s) invalid")
        return ERR
    print("OK: TAES weights file is valid")
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

