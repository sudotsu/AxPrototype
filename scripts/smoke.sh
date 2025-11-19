#!/usr/bin/env bash
set -euo pipefail

APP="https://${DOMAIN_APP}"
SEN="https://${DOMAIN_SENTINEL}"

echo "# Checking app health"
curl -sSf "$APP" >/dev/null || { echo "App fail"; exit 1; }

echo "# Checking sentinel health"
curl -sSf "$SEN/health" | grep -q '"status":"ok"' || { echo "Sentinel health fail"; exit 1; }

echo "# Forcing a verify pass"
curl -sSf "$SEN/verify" | grep -q '"verified":' || { echo "Verify endpoint fail"; exit 1; }

echo "OK"
