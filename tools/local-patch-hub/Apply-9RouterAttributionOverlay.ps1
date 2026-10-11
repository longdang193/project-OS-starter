[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$TargetRoot,
  [switch]$InstallGlobal,
  [switch]$AllowDowngrade,
  [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Install-9RouterGlobal.ps1")

function Invoke-Native {
  param([string]$File, [string[]]$Arguments)
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) { throw "$File failed with exit code $LASTEXITCODE." }
}

function Test-NativeSuccess {
  param([string]$File, [string[]]$Arguments)
  $previous = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $File @Arguments *> $null
    return $LASTEXITCODE -eq 0
  } finally { $ErrorActionPreference = $previous }
}

function Test-ThreeWayApply {
  param(
    [string]$File,
    [string]$TargetPath,
    [string[]]$ApplyFlags,
    [string]$PatchPath
  )

  $indexOutput = & $File -C $TargetPath rev-parse --git-path index 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Cannot resolve Git index for $TargetPath." }
  $indexPath = (Resolve-Path -LiteralPath (($indexOutput | Out-String).Trim())).Path
  $temporaryIndex = Join-Path ([IO.Path]::GetTempPath()) ("9router-attribution-index-" + [Guid]::NewGuid().ToString("N"))
  Copy-Item -LiteralPath $indexPath -Destination $temporaryIndex
  $previousIndex = $env:GIT_INDEX_FILE
  try {
    $env:GIT_INDEX_FILE = $temporaryIndex
    return Test-NativeSuccess $File (@("-C", $TargetPath, "apply") + $ApplyFlags + @("--3way", "--cached", "--", $PatchPath))
  } finally {
    if ($null -eq $previousIndex) { Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue }
    else { $env:GIT_INDEX_FILE = $previousIndex }
    if (Test-Path -LiteralPath $temporaryIndex -PathType Leaf) {
      [IO.File]::Delete($temporaryIndex)
    }
  }
}

$targetPath = (Resolve-Path -LiteralPath $TargetRoot).Path
$overlayRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "overlays\9router-attribution")).Path
$git = (Get-Command git -ErrorAction Stop).Source
$head = (& $git -C $targetPath rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Target is not a Git checkout: $targetPath" }

if ($InstallGlobal -and $VerifyOnly) { throw "-InstallGlobal cannot be combined with -VerifyOnly." }

$records = @(Get-ChildItem -LiteralPath $overlayRoot -Directory | ForEach-Object {
  $manifestPath = Join-Path $_.FullName "manifest.json"
  if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { return }
  $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
  [pscustomobject]@{
    Manifest = $manifest
    Patch = Join-Path $_.FullName ([string]$manifest.patch)
  }
})
if ($records.Count -eq 0) { throw "No 9router attribution overlays are registered under $overlayRoot" }

$applyFlags = @("--ignore-space-change", "--ignore-whitespace")
$selected = @($records | Where-Object { [string]$_.Manifest.baseCommit -eq $head }) | Select-Object -First 1
$alreadyApplied = $false
if ($null -eq $selected) {
  $applied = @($records | Where-Object {
    Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--reverse", "--check", "--", $_.Patch))
  })
  if ($applied.Count -eq 1) {
    $selected = $applied[0]
    $alreadyApplied = $true
  } elseif ($records.Count -eq 1) {
    $selected = $records[0]
  } else {
    $available = @($records | ForEach-Object { [string]$_.Manifest.baseCommit }) -join ", "
    throw "No 9router attribution overlay matches HEAD $head or an already-applied overlay. Available bases: $available"
  }
}

$patch = $selected.Patch
if (-not (Test-Path -LiteralPath $patch -PathType Leaf)) { throw "Overlay patch missing: $patch" }

if (-not $alreadyApplied -and
    (Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--reverse", "--check", "--", $patch)))) {
  $alreadyApplied = $true
}

if ($alreadyApplied) {
  if ($VerifyOnly) {
    Write-Output "Verified 9router attribution overlay $($selected.Manifest.version) is already active at $head."
    exit 0
  }
  if ($InstallGlobal) {
    Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
  }
  Write-Output "9router attribution overlay $($selected.Manifest.version) already active at $head; no overlay changes needed."
  exit 0
}

$checkArgs = @("-C", $targetPath, "apply") + $applyFlags + @("--check", "--", $patch)
if (Test-NativeSuccess $git $checkArgs) {
  if ($VerifyOnly) { throw "Overlay $($selected.Manifest.version) is available but not applied." }
  Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--", $patch))
  if ($InstallGlobal) {
    Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
  }
  Write-Output "Applied 9router attribution overlay $($selected.Manifest.version) at $head."
  exit 0
}

if (-not (Test-ThreeWayApply $git $targetPath $applyFlags $patch)) {
  throw "Overlay $($selected.Manifest.version) does not apply cleanly to HEAD $head. Rebase patch before update."
}

if ($VerifyOnly) {
  Write-Output "Verified 9router attribution overlay $($selected.Manifest.version) can be rebased onto $head."
  exit 0
}

$trackedChanges = @(& $git -C $targetPath status --porcelain=v1 --untracked-files=no)
if ($LASTEXITCODE -ne 0) { throw "Cannot inspect tracked changes in $targetPath." }
if ($trackedChanges.Count -gt 0) {
  throw "Target has tracked changes; clean them before applying a 3-way attribution overlay: $targetPath"
}

Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--3way", "--", $patch))
if ($InstallGlobal) {
  Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
}
Write-Output "Applied 9router attribution overlay $($selected.Manifest.version) at $head using Git 3-way merge."
