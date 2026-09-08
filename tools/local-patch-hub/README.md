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

## 9router security overlay

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
