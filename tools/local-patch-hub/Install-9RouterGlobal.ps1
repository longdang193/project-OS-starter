function Install-9RouterGlobal {
  param(
    [Parameter(Mandatory = $true)][string]$TargetPath,
    [switch]$AllowDowngrade
  )

  $npm = (Get-Command npm.cmd -ErrorAction Stop).Source
  $globalRoot = (& $npm "root" "-g" | Out-String).Trim()
  if ($LASTEXITCODE -ne 0) { throw "$npm global root lookup failed with exit code $LASTEXITCODE." }
  $globalBinRoot = Split-Path $globalRoot -Parent
  $targetPath = (Resolve-Path -LiteralPath $TargetPath -ErrorAction Stop).Path
  $git = (Get-Command git.exe -ErrorAction Stop).Source
  $targetPackagePath = Join-Path $targetPath "cli\package.json"
  if (-not (Test-Path -LiteralPath $targetPackagePath -PathType Leaf)) { throw "TargetPath is missing cli\package.json: $targetPath" }
  $targetPackage = Get-Content -Raw -LiteralPath $targetPackagePath | ConvertFrom-Json
  $targetVersion = [Version]$targetPackage.version
  $sourceCommit = (& $git -C $targetPath rev-parse HEAD 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch "^[0-9a-f]{40}$") { throw "TargetPath is not a Git checkout with a valid source commit: $targetPath" }
  function Get-PackageContentDigest {
    param([Parameter(Mandatory = $true)][string]$PackageRoot)
    $hashBuilder = [Text.StringBuilder]::new()
    $packageRootPath = (Resolve-Path -LiteralPath $PackageRoot -ErrorAction Stop).Path
    foreach ($file in @(Get-ChildItem -LiteralPath $packageRootPath -Recurse -File | Where-Object { $_.Name -ne "9router-install.json" } | Sort-Object FullName)) {
      $relativePath = [IO.Path]::GetRelativePath($packageRootPath, $file.FullName).Replace([IO.Path]::DirectorySeparatorChar, "/")
      $fileHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
      [void]$hashBuilder.Append($relativePath).Append([Environment]::NewLine).Append($fileHash).Append([Environment]::NewLine)
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes($hashBuilder.ToString())
    return ([Security.Cryptography.SHA256]::HashData($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
  }
  $installedPackagePath = Join-Path $globalRoot "9router\package.json"
  $packageRoot = Join-Path $globalRoot "9router"
  $cmdShim = Join-Path $globalBinRoot "9router.cmd"

  function Test-ExistingGlobalInstall {
    param(
      [Parameter(Mandatory = $true)][string]$PackageRoot,
      [Parameter(Mandatory = $true)][string]$CommandShim,
      [Parameter(Mandatory = $true)][string]$ExpectedVersion,
      [Parameter(Mandatory = $true)][string]$ExpectedSourceCommit
    )
    if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot "package.json") -PathType Leaf) -or -not (Test-Path -LiteralPath $CommandShim -PathType Leaf)) { return $false }
    try {
      $packageItem = Get-Item -LiteralPath $PackageRoot -Force
      if ($packageItem.LinkType) { return $false }
      $installedPackage = Get-Content -Raw -LiteralPath (Join-Path $PackageRoot "package.json") | ConvertFrom-Json
      if ([string]$installedPackage.version -ne $ExpectedVersion) { return $false }
      if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot "cli.js") -PathType Leaf)) { return $false }
      $installedAppPath = Join-Path $PackageRoot "app"
      if (-not (Test-Path -LiteralPath (Join-Path $installedAppPath "server.js") -PathType Leaf) -and -not (Test-Path -LiteralPath (Join-Path $installedAppPath "custom-server.js") -PathType Leaf)) { return $false }
      $receiptPath = Join-Path $PackageRoot "9router-install.json"
      if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) { return $false }
      $receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
      if ([int]$receipt.schemaVersion -ne 1 -or [string]$receipt.packageVersion -ne $ExpectedVersion -or [string]$receipt.sourceCommit -ne $ExpectedSourceCommit -or [string]$receipt.packageContentDigest -notmatch "^[0-9a-f]{64}$") { return $false }
      if ((Get-PackageContentDigest -PackageRoot $PackageRoot) -ne [string]$receipt.packageContentDigest) { return $false }
      $versionOutput = (& $CommandShim "--version" 2>&1 | Out-String).Trim()
      return $LASTEXITCODE -eq 0 -and $versionOutput -eq $ExpectedVersion
    } catch { return $false }
  }

  if (Test-ExistingGlobalInstall -PackageRoot $packageRoot -CommandShim $cmdShim -ExpectedVersion ([string]$targetPackage.version) -ExpectedSourceCommit $sourceCommit) {
    Write-Output "Global 9router package already matches version $($targetPackage.version) and verified content digest; skipping rebuild and replacement."
    return
  }

  if ((Test-Path -LiteralPath $installedPackagePath -PathType Leaf) -and -not $AllowDowngrade) {
    $installedPackage = Get-Content -Raw -LiteralPath $installedPackagePath | ConvertFrom-Json
    $installedVersion = [Version]$installedPackage.version
    if ($targetVersion -lt $installedVersion) {
      throw "Refusing to downgrade global 9router from $installedVersion to $targetVersion. Pass -AllowDowngrade only for an intentional older-version install."
    }
  }

  function Get-9RouterProcesses {
    @(Get-CimInstance Win32_Process | Where-Object {
      $commandLine = [string]$_.CommandLine
      ($_.Name -eq "node.exe" -and $commandLine -match "(?i)node_modules[\\/]+9router[\\/]+(cli\.js|app[\\/]+custom-server\.js)") -or
      ($_.Name -eq "cmd.exe" -and $commandLine -match "(?i)9router\.cmd") -or
      ($_.Name -in @("powershell.exe", "pwsh.exe") -and $commandLine -match "(?i)node_modules[\\/]+9router[\\/]+src[\\/]+cli[\\/]+tray[\\/]tray\.ps1")
    })
  }

  function Restore-9RouterGlobal {
    param(
      [Parameter(Mandatory = $true)][string]$RollbackRoot,
      [Parameter(Mandatory = $true)][string]$PackageRoot,
      [Parameter(Mandatory = $true)][string]$GlobalBinRoot
    )

    $failedRoot = Join-Path $RollbackRoot "failed"
    $failedPackageRoot = Join-Path $failedRoot "package"
    $failedBinRoot = Join-Path $failedRoot "bin"
    $rollbackPackageRoot = Join-Path $RollbackRoot "package"
    $rollbackBinRoot = Join-Path $RollbackRoot "bin"
    New-Item -ItemType Directory -Path $failedRoot, $failedBinRoot -Force | Out-Null

    if (Test-Path -LiteralPath $PackageRoot) {
      Move-Item -LiteralPath $PackageRoot -Destination $failedPackageRoot -Force
    }
    foreach ($binName in @("9router", "9router.cmd", "9router.ps1")) {
      $binPath = Join-Path $GlobalBinRoot $binName
      if (Test-Path -LiteralPath $binPath) {
        Move-Item -LiteralPath $binPath -Destination (Join-Path $failedBinRoot $binName) -Force
      }
      $rollbackBinPath = Join-Path $rollbackBinRoot $binName
      if (Test-Path -LiteralPath $rollbackBinPath) {
        Move-Item -LiteralPath $rollbackBinPath -Destination $binPath -Force
      }
    }
    if (Test-Path -LiteralPath $rollbackPackageRoot) {
      Move-Item -LiteralPath $rollbackPackageRoot -Destination $PackageRoot -Force
    }
  }

  function Ensure-NpmDependencies {
    param(
      [Parameter(Mandatory = $true)][string]$WorkingDirectory,
      [Parameter(Mandatory = $true)][string]$MarkerPath
    )

    if (Test-Path -LiteralPath $MarkerPath -PathType Leaf) { return }

    $dependencyLog = Join-Path ([IO.Path]::GetTempPath()) ("9router-deps-" + [Guid]::NewGuid().ToString("N") + ".log")
    $dependencyErrorLog = Join-Path ([IO.Path]::GetTempPath()) ("9router-deps-" + [Guid]::NewGuid().ToString("N") + ".err.log")
    $dependencyProcess = Start-Process -FilePath $npm -ArgumentList @("install", "--no-audit", "--no-fund", "--ignore-scripts") -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $dependencyLog -RedirectStandardError $dependencyErrorLog
    $dependencyExitCode = $dependencyProcess.ExitCode
    if ($dependencyExitCode -ne 0) {
      $dependencyDetails = @()
      if (Test-Path -LiteralPath $dependencyErrorLog -PathType Leaf) { $dependencyDetails += @(Get-Content -LiteralPath $dependencyErrorLog -Tail 20) }
      if (Test-Path -LiteralPath $dependencyLog -PathType Leaf) { $dependencyDetails += @(Get-Content -LiteralPath $dependencyLog -Tail 20) }
      throw "$npm install failed in $WorkingDirectory with exit code $dependencyExitCode. $($dependencyDetails -join ' ')"
    }
    Remove-Item -LiteralPath $dependencyLog, $dependencyErrorLog -Force -ErrorAction SilentlyContinue
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

  Ensure-NpmDependencies -WorkingDirectory $TargetPath -MarkerPath (Join-Path $targetPath "node_modules\next\package.json")
  Ensure-NpmDependencies -WorkingDirectory (Join-Path $targetPath "cli") -MarkerPath (Join-Path $TargetPath "cli\node_modules\esbuild\package.json")

  $cliPath = Join-Path $TargetPath "cli"
  $buildLog = Join-Path ([IO.Path]::GetTempPath()) ("9router-build-" + [Guid]::NewGuid().ToString("N") + ".log")
  $buildErrorLog = Join-Path ([IO.Path]::GetTempPath()) ("9router-build-" + [Guid]::NewGuid().ToString("N") + ".err.log")
  $buildProcess = Start-Process -FilePath $npm -ArgumentList @("run", "build") -WorkingDirectory $cliPath -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $buildLog -RedirectStandardError $buildErrorLog
  $buildExitCode = $buildProcess.ExitCode
  if ($buildExitCode -ne 0) {
    $buildDetails = @()
    if (Test-Path -LiteralPath $buildErrorLog -PathType Leaf) { $buildDetails += @(Get-Content -LiteralPath $buildErrorLog -Tail 20) }
    if (Test-Path -LiteralPath $buildLog -PathType Leaf) { $buildDetails += @(Get-Content -LiteralPath $buildLog -Tail 20) }
    throw "$npm build failed with exit code $buildExitCode. $($buildDetails -join ' ')"
  }
  Remove-Item -LiteralPath $buildLog, $buildErrorLog -Force -ErrorAction SilentlyContinue
  $builtAppPath = Join-Path $targetPath "cli\app"
  if (-not (Test-Path -LiteralPath (Join-Path $builtAppPath "server.js") -PathType Leaf) -and
      -not (Test-Path -LiteralPath (Join-Path $builtAppPath "custom-server.js") -PathType Leaf)) {
    throw "9router build is incomplete: missing cli\app\server.js and cli\app\custom-server.js."
  }
  $packageStage = Join-Path ([IO.Path]::GetTempPath()) ("9router-package-" + [Guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $packageStage | Out-Null
  $rollbackRoot = Join-Path ([IO.Path]::GetTempPath()) ("9router-rollback-" + [Guid]::NewGuid().ToString("N"))
  $packageRoot = Join-Path $globalRoot "9router"
  $rollbackPackageRoot = Join-Path $rollbackRoot "package"
  $rollbackBinRoot = Join-Path $rollbackRoot "bin"
  $rollbackReady = $false
  try {
    Push-Location -LiteralPath (Join-Path $TargetPath "cli")
    try {
      $packLog = Join-Path $packageStage "npm-pack.log"
      $packErrorLog = Join-Path $packageStage "npm-pack.err.log"
      $packProcess = Start-Process -FilePath $npm -ArgumentList @("pack", "--ignore-scripts", "--pack-destination", $packageStage) -WorkingDirectory (Join-Path $TargetPath "cli") -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $packLog -RedirectStandardError $packErrorLog
      $packExitCode = $packProcess.ExitCode
    } finally {
      Pop-Location
    }
    $packageFile = @(Get-ChildItem -LiteralPath $packageStage -Filter "9router-*.tgz" -File) | Select-Object -First 1
    if ($null -eq $packageFile) {
      $packDetails = @()
      if (Test-Path -LiteralPath $packErrorLog -PathType Leaf) { $packDetails += @(Get-Content -LiteralPath $packErrorLog -Tail 20) }
      if (Test-Path -LiteralPath $packLog -PathType Leaf) { $packDetails += @(Get-Content -LiteralPath $packLog -Tail 20) }
      throw "$npm pack failed with exit code $packExitCode and created no package archive. $($packDetails -join ' ')"
    }
    if ($packExitCode -ne 0) { Write-Warning "$npm pack returned exit code $packExitCode after creating $($packageFile.Name); continuing with the verified archive." }
    try {
      New-Item -ItemType Directory -Path $rollbackRoot, $rollbackBinRoot -Force | Out-Null
      if (Test-Path -LiteralPath $packageRoot) {
        $packageItem = Get-Item -LiteralPath $packageRoot -Force
        if ($packageItem.LinkType) {
          throw "Refusing to replace linked global 9router package: $packageRoot"
        }
        Move-Item -LiteralPath $packageRoot -Destination $rollbackPackageRoot -Force
      }
      foreach ($binName in @("9router", "9router.cmd", "9router.ps1")) {
        $binPath = Join-Path $globalBinRoot $binName
        if (Test-Path -LiteralPath $binPath) {
          Move-Item -LiteralPath $binPath -Destination (Join-Path $rollbackBinRoot $binName) -Force
        }
      }
      $rollbackReady = $true

      & $npm "install" "-g" "--force" $packageFile.FullName
      if ($LASTEXITCODE -ne 0) { throw "$npm global install failed with exit code $LASTEXITCODE." }

      $packageItem = Get-Item -LiteralPath $packageRoot -ErrorAction SilentlyContinue
      if ($null -eq $packageItem -or $packageItem.LinkType) {
        throw "Global 9router install is not a copied package directory: $packageRoot"
      }
      $entryPath = Join-Path $packageRoot "cli.js"
      $cmdShim = Join-Path $globalBinRoot "9router.cmd"
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
      $receipt = [ordered]@{
        schemaVersion = 1
        packageVersion = [string]$targetPackage.version
        sourceCommit = $sourceCommit
        packageContentDigest = Get-PackageContentDigest -PackageRoot $packageRoot
      }
      $receiptStage = Join-Path $packageStage "9router-install.json"
      [IO.File]::WriteAllText($receiptStage, ($receipt | ConvertTo-Json -Depth 5) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
      Move-Item -LiteralPath $receiptStage -Destination (Join-Path $packageRoot "9router-install.json") -Force
    } catch {
      $installError = $_
      $hasRollbackArtifacts = $rollbackReady -or
        (Test-Path -LiteralPath $rollbackPackageRoot) -or
        (@(Get-ChildItem -LiteralPath $rollbackBinRoot -File -ErrorAction SilentlyContinue).Count -gt 0)
      if ($hasRollbackArtifacts) {
        try {
          Restore-9RouterGlobal -RollbackRoot $rollbackRoot -PackageRoot $packageRoot -GlobalBinRoot $globalBinRoot
        } catch {
          throw "Global 9router install failed: $($installError.Exception.Message) Rollback failed: $($_.Exception.Message). Recovery artifacts remain at $rollbackRoot."
        }
      }
      throw $installError
    }

    if (Test-Path -LiteralPath $rollbackRoot) {
      Remove-Item -LiteralPath $rollbackRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
  } finally {
    if (Test-Path -LiteralPath $packageStage) {
      Remove-Item -LiteralPath $packageStage -Recurse -Force -ErrorAction SilentlyContinue
    }
  }

  Write-Output "Installed 9router global package and verified cli.js, 9router.cmd, version $versionOutput, source commit $sourceCommit, and content digest."
}
