param(
    [string]$SourceRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'generated_exports/project-OS-starter-kit'),
    [string]$TargetRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '..\project-OS-starter-kit')
)

$ErrorActionPreference = 'Stop'

$sourcePath = (Resolve-Path -LiteralPath $SourceRoot).Path
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

$repoRoot = Split-Path -Parent $PSScriptRoot
& python (Join-Path $repoRoot 'scripts/validate_starter_kit.py') --compare-kit-root $targetFullPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Starter kit synced: $sourcePath -> $targetPath"
