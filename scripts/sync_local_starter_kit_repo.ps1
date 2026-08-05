param(
    [string]$SourceRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'generated_exports/project-OS-starter-kit'),
    [string]$TargetRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '..\project-OS-starter-kit')
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $PSBoundParameters.ContainsKey('SourceRoot')) {
    & python (Join-Path $repoRoot 'scripts/build_starter_kit.py')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$sourcePath = (Resolve-Path -LiteralPath $SourceRoot).Path
& python (Join-Path $repoRoot 'scripts/validate_starter_kit.py') --kit-root $sourcePath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path -LiteralPath $TargetRoot)) {
    throw "Starter-kit target not found: $TargetRoot"
}

$targetPath = (Resolve-Path -LiteralPath $TargetRoot).Path
$sourceFullPath = [System.IO.Path]::GetFullPath($sourcePath)
$targetFullPath = [System.IO.Path]::GetFullPath($targetPath)
if ($sourceFullPath -eq $targetFullPath) {
    throw "Starter-kit source and target must differ: $sourceFullPath"
}

Get-ChildItem -LiteralPath $targetFullPath -Force |
    Where-Object { $_.Name -ne '.git' } |
    Remove-Item -Recurse -Force

Get-ChildItem -LiteralPath $sourceFullPath -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $targetFullPath -Recurse -Force
}

& python (Join-Path $repoRoot 'scripts/validate_starter_kit.py') --kit-root $sourceFullPath --compare-kit-root $targetFullPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Starter kit synced: $sourcePath -> $targetPath"
