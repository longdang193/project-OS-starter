[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = (git rev-parse --show-toplevel).Trim()
& python (Join-Path $repoRoot "scripts/sync_agent_adapters.py") --all-platforms --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
