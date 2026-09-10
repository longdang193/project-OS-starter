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

  $processes = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "node.exe" -and $_.CommandLine -match "(?i)9router.*(cli\.js|custom-server\.js)"
  })
  foreach ($process in $processes) {
    Stop-Process -Id $process.ProcessId -Force
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
  & $npm "install" "-g" (Join-Path $TargetPath "cli")
  if ($LASTEXITCODE -ne 0) { throw "$npm global install failed with exit code $LASTEXITCODE." }

  $packageRoot = Join-Path $globalRoot "9router"
  $entryPath = Join-Path $packageRoot "cli.js"
  $cmdShim = Join-Path (Split-Path $globalRoot -Parent) "9router.cmd"
  if (-not (Test-Path -LiteralPath $entryPath -PathType Leaf)) {
    throw "Global 9router install is incomplete: missing $entryPath"
  }
  if (-not (Test-Path -LiteralPath $cmdShim -PathType Leaf)) {
    throw "Global 9router install is incomplete: missing $cmdShim"
  }

  Write-Output "Installed 9router global package and verified cli.js and 9router.cmd."
}
