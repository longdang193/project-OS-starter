param(
    [string]$CoreRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'packages/harness-core'),
    [string]$HostRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '..\codex-harness-host')
)

$ErrorActionPreference = 'Stop'

$corePath = (Resolve-Path -LiteralPath $CoreRoot).Path
$hostPath = (Resolve-Path -LiteralPath $HostRoot).Path
$hostPython = Join-Path $hostPath '.venv\Scripts\python.exe'
$hostCommand = Join-Path $hostPath '.venv\Scripts\codex-harness-host.exe'
if (-not (Test-Path -LiteralPath $hostPython) -or -not (Test-Path -LiteralPath $hostCommand)) {
    throw "Host virtual environment is incomplete: $hostPath"
}

& uv pip install --python $hostPython --no-deps --editable $corePath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$identity = & $hostPython -c "import json; from harness_core.api import runtime_identity; print(json.dumps(runtime_identity(), sort_keys=True))"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$source = & $hostPython -c "from pathlib import Path; import harness_core.api; print(Path(harness_core.api.__file__).resolve())"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not $source.StartsWith((Join-Path $corePath 'src'), [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Host did not import editable harness-core source: $source"
}

& $hostCommand capabilities
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $hostCommand preflight
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Harness core deployed: $identity"
