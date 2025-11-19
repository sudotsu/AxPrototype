#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."
cd "$REPO_ROOT"

STATUS=0

echo "[validate_all] Governance config"
if [ -f "config/governance_coupling.json" ]; then
  python scripts/validate_governance_config.py config/governance_coupling.json || STATUS=1
else
  echo "WARN: config/governance_coupling.json not found"
fi

echo "[validate_all] TAES weights"
if [ -f "config/taes_weights.json" ]; then
  python scripts/validate_taes_weights.py config/taes_weights.json || STATUS=1
else
  echo "INFO: config/taes_weights.json not found (runtime will use defaults). To start, copy config/taes_weights.sample.json"
fi

exit $STATUS

