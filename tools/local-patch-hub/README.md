# Local patch hub

`project-OS-starter` owns local overlays and runtime launchers that must survive
OpenDesign and 9router updates.
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

Verification checks wrapper, handler, and compiled compact-fallback runtime signatures in both target and installed adapter bundles.

Apply source only in disposable verification targets; this avoids global Codex,
hook, daemon, and startup changes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1 -TargetRoot C:\path\to\LightMem2 -SkipInstall
```

To apply the overlay whenever the patched OpenDesign launcher starts, set `LIGHTMEM2_ROOT` or pass `-LightMem2Root` to `Start-OpenDesignPatched.ps1`.

Add a new versioned directory under `overlays/lightrsi-codex-hook-portable/` after rebasing the patch onto a new upstream commit. The current Codex compatibility overlay accepts explicit `/v1/responses/compact`, strips only historical `web_search_call` items on the outbound clone, tries upstream `/responses/compact`, and falls back to `/responses` on upstream `404`; ordinary `/responses` stays unchanged. Do not edit generated `dist/tokenpilot-codex-hook.cmd` files.

## 9router ownership

9router is maintained directly in the fork at
`https://github.com/longdang193/9router`. This patch hub no longer applies,
installs, launches, or verifies 9router overlays. Follow the fork's canonical
[`docs/UPSTREAM-SYNC.md`](https://github.com/longdang193/9router/blob/master/docs/UPSTREAM-SYNC.md)
for the one-time baseline, scheduled upstream synchronization, conflict
handling, privileged-path review, and rollback procedure.

The patch hub intentionally retains only the OpenDesign recovery and LightMem2
Codex hook overlay documented above. Do not add new 9router patch registries or
runtime launchers here.
