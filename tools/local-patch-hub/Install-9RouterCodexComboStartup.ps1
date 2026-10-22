[CmdletBinding()]
param(
  [string]$TargetRoot,
  [string]$TaskName = "ProjectOS-9RouterCodexCombo",
  [ValidateRange(0, 3600)][int]$DelaySeconds = 30,
  [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

function ConvertTo-CommandLineArgument {
  param([Parameter(Mandatory = $true)][string]$Value)
  return '"' + $Value.Replace('"', '\"') + '"'
}

if ($Uninstall) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
  Write-Output "Removed scheduled task $TaskName."
  exit 0
}

if ([string]::IsNullOrWhiteSpace($TargetRoot)) {
  throw "TargetRoot is required unless -Uninstall is supplied."
}

$targetPath = (Resolve-Path -LiteralPath $TargetRoot -ErrorAction Stop).Path
$launcherPath = Join-Path $PSScriptRoot "Start-9RouterCodexCombo.ps1"
if (-not (Test-Path -LiteralPath $launcherPath -PathType Leaf)) {
  throw "Combo launcher is missing: $launcherPath"
}
if (-not (Test-Path -LiteralPath (Join-Path $targetPath "tools\cgw-codex-shim\run.js") -PathType Leaf)) {
  throw "CGW Codex shim is missing under $targetPath"
}

$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
$arguments = @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  (ConvertTo-CommandLineArgument $launcherPath),
  "-TargetRoot",
  (ConvertTo-CommandLineArgument $targetPath)
) -join " "
$action = New-ScheduledTaskAction -Execute $powershell -Argument $arguments -WorkingDirectory $targetPath
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$trigger.Delay = "PT${DelaySeconds}S"
$principal = New-ScheduledTaskPrincipal `
  -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
  -LogonType Interactive `
  -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -MultipleInstances IgnoreNew `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $action `
  -Trigger $trigger `
  -Principal $principal `
  -Settings $settings `
  -Description "Starts the Project OS 9router transport and diagnostic Chat shim after user logon; LightRSI and codex-chatgpt-web own their lifecycles." `
  -Force | Out-Null

Write-Output "Registered $TaskName for user logon with a ${DelaySeconds}s delay."
Write-Output "The task starts the combo launcher without installing or downgrading global 9router."
