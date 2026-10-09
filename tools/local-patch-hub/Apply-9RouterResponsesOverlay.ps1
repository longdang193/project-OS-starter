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
  $temporaryIndex = Join-Path ([IO.Path]::GetTempPath()) ("9router-overlay-index-" + [Guid]::NewGuid().ToString("N"))
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
$overlayRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "overlays\9router-responses")).Path
$git = (Get-Command git -ErrorAction Stop).Source
$head = (& $git -C $targetPath rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Target is not a Git checkout: $targetPath" }

$transformerPath = Join-Path $targetPath "open-sse\transformer\responsesTransformer.js"
$translatorIndexPath = Join-Path $targetPath "open-sse\translator\index.js"
$responsesTranslatorPath = Join-Path $targetPath "open-sse\translator\response\openai-responses.js"
$streamPath = Join-Path $targetPath "open-sse\utils\stream.js"
$nativeFix = $false
if ((Test-Path -LiteralPath $transformerPath -PathType Leaf) -and
    (Test-Path -LiteralPath $translatorIndexPath -PathType Leaf) -and
    (Test-Path -LiteralPath $responsesTranslatorPath -PathType Leaf) -and
    (Test-Path -LiteralPath $streamPath -PathType Leaf)) {
  $transformer = [IO.File]::ReadAllText($transformerPath)
  $translatorIndex = [IO.File]::ReadAllText($translatorIndexPath)
  $responsesTranslator = [IO.File]::ReadAllText($responsesTranslatorPath)
  $stream = [IO.File]::ReadAllText($streamPath)
  $nativeFix = $transformer -match "responseOutput:\s*\[\]" -and
    $transformer -match "output:\s*state\.responseOutput\.filter\(Boolean\)" -and
    $translatorIndex -match "responseOutput:\s*\[\]" -and
    $responsesTranslator -match "state\.responseOutput\[Number\(data\.output_index\)\]" -and
    $responsesTranslator -match "output:\s*state\.responseOutput\.filter\(Boolean\)" -and
    $stream -match "reconstructedOutput = state\.responseOutput\.filter\(Boolean\)"
}

if ($nativeFix) {
  if ($VerifyOnly) {
    Write-Output "Verified 9router Responses output fix already present at $head."
    exit 0
  }
  if ($InstallGlobal) {
    Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
  }
  Write-Output "9router Responses output fix already present at $head; no overlay changes needed."
  exit 0
}

$records = @(Get-ChildItem -LiteralPath $overlayRoot -Directory | ForEach-Object {
  $manifestPath = Join-Path $_.FullName "manifest.json"
  if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { return }
  $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
  [pscustomobject]@{
    Manifest = $manifest
    Patch = Join-Path $_.FullName ([string]$manifest.patch)
  }
})

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
  } elseif (@($records).Count -eq 1) {
    $selected = $records[0]
  } else {
    $available = @($records | ForEach-Object { [string]$_.Manifest.baseCommit }) -join ", "
    throw "No 9router Responses overlay matches HEAD $head or an already-applied overlay. Available bases: $available"
  }
}

$patch = $selected.Patch
if (-not (Test-Path -LiteralPath $patch -PathType Leaf)) { throw "Overlay patch missing: $patch" }

if (-not $alreadyApplied -and
    (Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--reverse", "--check", "--", $patch)))) {
  $alreadyApplied = $true
}

$supersededPatch = $null
if ($selected.Manifest.supersedes) {
  $supersededPatch = Join-Path (Split-Path -Parent $patch) ([string]$selected.Manifest.supersedes)
}
$migrationNeeded = -not $alreadyApplied -and $null -ne $supersededPatch -and
  (Test-Path -LiteralPath $supersededPatch -PathType Leaf) -and
  (Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--reverse", "--check", "--", $supersededPatch)))

if ($migrationNeeded) {
  if ($VerifyOnly) {
    $verificationRoot = Join-Path ([IO.Path]::GetTempPath()) ("9router-overlay-verify-" + [Guid]::NewGuid().ToString("N"))
    $verificationCreated = $false
    try {
      Invoke-Native $git (@("-C", $targetPath, "worktree", "add", "--detach", $verificationRoot, $head))
      $verificationCreated = $true
      $changedPaths = @(& $git -C $targetPath diff --name-only HEAD --)
      if ($LASTEXITCODE -ne 0) { throw "Cannot inspect tracked changes in $targetPath." }
      foreach ($relativePath in $changedPaths) {
        $sourcePath = Join-Path $targetPath $relativePath
        $destinationPath = Join-Path $verificationRoot $relativePath
        if (Test-Path -LiteralPath $sourcePath -PathType Leaf) {
          $destinationParent = Split-Path -Parent $destinationPath
          if (-not (Test-Path -LiteralPath $destinationParent -PathType Container)) {
            New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
          }
          Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
        } elseif (Test-Path -LiteralPath $destinationPath) {
          Remove-Item -LiteralPath $destinationPath -Force
        }
      }
      $supersededPatchPaths = @(Get-Content -LiteralPath $supersededPatch | ForEach-Object {
        if ($_ -match '^\+\+\+ b/(.+)$') { $Matches[1] }
      })
      foreach ($relativePath in $supersededPatchPaths) {
        if ($changedPaths -contains $relativePath) { continue }
        $sourcePath = Join-Path $targetPath $relativePath
        $destinationPath = Join-Path $verificationRoot $relativePath
        if (Test-Path -LiteralPath $sourcePath -PathType Leaf) {
          $destinationParent = Split-Path -Parent $destinationPath
          if (-not (Test-Path -LiteralPath $destinationParent -PathType Container)) {
            New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
          }
          Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
        }
      }
      Invoke-Native $git (@("-C", $verificationRoot, "apply") + $applyFlags + @("--reverse", "--", $supersededPatch))
      $trackedChanges = @(& $git -C $verificationRoot status --porcelain=v1 --untracked-files=no)
      if ($LASTEXITCODE -ne 0) { throw "Cannot inspect tracked changes in verification checkout." }
      if ($trackedChanges.Count -gt 0) {
        throw "Target has unrelated tracked changes; clean them before migrating the Responses overlay: $targetPath"
      }
      if (-not (Test-NativeSuccess $git (@("-C", $verificationRoot, "apply") + $applyFlags + @("--check", "--", $patch)))) {
        throw "Overlay $($selected.Manifest.version) does not apply cleanly after removing superseded overlay."
      }
      Write-Output "Verified 9router Responses overlay $($selected.Manifest.version) can replace superseded overlay at $head."
    } finally {
      if ($verificationCreated) {
        Invoke-Native $git (@("-C", $targetPath, "worktree", "remove", "--force", $verificationRoot))
      }
    }
    exit 0
  }
  Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--reverse", "--", $supersededPatch))
  try {
    $trackedChanges = @(& $git -C $targetPath status --porcelain=v1 --untracked-files=no)
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect tracked changes in $targetPath." }
    if ($trackedChanges.Count -gt 0) {
      throw "Target has unrelated tracked changes; clean them before migrating the Responses overlay: $targetPath"
    }
    if (-not (Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--check", "--", $patch)))) {
      throw "Overlay $($selected.Manifest.version) does not apply cleanly after removing superseded overlay."
    }
    Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--", $patch))
  } catch {
    if (Test-NativeSuccess $git (@("-C", $targetPath, "apply") + $applyFlags + @("--check", "--", $supersededPatch))) {
      Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--", $supersededPatch))
    }
    throw
  }
  if ($InstallGlobal) {
    Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
  }
  Write-Output "Migrated 9router Responses overlay to $($selected.Manifest.version) at $head."
  exit 0
}

$appliedNow = $false
if (-not $alreadyApplied) {
  $checkArgs = @("-C", $targetPath, "apply") + $applyFlags + @("--check", "--", $patch)
  if (Test-NativeSuccess $git $checkArgs) {
    if ($VerifyOnly) { throw "Overlay $($selected.Manifest.version) is available but not applied." }
    Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--", $patch))
    $appliedNow = $true
  } elseif ($VerifyOnly) {
    if (-not (Test-ThreeWayApply $git $targetPath $applyFlags $patch)) {
      throw "Overlay $($selected.Manifest.version) does not apply cleanly to HEAD $head. Rebase patch before update."
    }
    Write-Output "Verified 9router Responses overlay can be rebased onto $head."
    exit 0
  } else {
    $trackedChanges = @(& $git -C $targetPath status --porcelain=v1 --untracked-files=no)
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect tracked changes in $targetPath." }
    if ($trackedChanges.Count -gt 0) {
      throw "Target has tracked changes; clean them before applying a 3-way overlay: $targetPath"
    }
    if (-not (Test-ThreeWayApply $git $targetPath $applyFlags $patch)) {
      throw "Overlay $($selected.Manifest.version) does not apply cleanly to HEAD $head. Rebase patch before update."
    }
    Invoke-Native $git (@("-C", $targetPath, "apply") + $applyFlags + @("--3way", "--", $patch))
    $appliedNow = $true
  }
}

if ($InstallGlobal) {
  if ($VerifyOnly) { throw "-InstallGlobal cannot be combined with -VerifyOnly." }
  Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
}

if ($appliedNow) { Write-Output "Applied 9router Responses overlay $($selected.Manifest.version) at $head." }
else { Write-Output "9router Responses overlay $($selected.Manifest.version) already active at $head." }
