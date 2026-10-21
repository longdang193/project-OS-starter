[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$TargetRoot,
  [switch]$InstallGlobal,
  [switch]$AllowDowngrade,
  [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Install-9RouterGlobal.ps1")

function Test-NativeSuccess {
  param([string]$File, [string[]]$Arguments)
  $previous = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $File @Arguments *> $null
    return $LASTEXITCODE -eq 0
  } finally { $ErrorActionPreference = $previous }
}

function Invoke-Native {
  param([string]$File, [string[]]$Arguments)
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) { throw "$File failed with exit code $LASTEXITCODE." }
}

function Test-ThreeWayApply {
  param(
    [string]$File,
    [string]$TargetPath,
    [string]$PatchPath
  )

  $indexOutput = & $File -C $TargetPath rev-parse --git-path index 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Cannot resolve Git index for $TargetPath." }
  $indexPath = (Resolve-Path -LiteralPath (($indexOutput | Out-String).Trim())).Path
  $temporaryIndex = Join-Path ([IO.Path]::GetTempPath()) ("9router-cgw-overlay-index-" + [Guid]::NewGuid().ToString("N"))
  Copy-Item -LiteralPath $indexPath -Destination $temporaryIndex
  $previousIndex = $env:GIT_INDEX_FILE
  try {
    $env:GIT_INDEX_FILE = $temporaryIndex
    return Test-NativeSuccess $File @(
      "-C", $TargetPath, "apply", "--ignore-space-change", "--ignore-whitespace",
      "--3way", "--cached", "--", $PatchPath
    )
  } finally {
    if ($null -eq $previousIndex) { Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue }
    else { $env:GIT_INDEX_FILE = $previousIndex }
    if (Test-Path -LiteralPath $temporaryIndex -PathType Leaf) {
      [IO.File]::Delete($temporaryIndex)
    }
  }
}

function Get-OverlayRecords {
  param([string]$OverlayRoot)
  $records = @(Get-ChildItem -LiteralPath $OverlayRoot -Directory | ForEach-Object {
    $manifestPath = Join-Path $_.FullName "manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { return }
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    if ([string]::IsNullOrWhiteSpace([string]$manifest.baseCommit) -or
        [string]$manifest.baseCommit -notmatch "^[0-9a-f]{40}$" -or
        [string]::IsNullOrWhiteSpace([string]$manifest.targetVersion) -or
        [string]::IsNullOrWhiteSpace([string]$manifest.patch)) {
      throw "Invalid 9router CGW overlay manifest: $manifestPath"
    }
    $patchPath = Join-Path $_.FullName ([string]$manifest.patch)
    if (-not (Test-Path -LiteralPath $patchPath -PathType Leaf)) {
      throw "9router CGW overlay patch is missing: $patchPath"
    }
    [pscustomobject]@{
      Manifest = $manifest
      Patch = $patchPath
    }
  })
  if ($records.Count -eq 0) { throw "No 9router CGW overlays are registered under $OverlayRoot" }
  return $records
}

function Get-TrackedChanges {
  param([string]$File, [string]$TargetPath)
  $changes = @(& $File -C $TargetPath status --porcelain=v1 --untracked-files=no)
  if ($LASTEXITCODE -ne 0) { throw "Cannot inspect tracked changes in $TargetPath." }
  return $changes
}

if ($InstallGlobal -and $VerifyOnly) {
  throw "-InstallGlobal cannot be combined with -VerifyOnly."
}

$targetPath = (Resolve-Path -LiteralPath $TargetRoot).Path
$overlayRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "overlays\9router-cgw")).Path
$git = (Get-Command git -ErrorAction Stop).Source
$head = (& $git -C $targetPath rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Target is not a Git checkout: $targetPath" }

$records = @(Get-OverlayRecords -OverlayRoot $overlayRoot)
$applyFlags = @("--ignore-space-change", "--ignore-whitespace")
$selected = @($records | Where-Object { [string]$_.Manifest.baseCommit -eq $head }) | Select-Object -First 1
$alreadyApplied = @($records | Where-Object {
  Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--reverse", "--check", "--", $_.Patch))
})

if ($alreadyApplied.Count -gt 1) {
  throw "Multiple 9router CGW overlays appear active at $head; resolve the target before continuing."
}

if ($alreadyApplied.Count -eq 1) {
  $selected = $alreadyApplied[0]
  $targetPackagePath = Join-Path $targetPath "cli\package.json"
  if (-not (Test-Path -LiteralPath $targetPackagePath -PathType Leaf)) {
    throw "Target is missing cli\package.json: $targetPath"
  }
  $targetPackage = Get-Content -Raw -LiteralPath $targetPackagePath | ConvertFrom-Json
  if ([Version]$targetPackage.version -ne [Version]$selected.Manifest.targetVersion) {
    throw "Active CGW overlay targets version $($selected.Manifest.targetVersion), but target is $($targetPackage.version)."
  }
  $receiptJson = [ordered]@{
    schemaVersion = 1
    overlayId = [string]$selected.Manifest.id
    overlayVersion = [string]$selected.Manifest.version
    baseCommit = [string]$selected.Manifest.baseCommit
    targetVersion = [string]$selected.Manifest.targetVersion
    packageVersion = [string]$targetPackage.version
    sourceHead = [string]$head
  } | ConvertTo-Json -Compress
  if ($InstallGlobal) {
    Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade -InstallReceiptJson $receiptJson
  }
  Write-Output "Verified 9router CGW overlay $($selected.Manifest.version) already active at $head."
  exit 0
}

if ($null -eq $selected) {
  if ($VerifyOnly) {
    $rebaseCandidate = @($records | Where-Object {
      Test-ThreeWayApply -File $git -TargetPath $targetPath -PatchPath $_.Patch
    } | Select-Object -First 1)
    if ($rebaseCandidate.Count -eq 1) {
      Write-Output "Verified 9router CGW overlay $($rebaseCandidate[0].Manifest.version) can be rebased onto $head; register a new exact-base overlay before installation."
      exit 0
    }
  }
  $available = (($records | ForEach-Object { "$($_.Manifest.baseCommit) ($($_.Manifest.targetVersion))" }) -join ", ")
  throw "No 9router CGW overlay matches HEAD $head. Rebase the overlay and add a new exact-base manifest. Available bases: $available"
}

$targetPackagePath = Join-Path $targetPath "cli\package.json"
if (-not (Test-Path -LiteralPath $targetPackagePath -PathType Leaf)) {
  throw "Target is missing cli\package.json: $targetPath"
}
$targetPackage = Get-Content -Raw -LiteralPath $targetPackagePath | ConvertFrom-Json
if ([Version]$targetPackage.version -ne [Version]$selected.Manifest.targetVersion) {
  throw "Refusing to apply CGW overlay $($selected.Manifest.version) to 9router version $($targetPackage.version); expected $($selected.Manifest.targetVersion)."
}

$directCheck = Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--check", "--", $selected.Patch))
if ($VerifyOnly) {
  if ($directCheck) { throw "9router CGW overlay $($selected.Manifest.version) is available but not applied at $head." }
  if (Test-ThreeWayApply -File $git -TargetPath $targetPath -PatchPath $selected.Patch) {
    Write-Output "Verified 9router CGW overlay $($selected.Manifest.version) can be applied to $head with Git 3-way merge."
    exit 0
  }
  throw "9router CGW overlay $($selected.Manifest.version) does not apply cleanly to HEAD $head. Rebase patch before update."
}

$trackedChanges = @(Get-TrackedChanges -File $git -TargetPath $targetPath)
if ($trackedChanges.Count -gt 0) {
  throw "Target has tracked changes; clean them before applying a 9router CGW overlay: $targetPath"
}

if ($directCheck) {
  Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--", $selected.Patch))
} elseif (Test-ThreeWayApply -File $git -TargetPath $targetPath -PatchPath $selected.Patch) {
  Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--3way", "--", $selected.Patch))
} else {
  throw "9router CGW overlay $($selected.Manifest.version) does not apply cleanly to HEAD $head. Rebase patch before update."
}

$receiptJson = [ordered]@{
  schemaVersion = 1
  overlayId = [string]$selected.Manifest.id
  overlayVersion = [string]$selected.Manifest.version
  baseCommit = [string]$selected.Manifest.baseCommit
  targetVersion = [string]$selected.Manifest.targetVersion
  packageVersion = [string]$targetPackage.version
  sourceHead = [string]$head
} | ConvertTo-Json -Compress
if ($InstallGlobal) {
  Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade -InstallReceiptJson $receiptJson
}
Write-Output "Applied 9router CGW overlay $($selected.Manifest.version) to $($selected.Manifest.targetVersion) at $head."
