Param()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Join-Path $ScriptDir '..'
Set-Location $RepoRoot

$status = 0

Write-Host "[validate_all] Governance config"
if (Test-Path "config/governance_coupling.json") {
  python scripts/validate_governance_config.py config/governance_coupling.json
  if ($LASTEXITCODE -ne 0) { $status = 1 }
} else {
  Write-Host "WARN: config/governance_coupling.json not found"
}

Write-Host "[validate_all] TAES weights"
if (Test-Path "config/taes_weights.json") {
  python scripts/validate_taes_weights.py config/taes_weights.json
  if ($LASTEXITCODE -ne 0) { $status = 1 }
} else {
  Write-Host "INFO: config/taes_weights.json not found (runtime will use defaults). To start, copy config/taes_weights.sample.json"
}

exit $status

