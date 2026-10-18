---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: native-app-server-result-publication
parent_spec: none
targets:
  - scripts/herdr_main_launcher.py
  - scripts/secretary_live_runtime.py
  - scripts/project_os_runtime/codex_app_server.py
  - scripts/project_os_runtime/secretary_results.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_live_runtime.py
  - tests/test_codex_app_server.py
  - tests/test_secretary_results.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-18-22-11-native-app-server-result-publication-plan.md
---

# Native App-Server Result Publication

## Goal

Make the native Codex app-server connection the ordinary semantic execution path
for managed Secretary results. Project OS authorizes a result only when it
proves that the launcher-owned attempt created and bound the native thread,
submitted the exact turn once, observed that turn terminate with
`status=completed`, captured assistant-owned final content, and durably
published and read back the result before retiring the owned process.

LightRSI is optional normalization, history, audit, or recovery support; it
must not rediscover a result already proven by the controlled native connection.
Herdr remains an independent lifecycle/transport surface, CoS remains
acceptance authority, and usage/receipt evidence remains independent.

## Implementation Outcomes

### One native protocol owner

Add one bounded in-process app-server client that owns the child process,
initialization handshake, thread/turn submission, and one continuous reader.
The reader routes JSON-RPC responses by request ID, turn/item notifications to
the bound-turn collector, and unsupported server requests to a fail-closed
protocol error. Unknown informational notifications are diagnostic-only when
they cannot affect attribution or completion. Do not add a daemon, event bus,
or competing stdout readers.

### Exact attempt and turn attribution

Carry the launcher-created `attempt_id` through the Secretary normal-run
boundary. Persist the native thread/session binding before prompt delivery and
persist the returned opaque `native_turn_id` immediately after `turn/start`.
Fresh threads use an explicit zero-prior-turn boundary; resumed threads use an
opaque provider-owned cursor. Project OS must not manufacture cursor formats,
parse native turn IDs, or require `session:tN` naming.

Final semantic content is the ordered, finalized assistant message content for
the exact bound turn. Accumulate by stable native item ID and content order;
exclude reasoning, tool calls/outputs, progress diagnostics, and other turns.
If the protocol cannot distinguish finalized assistant content reliably, fail
closed as a capability/protocol problem rather than selecting the last delta.

### Minimal durable semantic publication

Keep binding, the small immutable `secretary-native-submission.v1` acknowledgement,
and `secretary-native-result.v1` focused on semantic identity,
exact native identity, terminal status, assistant ownership, bounded redacted
content, and deterministic digest proof. Publish atomically and verify the
persisted bytes by read-back before releasing the native process. Identical
replay is idempotent; conflicting replay fails closed. Transport paths, pane
metadata, LightRSI executable paths, cleanup settlement, CoS acceptance,
strict receipts, and 9router usage are optional evidence planes.

### Restart-safe lifecycle and honest failures

Reconcile existing binding/result before retrying. A missing turn acknowledgement
with possibly delivered input is uncertain delivery and must never be
auto-resubmitted. Durable/resumable native threads are required when post-crash
native recovery is supported; ephemeral threads only support recovery after the
result was published while the connection still owned the evidence.

Use specific local classes including `NATIVE_PROTOCOL_INCOMPATIBLE`,
`NATIVE_INITIALIZATION_FAILED`, `NATIVE_BINDING_FAILED`,
`NATIVE_SUBMISSION_FAILED`, `NATIVE_TURN_FAILED`, `NATIVE_TURN_INTERRUPTED`,
`NATIVE_RESULT_TIMEOUT`, `NATIVE_RESULT_CONFLICT`,
`NATIVE_RESULT_PUBLICATION_FAILED`, and `NATIVE_RETIREMENT_UNVERIFIED`.
Reserve `BLOCKED_CAPABILITY` for an unavailable required interface or
unsupported protocol version. Missing usage is telemetry-incomplete, not
semantic failure.

### Evidence-backed rollout decision

Make the native path ordinary only after focused contract tests and one bounded
live probe prove the full success path. If the installed upstream interface
cannot provide the required native operations, record an immutable blocker with
the missing operation and observed version/capability evidence; do not replace
it with rollout-directory heuristics, pane text, or a second history lookup.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `fresh checkout from e7e995a695df4715a98234e15aed15e7af47821a`; preserve the existing untracked plans and unrelated work
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared Project OS source/tests/docs and plan ledger; run declared local tests, validators, and bounded capability probes without changing external configuration
- User-approval actions: external repository writes, credentials, installing/upgrading Codex/Herdr/LightRSI, push, merge, destructive cleanup, and publication outside this repository
- Parallel ownership: `none`; protocol, lifecycle, and semantic contracts share one sequential owner
- Sequential fallback: complete protocol and contract tests first; if required upstream operations remain unavailable, stop the live-proof lane while retaining local fail-closed changes

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-app-server-result-publication`
- Base commit: `e7e995a695df4715a98234e15aed15e7af47821a` (PR #103 merged on `main`)
- Expected workspace: `fresh checkout from the base; preserve existing untracked plans as separate artifacts`
- Next action: `none; implementation and final verification complete`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | protocol contract tests | `424 focused tests passed; one reader, handshake, exact completion, filtering, and cleanup covered` |
| Task 2 | `completed` | current | `codex` | Task 1 | binding/publication regression tests | `submission ack, native result, binding/read-back, idempotent/conflicting replay, and no-LightRSI native path covered` |
| Task 3 | `completed` | current | `codex` | Task 2 | failure and cleanup matrix | `native failure labels, reconciliation failures, and empty-inventory cleanup regression covered` |
| Task 4 | `completed` | current | `codex` | Tasks 2-3 | recovery and migration tests | `published-result read-back reuse, uncertain-submission no-resubmit, and no-LightRSI native path covered` |
| Task 5 | `completed` | current | `codex` | Tasks 1-4 | live proof or immutable blocker | `427 focused tests; repository/planning validators; 1454 passed, 2 skipped; starter-kit build/validation; bounded live app-server proof with exact binding, completed turn, assistant capture, publication/read-back, and settled retirement` |

## Task Breakdown

### Task 1: Implement the owned app-server protocol boundary

**Purpose:**
- Replace competing native stdout readers and incomplete handshake behavior with one bounded, testable app-server client.

**Task Function:**
- Implement and verify native JSON-RPC lifecycle and event routing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-risk backend protocol and process-lifecycle work requires direct source-first control.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused protocol tests and direct process assertions are task-local proof.

**Specification Coverage:**
- Complete `initialize`, then send the required `initialized` notification; route responses, notifications, and server requests through one reader owner; accept only bound-turn `status=completed`; keep the owned child alive through publication and read-back, then reap it on scope exit or failure.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py::run_normal`, `scripts/herdr_main_launcher.py::_confirm_codex_start`, `scripts/herdr_main_launcher.py::_codex_completion_snapshot`, and current Codex runtime discovery helpers.
- Modify: `scripts/project_os_runtime/codex_app_server.py` (new client), `scripts/secretary_live_runtime.py` integration seam, and only launcher lifecycle symbols needed to pass native mode and attempt identity.
- Verify: `tests/test_codex_app_server.py` (new), `tests/test_secretary_live_runtime.py`, `tests/test_herdr_main_launcher.py`.

**Dependencies:**
- Discover the installed app-server command/API and JSON-RPC method/event names from local configuration or documented upstream behavior. If unavailable, preserve a fail-closed capability result and do not invent a command.

**Authority:**
- Preauthorized local actions: add the client and focused tests; use fake app-server streams and bounded local process fixtures; run focused tests.
- Stop for: missing/incompatible upstream protocol, credentials, or required external installation/change.

**Steps:**
- [x] Step 1: Define internal protocol result types and failure mapping for initialization, thread creation, turn submission, notifications, server requests, EOF, timeout, and process exit.
- [x] Step 2: Start the child and record ownership immediately after `Popen`; send `initialize`, wait for its response, send `initialized`, then create a fresh or resumed thread.
- [x] Step 3: Route all messages through one bounded reader owner; fail closed on unsupported server requests or unrelated events that prevent exact attribution.
- [x] Step 4: Submit one turn, capture its opaque acknowledgement, and collect only finalized assistant message items for the bound thread and turn. Preserve item IDs/order, exclude reasoning, tool calls/outputs, progress diagnostics, and other turns, and require `turn.status == "completed"` before exposing completion.
- [x] Step 5: Expose a context-managed session or equivalent scoped owner; keep it alive through binding, turn acknowledgement, completion, semantic publication, and read-back, then terminate/reap it on scope exit or failure while retaining retirement diagnostics separately.

**Verification:**
- [x] Fake stream proves `initialize -> response -> send initialized -> thread/start -> turn/start -> finalized assistant items -> turn completed` with interleaved responses and informational notifications.
- [x] Failure tests prove termination/reaping after initialization, binding, submission, reader, timeout, and malformed-message failures.
- [x] Assertions prove `idle`, failed, interrupted, unresolved, wrong-thread, and wrong-turn events never produce semantic success.
- [x] Content tests prove stable item IDs/order, exclusion of reasoning/tool/progress content, and rejection when the protocol cannot distinguish finalized assistant content.
- Expected: one reader owner, exact terminal status, and concrete process ownership are observable.

**Exit Criteria:**
- The client produces bound completed-turn evidence or a specific fail-closed native failure without leaking or double-reading the child, and its owner remains alive until the caller finishes publication/read-back.

### Task 2: Bind the launcher attempt and publish the exact native result

**Purpose:**
- Make launcher identity, native binding, turn acknowledgement, semantic content, and publication/read-back one ordinary path.

**Task Function:**
- Reconcile attempt identity and durable semantic evidence across the launcher/runtime boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-file identity and persistence contract with focused regression proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: binding/result tests directly exercise replay behavior.

**Specification Coverage:**
- Preserve PR #103's launcher-owned `attempt_id`, correlation-only `invocation_id`, deterministic redact-once publication/read-back, optional transport metadata, legacy `native_completed_turn` read-only compatibility, and no fabricated JSON-RPC request ID. Add only the remaining native boundary simplification: binding precedes submission and an opaque turn acknowledgement is durably recorded immediately.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py::SecretaryNormalRequest`, `build_normal_launcher_command`, `_native_binding_for_submission`, `run_normal`, `_native_completed_turn`, `_result_source_authoritative`, `_project_semantic_result`; `scripts/project_os_runtime/secretary_results.py::publish_native_binding`, `parse_native_binding`, `publish_native_result`, `parse_native_result`.
- Modify: `scripts/secretary_live_runtime.py` normal-run integration and `scripts/project_os_runtime/secretary_results.py` schemas/validation; touch `scripts/herdr_main_launcher.py` only if the native-mode integration still needs a compatibility-preserving adapter change. Add tests for the existing PR #103 invariants and the new submission acknowledgement.
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_secretary_live_runtime.py`, `tests/test_secretary_results.py`.

**Dependencies:**
- Task 1 returns exact bound native evidence and opaque thread/turn identities.

**Authority:**
- Preauthorized local actions: update local request/CLI contracts, persistence schemas, and focused tests; preserve backward-readable artifacts where tests establish compatibility.
- Stop for: conflicting artifact ownership, destructive migration, or a required external schema decision not represented by source/tests.

**Steps:**
- [x] Step 1: Treat the existing launcher-owned attempt boundary as a preserved invariant and add regression coverage proving normal Secretary does not replace it with a new semantic attempt ID.
- [x] Step 2: Replace synthesized `lightrsi.codex.cursor/v1`, `session:tN`, mandatory `lightrsi_cli_path`, and rollout-derived identity with fresh zero-prior-turn proof or an opaque resumed cursor.
- [x] Step 3: Persist the binding before prompt delivery and publish a small immutable `secretary-native-submission.v1` acknowledgement containing the opaque `native_turn_id` immediately after acceptance; distinguish publication failure from submission failure.
- [x] Step 4: Build `secretary-native-result.v1` from exact native completion evidence, publish/read back before retirement, and keep transport/usage/cleanup outside semantic admission.
- [x] Step 5: Preserve PR #103's idempotent identical replay, conflicting replay rejection, stable stored redacted content/digest, optional transport metadata, and read-only legacy compatibility.

**Verification:**
- [x] Tests prove the preserved PR #103 attempt-ID and correlation invariants across binding, result, cleanup, reconciliation, and retry.
- [x] Tests prove binding-before-submission and turn-ack persistence ordering.
- [x] Tests prove exact completed content publishes/read-backs, identical replay is idempotent, and conflicting replay fails closed.
- [x] Tests prove legacy `native_completed_turn` remains read-only compatible and no fabricated request ID is required.
- Expected: result is usable without LightRSI CLI lookup, Herdr receipt, cleanup settlement, CoS acceptance, or usage rows.

**Exit Criteria:**
- A controlled native completion produces a minimal durable result bound to the exact attempt and opaque turn.

### Task 3: Correct failure classification and cleanup projection

**Purpose:**
- Prevent observability gaps and cleanup projection from turning proven semantic results into false failures or false resource quarantine.

**Task Function:**
- Trace failure and resource state transitions and add regression proof for independent evidence planes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: state-machine debugging across shared result and resource reducers.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic failure matrix is the bounded validator.

**Specification Coverage:**
- Reserve `BLOCKED_CAPABILITY` for unavailable capability; preserve semantic confirmation through missing usage, CoS rejection, missing receipt, cleanup unresolved, or cleanup failure after publication; settle empty/reaped inventories concretely.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py::canonical_resource_inventory`, `_owned_resources`, `_reduce_resource_evidence`, `_normalize_invocation_outcome`, `run_normal` finalization; failure helpers in `scripts/herdr_main_launcher.py`.
- Modify: those reducers/classifiers and focused tests.
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_live_stability_probe.py`, and launcher failure tests.

**Dependencies:**
- Task 2 defines authoritative semantic result and owned-process retirement boundary.

**Authority:**
- Preauthorized local actions: patch reducers/classifiers and add deterministic regression tests.
- Stop for: a transition owned outside Project OS or an unscoped behavior change affecting unrelated executors.

**Steps:**
- [x] Step 1: Map broad outcomes to narrow native failure classes while preserving independent semantic, cleanup, acceptance, receipt, and telemetry fields.
- [x] Step 2: Correct empty/settled resource projection and prove verified retirement does not synthesize quarantine.
- [x] Step 3: Prove semantic confirmation remains readable when cleanup, CoS, receipt, or usage evidence is missing/unresolved.
- [x] Step 4: Prove failed, interrupted, timed-out, ambiguous, stale, malformed, wrong-session, and wrong-turn paths cannot publish completed.

**Verification:**
- [x] Run the deterministic failure matrix, including process failure after publication and cleanup failure after publication.
- Expected: each case returns a narrow failure class, preserves independent planes, and leaves no false retry authorization.

**Exit Criteria:**
- Failure and cleanup states describe their owning plane without changing semantic truth or permitting unsafe resubmission.

### Task 4: Make recovery explicit and retire semantic handoff coupling

**Purpose:**
- Add reconciliation-before-retry and remove ordinary-path dependence on rollout discovery, handoff/ACK, and second history reconstruction.

**Task Function:**
- Implement recovery decisions and migrate legacy native attribution behind an explicit switch.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lifecycle migration with replay and compatibility risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: recovery and migration tests provide bounded proof.

**Specification Coverage:**
- Existing result is reused; binding without result reconciles the same native state; uncertain delivery never means not submitted; durable versus ephemeral recovery is explicit; rollout/handoff is not semantic authority. Ordinary live success never requires LightRSI rediscovery. LightRSI may validate, normalize, audit, or recover an already-bound native turn, but it may not establish attempt/session/turn attribution independently.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py::_codex_rollout_paths`, `_discover_codex_native_handoff`, `_await_native_handoff_ack`, `_confirm_codex_start`; `scripts/secretary_live_runtime.py::_wait_for_native_handoff`, `_write_native_handoff_ack`, `run_normal`; `scripts/project_os_runtime/reconciliation.py` and related tests. Verify `scripts/project_os_runtime/lightrsi_reader.py` only for legacy/history compatibility if the adapter is not modified.
- Modify: direct-path control flow and recovery callers; remove legacy code only after the switch and tests prove native mode.
- Verify: launcher/runtime/recovery tests and fresh-reader recovery fixture.

**Dependencies:**
- Tasks 1-3 complete; native binding/result schema and failure classes are stable.

**Authority:**
- Preauthorized local actions: add local migration switch, recovery tests, and documentation; remove ordinary-path rollout/handoff use after direct-path tests pass.
- Stop for: unresolved external capability, data migration requiring deletion, or uncertain delivery without reconciliation evidence.

**Steps:**
- [x] Step 1: Encode the hard recovery table: binding absent plus proven undelivered input permits a new attempt; binding plus result returns the result; fresh ephemeral thread plus accepted turn but no result after process loss is delivery-uncertain and unrecoverable; durable/resumable thread plus `native_turn_id` and no result resumes/queries the exact turn before any retry.
- [x] Step 2: Reconcile artifacts before retry and return durable result without relaunch or duplicate publication.
- [x] Step 3: Put rollout discovery and handoff/ACK behind an explicit legacy switch; direct mode must not read rollout directories or wait for handoff files.
- [x] Step 4: Document durable/resumable versus ephemeral recovery, retain only opaque provider cursors for resumed execution, and remove LightRSI readiness from the ordinary live path.

**Verification:**
- [x] Tests prove restart reuse, binding reconciliation, no auto-resubmit after uncertain acknowledgement, and fresh-reader result reuse.
- [x] Tests prove legacy mode is explicit and direct mode never calls rollout discovery or handoff acknowledgement.
- [x] Tests prove the four recovery states above, including the ephemeral accepted-but-unpublished stop condition.
- Expected: recovery is deterministic from durable evidence and never depends on a second observer rediscovering the answer.

**Exit Criteria:**
- Restart and migration behavior are explicit, tested, and fail closed where native evidence is insufficient.

### Task 5: Reconcile documentation and perform final proof

**Purpose:**
- Prove integrated behavior and remove stale architecture claims without publishing an unproven positive live result.

**Task Function:**
- Execute backend verification, live capability proof, documentation reconciliation, and final plan verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final cross-surface verification and acceptance evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final validators and retained live/blocker evidence are acceptance proof.

**Specification Coverage:**
- End-to-end exact attempt/thread/turn/result evidence, independent settlement, and honest upstream deferral.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Inspect/modify: `docs/operating_system/runtime/runtime-surfaces.md`, affected tests, canonical plan ledger, and generated surfaces only when canonical sources changed.
- Verify: native client, launcher, result reader, fresh recovery process, repository validators, full suite, and starter-kit checks when distributed surfaces changed.

**Dependencies:**
- Tasks 1-4 complete; deviations and upstream capability gaps are recorded in Git-tracked evidence.

**Authority:**
- Preauthorized local actions: run declared focused/full tests, validators, one bounded live probe, and documentation/generated-surface checks.
- Stop for: authentication/installation, unexpected external write, failed required validation, or any result not bound to the exact turn.

**Steps:**
- [x] Step 1: Run focused backend tests for protocol, lifecycle, binding, publication, recovery, and failure classification (`427 passed`).
- [x] Step 2: Run `py -B scripts/validate_repo_contracts.py --repo-root .`, `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-22-11-native-app-server-result-publication-plan.md`, `py -B -m pytest -q`, and `git diff --check` (`1454 passed, 2 skipped`; validators and diff check passed).
- [x] Step 3: Run one bounded live probe proving initialize/initialized, exact thread/turn binding, completed status, assistant capture, publication/read-back, and retirement (`run_normal` returned `reported`/`completed`; binding, submission, and result artifacts were read back; resource state was `settled` with `reuse_blocked: false`; no LightRSI configuration was required).
- [x] Step 4: Update ownership docs and remove stale ordinary-path references to rollout attribution, handoff/ACK authority, LightRSI CLI readiness, and fake capability checks; retain legacy compatibility only behind its explicit path after migration tests passed.
- [x] Step 5: Run starter-kit build/validation because distributed runtime documentation changed (`Starter kit built` and `Starter kit validation passed`).

**Verification:**
- [x] Fresh focused/full automated output with retained evidence.
- [x] Fresh live proof with exact native attribution and no synthetic success.
- Expected: `skill-verification-before-completion` can return `verified` only with complete evidence and no hidden required blocker.

**Exit Criteria:**
- Code, tests, docs, plan ledger, and evidence agree; native capability is proven or honestly deferred without weakening the semantic contract.

## Verification

- `py -B -m pytest -q tests/test_codex_app_server.py tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_results.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-22-11-native-app-server-result-publication-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- One bounded live app-server probe with exact attempt/thread/turn/result/read-back/retirement evidence, or immutable `BLOCKED_CAPABILITY` evidence naming the missing upstream operation and observed version.
- Starter-kit build and validation when distributed runtime surfaces changed.

## Completion Criteria

The plan may be marked `completed` only after `skill-verification-before-completion` returns `verified` and fresh evidence confirms:

1. One owned reader completes the initialization handshake and routes responses, notifications, and server requests without competing stdout readers.
2. The exact launcher-owned `attempt_id` is used for binding, result, cleanup, reconciliation, and retry; `invocation_id` is correlation-only.
3. Binding precedes submission and the opaque native turn acknowledgement is persisted immediately after acceptance.
4. Only the exact bound turn with terminal `status=completed`, assistant-owned bounded content, and deterministic digest proof can publish.
5. Publication is atomic, read-back verified, idempotent for identical replay, and conflicting replay fails closed.
6. Cleanup, CoS acceptance, receipts, and telemetry remain independent; verified retirement does not falsely quarantine an empty inventory.
7. Restart recovery reconciles artifacts before retry and never resubmits uncertain delivery automatically.
8. Project OS does not manufacture cursor formats, parse native turn IDs, require a LightRSI CLI path, or use rollout/handoff inference on the ordinary path.
9. Ordinary native success is authorized from controlled app-server evidence and does not depend on a second LightRSI lookup. LightRSI may validate, normalize, audit, or recover an already-bound native turn, but may not establish attempt/session/turn attribution independently.
10. Live proof is fresh, or the exact unavailable upstream capability is recorded as an immutable blocker without synthetic success.

Branch disposition, commit, push, PR, merge, and cleanup are separate authorized
actions and are not completion criteria for this plan.
