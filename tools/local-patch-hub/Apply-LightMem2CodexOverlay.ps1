[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$TargetRoot,
  [switch]$InstallStartup,
  [switch]$SkipInstall,
  [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"

function Invoke-Native {
  param(
    [string]$File,
    [string[]]$Arguments
  )

  & $File @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$File failed with exit code $LASTEXITCODE."
  }
}

function Test-NativeSuccess {
  param(
    [string]$File,
    [string[]]$Arguments
  )

  $previousErrorActionPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $File @Arguments *> $null
    return $LASTEXITCODE -eq 0
  } finally {
    $ErrorActionPreference = $previousErrorActionPreference
  }
}

function Test-WindowsHookWrapper {
  param([string]$Path)

  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return $false
  }
  $content = [IO.File]::ReadAllText($Path)
  return $content -match '(?s)\A@echo off\r?\nnode\.exe "%~dp0hooks-handler\.js" %\*\r?\n?\z'
}

function Test-CodexRuntime {
  param(
    [string]$Root,
    [bool]$RequireCompactCompatibility
  )

  $cliPath = Join-Path $Root "dist\cli.js"
  if (-not (Test-WindowsHookWrapper (Join-Path $Root "dist\tokenpilot-codex-hook.cmd")) -or
      -not (Test-Path -LiteralPath (Join-Path $Root "dist\hooks-handler.js") -PathType Leaf) -or
      -not (Test-Path -LiteralPath $cliPath -PathType Leaf)) {
    return $false
  }
  if (-not $RequireCompactCompatibility) { return $true }
  $content = [IO.File]::ReadAllText($cliPath)
  return $content -match 'endpointPath === "/responses/compact"' -and
    $content -match 'fallbackPayload \? params\.fallbackPayload\(payload\)' -and
    $content -match 'delete projected\.stream'
}

$targetPath = (Resolve-Path -LiteralPath $TargetRoot).Path
$overlayBase = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "overlays\lightrsi-codex-hook-portable")).Path
$scriptPath = (Resolve-Path -LiteralPath $MyInvocation.MyCommand.Path).Path
$git = (Get-Command git -ErrorAction Stop).Source

$headOutput = & $git -C $targetPath rev-parse HEAD 2>&1
if ($LASTEXITCODE -ne 0) {
  throw "Target is not a Git checkout: $targetPath"
}
$targetHead = ($headOutput | Out-String).Trim()

$records = @()
$manifestPaths = Get-ChildItem -LiteralPath $overlayBase -Directory |
  ForEach-Object { Join-Path $_.FullName "manifest.json" } |
  Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
foreach ($manifestPath in $manifestPaths) {
  $candidate = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
  $records += [pscustomobject]@{
    Manifest = $candidate
    Root = Split-Path -Parent $manifestPath
    PatchPath = Join-Path (Split-Path -Parent $manifestPath) ([string]$candidate.patch)
  }
}

$selected = @($records | Where-Object { [string]$_.Manifest.baseCommit -eq $targetHead }) | Select-Object -First 1
$alreadyApplied = $false
if ($null -eq $selected) {
  $appliedRecords = @($records | Where-Object {
    Test-NativeSuccess $git @("-C", $targetPath, "apply", "--reverse", "--check", "--", $_.PatchPath)
  })
  $compactionRecords = @($appliedRecords | Where-Object {
    [string]$_.Manifest.id -eq "lightrsi-codex-compaction-compatibility"
  })
  if ($compactionRecords.Count -eq 1) {
    $selected = $compactionRecords[0]
    $alreadyApplied = $true
  } elseif ($appliedRecords.Count -eq 1) {
    $selected = $appliedRecords[0]
    $alreadyApplied = $true
  } else {
    $available = @($records | ForEach-Object { [string]$_.Manifest.baseCommit }) -join ", "
    throw "No LightMem2 Codex overlay matches target HEAD $targetHead or an already-applied overlay. Available base commits: $available"
  }
}

$manifest = $selected.Manifest
$patchPath = $selected.PatchPath
if (-not (Test-Path -LiteralPath $patchPath -PathType Leaf)) {
  throw "Overlay patch missing: $patchPath"
}

$patchApplied = $false
$canApply = (-not $alreadyApplied) -and (Test-NativeSuccess $git @("-C", $targetPath, "apply", "--check", "--", $patchPath))
if ($canApply) {
  if ($VerifyOnly) {
    throw "Overlay $($manifest.version) is available but not applied."
  }
  Invoke-Native $git @("-C", $targetPath, "apply", "--", $patchPath)
  $patchApplied = $true
} elseif (-not (Test-NativeSuccess $git @("-C", $targetPath, "apply", "--reverse", "--check", "--", $patchPath))) {
  throw "Overlay $($manifest.version) does not apply cleanly and is not already applied."
}

$adapterPath = Join-Path $targetPath "components\adapters\codex"
$wrapperPath = Join-Path $adapterPath "dist\tokenpilot-codex-hook.cmd"
$runtimeWrapperPath = Join-Path $env:USERPROFILE ".local\share\lightrsi\codex-adapter\dist\tokenpilot-codex-hook.cmd"
$requireCompactCompatibility = [string]$manifest.id -eq "lightrsi-codex-compaction-compatibility"
$targetRuntimeReady = Test-CodexRuntime -Root $adapterPath -RequireCompactCompatibility:$requireCompactCompatibility
$runtimeRoot = Join-Path $env:USERPROFILE ".local\share\lightrsi\codex-adapter"
$installedRuntimeReady = Test-CodexRuntime -Root $runtimeRoot -RequireCompactCompatibility:$requireCompactCompatibility
$wrapperReady = $targetRuntimeReady -and $installedRuntimeReady
$needsInstall = $patchApplied -or -not $wrapperReady

if ($VerifyOnly) {
  if ($needsInstall) {
    throw "Overlay source is present, but generated Windows hook is stale or missing."
  }
  Write-Output "Verified LightMem2 Codex overlay $($manifest.version) at $targetHead."
  exit 0
}

if ($SkipInstall) {
  Write-Output "Applied LightMem2 Codex overlay source $($manifest.version) at $targetHead; generated install skipped."
  exit 0
}

if ($needsInstall) {
  $pnpm = (Get-Command pnpm -ErrorAction Stop).Source
  Invoke-Native $pnpm @("--dir", $adapterPath, "run", "build")
  Invoke-Native $pnpm @("--dir", $adapterPath, "run", "install:codex")
}

if ($InstallStartup) {
  $startupDir = [Environment]::GetFolderPath([Environment+SpecialFolder]::Startup)
  if ([string]::IsNullOrWhiteSpace($startupDir)) {
    throw "Windows Startup directory unavailable."
  }
  $logDir = Join-Path $env:LOCALAPPDATA "ProjectOS-starter"
  New-Item -ItemType Directory -Force -Path $startupDir, $logDir | Out-Null
  $startupPath = Join-Path $startupDir "ProjectOS-LightMem2-Codex-Overlay.cmd"
  $logPath = Join-Path $logDir "lightmem2-codex-overlay.log"
  $startupContent = "@echo off`r`npowershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`" -TargetRoot `"$targetPath`" >> `"$logPath`" 2>&1`r`n"
  [IO.File]::WriteAllText($startupPath, $startupContent, [Text.UTF8Encoding]::new($false))
  Write-Output "Installed startup reconciler: $startupPath"
}

if ($patchApplied) {
  Write-Output "Applied LightMem2 Codex overlay $($manifest.version) to $targetHead and rebuilt Codex adapter."
} elseif ($needsInstall) {
  Write-Output "Rebuilt Codex adapter from existing overlay $($manifest.version)."
} else {
  Write-Output "LightMem2 Codex overlay $($manifest.version) already active at $targetHead."
}
