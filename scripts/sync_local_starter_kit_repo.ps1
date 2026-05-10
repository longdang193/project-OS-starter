[CmdletBinding()]
param(
    [string]$KitRepoPath = "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit",
    [string]$OutputRoot = "generated_exports",
    [string]$ManifestPath = "repo_config/starter-kit-manifest.json",
    [string]$CommitMessage = "Sync starter kit from source repo",
    [switch]$Push,
    [switch]$NoPush,
    [switch]$AllowDirtySibling
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $root = git rev-parse --show-toplevel
    if (-not $root) {
        throw "Unable to resolve source repo root."
    }
    return $root.Trim()
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Command
    )

    Write-Host "==> $Label"
    Write-Host ("    " + ($Command -join " "))
    & $Command[0] $Command[1..($Command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Label"
    }
}

function Get-GitStatusLines {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoPath
    )

    $output = git -C $RepoPath status --short
    if (-not $output) {
        return @()
    }
    return @($output -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
}

function Assert-SiblingRepoReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoPath,
        [switch]$AllowDirty
    )

    if (-not (Test-Path -LiteralPath $RepoPath)) {
        throw "Sibling starter-kit repo not found: $RepoPath"
    }

    $gitDir = Join-Path $RepoPath ".git"
    if (-not (Test-Path -LiteralPath $gitDir)) {
        throw "Sibling path is not a git repo: $RepoPath"
    }

    if ($AllowDirty) {
        return
    }

    $statusLines = Get-GitStatusLines -RepoPath $RepoPath
    if ($statusLines.Count -gt 0) {
        $rendered = $statusLines -join "; "
        throw "Sibling repo has pre-existing dirty state. Re-run with -AllowDirtySibling only if intentional. Status: $rendered"
    }
}

function Sync-DirectoryMirror {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Generated starter-kit root not found: $Source"
    }
    if (-not (Test-Path -LiteralPath $Destination)) {
        throw "Sibling starter-kit repo path not found: $Destination"
    }

    $logPath = Join-Path $env:TEMP ("starter-kit-sync-" + [guid]::NewGuid().ToString() + ".log")
    $sourceNormalized = $Source.TrimEnd('\\')
    $destinationNormalized = $Destination.TrimEnd('\\')
    robocopy $sourceNormalized $destinationNormalized /MIR /XD ".git" /R:1 /W:1 /NFL /NDL /NP /LOG:$logPath | Out-Null
    $exitCode = $LASTEXITCODE
    if ($exitCode -ge 8) {
        $logText = Get-Content -Raw -LiteralPath $logPath
        throw "robocopy failed with exit code $exitCode. Log:`n$logText"
    }
}

function Invoke-GitPublish {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoPath,
        [Parameter(Mandatory = $true)]
        [string]$CommitMessage,
        [switch]$Push
    )

    $statusLines = Get-GitStatusLines -RepoPath $RepoPath
    if ($statusLines.Count -eq 0) {
        Write-Host "No sibling repo changes to commit."
        return
    }

    Write-Host "==> Stage sibling repo changes"
    git -C $RepoPath add -A
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to stage sibling repo changes."
    }

    $postAddStatus = Get-GitStatusLines -RepoPath $RepoPath
    if ($postAddStatus.Count -eq 0) {
        Write-Host "No staged sibling repo changes after add."
        return
    }

    Write-Host "==> Commit sibling repo changes"
    git -C $RepoPath commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to commit sibling repo changes."
    }

    if ($Push) {
        Write-Host "==> Push sibling repo main"
        git -C $RepoPath push origin main
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to push sibling repo main."
        }
    }
}

$repoRoot = Get-RepoRoot
$kitRoot = Join-Path $repoRoot $OutputRoot
$manifestFullPath = Join-Path $repoRoot $ManifestPath

Invoke-Step -Label "Validate repo config" -Command @("py", (Join-Path $repoRoot "scripts\validate_repo_config.py"))
Invoke-Step -Label "Sync agent adapters" -Command @("py", (Join-Path $repoRoot "scripts\sync_agent_adapters.py"))
Invoke-Step -Label "Validate repo contracts (fast)" -Command @("py", (Join-Path $repoRoot "scripts\validate_repo_contracts.py"), "--fast")
Invoke-Step -Label "Build starter kit" -Command @("py", (Join-Path $repoRoot "scripts\build_starter_kit.py"), "--repo-root", $repoRoot, "--manifest", $manifestFullPath, "--output-root", $kitRoot)

$manifest = Get-Content -Raw -LiteralPath $manifestFullPath | ConvertFrom-Json
$generatedKitRoot = Join-Path $kitRoot $manifest.outputRoot

Invoke-Step -Label "Validate generated starter kit" -Command @("py", (Join-Path $repoRoot "scripts\validate_starter_kit.py"), "--repo-root", $repoRoot, "--manifest", $manifestFullPath, "--kit-root", $generatedKitRoot)
Assert-SiblingRepoReady -RepoPath $KitRepoPath -AllowDirty:$AllowDirtySibling
Sync-DirectoryMirror -Source $generatedKitRoot -Destination $KitRepoPath
Invoke-Step -Label "Validate sibling parity" -Command @("py", (Join-Path $repoRoot "scripts\validate_starter_kit.py"), "--repo-root", $repoRoot, "--manifest", $manifestFullPath, "--kit-root", $generatedKitRoot, "--compare-kit-root", $KitRepoPath)

if (-not $NoPush) {
    Invoke-GitPublish -RepoPath $KitRepoPath -CommitMessage $CommitMessage -Push:$Push
}

Write-Host "Starter-kit sync complete."
Write-Host "Generated root: $generatedKitRoot"
Write-Host "Sibling repo: $KitRepoPath"
