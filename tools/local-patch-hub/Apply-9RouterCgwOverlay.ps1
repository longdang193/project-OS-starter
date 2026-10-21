[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$TargetRoot,
  [switch]$InstallGlobal,
  [switch]$AllowDowngrade,
  [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Install-9RouterGlobal.ps1")

$BaseCommit = "87a74e1bda3677193c6f71a7e2100c90311f0689"
$TargetVersion = [Version]"0.5.104"

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
    [string]$Git,
    [string]$TargetPath,
    [string]$PatchPath
  )

  $indexOutput = & $Git -C $TargetPath rev-parse --git-path index 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Cannot resolve Git index for $TargetPath." }
  $indexPath = (Resolve-Path -LiteralPath (($indexOutput | Out-String).Trim())).Path
  $temporaryIndex = Join-Path ([IO.Path]::GetTempPath()) ("9router-cgw-overlay-index-" + [Guid]::NewGuid().ToString("N"))
  Copy-Item -LiteralPath $indexPath -Destination $temporaryIndex
  $previousIndex = $env:GIT_INDEX_FILE
  try {
    $env:GIT_INDEX_FILE = $temporaryIndex
    return Test-NativeSuccess $Git @(
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

$targetPath = (Resolve-Path -LiteralPath $TargetRoot).Path
$overlayPath = Join-Path $PSScriptRoot "overlays\9router-cgw\87a74e1b"
$manifestPath = Join-Path $overlayPath "manifest.json"
$patchPath = Join-Path $overlayPath "9router-cgw.patch"
$git = (Get-Command git -ErrorAction Stop).Source

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $patchPath -PathType Leaf)) {
  throw "9router CGW overlay files are incomplete under $overlayPath."
}

$head = (& $git -C $targetPath rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Target is not a Git checkout: $targetPath" }

$packagePath = Join-Path $targetPath "cli\package.json"
if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) {
  throw "Target is missing cli\package.json: $targetPath"
}
$targetPackage = Get-Content -Raw -LiteralPath $packagePath | ConvertFrom-Json
$actualVersion = [Version]$targetPackage.version
if ($actualVersion -ne $TargetVersion) {
  throw "Refusing to apply CGW overlay to 9router version $actualVersion; expected $TargetVersion."
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$receiptJson = [ordered]@{
  schemaVersion = 1
  overlayId = [string]$manifest.id
  overlayVersion = [string]$manifest.version
  baseCommit = [string]$manifest.baseCommit
  targetVersion = [string]$manifest.targetVersion
  packageVersion = [string]$targetPackage.version
  sourceHead = [string]$head
} | ConvertTo-Json -Compress

$applyFlags = @("--ignore-space-change", "--ignore-whitespace")
$reverseCheck = Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--reverse", "--check", "--", $patchPath))
if ($reverseCheck) {
  if ($InstallGlobal) {
    Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade -InstallReceiptJson $receiptJson
  }
  Write-Output "Verified 9router CGW overlay at $head."
  exit 0
}

if ($head -ne $BaseCommit) {
  if ($VerifyOnly -and (Test-ThreeWayApply -Git $git -TargetPath $targetPath -PatchPath $patchPath)) {
    Write-Output "Verified 9router CGW overlay can be rebased onto $head."
    exit 0
  }
  throw "No 9router CGW overlay matches target HEAD $head. Rebase the overlay before applying it."
}

$directCheck = Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--check", "--", $patchPath))
if (-not $directCheck) {
  if ($VerifyOnly -and (Test-ThreeWayApply -Git $git -TargetPath $targetPath -PatchPath $patchPath)) {
    Write-Output "Verified 9router CGW overlay can be applied to $head with Git 3-way merge."
    exit 0
  }
  throw "9router CGW overlay does not apply cleanly to exact base $head."
}

if ($VerifyOnly) {
  throw "9router CGW overlay is available but not applied at $head."
}

Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--", $patchPath))
if ($InstallGlobal) {
  Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade -InstallReceiptJson $receiptJson
}
Write-Output "Applied 9router CGW overlay 1.0.0 to $targetVersion at $head."
