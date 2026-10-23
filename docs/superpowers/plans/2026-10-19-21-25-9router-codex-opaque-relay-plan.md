---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: superseded
layer: change
name: 9router-codex-opaque-relay
targets:
  - tools/local-patch-hub/Apply-9RouterCodexRelayOverlay.ps1
  - tools/local-patch-hub/overlays/9router-codex-relay/ce4460ef/manifest.json
  - tools/local-patch-hub/overlays/9router-codex-relay/ce4460ef/9router-codex-relay.patch
  - tools/local-patch-hub/README.md
  - tests/test_9router_codex_relay_overlay.py
  - external 9Router checkout at ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8
  - external codex-chatgpt-web checkout at the installed v6.1.12 baseline
  - docs/superpowers/plans/2026-10-19-21-25-9router-codex-opaque-relay-plan.md
---

# 9Router Codex Opaque Relay

Historical plan superseded and retired on October 23, 2026 during the CGW plan
review. Retained for historical context; no successor plan is required.

## Review Basis

This plan is based on `tools/local-patch-hub/README.md`, the supplied review
verdict, and the current Project OS checkout at commit
`61e1983147cd34846fdb759a644c15f6bca4cc89` on `main`.

The README establishes that 9Router changes are maintained as exact-base,
versioned local overlays, that unknown bases must stop without changes, and
that global installation is separate from source application. Existing
Responses, security, and attribution overlays already provide the local
patterns for `-VerifyOnly`, clean Git 3-way application, reverse checks, and
runtime installation verification.

The supplied review accepts an opaque relay as the first implementation
milestone and defers normal provider integration until a genuine native Codex
request completes through 9Router and `codex-chatgpt-web` without identity,
model, body, or streaming loss. The review also requires separate client and
upstream authentication, raw-byte forwarding, no automatic replay after
forwarding begins, explicit launcher-lifecycle proof, and fail-closed handling
for generic clients without native task context.

The review identifies three prerequisites that were not proven in the earlier
draft: native Codex normally enters through `/v1/responses`, the built-in
provider may not be able to supply a custom relay header, and the CGW launcher
may restore its own `openai_base_url`. A feasibility spike is therefore a
hard gate before any relay route or overlay is implemented. The spike must
select a supported route and authentication boundary or stop with a concrete
design blocker.

At drafting time, the Project OS checkout was observed clean at the commit
above; execution preserves the unrelated Project OS changes now present and
Task 6 rechecks this before implementation acceptance. The plan does not authorize changes
to installed Codex, `codex-chatgpt-web`, global 9Router, stored provider
credentials, generated `dist/tokenpilot-codex-hook.cmd` files, or normal
9Router provider execution before the relay gate passes.

## Goal

First prove that native Codex can reach a 9Router-controlled entrypoint with
authentic task metadata while the CGW launcher and built-in provider remain
usable. If that feasibility gate passes, implement and package a dedicated
localhost 9Router route that transparently relays native Codex Responses
requests to the local `codex-chatgpt-web` service. The relay must preserve the
original request bytes and upstream SSE bytes, preserve the exact model ID and
native task metadata, forward only the upstream credentials required by the
operation, propagate cancellation, and never retry or fall back after
forwarding begins.

The implementation ends at the opaque relay acceptance gate. Model catalog
changes, model aliases, normal provider registration, and broader 9Router UI
integration are a follow-on plan only after the gate passes.

## Implementation Outcomes

### Native routing feasibility before implementation

The plan first proves the actual Codex `base_url`, resulting request path,
credential mechanism, `/models` initialization behavior, and CGW launcher
route ownership. The relay is not implemented if native Codex cannot reach it
through the built-in provider or a separately approved, identity-preserving
entrypoint. A custom provider or fabricated metadata is not accepted as a
substitute for the managed CGW path.

### Strict opaque native relay

A dedicated `/v1/chatgpt-web/responses` route runs outside `handleChat()` and
outside `BaseExecutor` retry/fallback behavior. It reads the original request
body once, inspects a parsed copy only for admission checks, sends the original
bytes to a fixed loopback upstream, and streams the upstream response without
SSE parsing or reconstruction. `chatgpt-web/medium` remains
`chatgpt-web/medium`; no model prefix splitting, aliasing, instruction
rewriting, or synthetic task identity is allowed. The route enforces an
8-MiB body bound, validated metadata shape, manual redirect handling,
loopback-only listener and upstream checks, browser-origin rejection, and
socket-disconnect cancellation.

### Separate authentication and failure semantics

The relay uses the authentication boundary selected by the feasibility spike.
If the intended client can supply a dedicated non-`Authorization` access key,
the relay compares it in constant time and never forwards it. If the built-in
provider cannot supply that key, the plan must use the proven loopback-only
boundary plus CGW native task validation rather than inventing a credential or
metadata. In either mode, the relay never forwards the 9Router administrative
key or stored provider credentials. The incoming native `Authorization` value
is forwarded only when present and only as an upstream operation credential.
Missing or malformed `client_metadata["x-codex-turn-metadata"]` fails closed
before the upstream call; the relay never creates native metadata. HTTP errors,
upstream SSE `response.failed`, and ambiguous network failures remain failures
and are never converted into successful completions or automatic retries.

### Update-safe local overlay

The relay is represented by a new exact-base overlay under
`tools/local-patch-hub/overlays/9router-codex-relay/`, with a dedicated
reconciler and manifest. Applying, verifying, migrating, and reversing the
overlay follows the existing local-patch-hub rules and does not mutate a
checkout with unrelated tracked changes. Global installation remains an
explicit post-gate action.

### Native Codex coexistence evidence

Task 1 feasibility evidence is recorded from disposable clean checkouts and
bounded native-provider mock probes: the built-in `openai` provider reaches
`/v1/responses`, a prefixed `openai_base_url` reaches
`/v1/chatgpt-web/responses`, `GET` falls back with `426`, loopback-only access
plus CGW native metadata validation is selected, the observed native POST body is
51,937 bytes, and no `/v1/models` request appeared in the bounded run. The
installed CGW v6.1.12 launcher remains browser-only, so direct native
Codex-to-CGW and restart proof remain the blocked Task 5 gate.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-using-git-worktrees`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: current Project OS workspace for local plan, overlay, tests, and README; disposable clean external checkouts for 9Router and `codex-chatgpt-web`
- Commit policy: `no commits during execution`
- Preauthorized local actions: read repository and external checkout sources; create disposable clean checkouts; add or edit the named local overlay, manifest, tests, and README; edit the dedicated relay route and tests in the disposable 9Router checkout; run declared read-only, focused, and fixture-based checks
- User-approval actions: authentication, use of real Codex or CGW credentials, launcher/Codex/9Router process restarts, `-InstallGlobal`, changes to Codex or CGW configuration, external publication, push, merge, destructive cleanup, or discarding a checkout
- Parallel ownership: none; `README.md`, the new reconciler, overlay manifest, and local tests are shared integration surfaces and remain serialized
- Sequential fallback: complete Tasks 1–6 in order; if live credentials or full-harness capability are unavailable, stop at the last proven local task and record the blocked acceptance gate

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `61e1983147cd34846fdb759a644c15f6bca4cc89`
- Expected workspace: `preserve the existing Project OS modifications and untracked plans; add only the named relay artifacts and execution evidence`
- Next action: `Task 5 - complete the remaining native Codex lifecycle and same-turn relay gate; local relay-to-CGW path is proven`
- Blockers: `authenticated native Codex credentials/client lifecycle and same-turn cancellation/SSE digest proof remain unavailable; CGW is browser-only`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | disposable external checkouts | `codex` | none | native route, auth, and launcher feasibility gate | proven; see evidence below |
| Task 2 | `completed` | current plus disposable external checkouts | `codex` | Task 1 | observed compatibility contract and header matrix | proven; see execution evidence |
| Task 3 | `completed` | disposable 9Router checkout | `codex` | Task 2 | relay boundary tests and raw-byte/SSE assertions | proven; 8 focused tests pass |
| Task 4 | `completed` | current | `codex` | Task 3 | exact-base overlay, reverse, migration, and local pytest proof | proven; 26 focused tests pass |
| Task 5 | `blocked` | disposable external checkouts | `codex` | Task 4 | native Codex lifecycle probe and same-turn transport evidence | partial: disposable relay-to-CGW live boundary and restart evidence proven; native Codex lifecycle, authenticated turn, cancellation, and same-turn byte digests remain blocked |
| Task 6 | `completed` | current | `codex` | Task 5 | final repository and acceptance verification | reconciled; plan remains active because Task 5 is blocked |

## Task Breakdown

### Task 1: Prove native Codex routing feasibility

**Purpose:**
- Establish that the intended built-in Codex client can reach a 9Router-controlled entrypoint, authenticate without compromising native task identity, and coexist with the CGW launcher before any relay code is written.

**Task Function:**
- Native client routing feasibility spike and hard implementation gate.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: cross-process client configuration, authentication, launcher ownership, and mock-boundary reasoning are the critical path.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the single feasibility decision because it may require user-authorized local runtime inspection.

**Specification Coverage:**
- Native `/v1/responses` entrypoint, built-in provider constraints, relay authentication, CGW launcher route ownership, `/models` initialization, and preservation of authentic task metadata.

**Required Skills:**
- `skill-backend-verification`, `skill-systematic-debugging`, `skill-using-git-worktrees`

**Files And Symbols:**
- Inspect: external 9Router `src/app/api/v1/responses/route.js`, `src/app/api/v1/models/route.js`, `src/sse/services/model.js`, and `open-sse/executors/base.js`
- Inspect: external `codex-chatgpt-web` `src/adapters/chatgpt-web/environment.ts`, `src/native-passthrough.ts`, `scripts/smoke-release.ts`, and `docs/security-model.md`
- Verify: Codex built-in `openai` provider base URL behavior, resulting request path, header capability, CGW launcher `openai_base_url` ownership, and `/models` behavior

**Dependencies:**
- None. This task must complete before the route, authentication, or overlay contract is frozen.

**Authority:**
- Preauthorized local actions: inspect the named sources, create disposable mock services and clean checkouts, capture redacted request metadata, and run a bounded local Codex/CGW feasibility probe when already-authorized services are available.
- Stop for: inability to reach a controlled mock through the intended built-in provider, inability to supply the chosen relay authentication, CGW launcher route restoration, fabricated metadata, custom-provider substitution without approval, credential exposure, or installed-runtime mutation.

**Steps:**
- [x] Step 1: Create `$env:TEMP\9router-codex-relay-base` from the 9Router upstream repository and verify its HEAD is `ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8`; stop rather than silently rebasing if the requested source is not available at that commit.
- [x] Step 2: Create or select an isolated `codex-chatgpt-web` source checkout and record the installed v6.1.12/browser-only status without copying credentials into the repository.
- [x] Step 3: Identify the Codex `base_url` setting used by the built-in `openai` provider and prove the resulting path. Test whether a controlled mock can receive native traffic at `/v1/responses` without entering 9Router's normal `handleChat()` translation path.
- [x] Step 4: Test the authentication boundary against the built-in provider. Accept a dedicated relay header only if the real client can supply it without replacing upstream `Authorization`; otherwise select loopback-only access plus CGW native task validation and record that decision.
- [x] Step 5: Start the CGW launcher in a disposable configuration and prove whether it preserves the 9Router-owned client route across launcher restart. Record the exact supported arrangement or the concrete launcher conflict.
- [x] Step 6: Probe `/models` and any initialization calls needed by the native Codex session. Record whether the relay milestone can operate without model catalog changes.
- [x] Step 7: Capture a redacted native request-header inventory, native metadata shape, route result, authentication result, and launcher result. The output must select one route mode (`/v1/responses` direct entrypoint or an approved identity-preserving route shim) and one authentication mode (`dedicated header` or `loopback-only plus CGW validation`) for Task 2.

**Verification:**
- [x] `git -C $env:TEMP\9router-codex-relay-base status --short --branch`
- Expected: the source checkout is clean at the pinned base; the controlled mock receives a genuine built-in-provider request at the selected entrypoint; native metadata remains authentic; the selected authentication and launcher route survive the bounded probe; no credential or body content is stored in the repository.

**Exit Criteria:**
- A reproducible native entrypoint, authentication boundary, route-ownership arrangement, `/models` behavior, and request-header inventory are proven. If any critical item fails, stop before Task 2 and record whether the remedy requires a narrow 9Router entrypoint change, an isolated launch profile, or an additional CGW-side change.

**Execution Evidence (2026-10-19):**
- Clean disposable checkouts were created at `$env:TEMP\9router-codex-relay-base` (`ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8`) and `$env:TEMP\codex-chatgpt-web-v6.1.12` (tag `v6.1.12`, commit `cdfceafd51df9ab6f19818c145eac5a99c593a3d`). The installed CGW runtime reports `6.1.12` and `browser-only`; no credentials were copied.
- A temporary built-in `openai` Codex provider config reached a controlled loopback mock at `/v1/responses`. Native Codex first attempted WebSocket `GET /v1/responses`, then fell back to HTTP `POST /v1/responses`; the POST carried a 51,937-byte JSON body, `Authorization`, and `x-codex-turn-metadata`. The mock observed no `/v1/models` request in the bounded turn.
- A second bounded probe proved `openai_base_url = http://127.0.0.1:<port>/v1/chatgpt-web` produces `/v1/chatgpt-web/responses`, selecting the dedicated route shim. The mock also showed that `GET` must return `426` rather than `404` to avoid native retry noise before HTTP fallback.
- CGW source confirms its local Responses listener binds to `127.0.0.1`, returns `426` for WebSocket negotiation, validates native task identity from `x-codex-turn-metadata`, and forwards browser work through its own `/v1/responses` route. Its Codex integration owns `openai_base_url` only during explicit setup/connect operations; `serve`/launcher restart does not rewrite the route. The supported arrangement is CGW on its existing loopback port, 9Router on its own loopback port, and Codex pointed at the dedicated 9Router path.
- Selected route mode: the built-in `openai` provider uses the `openai_base_url` path prefix `http://127.0.0.1:<9router-port>/v1/chatgpt-web`, resolved by `src/app/api/v1/chatgpt-web/responses/route.js`; the active custom `9router` provider instead uses `[model_providers.9router].base_url` for the equivalent temporary probe. Selected authentication mode: loopback-only plus CGW native task validation. No dedicated relay header was observed or required, and native `Authorization` is not repurposed as a relay secret.

### Task 2: Freeze the observed compatibility contract

**Purpose:**
- Convert Task 1 evidence into the exact relay route, authentication, metadata, header, size, redirect, cancellation, and failure contract before source edits.

**Task Function:**
- Compatibility contract definition from observed native traffic.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-first reconciliation after the feasibility gate; no delegation benefit for a single contract owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the observed contract and admission decision.

**Specification Coverage:**
- Task 1 feasibility evidence; README overlay ownership; raw bytes, exact model IDs, native task metadata, model discovery, retry safety, and CGW browser-only limitations.

**Required Skills:**
- `skill-using-git-worktrees`, `skill-backend-verification`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `tools/local-patch-hub/README.md:9router overlays` and existing `Apply-9Router*Overlay.ps1` scripts
- Inspect: Task 1 route/auth evidence and external 9Router `src/app/api/v1/responses/route.js`, `src/sse/services/model.js`, and `open-sse/executors/base.js`
- Inspect: external `codex-chatgpt-web` `src/adapters/chatgpt-web/environment.ts`, `src/native-passthrough.ts`, and `docs/security-model.md`
- Verify: Task 1 selected entrypoint and authentication mode, installed CGW version, direct native request, and observed header matrix

**Dependencies:**
- Task 1 complete. Do not replace observed native evidence with assumptions about custom providers or reconstructed requests.

**Authority:**
- Preauthorized local actions: reconcile Task 1 evidence with source, define the selected route and authentication modes, define the observed native header allowlist, and record the contract in this plan and the Task 3 test fixture.
- Stop for: conflicting route or authentication evidence, an unbounded header allowlist, missing `/models` behavior, any request to reuse 9Router administrative credentials, or any need to modify installed runtime configuration.

**Steps:**
- [x] Step 1: Record the selected native ingress path and internal relay path, including whether `/v1/responses` is owned directly or reached through an approved route shim that bypasses `handleChat()`.
- [x] Step 2: Record the selected authentication mode and its non-forwarded secret boundary. If the mode is `dedicated header`, name the observed client configuration that supplies it; if the mode is `loopback-only`, record the listener binding and CGW validation responsibility.
- [x] Step 3: Define `MAX_RELAY_BODY_BYTES` as `8388608` and verify the observed native request is below the bound. Require a top-level JSON object, non-empty string `model`, object `client_metadata`, and the observed non-empty `client_metadata["x-codex-turn-metadata"]` shape.
- [x] Step 4: Build a versioned header matrix from the captured request. Test omission of `authorization`, `content-type`, `accept`, `user-agent`, `x-request-id`, `session_id`, `originator`, and `ChatGPT-Account-ID` individually; forward only headers proven necessary for the selected native turn.
- [x] Step 5: Freeze redirect behavior (`redirect: "manual"`), loopback-only upstream validation, loopback-only 9Router listener verification, rejection of browser `Origin` requests, `/models` handling, no model aliasing, and no automatic replay.

**Verification:**
- [x] `git -C $env:TEMP\9router-codex-relay-base status --short --branch`
- Expected: the plan contains one selected route mode, one selected authentication mode, a bounded observed header allowlist, a body-size limit, redirect/listener/origin rules, and a same-turn evidence method.

**Exit Criteria:**
- The observed compatibility contract is complete and reproducible. If Task 1 did not produce a supported route and authentication mode, implementation remains blocked and Task 3 is not authorized.

**Frozen Contract (2026-10-19):**
- Ingress is `POST /v1/chatgpt-web/responses`; `GET` returns `426` with no upstream call so native Codex falls back from WebSocket to HTTP. Existing `/v1/responses` remains untouched.
- The 9Router listener and `CODEX_RELAY_UPSTREAM_URL` must both resolve to loopback; the relay rejects any request carrying `Origin`, rejects generic clients without native task metadata, and forwards upstream only to the exact `/v1/responses` path on the CGW loopback listener.
- Authentication is loopback-only plus CGW validation. The relay forwards the native `Authorization` header unchanged for CGW's native passthrough boundary but never treats it as a relay credential, and forwards no 9Router administrative or stored provider credentials.
- The body limit is `MAX_RELAY_BODY_BYTES = 8388608`. The relay validates a top-level object, non-empty string `model`, object `client_metadata`, and non-empty `client_metadata["x-codex-turn-metadata"]`; it forwards the original bytes, not a reserialized object.
- The observed versioned allowlist is the native request set needed by the CGW boundary: `authorization`, `accept`, `content-type`, `user-agent`, `originator`, `version`, `x-codex-beta-features`, `x-codex-window-id`, `x-codex-turn-metadata`, `x-client-request-id`, `session-id`, and `thread-id`. Hop-by-hop headers, `host`, `connection`, `upgrade`, and any relay/admin/provider credential are stripped. Focused tests prove optional-header omission behavior; the allowlist remains versioned and reviewable.
- Upstream requests use `redirect: "manual"`; redirect responses, non-loopback destinations, malformed metadata, oversized bodies, browser-originated requests, and generic clients fail closed before forwarding. Upstream SSE status, headers, and bytes pass through unchanged; disconnect aborts the single upstream attempt, with no relay retry or fallback after forwarding begins.

### Task 3: Implement the strict opaque relay in 9Router

**Purpose:**
- Add one dedicated native relay route that preserves request identity, content, model IDs, cancellation, and streaming while bypassing normal 9Router executor behavior.

**Task Function:**
- Backend transport implementation with direct boundary tests.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: moderate backend reasoning, security-sensitive credential boundaries, and external route/runtime interaction.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the focused external route tests and Task 4 overlay tests provide the validation boundary; no independent writer is needed.

**Specification Coverage:**
- Strict opaque relay; separate authentication; fixed loopback upstream; exact model and metadata preservation; raw request forwarding; SSE passthrough; cancellation; zero retries; fail-closed generic clients.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: the external 9Router route owner selected by Task 2; use `src/app/api/v1/responses/route.js` only when Task 1 proves a safe pre-route dispatch, otherwise use `src/app/api/v1/chatgpt-web/responses/route.js`
- Inspect and keep separate: external 9Router `src/app/api/v1/responses/route.js`, `src/sse/services/model.js`, and `open-sse/executors/base.js`
- Add tests: external 9Router `tests/unit/chatgpt-web-responses-relay.test.js`
- Verify: request body bytes, forwarded headers, upstream URL, response status/headers, SSE bytes, abort signal, and upstream call count

**Dependencies:**
- Task 1 must prove the native entrypoint and authentication mode; Task 2 must freeze the route, header, size, listener, redirect, and origin contract.

**Authority:**
- Preauthorized local actions: edit the named route and external unit test in the disposable 9Router checkout; run mock-upstream boundary tests and inspect the resulting diff.
- Stop for: adding model aliases, changing `/v1/responses`, forwarding administrative or stored provider credentials, synthesizing native metadata, adding a retry/fallback path, or changing CGW.

**Steps:**
- [x] Step 1: Add the selected relay route outside `handleChat()` and outside `BaseExecutor`; reject methods other than `POST`, reject browser-originated requests with an `Origin` header, and reject a missing or malformed `Content-Type: application/json` request.
- [x] Step 2: Read the request body into one byte buffer and reject bodies over `MAX_RELAY_BODY_BYTES = 8388608`. Parse a separate inspection copy only to require the observed top-level object, non-empty string `model`, object `client_metadata`, and observed `client_metadata["x-codex-turn-metadata"]` shape; never serialize the inspection copy for forwarding.
- [x] Step 3: Enforce the Task 2 authentication mode. For `dedicated header`, compare the observed key with a constant-time comparison and consume it before forwarding. For `loopback-only`, enforce loopback ingress in the route and defer actual listener-binding proof to Task 5; rely on CGW native validation rather than inventing a relay credential.
- [x] Step 4: Validate `CODEX_RELAY_UPSTREAM_URL` as loopback-only with the exact `/v1/responses` path, use `redirect: "manual"`, and reject missing or unexpected upstream destinations before any upstream call.
- [x] Step 5: Forward the original bytes with only the headers proven necessary by Task 2's versioned matrix; strip hop-by-hop headers, any relay key, 9Router administrative credentials, and all stored provider credentials.
- [x] Step 6: Preserve the exact model string and all body fields, including `client_metadata["x-codex-turn-metadata"]`; do not split `chatgpt-web/medium`, rewrite instructions, add aliases, or create a replacement task identity.
- [x] Step 7: Pipe upstream status, content type, and SSE bytes directly to the client. Tie an `AbortController` to actual socket disconnect and abort the upstream request; do not parse, reconstruct, retry, or fallback after forwarding starts.
- [x] Step 8: Add tests for exact byte equality, exact model preservation, per-header omission, body-size rejection, metadata validation, selected authentication mode, constant-time key handling when applicable, non-loopback listener/upstream rejection, manual redirect rejection, browser-origin rejection, socket disconnect cancellation, upstream `event: error`, `response.failed` after HTTP 200, ambiguous network failure, and exactly one upstream attempt.

**Verification:**
- [x] `npm --prefix tests test -- unit/chatgpt-web-responses-relay.test.js`
- Expected: all relay boundary tests pass; the mock upstream receives one byte-identical body and one attempt; the client receives unmodified SSE error and completion bytes; rejected requests make zero upstream calls.

**Exit Criteria:**
- A clean 9Router checkout contains a dedicated relay route and focused tests that prove the complete opaque transport contract without touching normal provider execution.

### Task 4: Package the relay as an update-safe local overlay

**Purpose:**
- Make the proven relay installable and reversible through the project-owned patch hub without changing global runtimes during verification.

**Task Function:**
- Exact-base patch packaging, reconciler implementation, and local contract tests.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: localized PowerShell/Git overlay work with migration and no-clobber risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository pytest and disposable Git checkouts provide direct validation.

**Specification Coverage:**
- Exact-base overlays, unknown-base stop, already-applied detection, clean 3-way rebase checks, reverse applicability, unrelated-change protection, and README alignment.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`

**Files And Symbols:**
- Add: `tools/local-patch-hub/Apply-9RouterCodexRelayOverlay.ps1`
- Add: `tools/local-patch-hub/overlays/9router-codex-relay/ce4460ef/manifest.json`
- Add: `tools/local-patch-hub/overlays/9router-codex-relay/ce4460ef/9router-codex-relay.patch`
- Modify: `tools/local-patch-hub/README.md:81` under the 9router overlays section
- Add: `tests/test_9router_codex_relay_overlay.py`
- Reuse: `tools/local-patch-hub/Install-9RouterGlobal.ps1` without changing its process-stop, package-copy, downgrade, or executable-verification contract

**Dependencies:**
- Task 3 must produce the tested external diff from the pinned 9Router base.

**Authority:**
- Preauthorized local actions: add the named overlay files, reconciler, README commands, and pytest coverage; run `git apply --check`, reverse checks, temporary-index checks, and local pytest without global installation.
- Stop for: editing existing overlay versions, weakening tracked-change guards, changing global installation behavior, using a generated `dist` file as a source, or applying the patch to an unrelated checkout.

**Steps:**
- [x] Step 1: Export only the Task 3 route and tests into `9router-codex-relay.patch` against base `ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8` and create a manifest with the repository URL, exact base commit, patch filename, selected route/auth contract, and relay version `1.0.0`.
- [x] Step 2: Implement the reconciler with the existing overlay contract: exact-base selection, already-applied reverse check, `-VerifyOnly`, clean 3-way check in a temporary Git index, refusal on unrelated tracked changes, and no partial application.
- [x] Step 3: Keep `-InstallGlobal` opt-in and delegate to `Install-9RouterGlobal.ps1` only after source application; reject `-InstallGlobal -VerifyOnly` and preserve `-AllowDowngrade` semantics.
- [x] Step 4: Extend the README with apply and verify commands, the route/auth/environment contract, the no-retry/no-alias rule, the no-`/v1/models` rule, the launcher-lifecycle gate, and the explicit warning that live installation requires approval.
- [x] Step 5: Add local pytest assertions for manifest identity, patch paths and symbols, README commands and safeguards, exact-base and reverse behavior, temporary-index usage, tracked-change refusal, and no generated-file source dependency.

**Verification:**
- [x] `py -B -m pytest -q tests/test_9router_codex_relay_overlay.py tests/test_9router_responses_overlay.py tests/test_9router_security_overlay.py`
- Expected: new and existing overlay contract tests pass; existing overlays remain unchanged; the new patch is structurally bound to the pinned base.
- [x] `git -C $env:TEMP\9router-codex-relay-base apply --check -- $((Resolve-Path "tools/local-patch-hub/overlays/9router-codex-relay/ce4460ef/9router-codex-relay.patch").Path)` is executed from the disposable target checkout.
- Expected: the patch applies cleanly to the exact base, reverse application succeeds after a forward application, and `-VerifyOnly` does not mutate the target.

**Exit Criteria:**
- The relay is represented by a versioned, reversible, exact-base overlay and documented with the same safety contract as the existing 9Router overlays.

### Task 5: Prove native Codex integration and launcher coexistence

**Purpose:**
- Demonstrate that the real native Codex request remains trusted and transparent when routed through 9Router, including cancellation and restarts.

**Task Function:**
- End-to-end backend boundary verification and lifecycle compatibility probe.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: cross-process integration, native identity validation, and failure/restart semantics require more reasoning than local static tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the bounded live probe because credentials, process ownership, and evidence redaction must remain single-owner.

**Specification Coverage:**
- Direct baseline, relay path, exact request preservation, native task identity, model ID, source headers, SSE preservation, cancellation, no automatic replay, launcher restart stability, and generic-client fail-closed behavior.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: external CGW native task validation in `src/adapters/chatgpt-web/environment.ts` and `src/native-passthrough.ts`
- Inspect: CGW launcher ownership and Codex route configuration; do not edit the launcher in this phase
- Verify: installed 9Router route, CGW `/v1/responses` boundary, Codex request metadata, same-turn ingress/bridge/client byte digests, and process restart behavior
- Record: redacted probe evidence outside source control; no credentials, prompts, full request bodies, or private account data

**Dependencies:**
- Tasks 1–4 complete; the relay overlay is applied only in a disposable target first.

**Authority:**
- Preauthorized local actions: run the declared probe against already-authorized local services, capture redacted metadata and hashes, and apply the overlay to disposable targets.
- Stop for: missing native task context, any body/model/SSE mismatch, any automatic replay, launcher configuration overwrite, credential substitution, full-harness claim from browser-only CGW, or a request to install globally without explicit approval.

**Steps:**
- [x] Step 1: Apply the relay overlay to a disposable 9Router checkout without `-InstallGlobal`; start it with the Task 2 route on `127.0.0.1:20129`, `CODEX_RELAY_UPSTREAM_URL=http://127.0.0.1:17841/v1/responses`, and native-shaped bearer/metadata headers.
- [ ] Step 2: Send one genuine Codex request through the Task 2 selected native entrypoint and compare ingress bytes with bridge-bound bytes for that same request, bridge-returned bytes with client-delivered bytes for that same turn, exact model string at both boundaries, native metadata within that turn, selected source headers, upstream status, SSE event sequence, and completion identity. Compare direct and relayed runs only for equivalent successful native behavior, not identical response or SSE hashes.
- [ ] Step 3: Start receiving an upstream response, close the client socket, and prove the upstream receives cancellation, the client receives no synthetic completion, and the relay records exactly one attempt.
- [x] Step 4: Exercise missing native metadata, generic OpenAI-compatible input, malformed input, an `Origin` header, oversized bodies, and upstream redirects; focused boundary tests and the live probe prove fail-closed behavior without a successful native turn.
- [ ] Step 5: Restart the CGW launcher, Codex, and 9Router one at a time, then repeat one native turn; prove no component overwrites the relay route or changes the managed Codex destination.
- [x] Step 6: Preserve this redacted result record with immutable target HEADs, listener bindings, route/auth mode, failure classifications, restart results, and the explicit full-harness MCP blocker while CGW remains browser-only.

**Verification:**
- [ ] Direct native Codex-to-CGW baseline passes as an equivalent-behavior control; its response and SSE hashes are not compared with a separate relayed turn.
- [ ] Codex-to-9Router-to-CGW passes with the same exact model ID and native task identity.
- [ ] Request body and SSE event bytes are preserved; cancellation reaches upstream; no automatic replay occurs, including after an ambiguous network failure.
- [ ] Launcher, Codex, and 9Router restarts preserve routing without configuration fights.
- [ ] Generic clients without native context fail closed at the relay or CGW boundary, with no successful native turn or synthetic metadata.

**Exit Criteria:**
- All nine relay go/no-go conditions are proven, or the exact failed condition is recorded and no provider-integration work is authorized.

### Task 6: Final reconciliation and explicit provider-integration deferral

**Purpose:**
- Reconcile local source, overlay, tests, documentation, and live evidence, then close the milestone without claiming normal provider compatibility.

**Task Function:**
- Final artifact verification, scope reconciliation, and handoff preparation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence reconciliation is a single-owner acceptance activity.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is performed by the lead controller under `skill-verification-before-completion`.

**Specification Coverage:**
- All implementation outcomes; explicit separation between the opaque native route and deferred model catalog/provider integration.

**Required Skills:**
- `skill-verification-before-completion`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Verify: `tools/local-patch-hub/README.md`, `tools/local-patch-hub/Apply-9RouterCodexRelayOverlay.ps1`, new relay overlay directory, and `tests/test_9router_codex_relay_overlay.py`
- Verify: existing `tests/test_9router_responses_overlay.py`, `tests/test_9router_security_overlay.py`, and `tests/test_observe_9router_usage.py`
- Update: this plan with immutable evidence paths, deviations, blocked gates, and final task states

**Dependencies:**
- Task 5 must either pass the relay gate or produce a concrete blocked result.

**Authority:**
- Preauthorized local actions: run final local checks, inspect diffs, update this plan’s evidence and task states, and record the provider-integration deferral.
- Stop for: changing the relay contract, adding normal provider registration, adding model aliases, claiming full Codex compatibility, or changing global/installed runtimes.

**Steps:**
- [x] Step 1: Run the focused overlay tests, the existing 9Router overlay tests, the usage observer tests, and the full repository pytest suite.
- [x] Step 2: Run `git diff --check` and inspect `git diff --stat`; confirm only the planned local-patch-hub, test, README, and plan files changed.
- [x] Step 3: Run each new and existing `-VerifyOnly` command against disposable clean and already-applied targets; record the exact output and target HEAD.
- [x] Step 4: Record the relay gate result, selected route/auth mode, observed header matrix, any unavailable full-harness capability, and the explicit follow-on boundary: `/v1/models`, model aliases, normal provider registration, and UI integration remain out of scope.
- [x] Step 5: Keep the plan `active` because Task 5 remains blocked; only `skill-verification-before-completion` may authorize a later `completed` status.

**Verification:**
- [x] `py -B -m pytest -q tests/test_9router_codex_relay_overlay.py tests/test_9router_responses_overlay.py tests/test_9router_security_overlay.py tests/test_observe_9router_usage.py`
- Expected: focused local suite passes.
- [x] `py -B -m pytest -q`
- Expected: the full repository suite passes, or unrelated pre-existing failures are recorded with their exact test names and excluded from the relay acceptance claim.
- [x] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- Every required local artifact is reconciled with the tested relay contract, the final evidence is recorded, and normal provider integration is explicitly deferred unless the relay gate passes.

## Execution Evidence

- Task 1: disposable checkouts are `C:\tmp\9router-codex-relay-base` at `ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8` and `C:\tmp\codex-chatgpt-web-v6.1.12` at tag `v6.1.12`; no credentials were copied into repository files.

- Task 2: the frozen contract selects `POST /v1/chatgpt-web/responses`, `GET -> 426`, loopback-only access plus CGW native validation, `CODEX_RELAY_UPSTREAM_URL=http://127.0.0.1:17841/v1/responses`, an 8-MiB body bound, exact model/metadata preservation, manual redirects, and no replay.

- Task 3: the disposable route and test files are `C:\tmp\9router-codex-relay-target-5\src\app\api\v1\chatgpt-web\responses\route.js` and `C:\tmp\9router-codex-relay-target-5\tests\unit\chatgpt-web-responses-relay.test.js`; the focused boundary suite passes 10/10, covering raw body bytes, native `Content-Encoding: zstd` validation with unchanged forwarding, header filtering, SSE error/failed-completion passthrough, redirect rejection, one-attempt failure, cancellation, and Next URL canonicalization.

- Task 4: the exact-base overlay applies to `C:\tmp\9router-codex-relay-target-1`, `-VerifyOnly` succeeds after application, reverse application restores a clean target, and reapplication succeeds. Project OS overlay tests pass 26/26; `git diff --check` reports no errors.

- Task 5: partially proven but still blocked for full acceptance. CGW v6.1.12 is running on `127.0.0.1:17841`; the disposable patched 9Router route ran on `127.0.0.1:20129` with `CODEX_RELAY_UPSTREAM_URL=http://127.0.0.1:17841/v1/responses`. The direct temporary ChatGPT-authenticated native Codex baseline reached CGW over HTTP fallback and returned `DIRECT_CGW_OK`; the same temporary profile routed through the relay with `gpt-5.6-luna` and returned `RELAY_CHATGPT_AUTH_OK`, then repeated successfully with `gpt-5.6-sol` and returned `RELAY_SOL_OK`. A follow-up exact-ID probe with `gpt-6.1-sol` also returned `RELAY_GPT61_SOL_OK`, although the installed CGW CLI help advertises `gpt-6-sol` rather than `gpt-6.1-sol`, so backend model identity should not be inferred solely from completion success. All relay runs logged native `Content-Encoding: zstd`. This proves explicit model IDs can be sent through the relay without model aliasing or provider changes. A disposable harness defect was also confirmed and fixed: the HTTP upgrade socket lacked an `error` listener, so the expected WebSocket `426` fallback could crash the harness on `ECONNRESET`; the harness now handles that expected client close. Full acceptance remains blocked because same-turn byte digests, cancellation during streaming, Codex restart behavior, and the browser-only CGW launcher lifecycle are not fully proven. No global installation, provider/model/credential/permanent configuration change, or administrative credential forwarding was performed.

- The external 9Router broad Vitest run is not an acceptance gate: the relay-focused suite passes, while that broad run reports unrelated failures in existing translator, Windsurf, and other tests; the exact relay boundary remains green.

- Task 6: the full Project OS suite previously passed `1488 passed, 4 skipped`; the updated relay overlay applies and verifies on a clean target with `git diff --check` clean. The plan remains `active` with Task 5 explicitly `blocked`, and model discovery, aliases, normal provider registration, and UI integration remain deferred.
- Live-probe addendum: the first real Next route probe exposed a compatibility defect that static unit URLs did not cover. Next passed `request.url` as `http://localhost:20129/v1/chatgpt-web/responses` even when the TCP `Host` header was `127.0.0.1:20129`; the relay returned `403` before contacting CGW. Existing `dashboardGuard` already treats `localhost` as loopback, so the narrow fix was to add `localhost` to the relay's loopback set and add `accepts Next canonical localhost request URLs` coverage. The focused direct regression passed after the fix; the overlay patch was regenerated from raw Git bytes to avoid CRLF-induced whitespace noise.

- Live boundary evidence: direct native Codex with the temporary ChatGPT-authenticated profile reached `http://127.0.0.1:17841/v1`, observed the expected WebSocket `426`, fell back to HTTP, and returned `DIRECT_CGW_OK`. With only the ephemeral `model_provider=openai` and `openai_base_url=http://127.0.0.1:20129/v1/chatgpt-web` overrides, the same profile reached the relay, sent a zstd-compressed native request, and returned `RELAY_CHATGPT_AUTH_OK`. The relay log recorded `POST /v1/chatgpt-web/responses`, `contentEncoding: zstd`, and the native body magic `28b52ffd`; no provider, model, credential, or permanent configuration changed.

- Native Codex smoke evidence (2026-10-19): the earlier API-key session result was non-diagnostic for CGW and remains documented as a historical failed attempt. After the user completed sign-in, the separately approved temporary profile at `C:\tmp\codex-cgw-relay-auth-test` reported ChatGPT-native auth, and two ephemeral commands proved direct CGW and relayed completion without modifying the existing profile or provider. The relay command used only `model_provider="openai"`, `openai_base_url="http://127.0.0.1:20129/v1/chatgpt-web"`, and model `gpt-5.6-luna`.

- Root cause and disposition: the earlier failure was caused by the available session being API-key authenticated, which CGW rejects, while the later retry succeeded after the separately approved ChatGPT-native sign-in. The only confirmed relay-side defect was native zstd request validation; the route previously parsed compressed bytes as JSON and returned `400`. The route now validates a bounded decompressed copy and forwards the original bytes unchanged. The only live-harness defect was the unhandled expected upgrade-socket reset; it was patched in the disposable harness and did not require a product boundary relaxation.

- Remaining Task 5 gate: authenticated native completion identity is now proven for the temporary smoke path, but same-turn request/SSE byte digests, client cancellation during streaming, Codex restart behavior, and full browser-only CGW launcher lifecycle remain unproven; normal provider integration remains deferred.
## Verification

Use this final artifact-level verification after implementation tasks are complete:

- `py -B -m pytest -q tests/test_9router_codex_relay_overlay.py tests/test_9router_responses_overlay.py tests/test_9router_security_overlay.py tests/test_observe_9router_usage.py`
- `py -B -m pytest -q`
- `git diff --check`
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterCodexRelayOverlay.ps1 -TargetRoot $env:TEMP\9router-codex-relay-applied -VerifyOnly` after applying the relay overlay to that disposable target
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1 -TargetRoot $env:TEMP\9router-responses-applied -VerifyOnly` after applying the Responses overlay to its disposable target
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/local-patch-hub/Apply-9RouterSecurityOverlay.ps1 -TargetRoot $env:TEMP\9router-security-applied -VerifyOnly` after applying the security overlay to its disposable target

The final verification must include the direct native baseline and the live
relay probe from Task 5. Static overlay tests alone cannot establish native
Codex compatibility.

## Completion Criteria

The plan is ready for completion verification when:

1. native Codex reaches a controlled mock through the selected built-in-provider
   entrypoint, the selected authentication mode is supplied without weakening
   native identity, and CGW launcher route ownership survives restart;
2. the direct native Codex-to-CGW baseline is recorded as an equivalent-
   behavior control;
3. the dedicated relay route is implemented outside `handleChat()` and normal
   executor retry/fallback behavior;
4. request bytes, model ID, native task metadata, the observed versioned header
   allowlist, SSE bytes, cancellation after streaming begins, and failure
   semantics are proven at the direct boundary;
5. the relay enforces the bounded body, metadata, redirect, listener, and
   browser-origin security rules;
6. the selected authentication boundary is proven for the intended built-in
   client, and no administrative or stored provider credential reaches the
   bridge;
7. the exact-base overlay applies, verifies, migrates, and reverses without
   mutating unrelated tracked changes;
8. restart probes preserve route ownership and do not cause request replay;
9. generic clients without native context fail closed;
10. the full-harness MCP gate remains honestly blocked while CGW is
   browser-only; and
11. model discovery, aliases, normal provider integration, and UI changes remain
   outside this plan unless a new approved plan is created after the relay gate.

The plan may be marked `completed` only when
`skill-verification-before-completion` runs fresh final verification, confirms
these criteria against repository evidence, finds no unresolved required task,
failed required check, stale status, or unrecorded scope deviation, and returns
`verified`. The lead controller then updates the plan status.
