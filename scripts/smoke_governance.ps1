Param()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Join-Path $ScriptDir '..'
Set-Location $RepoRoot

python run_axp.py --smoke-governance

