[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Find-OpenDesignDaemon {
    $pipes = @(Get-ChildItem "\\.\pipe\" -ErrorAction SilentlyContinue |
        Where-Object Name -like "open-design-*")
    foreach ($pipeInfo in $pipes) {
        $pipe = $null
        try {
            $pipe = [IO.Pipes.NamedPipeClientStream]::new(
                ".",
                $pipeInfo.Name,
                [IO.Pipes.PipeDirection]::InOut,
                [IO.Pipes.PipeOptions]::None
            )
            $pipe.Connect(1000)
            $writer = [IO.StreamWriter]::new($pipe)
            $writer.AutoFlush = $true
            $writer.WriteLine('{"type":"sidecar:describe"}')
            $reader = [IO.StreamReader]::new($pipe)
            $read = $reader.ReadLineAsync()
            if (-not $read.Wait(1000)) { continue }
            $response = $read.Result | ConvertFrom-Json
            if ($response.ok -and $response.result.stamp.app -eq "daemon") {
                return [pscustomobject]@{
                    Endpoint = "\\.\pipe\$($pipeInfo.Name)"
                    DataDir = $response.result.resources.dataRoot
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
$bootstrapMutex = [System.Threading.Mutex]::new($false, "Local\OpenDesignMcpBootstrap")
$lockAcquired = $false
$runtime = $null
try {
    try {
        $lockAcquired = $bootstrapMutex.WaitOne([TimeSpan]::FromSeconds($startupBudgetSeconds))
    } catch [System.Threading.AbandonedMutexException] {
        $lockAcquired = $true
    }
    if (-not $lockAcquired) { throw "Open Design MCP bootstrap lock timed out." }

    $runtime = Find-OpenDesignDaemon
    if ($null -eq $runtime) {
        Start-Process -FilePath $exe -ArgumentList "--headless" -WindowStyle Hidden
        $deadline = (Get-Date).AddSeconds($readinessBudgetSeconds)
        do {
            Start-Sleep -Milliseconds 250
            $runtime = Find-OpenDesignDaemon
        } while ($null -eq $runtime -and (Get-Date) -lt $deadline)
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
