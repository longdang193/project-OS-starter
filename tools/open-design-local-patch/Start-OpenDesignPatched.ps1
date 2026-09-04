[CmdletBinding()]
param(
    [string]$LightMem2Root = $env:LIGHTMEM2_ROOT,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$OpenDesignArgs
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $scriptRoot "Apply-OpenDesignPatch.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not [string]::IsNullOrWhiteSpace($LightMem2Root)) {
    & (Join-Path $scriptRoot "Apply-LightMem2CodexOverlay.ps1") -TargetRoot $LightMem2Root
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$env:OD_DESKTOP_LOG_ECHO = "0"
$exe = Join-Path $env:LOCALAPPDATA "Programs\Open Design\Open Design.exe"
$existing = @(Get-Process -Name 'Open Design' -ErrorAction SilentlyContinue)
if ($existing.Count -gt 0) {
    $existing | Stop-Process -Force
    Start-Sleep -Seconds 2
    if (Get-Process -Name 'Open Design' -ErrorAction SilentlyContinue) {
        throw "OpenDesign processes remain after clean restart."
    }
}
if ($OpenDesignArgs.Count -gt 0) {
    Start-Process -FilePath $exe -ArgumentList $OpenDesignArgs
} else {
    Start-Process -FilePath $exe
}
