# Local patch hub

`project-OS-starter` owns local overlays that must survive OpenDesign updates.
Each overlay is keyed by exact target Git `HEAD`; unknown bases stop without changes.

## OpenDesign MCP recovery

Start OpenDesign through the patched launcher after installation or update:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Start-OpenDesignPatched.ps1
```

Launcher no longer force-stops an existing OpenDesign process. If an existing
desktop owner restart would interrupt a queued or running run, restart is
deferred and the new launcher exits; retry after that run reaches a terminal
state.

Verify Codex sees the configured server:

```powershell
codex mcp get open-design
```

Codex launches `Start-OpenDesignMcp.ps1`. It discovers the current daemon
sidecar pipe and data directory from the installed runtime, so OpenDesign
updates do not leave stale endpoint values in Codex config.
The launcher disables OpenDesign MCP's idle stdio shutdown, so an idle Codex
session does not later receive `Transport closed` from a dead MCP child.

Bootstrap probes for a healthy daemon before taking its named Windows mutex.
Discovery accepts a sidecar only after `sidecar:describe` identifies the
daemon and a fresh named-pipe connection receives `sidecar:status` reporting
`state=running` with a non-empty URL. OpenDesign sidecar IPC is request-scoped;
do not reuse the `describe` connection for readiness status. Cold
starts recheck after lock acquisition, and discovery, lock wait, daemon
startup, and readiness share one monotonic deadline. The current local
contract is `startup_timeout_sec = 90`, with a five-second final MCP-handshake
margin. Set `OPEN_DESIGN_MCP_STARTUP_TIMEOUT_SEC` only when Codex MCP timeout
is changed to the same value.

After installing or updating OpenDesign, refresh Codex registration from the
running local daemon. Use its current URL from OpenDesign MCP settings:

```powershell
$exe = Join-Path $env:LOCALAPPDATA "Programs\Open Design\Open Design.exe"
$cli = Join-Path $env:LOCALAPPDATA "Programs\Open Design\resources\app\prebundled\daemon\daemon-cli.mjs"
& $exe $cli mcp install codex --json --daemon-url <running-daemon-url>
```

If daemon and web pipes exist but MCP reports `Transport closed`, reload Codex
app-server. Do not change project artifacts or run state.

## LightMem2 Codex hook overlay

Apply and install login-time reconciliation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1 -TargetRoot C:\path\to\LightMem2 -InstallStartup
```

Run verification without changing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1 -TargetRoot C:\path\to\LightMem2 -VerifyOnly
```

To apply the overlay whenever the patched OpenDesign launcher starts, set `LIGHTMEM2_ROOT` or pass `-LightMem2Root` to `Start-OpenDesignPatched.ps1`.

Add a new versioned directory under `overlays/lightrsi-codex-hook-portable/` after rebasing the patch onto a new upstream commit. Do not edit generated `dist/tokenpilot-codex-hook.cmd` files.

## 9router overlays

Use a clean checkout that tracks upstream; keep fork experiments separate:

```powershell
git clone https://github.com/decolua/9router.git C:\path\to\9router-upstream
```

After updating that checkout from upstream, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterSecurityOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -InstallGlobal
```

The script reapplies the unmerged security fix with Git 3-way merge. It stops on conflicts instead of leaving a partial patch. Verify without changing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterSecurityOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -VerifyOnly
```

When upstream changes the patched files, create a new base directory under `overlays/9router-security/` and rebase the patch there. Keep old overlays for existing checkouts.

Apply the Responses API output compatibility overlay separately:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -InstallGlobal
```

Verify update safety without changing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -VerifyOnly
```

The Responses overlay fixes `response.completed.response.output`, which is required by `wire_api = "responses"`, across translated and native same-format passthrough streams. The reconciler accepts exact bases, already-applied overlays, upstream-native fixes, and clean Git 3-way rebases; whitespace-only line-ending changes do not block application. It checks every patched runtime path before treating an existing install as complete, so older partial overlays receive the missing fix. Rebase verification applies into a temporary Git index, so conflict checks do not mutate the target. Real 3-way application requires no tracked local changes and stops before mutation when preflight fails. `-InstallGlobal` stops running 9router Node processes before npm replacement, refuses to downgrade an installed newer version, then verifies global `cli.js` and `9router.cmd`; relaunch with `9router --tray --skip-update -p 20128`. Use `-AllowDowngrade` only for intentional older-version installs. When upstream changes a patched file, add a new exact-base directory under `overlays/9router-responses/` and rebase the patch there. Keep old overlays for existing checkouts.
