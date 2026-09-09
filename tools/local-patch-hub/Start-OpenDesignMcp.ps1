[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Get-RemainingMilliseconds {
    param([long]$DeadlineTicks)
    $remainingTicks = $DeadlineTicks - [Diagnostics.Stopwatch]::GetTimestamp()
    if ($remainingTicks -le 0) { return 0 }
    return [int][Math]::Min(
        2147483647,
        [Math]::Ceiling($remainingTicks * 1000 / [Diagnostics.Stopwatch]::Frequency)
    )
}

function Find-OpenDesignDaemon {
    param([long]$DeadlineTicks)
    $pipes = @(Get-ChildItem "\\.\pipe\" -ErrorAction SilentlyContinue |
        Where-Object Name -like "open-design-*")
    foreach ($pipeInfo in $pipes) {
        $pipe = $null
        try {
            $remaining = Get-RemainingMilliseconds $DeadlineTicks
            if ($remaining -le 0) { return $null }
            $pipe = [IO.Pipes.NamedPipeClientStream]::new(
                ".",
                $pipeInfo.Name,
                [IO.Pipes.PipeDirection]::InOut,
                [IO.Pipes.PipeOptions]::None
            )
            $pipe.Connect([int][Math]::Min(1000, $remaining))
            $writer = [IO.StreamWriter]::new($pipe)
            $writer.AutoFlush = $true
            $writer.WriteLine('{"type":"sidecar:describe"}')
            $reader = [IO.StreamReader]::new($pipe)
            $read = $reader.ReadLineAsync()
            $remaining = Get-RemainingMilliseconds $DeadlineTicks
            if ($remaining -le 0 -or -not $read.Wait([int][Math]::Min(1000, $remaining))) { continue }
            $response = $read.Result | ConvertFrom-Json
            if ($response.ok -and $response.result.stamp.app -eq "daemon") {
                $pipe.Dispose()
                $pipe = $null
                $statusPipe = $null
                try {
                    $statusPipe = [IO.Pipes.NamedPipeClientStream]::new(
                        ".",
                        $pipeInfo.Name,
                        [IO.Pipes.PipeDirection]::InOut,
                        [IO.Pipes.PipeOptions]::None
                    )
                    $remaining = Get-RemainingMilliseconds $DeadlineTicks
                    if ($remaining -le 0) { continue }
                    $statusPipe.Connect([int][Math]::Min(1000, $remaining))
                    $statusWriter = [IO.StreamWriter]::new($statusPipe)
                    $statusWriter.AutoFlush = $true
                    $statusWriter.WriteLine('{"type":"sidecar:status"}')
                    $statusReader = [IO.StreamReader]::new($statusPipe)
                    $statusRead = $statusReader.ReadLineAsync()
                    $remaining = Get-RemainingMilliseconds $DeadlineTicks
                    if ($remaining -le 0 -or -not $statusRead.Wait([int][Math]::Min(1000, $remaining))) { continue }
                    $status = $statusRead.Result | ConvertFrom-Json
                    if ($status.ok -and $status.result.state -eq "running" -and
                        $status.result.url -is [string] -and $status.result.url.Length -gt 0) {
                        return [pscustomobject]@{
                            Endpoint = "\\.\pipe\$($pipeInfo.Name)"
                            DataDir = $response.result.resources.dataRoot
                        }
                    }
                } finally {
                    if ($null -ne $statusPipe) {
                        $statusPipe.Dispose()
                    }
                }
            }
        } catch {
        } finally {
            if ($null -ne $pipe) {
                $pipe.Dispose()
            }
        }
    }
    return $null
}

$exe = Join-Path $env:LOCALAPPDATA "Programs\Open Design\Open Design.exe"
$cli = Join-Path $env:LOCALAPPDATA "Programs\Open Design\resources\app\prebundled\daemon\daemon-cli.mjs"
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Open Design executable not found: $exe" }
if (-not (Test-Path -LiteralPath $cli -PathType Leaf)) { throw "Open Design daemon CLI not found: $cli" }

$startupBudgetSeconds = 90
if ($env:OPEN_DESIGN_MCP_STARTUP_TIMEOUT_SEC) {
    $parsedBudget = 0
    if (-not [int]::TryParse($env:OPEN_DESIGN_MCP_STARTUP_TIMEOUT_SEC, [ref]$parsedBudget)) {
        throw "OPEN_DESIGN_MCP_STARTUP_TIMEOUT_SEC must be an integer."
    }
    $startupBudgetSeconds = $parsedBudget
}
if ($startupBudgetSeconds -lt 10) {
    throw "Open Design MCP startup timeout must be at least 10 seconds."
}
$readinessBudgetSeconds = $startupBudgetSeconds - 5
$deadlineTicks = [Diagnostics.Stopwatch]::GetTimestamp() +
    ($startupBudgetSeconds * [Diagnostics.Stopwatch]::Frequency)
$readinessDeadlineTicks = $deadlineTicks - (5 * [Diagnostics.Stopwatch]::Frequency)
$bootstrapMutex = [System.Threading.Mutex]::new($false, "Local\OpenDesignMcpBootstrap")
$lockAcquired = $false
$runtime = $null
try {
    $runtime = Find-OpenDesignDaemon $readinessDeadlineTicks
    if ($null -eq $runtime) {
        $remaining = Get-RemainingMilliseconds $deadlineTicks
        if ($remaining -le 0) { throw "Open Design MCP startup deadline expired." }
        try {
            $lockAcquired = $bootstrapMutex.WaitOne([TimeSpan]::FromMilliseconds($remaining))
        } catch [System.Threading.AbandonedMutexException] {
            $lockAcquired = $true
        }
        if (-not $lockAcquired) { throw "Open Design MCP bootstrap lock timed out." }

        $runtime = Find-OpenDesignDaemon $readinessDeadlineTicks
        if ($null -eq $runtime) {
            $remaining = Get-RemainingMilliseconds $readinessDeadlineTicks
            if ($remaining -le 0) { throw "Open Design MCP readiness deadline expired before daemon start." }
            Start-Process -FilePath $exe -ArgumentList "--headless" -WindowStyle Hidden
            do {
                Start-Sleep -Milliseconds 250
                $runtime = Find-OpenDesignDaemon $readinessDeadlineTicks
            } while ($null -eq $runtime -and (Get-RemainingMilliseconds $readinessDeadlineTicks) -gt 0)
        }
    }
} finally {
    if ($lockAcquired) { $bootstrapMutex.ReleaseMutex() }
    $bootstrapMutex.Dispose()
}
if ($null -eq $runtime) {
    throw "Open Design daemon sidecar did not become ready within $readinessBudgetSeconds seconds."
}

$env:ELECTRON_RUN_AS_NODE = "1"
$env:OD_DATA_DIR = $runtime.DataDir
$env:OD_MCP_BOOTSTRAP_ARGS = '["--headless"]'
$env:OD_MCP_BOOTSTRAP_COMMAND = $exe
$env:OD_SIDECAR_CLIENT_ENDPOINT = $runtime.Endpoint
& $exe $cli "mcp"
exit $LASTEXITCODE
