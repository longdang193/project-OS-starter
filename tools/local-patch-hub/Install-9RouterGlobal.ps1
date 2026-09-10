function Install-9RouterGlobal {
  param(
    [Parameter(Mandatory = $true)][string]$TargetPath,
    [switch]$AllowDowngrade
  )

  $npm = (Get-Command npm -ErrorAction Stop).Source
  $globalRoot = (& $npm "root" "-g" | Out-String).Trim()
  if ($LASTEXITCODE -ne 0) { throw "$npm global root lookup failed with exit code $LASTEXITCODE." }
  $targetPackage = Get-Content -Raw -LiteralPath (Join-Path $TargetPath "cli\package.json") | ConvertFrom-Json
  $targetVersion = [Version]$targetPackage.version
  $installedPackagePath = Join-Path $globalRoot "9router\package.json"
  if ((Test-Path -LiteralPath $installedPackagePath -PathType Leaf) -and -not $AllowDowngrade) {
    $installedPackage = Get-Content -Raw -LiteralPath $installedPackagePath | ConvertFrom-Json
    $installedVersion = [Version]$installedPackage.version
    if ($targetVersion -lt $installedVersion) {
      throw "Refusing to downgrade global 9router from $installedVersion to $targetVersion. Rebase overlay or pass -AllowDowngrade."
    }
  }

  function Get-9RouterProcesses {
    @(Get-CimInstance Win32_Process | Where-Object {
      $_.Name -eq "node.exe" -and $_.CommandLine -match "(?i)9router.*(cli\.js|custom-server\.js)"
    })
  }

  foreach ($process in @(Get-9RouterProcesses)) {
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
  }
  $stopDeadline = [DateTime]::UtcNow.AddSeconds(10)
  do {
    $remainingProcesses = @(Get-9RouterProcesses)
    if ($remainingProcesses.Count -eq 0) { break }
    Start-Sleep -Milliseconds 250
  } while ([DateTime]::UtcNow -lt $stopDeadline)
  if ($remainingProcesses.Count -gt 0) {
    $remainingIds = @($remainingProcesses | ForEach-Object { $_.ProcessId }) -join ", "
    throw "Cannot replace global 9router while processes remain: $remainingIds"
  }

  $cliPath = Join-Path $TargetPath "cli"
  $buildExitCode = 0
  Push-Location -LiteralPath $cliPath
  try {
    & $npm "run" "build"
    $buildExitCode = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  if ($buildExitCode -ne 0) { throw "$npm build failed with exit code $buildExitCode." }
  $builtAppPath = Join-Path $TargetPath "cli\app"
  if (-not (Test-Path -LiteralPath (Join-Path $builtAppPath "server.js") -PathType Leaf) -and
      -not (Test-Path -LiteralPath (Join-Path $builtAppPath "custom-server.js") -PathType Leaf)) {
    throw "9router build is incomplete: missing cli\app\server.js and cli\app\custom-server.js."
  }
  & $npm "install" "-g" "--force" (Join-Path $TargetPath "cli")
  if ($LASTEXITCODE -ne 0) { throw "$npm global install failed with exit code $LASTEXITCODE." }

  $packageRoot = Join-Path $globalRoot "9router"
  $entryPath = Join-Path $packageRoot "cli.js"
  $cmdShim = Join-Path (Split-Path $globalRoot -Parent) "9router.cmd"
  if (-not (Test-Path -LiteralPath $entryPath -PathType Leaf)) {
    throw "Global 9router install is incomplete: missing $entryPath"
  }
  $installedAppPath = Join-Path $packageRoot "app"
  if (-not (Test-Path -LiteralPath (Join-Path $installedAppPath "server.js") -PathType Leaf) -and
      -not (Test-Path -LiteralPath (Join-Path $installedAppPath "custom-server.js") -PathType Leaf)) {
    throw "Global 9router install is incomplete: missing standalone app under $installedAppPath"
  }
  if (-not (Test-Path -LiteralPath $cmdShim -PathType Leaf)) {
    throw "Global 9router install is incomplete: missing $cmdShim"
  }

  $versionOutput = (& $cmdShim "--version" 2>&1 | Out-String).Trim()
  $versionExitCode = $LASTEXITCODE
  if ($versionExitCode -ne 0 -or $versionOutput -ne [string]$targetPackage.version) {
    throw "Global 9router install is unusable: expected version $($targetPackage.version), got '$versionOutput'."
  }

  Write-Output "Installed 9router global package and verified cli.js, 9router.cmd, and version $versionOutput."
}
