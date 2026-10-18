---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: native-semantic-contract-finalization
parent_spec: none
targets:
  - scripts/project_os_runtime/codex_app_server.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - tests/test_codex_app_server.py
  - tests/test_secretary_results.py
  - tests/test_secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_skill_chief_of_staff.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-18-23-43-native-semantic-contract-finalization-plan.md
---

# Native Semantic Contract Finalization

## Review Basis

This plan reviews the supplied consolidated verdict against merged PR #104 at
`origin/main` commit `43b519b8c20a94d62fed86e650135b62a6dded04`. The current
checkout is an older pre-PR branch; implementation must start from `origin/main`
or a fresh worktree based on that commit. Existing untracked plans remain
preserved and are not part of this scope.

### Findings

### [P1] Recovery accepts an artifact's identity instead of the current request

`_reconcile_native_artifacts()` reads `attempt_id` from an existing result and
then validates the result against that same value. A reused output path can
therefore make a prior task appear to satisfy a different request. The smallest
safe correction is a deterministic request fingerprint persisted before
submission and matched against binding, submission, and result artifacts during
recovery.

### [P1] Final-answer collection does not prove final-answer provenance

The app-server collector accepts finalized assistant-like items and joins their
text, but the current contract does not require a protocol-supported final-answer
phase distinct from commentary or intermediate assistant messages. The smallest
safe correction is to preserve item boundaries, require exact thread/turn plus
final-answer provenance, reject unsupported protocol shapes, and treat identical
item replay as idempotent while rejecting conflicting payloads.

### [P1] Fatal reader wakeup can block while holding shared state

`CodexAppServerClient._set_fatal()` performs potentially blocking response-queue
writes while holding `_state_lock`. A full waiter queue can prevent both the
reader and request path from progressing, defeating the configured deadline. The
smallest safe correction is to snapshot waiters under the lock, publish fatal
state once, and wake waiters non-blockingly after releasing the lock.

### [P1] Semantic publication and retirement are conflated

The native path keeps the process owner alive through publication, but the final
outcome projection can still represent cleanup/retirement failure as publication
failure or settled resources. The smallest safe correction is to retain a
confirmed semantic result independently from settlement, expose structured
retirement proof, and classify failed retirement as
`NATIVE_RETIREMENT_UNVERIFIED` with recovery required.

### [P2] The direct Secretary path is still opt-in and legacy arbitration remains ordinary

`PROJECT_OS_CODEX_NATIVE_APP_SERVER=1` selects the direct path, while the default
still requires the Herdr/LightRSI path. The smallest safe correction is to make
the direct Secretary app-server path the default, keep legacy Secretary semantic
reconstruction behind an explicit compatibility mode, preserve CoS's canonical
Herdr transport for top-level MAIN AGENT lanes, and prohibit fallback after the
provider may have received `turn/start`.

### [P1] Current and legacy result contracts share too much validation

New app-server results still accept legacy authority/source alternatives and a
fabricated `completion_seq=1`. The smallest safe correction is a clean v2 current
writer/validator plus a tolerant read-only v1 legacy decoder; native IDs remain
opaque and no fabricated sequence field is used as proof.

### [P2] Deadline and ingress bounds are per-operation or late-applied

The current client uses a full timeout for individual waits and applies output
limits mainly at publication. The smallest safe correction is one attempt
deadline owned by Secretary and consumed by the client through publication/read-
back, bounded JSON/event/content ingress with explicit overflow failure, and
capability-driven event reduction without introducing a new compatibility service.

## Findings Preserved As Explicit Boundaries

The change is limited to Secretary's ordinary native semantic path. CoS
plan-bound top-level MAIN AGENT dispatch remains canonical through Herdr, which
continues to own lane delivery, DeepAgents pane execution, lifecycle diagnostics,
and settlement evidence. This plan does not remove, bypass, or redefine that
transport.

## Goal

Make the direct Codex app-server connection the ordinary semantic execution path
and close the remaining correctness gaps without adding a registry, database,
daemon, process pool, event bus, or second semantic observer.

A result is authoritative only when the current requested operation is bound to
one attempt, that attempt owns one native thread and one submitted native turn,
that exact turn completes with a protocol-supported finalized assistant answer,
and the redacted answer is atomically published and read back. Process
retirement, cleanup, CoS acceptance, and telemetry remain separate facts.

## Non-Goals

- Do not create a durable native-session service; ephemeral recovery remains
  conservative until measurements justify a separate capability.
- Do not remove LightRSI history, audit, replay, locking, or batching support;
  remove only its ordinary semantic-readiness and candidate-writer role.
- Do not remove, bypass, or redefine Herdr as the governed transport for CoS
  plan-bound top-level MAIN AGENT lanes. This plan removes Herdr/LightRSI only
  from ordinary Secretary native semantic reconstruction where the controlled
  app-server owns the required evidence.
- Do not automatically fall back to Herdr/LightRSI once `turn/start` may have
  been delivered. A fallback after binding is allowed only when non-delivery of
  `turn/start` is proven and the native process is verified settled.
- Do not weaken pre-submit binding, exactly-once submission, terminal completion,
  assistant ownership, bounded content, atomic publication, read-back,
  idempotent replay, conflict rejection, or independent acceptance/telemetry.

## Implementation Outcomes

### One current request identity

Derive a stable `request-fingerprint.v1` from exactly these canonical fields:
`task_sha256`, `repository_identity`, `git_revision`, `execution_role`,
`model_identity`, and `runtime_grant_digest`. Use the fixed field order and
canonical UTF-8 JSON encoding defined by one shared helper; absent optional
values use the canonical empty value. Exclude panes, temporary paths,
timestamps, process IDs, and executable paths. Persist the same fingerprint in
v2 binding, submission, and result artifacts before any recovery decision can
reuse them. Publication and recovery call this helper rather than deciding
field relevance independently.

### One strict current-result contract

Use `secretary-native-binding.v2`, `secretary-native-submission.v2`, and
`secretary-native-result.v2` for new app-server writes. Use one canonical
validator for publication, immediate read-back, recovery, and identical replay.
Require the versioned request fingerprint, attempt identity, native authority,
opaque session/thread/turn IDs, terminal `completed` status, assistant
ownership, semantic completeness, bounded redacted content, timestamp, and
content digest. Keep v1 artifacts strictly read-only through a separate legacy
decoder; do not add permanent conditional v1 branches to the current validator.

### One exact final-answer assembler

Collect only events for the bound thread and turn. Require assistant ownership,
finalized state, and protocol-supported final-answer provenance. Preserve item
boundaries and stable order. Identical duplicate item IDs are idempotent;
conflicting duplicate payloads fail closed. Unsupported provenance fails as
`NATIVE_PROTOCOL_INCOMPATIBLE` rather than concatenating commentary.

### Independent semantic and settlement state

A confirmed result remains confirmed even when retirement or cleanup is
unverified. Retirement evidence is structured and independently projected as
settled, unknown, or quarantined. Failed retirement uses
`NATIVE_RETIREMENT_UNVERIFIED` and sets recovery required without resubmitting a
confirmed turn.

### Direct default with explicit legacy Secretary mode

The default Secretary native mode is the owned app-server client. Legacy
Secretary semantic reconstruction is executable only by explicit migration or
debug selection; legacy artifact compatibility remains read-only. No automatic
fallback is allowed after `turn/start` may have been delivered. Ordinary
Secretary app-server execution does not read rollout directories, wait for
handoff/ACK files, or require LightRSI readiness. CoS top-level MAIN AGENT
dispatch remains on the canonical Herdr transport.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Plan state is Git-tracked; one lead controller owns the plan ledger.
- Start implementation from a clean worktree based on `origin/main` at
  `43b519b8c20a94d62fed86e650135b62a6dded04`.
- Preserve all unrelated working-tree changes and existing untracked plans.
- Use sequential tasks because protocol ownership, artifact identity, settlement,
  and default-path migration share the same semantic contract.
- Use focused red/green regression tests for every confirmed defect before broad
  integration verification.
- Keep legacy artifact compatibility read-only; legacy Secretary execution mode
  remains executable only by explicit selection until direct-path migration
  tests and one fresh live proof pass, after which deletion is a separate
  justified decision.
- No external authentication, installation, upstream repository edit, or
  destructive cleanup is authorized by this plan.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-semantic-contract-finalization`
- Base commit: `43b519b8c20a94d62fed86e650135b62a6dded04`
- Expected workspace: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\native-semantic-contract-finalization\project-OS-starter`; preserve existing untracked plans in the source checkout
- Next action: `execute Task 5: reconcile documentation and perform final proof`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | `codex/native-semantic-contract-finalization` | `codex` | none | request-fingerprint and strict-artifact regressions | `199 passed; focused and full result/runtime pair` |
| Task 2 | `completed` | `codex/native-semantic-contract-finalization` | `codex` | Task 1 | exact final-answer and fatal-reader regressions | `209 passed; protocol, artifact, and runtime focused suite` |
| Task 3 | `completed` | `codex/native-semantic-contract-finalization` | `codex` | Tasks 1-2 | independent publication/retirement state proof | `retirement evidence, confirmed-result preservation, and recovery regression passed` |
| Task 4 | `completed` | `codex/native-semantic-contract-finalization` | `codex` | Tasks 1-3 | default-path and legacy-isolation proof | `386 launcher/CoS tests passed; direct default and explicit legacy mode covered` |
| Task 5 | `completed` | `codex/native-semantic-contract-finalization` | `codex` | Tasks 1-4 | docs, validators, full suite, and bounded live proof | `1464 passed, 2 skipped; validators passed; bounded live probe reported OK with v2 publication and retired process` |

## Task Breakdown

### Task 1: Bind recovery to the current request and strict current artifacts

**Purpose:**
- Prevent stale output-path reuse and remove semantic ambiguity between new
  app-server results and historical LightRSI results.

**Task Function:**
- Implement request identity and current-result contract validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-risk identity and persistence contract work requires
  source-first control.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused artifact tests are the direct proof boundary.

**Specification Coverage:**
- Current request fingerprint is authoritative for recovery; artifact identity
  cannot redefine the requested operation.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`,
  `_run_normal_via_native_app_server`; `scripts/project_os_runtime/secretary_results.py:_validate_contract`.
- Modify: `scripts/project_os_runtime/secretary_results.py`,
  `scripts/secretary_live_runtime.py`.
- Verify: `tests/test_secretary_results.py`,
  `tests/test_secretary_live_runtime.py`.

**Dependencies:**
- Start from merged PR #104; preserve existing idempotent publication and
  uncertain-submission behavior.

**Authority:**
- Preauthorized local actions: edit declared source/tests and run focused tests.
- Stop for: schema migration requiring deletion, unresolved request fields, or
  any artifact whose current-request identity cannot be proven.

**Steps:**
- [x] Step 1: Define the versioned `request-fingerprint.v1` helper with one fixed
  field order, canonical encoding, and canonical empty values; add its digest
  to new binding, submission, and current app-server result artifacts.
- [x] Step 2: Introduce strict `secretary-native-binding.v2`,
  `secretary-native-submission.v2`, and `secretary-native-result.v2` validators;
  make v1 artifacts read-only through a separate compatibility decoder; remove
  `completion_seq` as current-path proof.
- [x] Step 3: Reconcile only when the current request fingerprint matches every
  available artifact; classify stale/conflicting evidence without relaunching or
  returning the old result.
- [x] Step 4: Add red tests for reused output paths, mismatched binding/submission/
  result identities, identical replay, conflicting replay, fixed fingerprint
  vectors, v1 read-only compatibility, and v2 required fields; implement the
  smallest passing correction.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py -k "fingerprint or reconcile or replay or conflict or legacy"`
- Expected: stale artifacts never satisfy a new request; matching artifacts reuse
  once; conflicting artifacts fail closed.

**Exit Criteria:**
- Recovery decisions are made from the current request and strict current
  artifacts, not from identity copied out of an old result.

### Task 2: Harden protocol routing and final-answer provenance

**Purpose:**
- Prevent commentary contamination, duplicate corruption, and fatal-path hangs.

**Task Function:**
- Correct the single app-server reader and bounded exact-turn collector.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: protocol and concurrency correctness require direct control.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fake-stream and deadline tests directly exercise the reader.

**Specification Coverage:**
- One reader classifies JSON-RPC envelopes structurally and exposes only exact,
  finalized, final-answer assistant content for the bound turn.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/codex_app_server.py:_read_stdout`,
  `_set_fatal`, `_request`, `wait_for_turn`.
- Modify: `scripts/project_os_runtime/codex_app_server.py`,
  `scripts/secretary_live_runtime.py` for the attempt deadline owner and
  publication/read-back budget.
- Verify: `tests/test_codex_app_server.py`.

**Dependencies:**
- Task 1 defines current artifact fields consumed by the collector.

**Authority:**
- Preauthorized local actions: edit the owned client/tests and run protocol tests.
- Stop for: installed protocol fields that cannot distinguish final answer from
  commentary; record `NATIVE_PROTOCOL_INCOMPATIBLE` rather than guessing.

**Steps:**
- [x] Step 1: Create one absolute `attempt_deadline` in
  `_run_normal_via_native_app_server`; pass it into `CodexAppServerClient` and
  consume the same remaining budget through initialize, thread/start,
  turn/start, collection, publication, and read-back. Use a separate small
  `retirement_deadline` grace interval only for process settlement.
- [x] Step 2: Fix fatal publication to set shared state and snapshot waiters
  under lock, then wake them non-blockingly outside the lock; add a shared fatal
  event or equivalent bounded wakeup check.
- [x] Step 3: Classify messages as response, notification, or server request by
  envelope shape rather than matching IDs alone; fail closed on unsupported
  server requests.
- [x] Step 4: Preserve item IDs/order and require exact thread/turn,
  assistant-owned, finalized, final-answer provenance. Treat identical duplicate
  payloads as no-ops and conflicting payloads as protocol conflicts.
- [x] Step 5: Bound message bytes, retained items, per-item text, total semantic
  content, and queued events. Filter irrelevant notifications before enqueue;
  required event oversize or queue overflow is classified explicitly as
  `NATIVE_RESULT_LIMIT_EXCEEDED`, wakes waiters, and never silently drops
  exact-turn evidence or blocks the reader.
- [x] Step 6: Add red tests for commentary-before-answer, intermediate assistant
  messages, other turns, duplicate IDs, conflicting IDs, full-queue malformed
  input, unsupported server requests, EOF, timeout, over-limit content, and
  publication/read-back deadline exhaustion.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_live_runtime.py`
- Expected: the reader exits within the configured deadline, never publishes
  commentary as the answer, and accepts only a proven final answer.

**Exit Criteria:**
- The client has one non-deadlocking reader, structural JSON-RPC routing, strict
  final-answer provenance, and bounded resource use.

### Task 3: Separate semantic confirmation from retirement and cleanup

**Purpose:**
- Preserve confirmed answers while reporting process-settlement uncertainty
  honestly.

**Task Function:**
- Reconcile semantic outcome, retirement proof, resource state, and recovery.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-cutting lifecycle state must remain under one owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct runtime failure-matrix tests provide proof.

**Specification Coverage:**
- Publication confirmation and retirement are independent state transitions.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`,
  `_reduce_resource_evidence`, `canonical_resource_inventory`,
  `_run_normal_via_native_app_server`; `scripts/project_os_runtime/reconciliation.py`
  only if a shared reducer is proven to own the projection.
- Modify: `scripts/project_os_runtime/codex_app_server.py::close`,
  `scripts/secretary_live_runtime.py` native retirement/projection owner, and
  only a shared reducer when required by direct-native evidence.
- Verify: `tests/test_secretary_live_runtime.py`, with Herdr cleanup regression
  coverage but no Herdr cleanup implementation change unless the reducer is
  demonstrably shared.

**Dependencies:**
- Tasks 1-2 provide a confirmed current result and exact native evidence.

**Authority:**
- Preauthorized local actions: edit lifecycle projection and focused tests.
- Stop for: any change that makes cleanup/acceptance/telemetry a prerequisite
  for an already confirmed semantic result.

**Steps:**
- [x] Step 1: Model semantic `unpublished -> confirmed` separately from
  settlement `active -> retired -> retirement_unverified`.
- [x] Step 2: Verify terminate/kill exit evidence in
  `CodexAppServerClient.close()` and expose structured retirement proof in the
  final Secretary invocation output without mutating the semantic result
  artifact or adding a retirement sidecar.
- [x] Step 3: Map publication-success plus retirement-failure to confirmed
  semantic result, unknown/quarantined resource state, recovery required, and
  `NATIVE_RETIREMENT_UNVERIFIED`.
- [x] Step 4: Add red tests for publication failure, retirement failure after
  publication, cleanup failure after publication, result-only restart recovery
  (`semantic=confirmed`, `settlement=unknown`, recovery required when policy
  requires), and empty-inventory verified settlement. Preserve CoS/Herdr cleanup
  semantics with regression-only coverage.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_attempt_contract.py`
- Expected: confirmed results survive settlement uncertainty; no false `settled`
  or publication failure is synthesized.

**Exit Criteria:**
- Semantic confirmation, retirement, cleanup, CoS acceptance, and telemetry are
  independently observable and recoverable.

### Task 4: Make direct Secretary native semantics default and isolate legacy semantic reconstruction

**Purpose:**
- Stop requiring LightRSI/Herdr semantic reconstruction for ordinary native
  Secretary execution and remove duplicated protocol ownership without changing
  canonical CoS top-level MAIN AGENT transport.

**Task Function:**
- Migrate the mode contract and retire ordinary-path reconstruction machinery.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: migration changes default behavior and has duplicate-work
  risk, so it requires direct integration control.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: launcher/runtime tests prove mode selection and submission
  boundaries.

**Specification Coverage:**
- Direct app-server is default for Secretary native semantics; legacy Secretary
  semantic reconstruction is explicit and cannot be used as a post-submission
  fallback or independent current-result writer. CoS plan-bound Codex and
  DeepAgents lanes continue through Herdr.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:run_normal`,
  `_run_normal_via_native_app_server`; `scripts/herdr_main_launcher.py` native
  launch/parser and handoff/ACK symbols; runtime documentation.
- Modify: `scripts/secretary_live_runtime.py`,
  `scripts/herdr_main_launcher.py`, and only the shared app-server owner needed
  to remove duplicate parsing.
- Verify: `tests/test_secretary_live_runtime.py`,
  `tests/test_herdr_main_launcher.py`, `tests/test_codex_app_server.py`.

**Dependencies:**
- Tasks 1-3 complete; no fallback may be introduced while submission uncertainty
  remains unresolved.

**Authority:**
- Preauthorized local actions: add explicit legacy-mode selection, update tests,
  and remove ordinary-path rollout/handoff/readiness calls.
- Stop for: a required upstream protocol capability not exposed by the installed
  Codex app-server; record a precise capability blocker instead of adding pane or
  rollout inference.

**Steps:**
- [x] Step 1: Make direct app-server mode the default for Secretary native
  semantics and require explicit selection for legacy Secretary semantic
  reconstruction; keep v1 artifact compatibility read-only.
- [x] Step 2: Define fallback precisely: after binding, fallback is allowed only
  when `turn/start` is proven not attempted or delivered and the native process
  is verified settled; once `turn/start` may have been sent, never auto-fallback.
- [x] Step 3: Route all ordinary Secretary app-server execution through
  `CodexAppServerClient`; remove duplicate launcher protocol parsing and ordinary
  only the duplicate Secretary app-server protocol branch and its
  rollout-directory/handoff/ACK attribution while preserving Herdr's canonical
  CoS dispatch, delivery evidence, lifecycle diagnostics, and settlement evidence.
- [x] Step 4: Remove LightRSI readiness gating and active legacy candidate writes
  from ordinary Secretary semantic completion while preserving historical readers
  and explicit legacy Secretary mode.
- [x] Step 5: Add red tests proving default direct Secretary mode, explicit legacy
  Secretary mode, no LightRSI requirement, no rollout reads, the precise fallback
  boundary, one protocol owner, and unchanged CoS→Herdr dispatch for Codex and
  DeepAgents lanes.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py`
- Expected: direct Secretary mode is selected without LightRSI, legacy Secretary
  mode is opt-in, uncertain delivery is never silently resubmitted, and CoS
  top-level lanes still use Herdr.

**Exit Criteria:**
- New Secretary native execution has one semantic source and one protocol owner;
  legacy artifact compatibility is read-only, legacy Secretary execution is
  explicit and temporary, and CoS Herdr transport remains canonical.

### Task 5: Reconcile documentation and perform final proof

**Purpose:**
- Prove the integrated contract and align canonical documentation with the new
  ownership model.

**Task Function:**
- Execute backend verification, documentation reconciliation, and final plan
  acceptance proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final cross-surface verification and acceptance evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository validators, full suite, and bounded live proof.

**Specification Coverage:**
- Exact request/attempt/thread/turn/result evidence, independent settlement,
  explicit legacy compatibility, and no stale ownership claims.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`,
  `skill-code-standards`

**Files And Symbols:**
- Inspect/modify: `docs/operating_system/runtime/runtime-surfaces.md`, affected
  tests, this plan, and generated surfaces only when canonical sources changed.
- Verify: native client, result reader, recovery process, launcher boundaries,
  repository validators, full suite, and one bounded live run.

**Dependencies:**
- Tasks 1-4 complete; all deviations and capability limits are recorded in Git.

**Authority:**
- Preauthorized local actions: run declared tests, validators, documentation
  checks, and one bounded live probe.
- Stop for: authentication/installation, unexpected external write, failed
  required validation, or any result not bound to the exact current request.

**Steps:**
- [x] Step 1: Run focused protocol, artifact, lifecycle, launcher, and recovery
  tests with fresh output.
- [x] Step 2: Run repository contract/planning validators, full `pytest`,
  `git diff --check`, and starter-kit checks when distributed surfaces changed.
- [x] Step 3: Run one bounded live native app-server probe proving current request
  fingerprint, binding-before-submit, exact turn completion, final-answer
  provenance, publication/read-back, retirement evidence, and independent
  outcome projection; record an immutable capability blocker if unavailable.
- [x] Step 4: Reconcile documentation and plan ledger; mark the plan completed
  only after verification returns `verified`.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-23-43-native-semantic-contract-finalization-plan.md`
- [x] `py -B -m pytest -q`
- [x] `git diff --check`
- Expected: fresh automated evidence, exact native live proof or an immutable
  named capability blocker, no unchecked required plan item, and no stale
  ordinary-path ownership claim.

**Exit Criteria:**
- Code, tests, artifacts, documentation, generated outputs, and plan ledger
  agree; the direct Secretary path is authoritative by default, all remaining
  Secretary legacy behavior is explicitly bounded, and canonical CoS→Herdr
  transport behavior is unchanged.

## Verification

- Focused protocol, artifact, lifecycle, and launcher tests from Tasks 1-4.
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-23-43-native-semantic-contract-finalization-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- Starter-kit build and validation when distributed runtime surfaces change.
- One bounded live app-server probe with exact current-request, binding, turn,
  answer, publication/read-back, and retirement evidence, or immutable
  `BLOCKED_CAPABILITY` evidence naming the missing interface and observed version.

## Completion Criteria

The plan may be marked `completed` only after fresh verification proves:

1. Recovery rejects stale output-path artifacts and reuses only artifacts whose
   request fingerprint, attempt, binding, submission, and result all match.
2. The app-server reader cannot deadlock on fatal publication, classifies JSON-RPC
   envelopes structurally, and enforces one bounded attempt deadline.
3. Only exact-turn, assistant-owned, finalized final-answer content can publish;
   commentary, reasoning, tools, other turns, duplicate conflicts, and unsupported
   provenance fail closed.
4. Current app-server writes use one strict validator and do not rely on
   fabricated completion sequences; current writes use the v2 artifact family,
   while v1 historical artifacts remain read-only.
5. Semantic confirmation survives retirement/cleanup uncertainty and exposes
   `NATIVE_RETIREMENT_UNVERIFIED` without falsely reporting settled resources.
6. Direct app-server mode is the default for Secretary native semantics, legacy
   Secretary execution is explicit, no automatic fallback occurs once `turn/start`
   may have been delivered, and no second semantic writer exists on the ordinary
   path.
7. Documentation and generated surfaces state the same ownership model as code,
   tests, and durable artifacts.
8. Full automated verification and bounded live proof pass, or the exact
   unavailable upstream capability is recorded immutably without synthetic success.
9. CoS plan-bound execution continues to dispatch top-level MAIN AGENTS through
   Herdr; this change does not alter CoS transport, lane ownership, or acceptance.
10. Retirement evidence is persisted in the final invocation output; result-only
    crash recovery reports semantic confirmation with unknown settlement rather
    than synthesizing settled resources or adding an unneeded sidecar.

Branch creation, commit, push, PR, merge, and worktree cleanup are separate
authorized actions and are not completion criteria for this implementation plan.
