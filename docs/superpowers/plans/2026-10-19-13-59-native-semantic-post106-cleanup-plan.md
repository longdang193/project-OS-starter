---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: native-semantic-post106-cleanup
parent_spec: none
targets:
  - scripts/project_os_runtime/codex_app_server.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/project_os_runtime/__init__.py
  - scripts/project_os_runtime/lightrsi_reader.py
  - scripts/secretary_live_runtime.py
  - tests/test_codex_app_server.py
  - tests/test_secretary_results.py
  - tests/test_secretary_live_runtime.py
  - tests/test_lightrsi_reader.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-19-13-59-native-semantic-post106-cleanup-plan.md
---

# Native Semantic Post-#106 Cleanup

## Review Basis

This plan reviews the supplied consolidated verdict against the merged PR #106
checkout at `0bece4e` (`main` and `origin/main`). The focused baseline run on
October 19, 2026 passed:

```text
210 passed in 2.60s
```

The verdict is directionally correct, but it should be narrowed to residual
implementation cleanup. PR #106 already establishes the current native v3
writer, binding-before-submit order, no automatic retry after uncertain
submission, result read-back, and the CoS-to-Herdr governed execution boundary.
No new semantic architecture or schema version is justified.

### Confirmed remaining findings

- `[P1]` `CodexAppServerClient.start_thread()` does not pass the resolved model
  to `thread/start`. `secretary_live_runtime.py` fingerprints the model from
  the request/profile, so the recorded identity can differ from the native
  execution configuration.
- `[P1]` The owned app-server writer does not handle short writes, uses a
  binary/text fallback, waits indefinitely on `queue.get()`, and `close()` does
  not send a writer sentinel or join reader/writer threads. `_read_stdout()`
  applies the byte limit after `readline()` may already have allocated a full
  oversized frame.
- `[P1]` A rejected rerun can overwrite the existing invocation output through
  the exception path in `_run_normal_via_native_app_server()`. That can destroy
  the independent recovery record even when the native result/binding/
  submission artifacts are valid.
- `[P1]` Recovery derives `attempt_id` from the persisted result and does not
  bind the preserved retirement record to that same attempt across every
  artifact. The result, binding, submission, and retirement evidence need one
  exact logical-operation, fingerprint, attempt, session, thread, and turn
  identity.
- `[P2]` Explicit resume still requires a manually supplied logical operation
  ID. Existing v3 evidence should be sufficient to discover and verify that ID
  when the caller omits it; a conflicting supplied ID must remain rejected.
- `[P2]` Project OS still carries the LightRSI live result reader and broad
  legacy semantic-selection branches. The current v3 validator is already
  strict; historical v1/v2 decoders must remain read-only, while current native
  execution should have one semantic validator and no live LightRSI observer.
- `[P2]` `_normal_request_fingerprint()` is stale and does not use the resolved
  runtime facts, while `run_normal()` and `_resolve_normal_request()` both read
  the Git anchor. The effective execution context should be resolved once and
  reused for fingerprinting, native binding, diagnostics, and recovery.

### Already satisfied and preserved

- Current v3 publication requires the app-server authority, native completed
  turn source, final-answer provenance, assistant ownership, and completed
  terminal status.
- Native binding is persisted before `turn/start`; a submission artifact blocks
  automatic resubmission when delivery may be uncertain.
- CoS plan-bound execution continues through Herdr, which owns governed lane
  delivery, lifecycle diagnostics, and settlement evidence.
- LightRSI internals, history, context optimization, replay, and audit remain
  outside this plan. Only Project OS's obsolete live semantic dependency is
  removed.

## Goal

Close the remaining post-#106 correctness and ownership gaps in the direct
Secretary Codex app-server path. Make recorded execution identity describe what
actually runs, preserve valid recovery evidence, finish owned process/thread
lifecycle handling, keep v3 stable, remove obsolete live LightRSI semantic
plumbing, and align documentation and tests with the resulting architecture.

## Implementation Outcomes

### One effective native execution context

Secretary resolves repository, Git revision, workspace reuse state, provider,
model, profile, role, grant digest, task identity, and logical operation once.
The resolved model and provider are bound to the native app-server launch, and
the resolved facts are reused consistently across v3 binding, diagnostics,
result read-back, and recovery. Only the computational semantic subset feeds
`request_fingerprint`; logical operation identity, workspace dirty state, and
`reuse_allowed` remain separate execution-context fields. Unknown workspace
identity permits execution but disables result reuse.

### Bounded owned transport and retirement

The app-server client writes complete binary frames or fails explicitly,
rejects expired queued work, bounds frame ingress before unbounded allocation,
and retires the child plus reader/writer threads within explicit limits. Thread
and process retirement evidence is available to settlement without converting a
confirmed semantic result into a false success.

### Recovery-safe v3 semantics

Rejected invocations never replace valid invocation output. Resume discovers the
logical operation from mutually consistent v3 artifacts when possible and
accepts only an exact artifact set. Retirement evidence is preserved only when
it matches the same attempt and native identities. Current v3 remains the only
write contract; v1/v2 remain tolerant read-only compatibility decoders.

### Simplified ownership and documentation

Project OS no longer uses LightRSI as a live Secretary semantic observer or
retains dead native compatibility orchestration. Herdr remains the governed
execution transport, LightRSI remains a context/history/replay/audit system,
and the runtime documentation states those boundaries without stale opt-in or
legacy-path claims.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the declared source, test, and documentation files; run the declared local tests, validators, diff checks, and one bounded native probe
- User-approval actions: push, merge, publication, dependency installation, external authentication, destructive recovery, or edits outside the declared targets
- Parallel ownership: `none; shared runtime and contract files require sequential edits`
- Sequential fallback: execute Tasks 1 through 5 in order, then execute Task 6 final verification and documentation reconciliation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `0bece4e`
- Expected workspace: `clean`
- Next action: none; implementation and final verification are complete
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused identity and binding tests | `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_live_runtime.py` — 191 passed |
| Task 2 | `completed` | current | `codex` | Task 1 | focused transport and lifecycle tests | `py -B -m pytest -q tests/test_codex_app_server.py` — 20 passed |
| Task 3 | `completed` | current | `codex` | Task 1 | recovery, conflict, and retirement tests | `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py -k "reconcil or conflict or retirement or resume or submission"` — 23 passed; broader native/result/runtime proof — 220 passed |
| Task 4 | `completed` | current | `codex` | Task 1, Task 3 | v3 validator and resume tests | `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py -k "v3 or resume or transport or legacy"` — 20 passed; broader runtime/result proof — 202 passed |
| Task 5 | `completed` | current | `codex` | Task 2, Task 4 | no-live-LightRSI and stale-symbol checks | `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py tests/test_herdr_main_launcher.py` — 550 passed; stale-symbol and cursor-scope checks passed |
| Task 6 | `completed` | current | `codex` | Tasks 1-5 | repository validators, full suite, and bounded live probe | focused matrix — 330 passed; repository and planning validators passed; full suite — 1458 passed, 2 skipped; diff check passed; bounded native probe `b74f80f4f8984dd7ae1711f5adbc225e` settled and retired |

## Task Breakdown

### Task 1: Bind the effective native execution context

**Purpose:**
- Make the model and other recorded identity facts describe the native
  execution that is actually launched.

**Task Function:**
- Canonical execution-context binding

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source change with direct contract and test impact

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task-local tests are sufficient before the independent final verification gate

**Specification Coverage:**
- Supplied verdict sections 1 and 11: resolve once, bind provider and model,
  apply the same effective context, and fingerprint only its computational
  semantic subset.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_resolve_normal_request`, `_normal_request_fingerprint`, `run_normal`
- Inspect: `scripts/project_os_runtime/codex_app_server.py:CodexAppServerClient.start_thread`
- Modify: `scripts/secretary_live_runtime.py:_resolve_normal_request`, `_run_normal_via_native_app_server`, `run_normal`
- Modify: `scripts/project_os_runtime/codex_app_server.py:CodexAppServerClient.start_thread`
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_codex_app_server.py`

**Dependencies:**
- Current v3 schema fields and existing profile-model resolution remain the
  source of truth; do not introduce a provider registry or schema v4.

**Authority:**
- Preauthorized local actions: edit the listed runtime/client/test symbols and run their focused tests.
- Stop for: unsupported app-server model parameter semantics, changed repository base, external authentication, or a required new configuration source.

**Steps:**
- [x] Step 1: Replace the stale fingerprint helper path with one immutable
  `ResolvedExecutionContext` returned by the resolver. Define its semantic
  fingerprint subset explicitly; exclude `logical_operation_id`, workspace
  dirty state, and `reuse_allowed` from `request_fingerprint`.
- [x] Step 2: Resolve provider configuration and model together, pass the
  provider through the existing app-server launch configuration, pass the
  model through `thread/start`, and record both applied values in invocation
  evidence.
- [x] Step 3: Resolve the Git anchor and workspace state once. Apply the reuse
  rule explicitly: clean/resolved revision permits reuse; deterministically
  fingerprintable relevant changes contribute their digest; unidentified
  relevant changes still execute but set `reuse_allowed=false`.
- [x] Step 4: Add tests where profile provider/model differ from ambient Codex
  defaults, proving native launch, `thread/start`, fingerprint subset, and
  diagnostics agree while workspace uncertainty disables reuse without blocking
  execution.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_live_runtime.py -k "model or resolved_request or fingerprint or thread"` — 191 passed
- Expected: the resolved provider and model are bound to native execution and
  persisted evidence; only the semantic fingerprint subset is hashed; unknown
  or unidentified workspace identity disables reuse without blocking execution.

**Exit Criteria:**
- One resolved context feeds native launch, fingerprinting, diagnostics, and
  recovery, with focused regression proof.

### Task 2: Complete bounded writer, reader, and process shutdown

**Purpose:**
- Ensure the owned app-server client cannot claim transport success for a
  partial frame or leave daemon threads waiting after retirement.

**Task Function:**
- Owned transport lifecycle hardening

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: concurrency and deadline behavior require direct controller review

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic fake-process tests cover the bounded contract

**Specification Coverage:**
- Supplied verdict section 2: complete writes, bounded queue work, bounded
  ingress, writer sentinel, joins, and explicit retirement evidence.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/codex_app_server.py:CodexAppServerClient._send`, `_write_loop`, `_read_stdout`, `close`
- Modify: `scripts/project_os_runtime/codex_app_server.py:CodexAppServerClient._send`, `_write_loop`, `_read_stdout`, `close`
- Verify: `tests/test_codex_app_server.py`

**Dependencies:**
- Task 1 supplies the attempt deadline and native request shape.

**Authority:**
- Preauthorized local actions: edit the client and its deterministic fake-process tests; run focused transport tests.
- Stop for: a required OS-specific process primitive, unbounded real dependency, or behavior that cannot be proven with the existing app-server boundary.

**Steps:**
- [x] Step 1: Make the writer queue carry the attempt deadline and reject
  expired queued work before writing.
- [x] Step 2: Use a binary-only frame writer that loops over short writes,
  rejects non-positive progress, flushes once, and acknowledges only a complete
  frame; remove the text fallback.
- [x] Step 3: Retain binary `readline(MAX_FRAME_BYTES + 1)` and reject oversized
  or unterminated frames before decoding; remove the text/fake fallback instead
  of adding a custom accumulating parser.
- [x] Step 4: Bound caller waits and check deadlines before queue chunks; when
  shutdown needs to unblock a blocking pipe operation, terminate/close the
  child and then perform bounded joins. Do not claim that the blocking OS pipe
  write itself observes a Python deadline. Add a writer sentinel and join only
  the writer and stdout-reader threads that actually exist; remove dead stderr
  reader/drain lifecycle residue.
- [x] Step 5: Add tests for short writes, zero-progress failure, expired queue
  entries, oversized input, missing newline, sentinel shutdown, bounded joins,
  and repeated close stability.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py` — 20 passed
- Expected: complete frames are acknowledged only after full binary delivery;
  malformed or oversized frames fail closed; caller waits and shutdown joins
  stay bounded, and every actually owned thread exits or is explicitly reported
  as unverified within the retirement bound.

**Exit Criteria:**
- Client transport and retirement have one bounded lifecycle with no blocking
  shutdown path outside the attempt/retirement limits.

### Task 3: Preserve recovery evidence and bind retirement to the exact attempt

**Purpose:**
- Prevent a rejected invocation from destroying valid evidence and prevent
  recovery from accepting retirement facts belonging to another attempt.

**Task Function:**
- Recovery identity and evidence preservation

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-risk artifact identity and failure-state behavior

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing artifact fixtures can prove identity and non-overwrite behavior

**Specification Coverage:**
- Supplied verdict sections 3, 4, and 8: preserve valid output, match exact
  attempt identity, and never auto-resubmit uncertain delivery.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`, `_run_normal_via_native_app_server`, `_apply_native_retirement_evidence`
- Inspect: `scripts/project_os_runtime/secretary_results.py:parse_native_result`, `parse_native_binding`, `parse_native_submission`
- Modify: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`, `_run_normal_via_native_app_server`
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_secretary_results.py`

**Dependencies:**
- Task 1 provides the canonical request fingerprint and logical operation.
- Task 2 provides bounded process retirement evidence.

**Authority:**
- Preauthorized local actions: edit recovery/publication code and artifact fixtures; run focused recovery tests.
- Stop for: any proposal to add a global registry, background reconciler, new sidecar family, or automatic resubmission after possible `turn/start` delivery.

**Steps:**
- [x] Step 1: Validate result, binding, and submission as one exact identity set
  including logical operation, fingerprint, attempt, session, thread, and turn.
- [x] Step 2: Store retirement identity in the invocation retirement evidence,
  or in an explicitly linked durable record, with the exact logical operation,
  fingerprint, attempt, session, thread, and turn identity. Require all six
  values to match before using preserved retirement evidence in recovery.
- [x] Step 3: Change the normal exception path so a rejected or conflicting
  invocation never writes or overwrites the requested output path. Retain the
  failure in memory and report it through the existing error channel without
  mutating another invocation's output.
- [x] Step 4: Keep semantic confirmation independent from retirement; report
  unknown retirement as recovery-required instead of synthesizing settled or
  not-required cleanup.
- [x] Step 5: Add tests for conflicting output paths, mismatched retirement
  attempts, preserved prior retirement, binding-only crash recovery, and no
  automatic retry after uncertain submission.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py -k "reconcil or conflict or retirement or resume or submission"` — 23 passed
- Expected: valid prior invocation output remains byte-for-byte unchanged after
  a rejected rerun because the rejected invocation does not write that path;
  mismatched artifacts fail closed; confirmed semantic results retain
  recovery-required settlement when retirement is unknown.

**Exit Criteria:**
- Recovery is exact-attempt and non-destructive, and no failure path can erase
  authoritative evidence.

### Task 4: Make resume self-discovering and keep v3 as the sole current semantic contract

**Purpose:**
- Remove caller dependence on manually copied operation IDs and eliminate
  duplicate current-semantic validation without redefining historical evidence.

**Task Function:**
- Contract boundary and resume simplification

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract compatibility and read-only historical migration behavior

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: contract fixtures and current runtime tests cover the boundary

**Specification Coverage:**
- Supplied verdict sections 5, 6, and 7: v3 stability, one current authority/
  source pair, and self-discovering explicit resume.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_results.py:_validate_contract`, `parse_native_result`, `parse_native_binding`, `parse_native_submission`
- Inspect: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`, `_result_source_authoritative`, `_select_authoritative_result_source`
- Modify: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts` and the current v3 consumer boundary only
- Modify: `scripts/project_os_runtime/secretary_results.py` only where duplicate v3 checks or resume identity extraction are proven redundant
- Verify: `tests/test_secretary_results.py`, `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Task 3 establishes exact artifact identity and non-destructive recovery.
- Historical v1/v2 decoders remain available for read-only parsing and are not
  rewritten to match v3.

**Authority:**
- Preauthorized local actions: edit current v3 consumption and resume discovery in the declared files; run contract tests.
- Stop for: schema renaming, v4 creation, reinterpretation of published v1/v2 evidence, or removal of a validator still required by governed legacy probes.

**Steps:**
- [x] Step 1: Resolve resume identity from mutually consistent v3 artifacts
  before allocating any fresh logical operation UUID when `--resume` omits an
  ID. Reject partial or conflicting artifact sets before normal execution.
- [x] Step 2: Reject a supplied operation ID that disagrees with discovered
  evidence, while allowing a matching explicit ID to continue through the same
  exact identity checks.
- [x] Step 3: Make direct current-v3 Secretary results bypass generic legacy
  semantic arbitration and use the canonical v3 validator for authority,
  source, provenance, and publication checks. Retain generic legacy/probe
  arbitration only where Herdr or probe compatibility still owns it.
- [x] Step 4: Add tests for omitted operation IDs, proving no fresh UUID is
  allocated before discovery, matching explicit IDs,
  conflicting explicit IDs, transport metadata omission, and historical v1/v2
  read compatibility.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py -k "v3 or resume or transport or legacy"` — 20 passed
- Expected: current native writes and reads remain v3-only; v1/v2 parse as
  historical evidence; resume works without a copied operation ID only when the
  artifact set is mutually consistent.

**Exit Criteria:**
- Current semantic admission has one v3 authority/source validator, explicit
  resume is self-discovering, and historical contracts remain unchanged.

### Task 5: Remove obsolete Project OS LightRSI and native compatibility plumbing

**Purpose:**
- Delete dead live semantic reader code after the current call graph proves
  that Secretary normal mode and governed Herdr observation no longer depend on
  it.

**Task Function:**
- Compatibility-surface deletion

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deletion follows call-graph and test proof rather than assumption

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: stale-symbol searches and focused replacement tests prove the deletion boundary

**Specification Coverage:**
- Supplied verdict sections 9, 10, and 16: remove Project OS's live LightRSI
  reader and binary/text compatibility branches while leaving LightRSI internals
  and governed Herdr execution intact.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_submitted_codex`, `_observe_bound_lightrsi_result`, `_configured_lightrsi_reader`
- Inspect: `scripts/project_os_runtime/__init__.py` LightRSI exports and `scripts/project_os_runtime/lightrsi_reader.py`
- Modify: `scripts/secretary_live_runtime.py`, `scripts/project_os_runtime/__init__.py`, and `scripts/project_os_runtime/lightrsi_reader.py` only after call-site proof; delete `tests/test_lightrsi_reader.py` only when its reader is deleted and no independent consumer remains
- Verify: `tests/test_secretary_live_runtime.py` and repository-wide stale-symbol searches

**Dependencies:**
- Tasks 2 and 4 provide the native transport and semantic contract that replace
  the obsolete live reader path.
- Preserve any LightRSI package code that has an independent current consumer;
  delete only Project OS-owned live semantic integration with no remaining
  caller.

**Authority:**
- Preauthorized local actions: remove declared dead symbols, update their direct tests, and run stale-symbol and focused test checks.
- Stop for: an active non-Secretary consumer, a required governed Herdr behavior, or a dependency that would force LightRSI internals to change.

**Steps:**
- [x] Step 1: Confirm the current call graph and classify each LightRSI reader
  call as normal semantic execution, governed observation, or historical test.
- [x] Step 2: Remove the normal semantic reader and any duplicate native
  compatibility branch, preserving Herdr-owned diagnostics and v1/v2 decoders.
- [x] Step 3: Remove now-unused exports, constants, imports, and tests; update
  probe tests to assert the remaining owner boundary.
- [x] Step 4: Verify no current source references the deleted live reader or
  native rollout/handoff compatibility symbols. Permit `pre_submit_cursor` only
  where it remains part of historical v1/v2 compatibility decoders or their
  fixtures; it must not remain in current v3/native rollout logic.

**Verification:**
- [x] `rg -n "LightRSIResultReader|_observe_bound_lightrsi_result|_configured_lightrsi_reader|PROJECT_OS_CODEX_NATIVE_APP_SERVER" scripts tests docs/operating_system` — no current matches
- [x] `rg -n "pre_submit_cursor" scripts tests docs/operating_system` — matches limited to v1/v2 compatibility validators
- Expected: no current Project OS Secretary live semantic reader or stale native
  rollout symbols remain; any retained `pre_submit_cursor` reference is confined
  to historical v1/v2 compatibility surfaces, and independent LightRSI
  internals are explicitly documented and tested.

**Exit Criteria:**
- Compatibility deletion is call-graph justified, leaves CoS-to-Herdr intact,
  and has no stale-symbol or focused-test failures.

### Task 6: Reconcile documentation and complete verification

**Purpose:**
- Prove the integrated behavior and make the runtime documentation state the
  same ownership and compatibility model as the code.

**Task Function:**
- Final integration verification and documentation reconciliation

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence and repository contract reconciliation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `skill-verification-before-completion` owns the final gate

**Specification Coverage:**
- Supplied verdict sections 13-17 and final steady state: preserve safeguards,
  keep evidence planes independent, keep classifications narrow, leave LightRSI
  internals alone, and document the final architecture.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed runtime and test files from Tasks 1-5
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `docs/superpowers/plans/2026-10-19-13-59-native-semantic-post106-cleanup-plan.md`

**Dependencies:**
- Tasks 1-5 complete with accepted task-local proof and no unresolved scope
  deviation.

**Authority:**
- Preauthorized local actions: update the declared runtime documentation and run all declared repository checks plus one bounded local native probe.
- Stop for: authentication, unavailable upstream capability without immutable evidence, failed required validation, or any result not bound to the exact current request.

**Steps:**
- [x] Step 1: Update runtime documentation after code changes so it states
  Secretary direct app-server v3 semantics, Herdr governed execution, and
  LightRSI history/context/replay/audit ownership.
- [x] Step 2: Run focused native, result, lifecycle, compatibility, and
  CoS/Herdr preservation suites. Assert that direct Secretary normal execution
  uses the app-server without Herdr or LightRSI, CoS Codex lanes use Herdr, and
  CoS DeepAgents lanes use Herdr/dcode-project. Focused matrix passed: 330 tests.
- [x] Step 3: Run repository contract and planning validators, full pytest, and
  `git diff --check`.
  Repository contract validation passed; planning artifact validation passed;
  full suite passed with 1458 passed and 2 skipped; `git diff --check` passed.
- [x] Step 4: Generate a unique probe ID, run one bounded native Secretary probe
  under `.tmp-tests/native-semantic-post106-cleanup/$probe/` as shown in the
  verification command, and record exact binding, submission, result,
  read-back, and retirement evidence. Record
  an immutable capability blocker instead of synthetic success if the upstream
  app-server is unavailable; clean only that disposable probe root after
  preserving required evidence. Probe `b74f80f4f8984dd7ae1711f5adbc225e`
  returned `READY`; provider `9router`, model `combo-normal`, transport
  `codex-app-server`, v3 request fingerprint and logical operation binding were
  present; the semantic result was reported, retirement was `retired`,
  finalization was `settled`, and `recovery_required=false`. The exact probe
  root was removed after evidence capture.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py` — 330 passed
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .` — passed
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-13-59-native-semantic-post106-cleanup-plan.md` — passed
- [x] `py -B -m pytest -q` — 1458 passed, 2 skipped
- [x] `git diff --check` — passed
- [x] `$probe = [guid]::NewGuid().ToString('N'); py -B scripts/secretary_live_runtime.py run --output ".tmp-tests/native-semantic-post106-cleanup/$probe/live-result.json" --cwd . --task "Return the word READY and nothing else."` — probe `b74f80f4f8984dd7ae1711f5adbc225e` passed and its disposable root was cleaned
- Expected: all declared checks pass; the live probe proves exact current-request
  binding and independent retirement or records the exact unavailable capability
  without synthetic success.

**Exit Criteria:**
- Code, tests, documentation, generated surfaces, and this plan agree; fresh
  verification returns `verified`; no required task, blocker, or scope
  deviation remains unrecorded.

## Verification

- `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-13-59-native-semantic-post106-cleanup-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- One bounded native Secretary run with exact request binding, v3 publication/read-back, and independent retirement evidence, or immutable named capability-blocker evidence.

## Completion Criteria

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified` and fresh evidence proves:

1. The provider used to launch the native app-server and the model sent to
   native `thread/start` match the resolved provider/model and diagnostic
   invocation evidence.
2. Workspace/Git identity is resolved once; unknown identity disables reuse but
   does not block ordinary execution.
3. The app-server client handles short writes, bounded frame ingress, expired
   queued work, sentinel shutdown, bounded joins, and explicit unknown
   retirement.
4. A rejected invocation never overwrites valid prior invocation output.
5. Recovery requires one exact logical-operation, fingerprint, attempt, session,
   thread, and turn identity, and preserves only matching retirement evidence.
6. Explicit resume discovers a consistent v3 operation ID before allocating a
   fresh one when the caller omits it, while conflicting or partial artifacts
   fail closed.
7. Current v3 remains the only semantic write contract; v1/v2 remain read-only
   compatibility evidence; no new schema or semantic architecture is added.
8. Project OS has no obsolete live LightRSI Secretary semantic observer or dead
   native rollout/compatibility path, while CoS-to-Herdr execution remains
   unchanged.
9. Documentation and tests describe the same current ownership model.
10. Focused tests include the CoS/Herdr preservation boundaries; repository
    validators, full suite, diff check, and bounded live proof pass, or the
    exact upstream capability blocker is recorded immutably without synthetic
    success.
11. No final verification command refers to a compatibility test deleted by
    Task 5, and any remaining `pre_submit_cursor` reference is limited to
    historical v1/v2 compatibility surfaces.

Branch creation, commit, push, PR, merge, and worktree cleanup remain separate
authorized actions and are not completion criteria for this plan.
