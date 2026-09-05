# OpenDesign local patch hub

`project-OS-starter` owns local overlays that must survive OpenDesign updates.
Each overlay is keyed by exact target Git `HEAD`; unknown bases stop without changes.

## OpenDesign MCP recovery

Start OpenDesign through the patched launcher after installation or update:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/open-design-local-patch/Start-OpenDesignPatched.ps1
```

Launcher no longer force-stops an existing OpenDesign process. If an existing
desktop owner restart would interrupt a queued or running run, restart is
deferred and the new launcher exits; retry after that run reaches a terminal
state.

Verify Codex sees the configured server:

```powershell
codex mcp get open-design
```

If daemon and web pipes exist but MCP reports `Transport closed`, reload Codex
app-server. Do not change project artifacts or run state.

## LightMem2 Codex hook overlay

Apply and install login-time reconciliation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/open-design-local-patch/Apply-LightMem2CodexOverlay.ps1 -TargetRoot C:\path\to\LightMem2 -InstallStartup
```

Run verification without changing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/open-design-local-patch/Apply-LightMem2CodexOverlay.ps1 -TargetRoot C:\path\to\LightMem2 -VerifyOnly
```

To apply the overlay whenever the patched OpenDesign launcher starts, set `LIGHTMEM2_ROOT` or pass `-LightMem2Root` to `Start-OpenDesignPatched.ps1`.

Add a new versioned directory under `overlays/lightrsi-codex-hook-portable/` after rebasing the patch onto a new upstream commit. Do not edit generated `dist/tokenpilot-codex-hook.cmd` files.
