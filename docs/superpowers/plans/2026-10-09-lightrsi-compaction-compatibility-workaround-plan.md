---
layer: change
artifact_type: plan
contract_version: "1"
status: active
template_id: implementation-plan
name: lightrsi-compaction-compatibility-workaround
targets:
  - docs/superpowers/plans/2026-10-09-lightrsi-compaction-compatibility-workaround-plan.md
  - external LightRSI Codex adapter checkout at resolved target commit
  - external 9Router Responses/SSE checkout at resolved target commit
  - tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/<resolved-target-head>/
  - tools/local-patch-hub/overlays/9router-responses/<resolved-target-head>/
  - tests/test_lightrsi_codex_overlay.py
  - tests/test_9router_responses_overlay.py
---

# LightRSI Compaction Compatibility Workaround Plan

## Goal

Validate and, only when proven safe, prevent Codex compaction failures caused
by restored hosted `web_search_call` history without changing canonical
conversation history. Prefer router preservation only when the provider
supports it; current direct evidence selects LightRSI request-only stripping
for explicit compact requests. Preserve upstream SSE errors through 9Router.
Keep behavior narrow, route-specific, feature-gated, reversible, and removable
after upstream repair.

## Implementation Outcomes

- Exact or structurally equivalent failing request has route-specific causal
  evidence before runtime edits.
- Historical `web_search_call` preservation is tested before removal.
- 9Router applies one selected compatibility policy — `off` or `preserve` —
  only at a reliably identified compact boundary.
- LightRSI applies only transparent compact routing or the separately selected
  request-only `strip` fallback; it never injects the preservation schema.
- Current provider capability evidence keeps router preservation `off` and
  forwards LightRSI compact projections to upstream `/responses/compact` when
  available, with normal `/responses` fallback on provider `404`.
- Retained items preserve deep equality, relative order, IDs, content, and opaque fields.
- Canonical history and ordinary `/responses` traffic remain unchanged.
- Ambiguous or unmarked ordinary `/responses` traffic is forwarded unchanged.
- Explicit required dependency breaks reject the rewrite before send; unknown
  reference semantics do not trigger extra deletion.
- Normalized request sends once; no compatibility retry occurs in MVP.
- 9Router preserves upstream SSE errors only at demonstrated loss points,
  instead of converting them to HTTP `200` empty-stream failures.
- A successful compact result is followed by a successful normal turn on the
  same thread.
- Overlay artifacts remain bound to exact target commits and can be reversed.

## Task Breakdown

- Inventory LightRSI, 9Router, provider, and runtime boundaries.
- Reproduce compaction loss and verify route-specific causal evidence.
- Implement and test the smallest router-first compatibility boundary.
- Package exact-base overlays, verify clean apply/reverse, and defer rollout.

## Verdict Review

The consolidated recommendation supersedes the earlier strip-first sequence.
Required corrections before execution:

- Treat exact route-specific reproduction as a hard admission gate, not
  background evidence.
- Test preservation before stripping. A candidate declaration must prove both
  historical-item acceptance and zero new hosted-search execution.
- Separate explicit `/responses/compact` from local summarization through
  ordinary `/responses`; do not infer compaction from payload shape or prompt
  text.
- Keep policy selection offline. Production performs one selected projection and
  one upstream attempt; no inject-then-strip retry state machine.
- Define structural validation concretely. At minimum, prove retained-item
  deep equality, relative order, IDs, and ordinary tool dependency closure.
  Validate citation or annotation references only when an explicit required ID
  dependency is present; preserve annotations when semantics are unknown.
- Limit filtering to an explicit input array. Forward unchanged when input is
  opaque, server-referenced, malformed, or otherwise outside the proven shape.
- Verify LightRSI and 9Router source checkouts before naming final symbols or
  overlay base commits. Current workspace stores overlay tooling, not those
  upstream runtime sources.
- Prove inbound `/v1/responses/compact` routing and the actual provider target
  independently. Do not assume the provider exposes `/responses/compact`.
- Treat 9Router output reconstruction and SSE error preservation as separate
  changes. A transformer unit test does not prove compact-route behavior.
- Prefer 9Router as preservation owner only when its trusted `_compact` route
  reaches a supported provider transport; direct capability evidence may select
  LightRSI fallback instead.
- Reject broad historical-item predicates. Ordinary `/responses` requests with
  historical `web_search_call` remain unchanged unless current configuration
  independently enables search.
- Preserve exact existing search declarations and restrictions across both
  top-level `tools` and Lite `additional_tools`; conflicting declarations are
  unsupported rather than merged speculatively.

## Execution Approach

- Mode: inline sequential
- Coordination: git-tracked
- Required skills: `skill-backend-verification`, `skill-test-driven-development`,
  `skill-code-standards`, `skill-verification-before-completion`
- Isolation: target checkouts must be disposable or managed worktrees; do not
  modify installed global runtimes during development
- Commit policy: no commits during implementation unless explicitly authorized
- Stop conditions: failed route-specific reproduction, missing fixture
  provenance, unknown compaction purpose, unsafe tool authority expansion,
  unsupported preservation schema, unknown target source, secret exposure,
  dangling retained references, unsafe retry, or request mutation outside
  compaction

## Coordination State

- Coordination owner: `lead-controller`
- Coordination schema: `1`
- Branch: `codex/launch-preparation-convergence`
- Base commit: `46d9323995622a677c6cc7df010b374506c7dfe7`
- Expected workspace: current checkout; preserve unrelated 9Router changes; do not mutate installed runtimes
- Next action: retain core source/test changes; isolate 9Router before any overlay work
- Blockers: 9Router checkout contains unrelated user changes and uncommitted SSE work; no production install or rollout authorized

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current plus verified external checkouts | `codex` | none | source inventory and LightRSI baseline | Source targets recorded; current Codex adapter suite: 476 passed, 0 failed; typecheck passed |
| Task 2 | `completed` | current plus external provider route | `codex` | Task 1 | route replay, removal control, search count, continuation disposition | Fresh authorized replay: `/responses/compact` returned `404` with preserved and stripped payloads; normal `/responses` historical-search payload returned HTTP `200` SSE error, while stripped control completed with zero search events; exact original fixture remains unavailable |
| Task 3 | `completed` | 9Router disposable checkout | `codex` | Task 2 | corrected preservation behavior and provider capability proof | upstream `/responses/compact` returned 404; router preserve stays off |
| Task 4 | `completed` | LightRSI disposable checkout | `codex` | Task 3 | fallback projection tests and owner selection | explicit compact route strips historical search items on cloned request payload; ordinary route remains unchanged |
| Task 5 | `completed` | LightRSI disposable checkout | `codex` | Task 4 | inbound compact route, native compact target, and fallback tests | compact inbound accepted; upstream `/responses/compact` is attempted first and `/responses` is used only after `404` |
| Task 6 | `completed` | isolated `C:\tmp\9router-compaction-compat-e0be411` plus LightRSI route boundary | `codex` | Task 1, Task 3 | focused SSE tests plus compact-route boundary proof | Clean detached worktree created at `e0be411184e67687171a1e13ae2e5686c14dd43a`; focused assertions passed; Vitest unavailable locally, no dependency install performed |
| Task 7 | `completed` | overlay tooling plus isolated target worktrees | `codex` | Task 5, Task 6 | exact target-commit overlay validation | 9Router and LightRSI manifests/patches added; clean-base apply and reverse checks pass; overlay tests pass `3` |
| Task 8 | `completed` | LightRSI disposable integration workspace | `codex` | Task 5, Task 6 | compact success plus same-thread continuation | compact non-stream, compact SSE, and normal continuation route tests pass |
| Task 9 | `completed` | disposable install verification workspace | `codex` | Task 8 | rollback and installation checks | exact-base apply/reverse, LightRSI typecheck and `476` adapter tests, 9Router smoke, guard checks, clean restored HEADs; production rollout deferred |

## Policy Decision Tree

1. If explicit `/responses/compact` routing cannot be identified reliably,
   leave request unchanged and fix the routing owner instead.
2. If corrected 9Router preservation with execution disabled succeeds on a
   supported provider transport and continuation succeeds, select router
   `preserve` and keep LightRSI fallback `off`.
3. Otherwise, if LightRSI request-only removal succeeds with continuation and
   all retention checks pass, select LightRSI `strip`; upstream target remains
   normal `/responses` unless provider capability proves otherwise.
4. Otherwise select `off` and surface the original failure.

Production never probes one policy, fails, then retries with another policy.

### Task 1: Materialize Target Sources And Establish Baseline

**Purpose:** Resolve repository truth before implementation.

**Task Function:** Repository inspection and baseline verification.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Architecture, ownership, overlay reversibility.

**Required Skills:** `skill-code-standards`.

**Files And Symbols:**

- External LightRSI Codex adapter source; resolve actual compaction request
  boundary and configuration owner.
- External 9Router source paths already represented by the current overlay,
  including `open-sse/transformer/responsesTransformer.js`,
  `open-sse/translator/index.js`,
  `open-sse/translator/response/openai-responses.js`, and
  `open-sse/utils/stream.js`.
- Current overlay tooling:
  `tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1`,
  `tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1`.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: inspect source, inspect history, capture commit IDs, and create redacted structural fixtures.
- Stop for: authentication, installation, global-runtime mutation, or missing target source.

**Steps:**

1. Record LightRSI and 9Router repository URLs, target HEADs, package versions,
   launch commands, and current overlay applicability.
2. Locate the actual `/responses/compact` request construction and the nearest
   existing Codex adapter tests.
3. Classify each compaction transport separately: explicit
   `POST /v1/responses/compact`, local summarization through `/v1/responses`,
   and ordinary `/v1/responses` traffic.
4. Record the reliable compaction signal for each transport. Do not use
   `tools: []`, historical `web_search_call`, or summarization prompt text as
   an implicit signal.
5. Prove explicit compact routing is `POST /v1/responses/compact` inbound and
   that LightRSI forwards to upstream `/v1/responses/compact`, not the normal
   `/v1/responses` helper.
6. Locate 9Router's raw SSE error handling and completion-success path.
7. Confirm where configuration and operational tracing are canonical.
8. Record unresolved source or capability gaps in this plan before proceeding.

**Verification:** Source paths exist; target HEADs are recorded; inbound and
outbound compact endpoints are proven; existing tests and overlay dry-runs
execute without changing installed runtimes.

**Exit Criteria:** Both target repositories are materialized at known commits;
the compact route is proven end-to-end at the endpoint level; otherwise
execution stops with a concrete missing-source or routing blocker.

### Task 2: Prove Route-Specific Causality And Freeze Fixtures

**Purpose:** Establish the failure and comparison controls independently for
each compaction transport before choosing a production policy.

**Task Function:** Reproduction and backend boundary verification.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Causal validation, transport identity, and
regression fixture.

**Required Skills:** `skill-backend-verification`, `skill-test-driven-development`.

**Files And Symbols:** Private exact fixture and redacted/minimized fixture
locations in the LightRSI target test tree, selected during Task 1; no
credentials, URLs, reasoning text, or full conversation content in repository
telemetry.

**Dependencies:** Task 1.

**Authority:**
- Preauthorized local actions: replay the approved captured route, preserve sanitized evidence, and write redacted fixtures.
- Stop for: missing fixture provenance, new authentication, secret exposure, or unapproved provider access.

**Steps:**

1. Pin Codex version, LightRSI version, 9Router version, provider, model,
   endpoint, configuration, and fixture hash.
2. For explicit `/responses/compact`, replay the original payload and record
   the known failure.
3. Test any endpoint-supported historical schema mechanism without assuming
   `/responses` tool fields work on `/responses/compact`.
4. Remove exactly the historical `web_search_call` items as a removal control,
   leaving all other fields and item objects unchanged.
5. For local summarization through `/responses`, test current/default tools,
   `tools:[web_search]` with `tool_choice:"none"`, and removal control.
6. Repeat each comparison enough to distinguish deterministic behavior from
   transient success; record attempts, completion status, and every search
   event.
7. Execute one normal follow-up turn after each successful compaction and
   compare tool authority with baseline.
8. Store the exact sensitive reproduction outside source control with a hash.
9. Minimize and redact a source-controlled fixture only after proving the
   structural fixture preserves the relevant behavior.
10. Freeze structural hashes for original, candidate, projected, compact, and
    follow-up results; prove canonical history is unchanged.

**Verification:** Each tested route has reproducible baseline evidence; the
preservation candidate, removal control, search-execution count, continuation,
tool authority, retained-item equality, and canonical-history result are
recorded separately.

**Exit Criteria:** Evidence identifies one safe policy per verified route. If
the original failure cannot be reproduced, compaction purpose is ambiguous,
preservation expands authority, or removal does not preserve required state,
keep policy `off` and stop runtime edits.

### Task 3: Validate Corrected 9Router Preservation

**Purpose:** Validate the narrow router-owned compatibility path before
accepting a lossy LightRSI projection.

**Task Function:** Router compatibility implementation and boundary verification.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Tool authority, transport compatibility, and policy
selection.

**Required Skills:** `skill-backend-verification`,
`skill-test-driven-development`.

**Files And Symbols:** 9Router compact route, `_compact` marker, transport
selection, tool normalization, exact route fixtures, provider traces, and
focused router tests identified in Tasks 1–2.

**Dependencies:** Task 2.

**Authority:**
- Preauthorized local actions: edit isolated 9Router compatibility code and
  focused tests; run validation probes and record evidence.
- Stop for: production enablement, fallback retries, or authority expansion.

**Steps:**

1. Gate compatibility on trusted compact identity (`_compact` plus the proven
   compact route); ordinary `/responses` history stays unchanged.
2. Inspect both top-level `body.tools` and Lite `input[].additional_tools` for
   existing `web_search` declarations.
3. Preserve one existing declaration exactly, including restrictions and
   placement semantics; reject conflicting declarations as unsupported.
4. Synthesize a compatibility declaration only for the proven empty-tool
   compact shape and only with execution restriction accepted by the actual
   compact transport.
5. Add direct tests for compact history, compact without history, ordinary
   history, `_autoCodexWebSearch`, top-level restrictions, Lite restrictions,
   zero new search, and no declaration leakage on the next ordinary turn.
6. Assert the actual outbound URL ends in `/responses/compact`.
7. Prove zero new search events, successful compaction, same-thread
   continuation, and unchanged authority; otherwise select router `off`.

**Verification:** Preservation, restriction equality, search suppression,
continuation, authority equality, canonical-history equality, and removal
control are recorded with pinned route identity.

**Exit Criteria:** Corrected router preservation is evidence-backed on the
actual compact route. Missing or ambiguous evidence selects router `off`; no
LightRSI fallback is enabled from synthetic success alone.

### Task 4: Implement Selected LightRSI Routing And Fallback

**Purpose:** Add transparent compact forwarding and, only when Task 3 fails,
the smallest request-only stripping fallback.

**Task Function:** Focused adapter routing and fallback implementation.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Route ownership, fallback policy, explicit-history
scope, dependency safety, retry policy.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`.

**Files And Symbols:** LightRSI compact route and endpoint resolver discovered
in Task 1, existing Codex adapter tests, and the fallback projection owner only
if source inspection confirms one exists.

**Dependencies:** Task 3.

**Authority:**
- Preauthorized local actions: edit LightRSI compaction-adapter code and focused tests only.
- Stop for: edits to Context Cleaner, general reduction, normal `/responses`, or canonical history persistence.

**Steps:**

1. Add transparent inbound and outbound `/responses/compact` forwarding without
   reusing the normal `/responses` upstream helper.
2. Keep LightRSI compatibility policy to `off` or `strip`, defaulting to `off`.
3. Gate `strip` by reliable compact purpose, route, provider, endpoint, wire
   API, and material model/protocol dimensions.
4. For `strip`, omit only exact historical `web_search_call` items from a
   request-only projection.
5. Preserve retained-item deep equality, relative ordering, IDs, annotations,
   instructions, reasoning, ordinary calls, outputs, opaque fields, and unknown
   items.
6. Reject explicit required dependency breaks before send; preserve unknown
   reference semantics without speculative deletion.
7. Leave opaque `previous_response_id` or server-side history unchanged.
8. Send once and return operational metadata without logging payload contents.

**Verification:** Tests cover transparent compact forwarding, `off` and `strip`,
route/purpose mismatch, ambiguous `/responses`, unsupported shapes, dependency
validation, deep equality, canonical immutability, and repeat normalization.

**Exit Criteria:** Compact forwarding works unchanged; selected stripping
applies only at its verified boundary; ordinary traffic and unsupported shapes
remain unchanged; no compatibility retry exists.

### Task 5: Integrate LightRSI Route And Telemetry

**Purpose:** Apply selected projection exactly once at the live compaction
boundary.

**Task Function:** Backend integration.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Request behavior, telemetry, side-effect safety.

**Required Skills:** `skill-backend-verification`, `skill-code-standards`.

**Files And Symbols:** The compaction handler and existing tracing/configuration
owners resolved in Task 1.

**Dependencies:** Task 4.

**Authority:**
- Preauthorized local actions: edit compaction integration, configuration, and focused tests only.
- Stop for: retries, capability registries, persistence layers, thread creation, or ordinary-traffic rewrites.

**Steps:**

1. Route explicit compact requests to `/responses/compact` inbound and
   outbound before any fallback projection.
2. Apply the selected LightRSI fallback before the first upstream request.
3. Forward unchanged when disabled, purpose-ambiguous, route-unverified, or
   input is outside explicit-array scope.
3. Reject validation failure without upstream call or session mutation.
4. Send the transformed request once; surface failure unchanged.
5. Emit only operational metadata: rule ID, route, counts, changed state,
   validation result, upstream outcome, and duration.
6. Keep compatibility diagnostics out of model-visible context and session
   state.

**Verification:** Direct boundary tests assert inbound and outbound compact
classification, compact URL selection, upstream call count, exact forwarded
request, canonical immutability, disabled behavior, ambiguous-route behavior,
and no retry.

**Exit Criteria:** The selected policy succeeds through the integrated LightRSI
boundary on the exact fixture; the correct upstream endpoint is called once;
unaffected request classes retain existing behavior.

### Task 6: Preserve 9Router SSE Error Semantics

**Purpose:** Stop diagnostic masking independently of LightRSI transformation.

**Task Function:** Router stream/error handling.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Error ownership and observability.

**Required Skills:** `skill-backend-verification`, `skill-test-driven-development`.

**Files And Symbols:** 9Router SSE transformer, translator, stream utility,
and tests identified in Task 1; current overlay references are not assumed to
contain this fix.

**Dependencies:** Task 1 and Task 3; independent of LightRSI Tasks 2, 4, and 5.

**Authority:**
- Preauthorized local actions: edit demonstrated 9Router SSE/error loss points and focused tests only.
- Stop for: unproven route changes, response reconstruction changes outside scope, or production deployment.

**Steps:**

1. Prove the exact route where 9Router loses upstream `event: error` or
   `response.failed`; change only demonstrated loss points.
2. Detect upstream `event: error` before treating HTTP `200` as success.
3. Preserve meaningful upstream error type/message/status or equivalent
   structured failure for the consumer.
4. Ensure missing `response.completed` cannot become successful empty streaming
   output.
5. Keep successful Responses output reconstruction behavior unchanged.
6. Add raw SSE, HTTP, and completed-response regression tests.

**Verification:** Raw upstream error reaches consumer with original diagnostic
on the compact route; successful completion still emits required output; empty
stream is not reported as successful compaction; ordinary Responses behavior is
unchanged.

**Exit Criteria:** Focused router tests pass and direct compact-route boundary
probe shows no error masking. Generic transformer tests alone do not complete
this task.

### Task 7: Package Reversible Local Overlays If Required

**Purpose:** Make target changes installable and update-safe from this repository.

**Task Function:** Overlay packaging and repository integration.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Reversibility, exact-base safety, generated surface
ownership.

**Required Skills:** `skill-code-standards`, `skill-verification-before-completion`.

**Files And Symbols:**

- `tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/`.
- `tools/local-patch-hub/overlays/9router-responses/`.
- `tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1`.
- `tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1`.
- `tests/test_lightrsi_codex_overlay.py`.
- `tests/test_9router_responses_overlay.py`.

**Dependencies:** Tasks 5–6. This task is conditional and must not block core
LightRSI or 9Router correctness when direct target-repository deployment is
available.

**Authority:**
- Preauthorized local actions: add versioned patches, manifests, and overlay tests bound to resolved target HEADs.
- Stop for: generated-agent edits, package downgrades, or installation into global runtimes.

**Steps:**

1. Export minimal LightRSI and 9Router patches from target checkouts.
2. Add manifests with target repository, exact base commit, patch path, and
   workaround version.
3. Extend existing installers only where new patch paths require it.
4. Add overlay tests for exact-base selection, reverse applicability, and
   verification-only behavior.
5. Keep existing overlay versions intact.

**Verification:** `git apply --check` and reverse checks pass; overlay tests
cover clean, already-applied, wrong-base, and tracked-change cases.

**Exit Criteria:** When overlay deployment is required, fresh target checkouts
apply cleanly; installed runtime is untouched during test; reverse patch restores
original source. When direct target-repository deployment is used, record
`not applicable` and do not block correctness acceptance.

### Task 8: End-To-End Correctness And Continuity

**Purpose:** Prove compatibility, continuity, diagnostics, and rollback.

**Task Function:** Final backend verification.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** All implementation outcomes.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`.

**Files And Symbols:** Target integration tests, redacted fixtures, overlay
manifests, and current repository tests.

**Dependencies:** Tasks 2–6.

**Authority:**
- Preauthorized local actions: run focused tests and approved direct probes; record evidence.
- Stop for: production deployment, credential changes, destructive cleanup, or unapproved external calls.

**Steps:**

1. Run LightRSI unit and integration tests.
2. Run 9Router SSE/error tests.
3. Replay original, preservation candidate, and selected policy fixtures
   through the exact LightRSI + 9Router route.
4. Confirm compaction success and immediate same-thread normal-turn success.
5. Confirm zero search execution during preservation tests and no authority
   expansion on the next ordinary turn.
6. Confirm ordinary `/responses`, ambiguous-purpose routes, disabled policy,
   and server-referenced history remain unchanged.
7. Confirm telemetry contains no search content, URLs, reasoning, credentials,
   or full request bodies.
8. Record exact commands, exit status, attempt counts, and remaining limits.

**Verification:** Fresh automated output plus direct boundary evidence proves
success, failure, no retry multiplication, continuity, side-effect safety, and
rollback.

**Exit Criteria:** Original payload fails reproducibly; selected policy compacts
successfully; retained items deep-equal and ordered; search execution remains
zero where required; correct upstream compact endpoint is used; same-thread
continuation succeeds; ordinary traffic is unchanged; otherwise rollout stops.

### Task 9: Rollback And Installation Verification

**Purpose:** Prove deployment safety after core correctness passes.

**Task Function:** Release and rollback verification.

**Template Profile:**
- Controller-selected: `normal`

**Specification Coverage:** Reversibility and retirement.

**Required Skills:** `skill-verification-before-completion`.

**Files And Symbols:** Overlay manifests and installers when Task 6 applies;
otherwise target-repository deployment records.

**Dependencies:** Task 7 when applicable; otherwise Task 8.

**Authority:**
- Preauthorized local actions: run rollback and verification-only checks in disposable or isolated targets.
- Stop for: production rollout, branch disposition, or deletion of retained evidence.

**Steps:**

1. Disable policy and verify unchanged forwarding.
2. Reverse-apply overlays when overlays were packaged.
3. Confirm wrong-base and tracked-change protections.
4. Record rollback command, exit status, and restored target HEAD.

**Verification:** Workaround can be disabled or reversed without mutating
canonical history or leaving partial installation state.

**Exit Criteria:** Rollback/install evidence passes, or deployment remains
blocked while core correctness evidence remains preserved.

## Rollout And Retirement

- Ship policy `off` first; enable `preserve_with_schema` or `strip` only after
  route-specific Tasks 2–5 pass.
- Keep original failing fixture, preservation candidate, and selected projection
  permanently redacted.
- Monitor policy, route, normalization count, search-execution count, upstream
  outcome, continuation success, and masked-error count.
- Periodically replay original payload with workaround disabled after upstream or
  router updates.
- Disable, observe, then remove the rule only after repeated original-payload
  success, valid same-thread continuation, and no authority expansion.

## Execution Record

### Task 1 — Completed With Findings

- LightRSI checkout: `C:\Users\HOANG PHI LONG DANG\repos\longdang193\LightRSI`
  at `c05cafe502fb474ab28e29e9e184adba8446a6a1`; working tree clean.
- 9Router checkout: `C:\Users\HOANG PHI LONG DANG\repos\9router` at
  `e0be411184e67687171a1e13ae2e5686c14dd43a`; working tree contains unrelated
  user changes plus current uncommitted SSE edits.
- LightRSI inbound gateway currently accepts exact `POST /v1/responses`; pure
  forwarding separately handles `/v1/responses` and `/v1/chat/completions`.
- LightRSI upstream `endpointFor()` currently resolves only
  `/v1/responses`; no compact endpoint exists yet.
- 9Router has `POST /v1/responses/compact`, but its route marks the body with
  `_compact` and reuses the normal `handleChat` pipeline. This requires direct
  boundary proof before treating it as a valid compact upstream route.
- Baseline command completed successfully: LightRSI Codex adapter test suite,
  `473` passed, `0` failed.
- Fresh local rerun completed successfully: `pnpm lightrsi:test`, `35` passed,
  `0` failed. This is current source-local proof, not provider replay.
- Current Codex adapter rerun completed successfully: `476` passed, `0` failed.
  Codex adapter typecheck also passed.
- Source inspection confirms 9Router `POST /v1/responses/compact` sets
  `_compact` and `CodexExecutor.buildUrl()` appends `/compact`; direct provider
  boundary proof remains outstanding.

### Task 2 — Completed With Authorized Direct Replay

- Exact historical 429-item fixture remains unavailable; no private session log
  was promoted to source-controlled evidence.
- Authorized direct replay used existing Codex credentials and the verified
  provider route. `/responses/compact` returned `404` for both preserved and
  stripped payloads.
- Normal `/responses` with historical `web_search_call` items returned HTTP
  `200` plus an upstream SSE `error` and no `response.completed` event.
- Normal `/responses` after stripping historical search items completed with no
  search events. This selects the LightRSI request-only fallback and leaves
  router preservation disabled.

### Task 6 — Completed; Router Preservation Disabled

- Preserved upstream `event: error` SSE payloads in
  `open-sse/transformer/responsesTransformer.js` instead of emitting an empty
  `response.completed` event.
- Preserved upstream error details and failed status in
  `open-sse/transformer/streamToJsonConverter.js` for non-streaming clients.
- Added focused regression coverage in
  `tests/unit/responses-stream-error-preservation.test.js`.
- Focused verification passed previously: `3` test files, `8` tests.
- Fresh rerun command `npm test -- --run
  unit/responses-stream-error-preservation.test.js
  unit/responses-transformer-completed-output.test.js` passed `2` files and
  `4` tests. It remains generic transformer proof only.
- Broader adjacent run retains one unrelated pre-existing failure in
  `openai-responses-nonstream.test.js`: its `@/lib/usageDb.js` mock omits
  `trackPendingRequest`.
- LightRSI route-level verification now covers compact non-stream, compact SSE,
  and normal same-thread continuation behavior.
- 9Router primary checkout remains uncommitted and contains unrelated user
  changes; isolated verification worktree is
  `C:\tmp\9router-compaction-compat-e0be411`. No production install or rollout
  was attempted.
- Clean worktree assertions covered compact URL selection, SSE error
  preservation, no invented completion event, and non-stream failed JSON error
  details. Full Vitest run was not possible because no `vitest` binary is
  installed; no package installation was performed.

### Task 4/5/8 — Completed In LightRSI Checkout

- Added explicit non-pure `POST /v1/responses/compact` acceptance.
- Compact projection clones request payload and removes only historical
  `type === "web_search_call"` input items; canonical journal input remains
  unchanged.
- Shared projection now covers both non-stream and SSE upstream dispatch.
- Route tests pass for compact non-stream stripping, compact SSE completion, and
  same-thread continuation with ordinary-route history preserved.

### Tasks 7 And 9 — Completed

- Added exact-base 9Router compatibility overlay at
  `tools/local-patch-hub/overlays/9router-responses/e0be4111/`.
- Added exact-base LightRSI compact-route overlay at
  `tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/c05cafe5/`.
- Clean-base apply and reverse checks pass for both overlays.
- `python -m pytest tests/test_9router_responses_overlay.py tests/test_lightrsi_codex_overlay.py -q`
  passes `3` tests.
- Primary checkouts retain unrelated user changes; no production rollout was
  performed. The pre-switch LightRSI apply path invoked `install:codex`, but
  post-run config and hook hashes matched existing backups; future verification
  uses `-SkipInstall`.
- Disposable 9Router apply passed; reverse apply restored
  `e0be411184e67687171a1e13ae2e5686c14dd43a` cleanly.
- Disposable LightRSI apply passed; reverse apply restored
  `c05cafe502fb474ab28e29e9e184adba8446a6a1` cleanly.
- LightRSI typecheck passed; adapter suite passed `476` tests with `0` failures,
  including compact non-stream, compact SSE, and same-thread continuation.
- 9Router Node smoke passed for request-local compact routing, preserved SSE
  errors, no fabricated completion, and failed JSON diagnostics.
- 9Router wrong-base and tracked-change guards rejected as expected; both
  disposable targets ended clean at original HEAD.
- Vitest binary remains unavailable; no dependency installation performed.
- Added `-SkipInstall` so future source-only overlay verification cannot invoke
  global Codex, hook, daemon, or startup installation.

## Open Questions Or Assumptions

- Actual LightRSI compaction symbol, config owner, reliable local-compaction
  signal, and test command are not present in current workspace; Task 1 must
  resolve them.
- It is unknown whether `/responses/compact` accepts historical tool schema or
  `tool_choice:"none"`; validate on that route rather than inheriting ordinary
  `/responses` behavior.
- It is unknown whether 9Router's compatibility declaration must remain in
  `body.tools` or may be represented through Lite `additional_tools`; preserve
  the source declaration and placement semantics until route tests prove a
  transport conversion is safe.
- It is unknown whether conflicting top-level and Lite search declarations have
  a safe precedence; treat conflicts as unsupported rather than merging them.
- It is unknown whether local summarization exposes a trustworthy compaction
  marker to LightRSI. If not, LightRSI must not rewrite that traffic; Codex's
  compaction builder owns the fix.
- Citation annotations may reference omitted search-event IDs. Task 2 must
  determine whether an explicit required dependency exists. Reject only when
  proven broken; preserve unknown reference semantics unchanged.
- The static provider, endpoint, and model/route identity dimensions available in
  LightRSI must be named before enabling the flag.
- The exact upstream HTTP status/event contract for preserved SSE errors must be
  confirmed at each demonstrated 9Router loss point before choosing response
  shape.
- Existing LightRSI capability infrastructure is not verified in this workspace;
  do not create or assume a registry until source inspection proves one exists.

## Review Verdict

**core implementation and reversible packaging verified; production installation deferred**
— router-first ownership, LightRSI fallback scope, route-specific causal proof,
SSE preservation, same-thread continuation, exact-base overlays, and reverse
checks are verified. Persistent global installation and production rollout remain
deferred; disposable overlay rollback is verified.

## Verification

- Required route, adapter, overlay, and reverse-application checks pass.
- Full repository validation must pass before publication.
- No production installation or global runtime mutation occurs.

## Completion Criteria

- Required route, adapter, overlay, and reverse-application checks pass.
- No production installation or global runtime mutation occurs.
- Unknown capability and rollout questions remain explicit; no unsupported causal claim is published.
