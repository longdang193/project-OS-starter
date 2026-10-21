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

When upstream changes the patched files, create a new base directory under `overlays/9router-security/` and rebase the patch there. Current security bases include `eb712ca8` (`0.5.69`) and `ce4460ef` (`0.5.99`). Keep old overlays for existing checkouts.

Apply the Responses API output compatibility overlay separately:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -InstallGlobal
```

Verify update safety without changing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -VerifyOnly
```

Current 9router Responses overlays cover `0.5.65` (`e0be4111`), `0.5.69`
(`eb712ca8`), and `0.5.99` (`ce4460ef`). The Responses overlay fixes
`response.completed.response.output`, preserves upstream SSE errors instead of
inventing empty completion events, and keeps Codex compact URL selection
request-local. The reconciler accepts exact bases, already-applied overlays,
upstream-native fixes, and clean Git 3-way rebases; whitespace-only line-ending
changes do not block application. It checks every patched runtime path before
treating an existing install as complete, so older partial overlays receive the
missing fix. Rebase verification applies into a temporary Git index, so conflict
checks do not mutate the target. `-InstallGlobal` stops and waits for all 9router
Node processes, validates `cli\app` before replacement, packs the CLI before
global install so npm cannot leave a Junction to a disposable worktree, rejects
linked global packages, then verifies global `cli.js`, standalone app files,
`9router.cmd`, and executable version; relaunch with
`9router --tray --skip-update -p 20128 -H 127.0.0.1`. Use `-AllowDowngrade` only for
intentional older-version installs. When upstream changes a patched file, add a
new exact-base directory under `overlays/9router-responses/` and rebase the patch
there. Keep old overlays for existing checkouts.

## 9router + CGW combo runtime

The CGW combo requires the exact `0.5.104` runtime overlay below. The overlay
adds the CGW Chat shim, real inference-based model tests, and per-request
`reasoning_effort` support. The shim translates the public Chat Completions
request into a direct authenticated CGW Responses request; it does not launch
`codex exec` and must not route `cgw/*` through the 9router Codex provider.

Apply and install the pinned runtime overlay from a clean `v0.5.104` checkout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1 `
  -TargetRoot C:\path\to\9router-v0.5.104 `
  -InstallGlobal
```

The overlay refuses unknown commits and versions, refuses downgrade unless
`-AllowDowngrade` is explicit, and stops before changing files on a conflict.
After the package, entry point, standalone app, command shim, and version are
verified, the installer atomically writes `9router-cgw-overlay.json` into the
global package. `Start-9RouterCodexCombo.ps1` requires that receipt instead of
searching compiled JavaScript for fragile source markers. If `9router.cmd` or
`cli.js` is missing, rerun the same `Apply-9RouterCgwOverlay.ps1 -InstallGlobal`
command; it can repair the incomplete installation without first running the
upstream `npm install -g 9router` package.

Keep the local environment in the target checkout at
`C:\path\to\9router\.env`. The shim loads that file automatically; never
commit it or print its values. Configure the dedicated shim key, stable model
aliases, the CGW loopback base URL, and one local-only CGW bearer source:

```dotenv
CGW_SHIM_API_KEY=use-a-dedicated-local-key
CGW_SHIM_MODEL_ALIASES_JSON={"gpt-6.1-sol":"chatgpt-web/gpt-6-sol","gpt-5.6-sol":"chatgpt-web/gpt-5.6-sol"}
CGW_SHIM_CGW_BASE_URL=http://127.0.0.1:17841/v1
CGW_SHIM_CGW_BEARER_FILE=C:\\Users\\me\\.codex\\cgw-bearer.env
```

CGW aliases must target `chatgpt-web/*`; raw `gpt-*` targets enter the native Codex passthrough and can consume Codex quota. A regular `sk-*` API key is not a CGW bearer. The launcher refuses to start a
shim with no bearer source, so an incorrectly configured installation cannot
silently consume Codex quota through a native fallback.

Start both loopback services against the already-installed global 9router:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Start-9RouterCodexCombo.ps1 `
  -TargetRoot C:\path\to\9router
```

To avoid rerunning the launcher after every Windows restart, register a
per-user logon task once. This starts the same launcher 30 seconds after each
Windows logon and does not store `.env` values or API keys in Task Scheduler:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Start-9RouterCodexCombo.ps1 `
  -TargetRoot C:\path\to\9router `
  -InstallStartup
```

The launcher verifies 9router health and the shim listener. Model tests still
send a real `POST http://127.0.0.1:20129/v1/chat/completions` prompt; they do
not use a catalog-only shortcut. The shim then sends `POST
http://127.0.0.1:17841/v1/responses` with the requested model and optional
reasoning effort.

Use the existing startup uninstall command to remove the automatic task:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Install-9RouterCodexComboStartup.ps1 `
  -Uninstall
```

Keep the global runtime on the current release (`0.5.104` at this gate) before
starting the combo. The overlay installer owns replacement and rollback; use
`-InstallGlobal` to repair or refresh it. Do not use `-AllowDowngrade` for the
combo.
Apply the attribution persistence overlay separately:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterAttributionOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -InstallGlobal
```

Verify update safety without changing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterAttributionOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -VerifyOnly
```

The attribution overlays target `0.5.69` (`eb712ca8`) and `0.5.99`
(`ce4460ef`). The current `0.5.99` overlay is rebased over the newer
`toolNameMap` and schema layout while preserving
`x-lightrsi-request-id`, `x-lightrsi-provider-attempt-id`, and the router-owned
immutable `routerRecordId` through usage history and request details, including
streaming, forced-SSE, success, and failure paths. The reconciler accepts the
exact base, an already-applied overlay, and a clean Git 3-way rebase; it stops
on conflicts or unrelated tracked changes instead of leaving a partial patch.
When upstream changes a patched file, add a new exact-base directory under
`overlays/9router-attribution/` and rebase the patch there. Keep old overlays
for existing checkouts. Live economics remain blocked until deployed,
authenticated ID-join proof passes.

## 9router Codex opaque relay overlay

The Codex opaque relay is a separate exact-base overlay for the `0.5.99`
9router source at commit `ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8`. It adds
`/v1/chatgpt-web/responses` without changing the existing `/v1/responses`
route, normal provider execution, model aliases, or UI integration.

Apply the relay overlay to a clean or disposable source checkout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterCodexRelayOverlay.ps1 -TargetRoot C:\path\to\9router-upstream
```

Verify an already-applied overlay without changing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterCodexRelayOverlay.ps1 -TargetRoot C:\path\to\9router-upstream -VerifyOnly
```

The route is a loopback-only, POST-only opaque relay. Next may canonicalize a local request URL to `localhost` even when the listener is bound to `127.0.0.1`; both names are treated as loopback. It requires native Codex
Bearer authorization, `Content-Type: application/json`, and matching native
`x-codex-turn-metadata` in the header and body. Set the upstream only through
the process environment, using an exact loopback Responses URL:

```powershell
$env:CODEX_RELAY_UPSTREAM_URL = "http://127.0.0.1:17841/v1/responses"
```

The relay forwards the original request bytes and a versioned allowlist of
observed native headers, including native `Content-Encoding: zstd`, streams
upstream status and SSE bytes without parsing, and propagates client
cancellation. It validates a bounded decompressed copy of zstd requests while
forwarding the original compressed bytes unchanged. It rejects browser `Origin` requests,
non-loopback upstreams, redirects, oversized bodies above `8388608` bytes,
generic requests without native metadata, and no automatic replay after
forwarding begins. It does not
forward administrative or stored provider credentials. `GET` returns `426` so
native WebSocket negotiation fails closed before the HTTP Responses fallback;
there is no relay `/v1/models` route and no model aliasing.

Keep `codex-chatgpt-web` on its own loopback port, normally
`127.0.0.1:17841`, and verify launcher restart ownership before any live
installation. `-InstallGlobal` remains opt-in and requires explicit approval;
source application and verification do not alter installed 9router or stored
credentials. Full native Codex-to-CGW proof remains a separate acceptance gate
when the CGW launcher is browser-only.