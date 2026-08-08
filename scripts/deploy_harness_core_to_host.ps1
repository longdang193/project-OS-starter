param(
    [string]$HostRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '..\codex-harness-host')
)

$ErrorActionPreference = 'Stop'

$hostPath = (Resolve-Path -LiteralPath $HostRoot).Path
$uvRuntime = @("run", "--locked", "--project", $hostPath)

$identity = & uv @uvRuntime python -c "import json; from harness_core.api import runtime_identity; print(json.dumps(runtime_identity(), sort_keys=True))"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$provenance = & uv @uvRuntime python -c "from importlib.metadata import distribution; print(distribution('harness-core').read_text('direct_url.json') or '')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($provenance -match '"editable"\s*:\s*true') {
    throw "Host runtime did not load locked harness-core: $provenance"
}

& uv @uvRuntime codex-harness-host capabilities
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& uv @uvRuntime codex-harness-host preflight
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Harness core runtime verified: $identity"
