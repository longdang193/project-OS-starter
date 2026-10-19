---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: native-semantic-residual-closure
parent_spec: none
targets:
  - scripts/project_os_runtime/codex_app_server.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - tests/test_codex_app_server.py
  - tests/test_secretary_results.py
  - tests/test_secretary_live_runtime.py
  - tests/test_live_stability_probe.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_skill_chief_of_staff.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl
  - docs/superpowers/plans/2026-10-19-10-59-native-semantic-residual-closure-plan.md
---

# Native Semantic Residual Closure

## Review Basis

This plan reviews the supplied consolidated verdict against the current
Project OS checkout at `85de8c0` (`main` and `origin/main`) and the focused
baseline test run on October 19, 2026:

```text
437 passed in 4.42s
```

The verdict is directionally accepted. It does not require another architecture
redesign. It identifies residual correctness and deletion work around the
already-proven direct Codex app-server path.

### Confirmed findings

- `SecretaryNormalRequest` permits empty repository, Git, model, and grant
  identity fields, while `_normal_request_fingerprint()` falls back to
  environment variables. `_run_normal_via_native_app_server()` obtains the
  Git revision through `_read_only_git_anchor()` but discards it before
  fingerprinting. This leaves stale-result rejection dependent on caller
  configuration rather than canonical runtime facts.
- `_reconcile_native_artifacts()` trusts the attempt identity read from the
  existing result, does not compare a logical-operation identity, does not
  compare `native_thread_id` across every artifact, and reconstructs
  `cleanup: {state: not_required}` after a crash. Existing invocation output is
  not used as independent retirement evidence.
- `CodexAppServerClient.wait_for_turn()` stores inferred arrival order in the
  replay record. An identical replay of an item without an explicit native
  order can therefore conflict only because it arrived at a different time.
  `_read_stdout()` also applies its byte limit after `readline()` has already
  allocated the complete line, and `_send()`/`close()` still contain blocking
  operations outside the semantic deadline.
- `secretary-native-result.v2` currently accepts both LightRSI and app-server
  authority values and both current content-source values. The validator does
  not enforce one current authority/source pair, while runtime code repeats
  semantic-source checks outside `secretary_results.py`. Existing v2 artifacts
  are already published evidence, so this change must not redefine their
  meaning in place.
- Direct app-server orchestration and compatibility reconstruction remain in
  `herdr_main_launcher.py` and `secretary_live_runtime.py`, including the
  native-mode flag, rollout discovery, fabricated cursor, handoff/ACK files,
  and legacy writer/execution path. The current docs still describe direct
  app-server execution as selected by an environment flag and retain stale
  `v1` publication language.

### Preserved boundaries and non-goals

- Keep `CoS -> Herdr -> top-level MAIN AGENT` for governed lane delivery,
  lifecycle, diagnostics, and settlement evidence.
- Keep LightRSI for history, context optimization, replay, audit, and measured
  diagnostic work; do not add a completed-turn semantic interface to LightRSI.
- Keep semantic result, execution, settlement, acceptance, observability, and
  economics as independent evidence planes.
- Do not add a database, durable session service, process pool, global result
  registry, background reconciler, second semantic reader, or general
  transport-mode registry.

## Goal

Close the remaining correctness gaps in the direct Secretary Codex app-server
path, make recovery reconstruct only authoritative facts, introduce a singular
current `v3` contract without redefining published `v1`/`v2` evidence, and
remove duplicate native orchestration without changing the canonical
CoS-to-Herdr transport boundary.

## Implementation Outcomes

### Canonical request and recovery identity

Every ordinary Secretary run resolves repository, Git revision, model, role,
grant, task, and logical-operation facts from their owning sources before
binding. One `request-fingerprint.v1` is computed from the resolved
computational facts and reused for binding, submission, publication, read-back,
and recovery. Logical-operation identity remains separate from computational
fingerprint so an intentional retry with an identical request is not mistaken
for an old operation. A caller-managed operation identity is durable across
restarts; a standalone invocation gets a new identity unless the caller
explicitly requests resume of an existing operation. Reusing an output path or
matching a fingerprint alone never implies resume. Resolved context uses
`resolved`, `not_applicable`, and `unknown` states: repository identity and Git
revision are mandatory, and unknown semantically relevant identity disables
reuse rather than hashing an empty value.

Recovery reuses a result only when the current logical operation and request
fingerprint match, and when binding, submission, and result agree on attempt,
session, thread, and turn. Settlement is reconstructed independently from
durable invocation evidence; missing or uncertain retirement remains unknown
or quarantined and never becomes `settled` through result publication alone.

### Bounded, replay-safe native collection

The app-server client treats duplicate item IDs as idempotent when semantic and
provenance payloads match, retains first-established native order, and rejects
true conflicts. A shared semantic-content budget leaves room for the bounded
serialized artifact. Incoming JSON framing, writes, event queues, publication,
read-back, and retirement all have explicit bounded behavior under one semantic
attempt deadline plus a separate retirement grace budget.

### Singular current result contract

New writes use singular current `secretary-native-binding.v3`,
`secretary-native-submission.v3`, and `secretary-native-result.v3`. The v3
result requires Codex app-server authority, the
`native_app_server_completed_turn` source, `native_final_answer` provenance,
assistant ownership, logical operation, request fingerprint, attempt,
native session/thread/turn, completed status, and content digest facts.
Transport pane/session/agent metadata remains optional diagnostics. Existing
`v1` and `v2` artifacts remain read-only compatibility decoders; no current
writer emits them.

### One native protocol owner and aligned documentation

`codex_app_server.py` owns Codex JSON-RPC. `secretary_live_runtime.py` owns
direct Secretary-native orchestration. `herdr_main_launcher.py` owns governed
Herdr execution and observation only. Rollout discovery, fabricated cursors,
handoff/ACK reconstruction, duplicate app-server launcher code, fake capability
probes, and stale mode selection are removed. Canonical runtime documentation
describes the same ownership and compatibility model as the code.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared files, add or revise focused tests, run declared repository validators, run bounded local probes, and update this plan's task evidence
- User-approval actions: push, merge, publication, external repository writes, destructive recovery, branch changes, worktree cleanup, or any scope expansion beyond the declared files
- Parallel ownership: `none`; all tasks touch shared semantic contracts or their direct consumers
- Sequential fallback: complete Tasks 1 through 4 in order, then run Task 5 only after all required producer changes and focused tests pass

## Task Breakdown

### Task 1: Resolve request identity and truthful recovery

**Purpose:**
- Make request identity canonical and make crash recovery distinguish semantic
  confirmation from settlement evidence.

**Task Function:**
- Establish the shared request/recovery contract and its direct runtime proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-module backend contract work with identity and recovery risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused contract and runtime tests provide the bounded proof.

**Specification Coverage:**
- Automatic resolved request context; one versioned fingerprint; logical
  operation distinct from fingerprint; full attempt/session/thread/turn chain;
  reconcile-before-resubmit; independent settlement; atomic invocation output.

**Required Skills:**
- `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:SecretaryNormalRequest`,
  `ResolvedSecretaryRequest`,
  `_normal_request_fingerprint`, `_read_only_git_anchor`,
  `_normalize_invocation_outcome`, `_reconcile_native_artifacts`,
  `_run_normal_via_native_app_server`, `run_normal`
- Inspect: `scripts/project_os_runtime/secretary_results.py:request_fingerprint`,
  `_validate_binding`, `_validate_submission`, `_validate_contract`,
  `parse_native_binding`, `parse_native_submission`, `parse_native_result`
- Modify: `scripts/secretary_live_runtime.py` and
  `scripts/project_os_runtime/secretary_results.py`
- Verify: `tests/test_secretary_live_runtime.py` and
  `tests/test_secretary_results.py`

**Dependencies:**
- Current checkout `85de8c0` and the confirmed baseline test run.

**Authority:**
- Preauthorized local actions: add the resolved request context and logical-operation fields, change artifact parsing/publication, add atomic invocation-output writing, and add focused regression tests.
- Stop for: a required identity owner is not discoverable from current Project OS sources, an existing consumer requires the old artifact shape, or recovery would need a new registry or sidecar.

**Steps:**
- [x] Step 1: Add an immutable resolved request context owned by
  `secretary_live_runtime.py` containing `task_sha256`, repository identity,
  Git revision, execution role, effective model identity, and effective runtime
  grant digest. Resolve values from the existing Git/profile/runtime owners;
  remove environment-variable fallback as the source of truth. Model each
  field as `resolved`, `not_applicable`, or `unknown`; preserve explicit
  `not_applicable` only where the fact truly does not apply. Repository identity
  and Git revision are mandatory, repository identity is stable across Git
  worktrees, and unknown computation identity disables reuse.
- [x] Step 2: Keep `logical_operation_id` separate from the fingerprint and give
  it a durable or caller-owned source. A managed caller supplies an existing
  operation identity; a standalone invocation creates a new one by default;
  explicit resume reuses the operation identity recovered from its durable
  binding/result evidence. Do not infer resume from an output path or matching
  fingerprint. Carry the identity through invocation output, binding,
  submission, and result artifacts. Compute `request-fingerprint.v1` exactly
  once from the resolved computational context.
- [x] Step 3: Require the logical-operation identity in current v3 binding,
  submission, and result artifacts. Extend `parse_native_*` APIs to compare the
  current operation, fingerprint, attempt, session, thread, and turn rather
  than taking the expected attempt from the artifact being recovered. Leave
  historical v1/v2 parsing available through read-only compatibility decoders.
- [x] Step 4: Rewrite `_reconcile_native_artifacts()` around the compact
  decision table: matching result plus matching binding and submission reuses
  semantic evidence; any accepted or uncertain submission never auto-resubmits;
  after restart, a binding without a submission is delivery-uncertain and never
  auto-resubmits. Only a same-process failure where code knows `turn/start` was
  never attempted and verified child retirement may start a new attempt; do not
  add durable artifacts solely to optimize that case. A different logical
  operation never reuses an identical fingerprint.
- [x] Step 5: Read prior invocation output only for settlement evidence. Preserve
  `retired`, `unknown`, or `quarantined` state; never synthesize
  `cleanup:not_required` from result presence. Add a small atomic temp-file,
  flush, `fsync`, and replace helper for invocation output and use it on the
  normal path before any recovery result is returned.
- [x] Step 6: Add regressions for stale output paths, unknown repository or Git
  identity, logical-operation mismatch, explicit resume, matching recovery with
  unknown retirement, same-process known-never-attempted retry, restart
  binding-only uncertainty with no auto-retry, accepted submission without
  result, thread mismatch, atomic output replacement, and semantic confirmation
  surviving retirement uncertainty.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py`
- Expected: current identity is resolved without environment-only Git facts;
  stale and cross-operation artifacts are rejected; uncertain delivery is never
  resubmitted; matching recovery preserves independent settlement state.

**Exit Criteria:**
- One resolved request context and one fingerprint govern the full native
  attempt, and recovery no longer invents cleanup or accepts the artifact's own
  identity as proof of current-request ownership.

### Task 2: Bound native event collection and retirement

**Purpose:**
- Make replay, input framing, writes, event queues, deadlines, and retirement
  behavior fail closed without late allocation or hidden blocking.

**Task Function:**
- Harden the owned Codex JSON-RPC client at its direct process boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded process I/O and lifecycle work with concurrency risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fake-process boundary tests cover the required I/O and timing cases.

**Specification Coverage:**
- First-occurrence item ordering; idempotent identical replay; true conflict
  rejection; shared content/artifact budgets; bounded wire input; one semantic
  deadline; bounded writes; separate retirement grace; narrow failure classes.

**Required Skills:**
- `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/codex_app_server.py:wait_for_turn`,
  `_send`, `_read_stdout`, `_set_fatal`, `_put_event`, `close`, `_deadline`
- Inspect: `scripts/project_os_runtime/secretary_results.py:NATIVE_RESULT_MAX_BYTES`
- Modify: `scripts/project_os_runtime/codex_app_server.py` and the shared
  budget constants in `scripts/project_os_runtime/secretary_results.py`
- Verify: `tests/test_codex_app_server.py`,
  `tests/test_secretary_results.py`, and
  `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Task 1's current v3 identity fields and artifact-size owner.

**Authority:**
- Preauthorized local actions: change the owned app-server client's framing, queue wakeup, send, wait, close, and item-reduction logic and add fake-process regressions.
- Stop for: a solution requires a new transport service, unbounded background writer, event bus, or a change to the Codex protocol beyond the existing JSON-RPC boundary.

**Steps:**
- [x] Step 1: Change duplicate-item reduction so the first item ID establishes
  native or inferred order once. Later identical IDs compare semantic text and
  final-answer provenance but ignore arrival position; conflicting payloads
  remain `NATIVE_PROTOCOL_INCOMPATIBLE`.
- [x] Step 2: Establish one shared serialized-result budget and a shared
  serialization-size helper using the exact JSON settings used for publication.
  Account for UTF-8 bytes after escaping, redaction, metadata, and a fixed
  maximum metadata reserve; use `ensure_ascii=False` consistently when
  compatible with the artifact contract. Reject oversized semantic content
  before publication with `NATIVE_RESULT_LIMIT_EXCEEDED`, while the final
  publisher remains authoritative for exact serialized size.
- [x] Step 3: Make the app-server stdio boundary binary. Read no more than
  `MAX_MESSAGE_BYTES + 1` bytes until newline, reject an unterminated or
  oversized frame, then decode UTF-8 and parse JSON. Write serialized JSON
  bytes plus `b"\n"`. Terminate the owned child through the existing retirement
  path after an overflow.
- [x] Step 4: Make `_set_fatal()` snapshot response queues under `_state_lock`,
  release the lock, and wake waiters non-blockingly. Keep event-queue overflow
  classified as a bounded result failure rather than allowing the reader thread
  to deadlock on a full waiter queue.
- [x] Step 5: Bound outgoing JSON message size and reproduce a blocked-write
  case at the current process boundary before changing concurrency. If strict
  cancellation is necessary, use one owned writer mechanism for the client
  lifetime, never one background thread per write or a new transport subsystem.
  Carry the absolute attempt deadline through initialize, thread/start,
  turn/start, event collection, publication, and read-back; child termination
  remains part of the retirement contract, and an unproven writer retirement
  produces retirement-unknown evidence.
- [x] Step 6: Give `close()` a separate short retirement grace budget. Persist
  `retired` only after an observed exit; otherwise return explicit unknown
  evidence and let runtime projection classify `NATIVE_RETIREMENT_UNVERIFIED`
  without invalidating confirmed semantic content.
- [x] Step 7: Add regressions for reordered duplicate replay, conflicting replay,
  oversized frames, malformed frames, full response queues, blocked writes,
  deadline exhaustion during every blocking phase, successful retirement,
  retirement timeout, and semantic-result preservation after retirement failure.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py`
- Expected: replay timing cannot create a false conflict; memory and serialized
  size are bounded before allocation/publication; all blocking phases honor the
  attempt deadline; retirement uncertainty is explicit and non-settling.

**Exit Criteria:**
- The native client has no known unbounded ingress, fatal-wakeup deadlock, or
  semantic-path blocking operation outside its declared deadline and grace
  budgets.

### Task 3: Introduce singular current v3 and canonical validation

**Purpose:**
- Remove current-contract cross-pairings and make one module authoritative for
  current semantic admission.

**Task Function:**
- Consolidate schema validation and separate historical decoding from current
  publication.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract simplification with migration and compatibility risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: schema fixtures and runtime admission tests cover the contract.

**Specification Coverage:**
- App-server-only v3 authority/source pair; required native thread and durable
  final-answer provenance; optional transport diagnostics; v1 and v2 read-only
  compatibility decoders; duplicate semantic validation removed; no fabricated
  completion sequence.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_results.py:_validate_contract`,
  `_validate_legacy_contract`, `normalize_for_publication`,
  `publish_native_result`, `publish_legacy_native_result`, `parse_native_result`
- Inspect: `scripts/secretary_live_runtime.py:_result_source_authoritative`,
  `_project_semantic_result`, `_run_normal_via_native_app_server`,
  `_run_normal_via_legacy_lightrsi`
- Modify: `scripts/project_os_runtime/secretary_results.py`,
  `scripts/secretary_live_runtime.py`,
  `tests/test_secretary_results.py`, and
  `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Tasks 1 and 2 define the current identity and bounded content fields.

**Authority:**
- Preauthorized local actions: add strict v3 validation and writers, retain v1/v2 read-only decoders, remove duplicate runtime semantic checks, delete unused legacy publication APIs, and update current-contract fixtures and tests.
- Stop for: a discovered migration consumer requires published v2 semantics to change, a required v3 final-answer provenance field cannot be obtained from the current app-server protocol, or a v2 consumer cannot be kept on the historical decoder path.

**Steps:**
- [x] Step 1: Introduce current v3 with the exact pair
  `native_authority=codex-app-server` and
  `content_source=native_app_server_completed_turn`. Preserve historical v1 and
  v2 authority/source values only inside read-only compatibility decoders.
- [x] Step 2: Require logical operation, request fingerprint, attempt, session,
  thread, turn, `terminal_status=completed`,
  `answer_provenance=native_final_answer`, `assistant_owned=true`, observed time,
  semantic content, and digest for v3.
  Make `transport` metadata optional in binding/result artifacts; do not require
  pane, transport session, or agent name for semantic admission.
- [x] Step 3: Keep v1 and existing v2 artifacts readable without redefining
  their historical meaning. Remove `completion_seq` as proof from the current
  v3 path, retain tolerant decoding only where the historical decoders require
  it, and ensure no current writer emits fabricated counters or v1/v2 artifacts.
- [x] Step 4: Make `secretary_results.py` the only current semantic validator.
  Replace runtime source/authority/status duplication with calls to the
  validator and retain runtime checks only for invocation and settlement
  context.
- [x] Step 5: Delete `publish_legacy_native_result()` only after repository-wide
  consumer search confirms it is unused. Keep `parse_native_result()` able to
  decode historical v1 and v2 evidence without allowing it to publish or satisfy
  current v3 admission. Leave executable legacy Secretary deletion to Task 4.
- [x] Step 6: Add positive and negative fixtures for the exact v3 pair, missing
  thread, missing provenance, missing assistant ownership, optional transport
  metadata, historical v1/v2 read-only decoding, mixed authority/source
  rejection in v3, fabricated sequence rejection, and canonical validator use.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py`
- Expected: only the app-server v3 pair publishes; v1/v2 parse but cannot write;
  runtime has one current semantic validator; all mixed and incomplete v3
  shapes fail closed with narrow failure kinds.

**Exit Criteria:**
- Current semantic admission is singular, strict, and independent of LightRSI
  or transport diagnostics.

### Task 4: Remove duplicate native launcher compatibility machinery

**Purpose:**
- Leave one Codex JSON-RPC owner while preserving governed CoS-to-Herdr lanes.

**Task Function:**
- Delete obsolete direct-native launcher orchestration and prove the retained
  transport boundary remains unchanged.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-file deletion with explicit compatibility and boundary risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: launcher regression tests and repository search provide the proof.

**Specification Coverage:**
- Direct app-server is the ordinary default; no automatic fallback after
  `turn/start`; Herdr retains governed delivery/observation; rollout/handoff,
  fabricated cursor, duplicate app-server branch, fake capability checks, and
  obsolete mode flags are removed.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:build_normal_launcher_command`,
  `_normal_managed_result_capability_available`,
  `_run_normal_via_legacy_lightrsi`, `_native_binding_for_submission`,
  `_wait_for_native_handoff`, `_write_native_handoff_ack`, `run_normal`
- Inspect: `scripts/herdr_main_launcher.py:_run_native_app_server`,
  `_launch_codex_native_app_server`, `_app_server_request`,
  `_discover_codex_native_handoff`, `_codex_rollout_paths`,
  `_await_native_handoff_ack`, `build_parser`, `_main_body`
- Modify: `scripts/secretary_live_runtime.py` and
  `scripts/herdr_main_launcher.py`
- Verify: `tests/test_secretary_live_runtime.py` and
  `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 3's strict v3 writer and read-only v1/v2 decoders.

**Authority:**
- Preauthorized local actions: remove duplicate direct app-server launcher branches, rollout/handoff/cursor artifacts, fake capability probes, obsolete mode flags, and their tests while preserving Herdr governed execution and diagnostic observation.
- Stop for: a concrete repository consumer still requires the deleted direct-native launcher or handoff artifact, or the deletion would change CoS-to-Herdr lane delivery, settlement, or acceptance ownership.

**Steps:**
- [x] Step 1: Make `run_normal()` invoke the direct app-server path by default
  without `PROJECT_OS_CODEX_NATIVE_APP_SERVER`; remove automatic fallback to
  Herdr/LightRSI after any possible native submission.
- [x] Step 2: Remove the native app-server branch from
  `herdr_main_launcher.py`, including its parser flags, JSON-RPC client helper,
  direct launch function, native binding writer, and direct-turn completion
  path. Leave the launcher responsible for governed Herdr MAIN AGENT execution.
- [x] Step 3: Remove rollout-directory diffing, `_native_cursor`, handoff and
  ACK files, and the corresponding Secretary wait/write helpers. Do not remove
  ordinary Herdr diagnostic fields that remain explicitly non-semantic.
- [x] Step 4: Remove `_normal_managed_result_capability_available()` and fake
  import-callable capability checks. Let real executable/protocol/provenance
  boundaries classify initialization, protocol, binding, submission, and
  result failures.
- [x] Step 5: Remove the executable legacy Secretary selector and both
  native-mode flags after the repository search in Task 3 confirms no concrete
  migration consumer. Preserve v1/v2 decoders as historical read-only behavior.
- [x] Step 6: Update launcher/runtime tests to prove direct Secretary execution
  does not require Herdr or LightRSI, uncertain delivery never falls back,
  obsolete artifacts are not created, and CoS plan-bound execution still uses
  Herdr's existing governed path. Include focused assertions from
  `tests/test_herdr_parallel_dispatch.py` and `tests/test_skill_chief_of_staff.py`:
  direct normal execution uses the app-server client without Herdr/LightRSI;
  CoS `codex` MAIN lanes use Herdr; and CoS `deepagents` MAIN lanes use the
  Herdr / `dcode-project` path.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py`
- Expected: direct normal execution owns one app-server client; no rollout,
  cursor, handoff, ACK, or legacy writer path remains; CoS-to-Herdr tests stay
  green and no post-submission fallback is possible.

**Exit Criteria:**
- `herdr_main_launcher.py` is no longer a second native semantic owner, and
  `secretary_live_runtime.py` has one direct current path plus read-only history
  decoding.

### Task 5: Reconcile documentation and complete verification

**Purpose:**
- Prove the final architecture at repository and direct runtime boundaries and
  align canonical documentation with the implementation.

**Task Function:**
- Perform final evidence collection, plan reconciliation, and acceptance review.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: broad verification with backend boundary and lifecycle proof.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently verify the final contract, deletion surface,
  and required proof before any completion claim.

**Specification Coverage:**
- Direct Secretary works without Herdr/LightRSI; CoS plan-bound work remains
  Herdr-governed; stale results do not recover; identical replay succeeds;
  uncertain delivery never resubmits; retirement uncertainty never settles;
  docs state one current architecture.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: all Task 1-4 modified files, `docs/operating_system/runtime/runtime-surfaces.md`, and the final Git diff
- Modify: `docs/operating_system/runtime/runtime-surfaces.md` and this plan's evidence only
- Verify: repository contract validators, focused tests, full tests, diff checks, and one bounded live app-server run

**Dependencies:**
- Tasks 1-4 completed with accepted task-local proof and no unrecorded scope deviation.

**Authority:**
- Preauthorized local actions: update canonical runtime documentation, run declared validators/tests/diff checks, run one bounded local native probe, and record exact unavailable capability evidence.
- Stop for: failed required proof, stale plan/Git state, an unexpected external dependency, or any live result that is not bound to the exact current request and retirement evidence.

**Steps:**
- [x] Step 1: Rewrite the Secretary runtime section in
  `docs/operating_system/runtime/runtime-surfaces.md` to state direct
  app-server strict v3 as ordinary semantics, v1/v2 as historical read-only,
  Herdr as the CoS governed lane owner, and LightRSI as optional history/audit/
  replay support. Remove contradictory opt-in and v1-publication language.
- [x] Step 2: Run focused tests and repository validators with fresh output:
  `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py`,
  `py -B scripts/validate_repo_contracts.py --repo-root .`, and
  `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-10-59-native-semantic-residual-closure-plan.md`.
- [x] Step 3: Run the full suite with `py -B -m pytest -q` and
  `git diff --check`. Any unrelated pre-existing failure is recorded with its
  exact command output and is not silently fixed in this scope.
- [x] Step 4: Run one bounded direct probe with
  `py -B scripts/secretary_live_runtime.py run --output .tmp-tests/native-semantic-residual-closure/live-result.json --cwd . --task "Return the word READY and nothing else."`.
  Confirm resolved request identity, binding-before-submit, exact thread/turn,
  final-answer provenance, atomic publication/read-back, and independent
  retirement evidence. If the required Codex app-server interface is genuinely
  unavailable, record `BLOCKED_CAPABILITY` with the missing executable or
  protocol operation and observed version; do not synthesize success.
- [x] Step 5: Reconcile every task checklist, deviation, blocker, and evidence
  entry. The approved plan is marked `completed` only after
  `skill-verification-before-completion` evidence is fresh and all required
  proof passes.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-10-59-native-semantic-residual-closure-plan.md`
- [x] `py -B -m pytest -q`
- [x] `git diff --check`
- [x] `py -B scripts/secretary_live_runtime.py run --output .tmp-tests/native-semantic-residual-closure/live-result.json --cwd . --task "Return the word READY and nothing else."`
- Expected: all required automated checks pass; the live probe proves exact
  current-request binding and independent retirement, or records an immutable
  capability blocker without synthetic success.

## Execution Evidence

- Focused proof: `542 passed` across the six declared runtime/result/server/
  launcher suites; the final runtime/stability subset passed `190 tests`.
- Repository proof: `validate_repo_contracts.py` passed all contract, adapter,
  template, metadata, generated-header, drift, and repo-config checks;
  `validate_planning_lifecycle.py` passed before completion and is rerun after
  this status/evidence reconciliation; `git diff --check` passed.
- Full proof: `py -B -m pytest -q` passed with `1457 passed, 2 skipped`.
- Live proof on October 19, 2026: the bounded probe returned exit code `0` and
  semantic content `READY`. Binding, submission, and result artifacts all use
  v3 and share logical operation `ada45a0ac2d44ac0907e6b90e4d75945`, request
  fingerprint `fbe08c5efb8fb84a9092e52729019f7f9514c4624d1bb1dab7ede9065745b28c`,
  session `01a153c4-0b6c-7c13-9e04-a024abbdffb2`, thread, and accepted turn;
  result provenance is `native_final_answer` /
  `native_app_server_completed_turn`, and retirement is independently
  observed as `retired` with top-level and inventory settlement.
- Plan-aligned maintenance: updated fail-closed evidence references after
  removing obsolete tests, and synchronized empty native resource inventory
  settlement with verified retirement evidence. No unrelated scope deviation
  or capability blocker remains.

**Exit Criteria:**
- Code, tests, docs, generated surfaces, and this plan agree on one current
  native semantic path; all required proof is fresh and recorded; no required
  identity, recovery, deletion, or validation task remains unresolved.

## Verification

- `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-10-59-native-semantic-residual-closure-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- One bounded direct app-server run with exact request binding, publication/read-back,
  and retirement evidence, or an immutable named capability blocker.

## Completion Criteria

The plan is ready for completion verification only when:

1. Request identity is resolved from canonical runtime owners, the fingerprint
   is computed once, and logical operation identity is separate from it.
2. Recovery matches current logical operation, fingerprint, attempt, session,
   thread, and turn; accepted or uncertain delivery never auto-resubmits.
3. Recovery preserves prior retirement evidence and never synthesizes
   `cleanup:not_required` or `settled` from result publication.
4. Duplicate replay is idempotent by semantic/provenance payload, while true
   conflicts remain rejected.
5. Wire input, semantic content, artifact publication, writes, event queues,
   and retirement are bounded with explicit timeout and failure behavior.
6. Current v3 has one app-server authority/source pair, durable final-answer
   provenance, and one canonical semantic validator; v1/v2 are read-only
   compatibility decoders and no current writer emits fabricated sequence
   proof.
7. Direct Secretary execution is the default and has no automatic fallback
   after possible submission; duplicate launcher app-server orchestration and
   rollout/handoff/cursor compatibility machinery are removed.
8. CoS plan-bound execution still dispatches through Herdr and retains its
   transport, lifecycle, diagnostics, settlement, and acceptance ownership.
9. LightRSI remains unchanged except for removal of Project OS dependencies on
   it for ordinary semantic completion.
10. Documentation and tests state the same current architecture, and all final
    automated and bounded live proof is fresh or records the exact unavailable
    capability without synthetic success.

Branch creation, commit, push, PR, merge, and worktree cleanup remain separate
authorized actions and are not completion criteria for this plan.
