---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
distribution_tier: project
name: cgw-runtime-ownership-convergence
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1
  - tools/local-patch-hub/Start-9RouterCodexCombo.ps1
  - tools/local-patch-hub/README.md
  - tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch
  - tests/test_9router_cgw_overlay.py
  - tests/test_9router_global_install.py
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - .github/workflows/runtime-contracts.yml
---

# CGW Runtime Ownership Convergence

## Goal

Make the CGW-backed web execution path predictable under contention by giving
each boundary one owner, carrying one attempt deadline through every phase,
classifying local capacity failures structurally, and proving the installed
overlay against the exact 9Router base it targets.

Preserve these ownership boundaries:

- Herdr owns pane lifecycle, normal CGW admission, and scheduling.
- 9Router owns transport and provider-versus-local failure classification.
- The shim owns only a bounded defensive queue and request cancellation.
- CGW owns actual provider execution capacity.
- Patch-hub owns overlay installation, receipts, and rollback.

Do not add another scheduler, reconciliation daemon, retry loop, account
fallback path, queue, or runtime registry. Do not reduce the shim queue's
default capacity without measurements showing that the defensive boundary is
causing material harm.

## Implementation Outcomes

### One bounded Herdr attempt

Herdr carries one absolute monotonic deadline from attempt admission through
shared CGW lock acquisition, prompt submission, and idle completion. Lock wait
and completion wait consume the same budget; pane ownership remains fail-fast.
The shared lock identity and preflight endpoint are derived from resolved
runtime configuration rather than hard-coded unrelated-instance ports.

### One local-capacity contract

The shim emits a structured local-capacity error for queue saturation while
retaining the existing HTTP boundary. 9Router classifies that code only in the
CGW context, stops account fallback, quota backoff, and combo branching for the
same local boundary, and never classifies identical prose from another provider
as CGW saturation.

### A defensive, cancellable shim queue

The shim keeps one active request plus its bounded defensive buffer, but queued
entries can be canceled or expire by queue-age/deadline before consuming
execution capacity. Disconnected requests do not remain indefinitely in the
queue. The shim remains a safety boundary for bypasses and duplicate attempts,
not the normal scheduler.

### A single readiness and installation contract

Herdr's normal admission check is explicitly a cheap listener/configuration
check and is not represented as authenticated inference proof. Startup,
installation acceptance, and explicit diagnostics use one authenticated minimal
inference contract. The overlay installer requires exact agreement among
manifest base, target HEAD, target package version, and receipt; 3-way apply is
diagnostic-only and cannot silently turn an old overlay into an installed one.

### Executable regression proof

Focused tests prove the total attempt deadline, cross-process lock behavior,
structured provider-scoped queue classification, queue cancellation and age
expiry, exact-base overlay selection, and one active CGW execution without
duplicate attempts or combo fallback. CI applies the pinned overlay in a
disposable 9Router checkout and runs the actual patched 9Router tests plus shim
tests instead of checking patch text alone.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-cgw-runtime-operations`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-central-config-layer`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `task-specific worktree created from the recorded base commit`; preserve unrelated user edits in the current workspace
- Commit policy: `no commits during execution until the plan is approved and the lead controller accepts each task-local proof`
- Preauthorized local actions: `read and edit the named repository files, create focused tests and disposable fixtures, run declared local checks, and inspect configured local CGW/9Router processes without changing credentials or permanent external runtime state`
- User-approval actions: `push, merge, publication, global runtime installation, credential changes, provider configuration changes, destructive recovery, and deletion or discard of unrelated user work`
- Parallel ownership: `none; the overlay patch is a shared canonical write surface and the readiness, error, and queue contracts must converge before integration proof`
- Sequential fallback: `Task 1 baseline, then Tasks 2-6 in order, then Task 7 final integration and verification`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-runtime-ownership-convergence`
- Base commit: `558a73ae809af857400ce74efc0b8ffbdb17b728`
- Expected workspace: `current workspace retains user edits in docs/operating_system/runtime/runtime-surfaces.md, scripts/deploy_agent_runtime.py, and tests/test_deploy_agent_runtime.py; CGW implementation uses a separate worktree`
- Next action: `after approval, create the isolated worktree, activate this plan, and run Task 1 baseline inventory`
- Blockers: `none; live CGW inference evidence is not a prerequisite for local contract work, but final live proof must stop as blocked if configured credentials or endpoints are unavailable`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | worktree | `unresolved` | none | baseline focused tests and source/ownership inventory | pending |
| Task 2 | `pending` | worktree | `unresolved` | Task 1 | Herdr deadline and lock regression suite | pending |
| Task 3 | `pending` | worktree | `unresolved` | Task 1 | structured local-capacity contract tests | pending |
| Task 4 | `pending` | worktree | `unresolved` | Task 3 | cancellation, queue-age, and bounded-capacity tests | pending |
| Task 5 | `pending` | worktree | `unresolved` | Tasks 1-4 | readiness/configuration and identity contract tests | pending |
| Task 6 | `pending` | worktree | `unresolved` | Task 1 | exact-base overlay and receipt tests | pending |
| Task 7 | `pending` | worktree | `unresolved` | Tasks 2-6 | disposable overlay integration and final verification | pending |

## Task Breakdown

### Task 1: Establish baseline and ownership map

**Purpose:**
- Record source truth, current tests, generated/embedded overlay boundaries,
  preserved user changes, and the exact callers that participate in the CGW
  attempt so later edits do not introduce a second owner.

**Task Function:**
- Repository truth, ownership, and regression-boundary audit.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `low ambiguity; source, tests, and the pasted review are the authoritative inputs`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `the inventory and baseline commands are directly reproducible`

**Specification Coverage:**
- Preserve the confirmed ownership split; use current source and tests over
  stale review assumptions; exclude unrelated working-tree edits; identify
  canonical overlay sources before modifying generated or embedded content.

**Required Skills:**
- `skill-cgw-runtime-operations`
- `skill-systematic-debugging`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_preflight_profile_runtime`, `_exclusive_file_lock`, `_shared_web_runtime_lock`, `_submit_codex_prompt`, `_wait_for_shared_web_runtime_turn`
- Inspect: `tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1:Get-OverlayRecords`, exact-base selection, receipt construction, and apply/verify branches
- Inspect: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:accountFallback.js`, `ping.js`, `model.js`, `server.js`, and patched unit tests
- Inspect: `tests/test_herdr_main_launcher.py`, `tests/test_9router_cgw_overlay.py`, `tests/test_9router_global_install.py`, `tests/test_skill_cgw_runtime_operations.py`
- Verify: `git status --short --branch`, `git log -5 --oneline`, current overlay manifest, and existing focused test commands

**Dependencies:**
- None; use base commit `558a73ae809af857400ce74efc0b8ffbdb17b728` and preserve the three unrelated modified files named in Coordination State.

**Authority:**
- Preauthorized local actions: `read repository files, inspect the overlay and runtime configuration, run baseline tests, and record preserved workspace changes`
- Stop for: `a different base commit, a conflicting ownership rule, a missing canonical overlay source, or a baseline failure that changes the approved CGW scope`

**Steps:**
- [ ] Step 1: Create the isolated worktree from base `558a73ae809af857400ce74efc0b8ffbdb17b728`; copy this proposed plan into the worktree and change only its status to `active` after approval.
- [ ] Step 2: Inventory all Herdr shared-lock callers, attempt-deadline helpers, preflight consumers, 9Router queue/fallback paths, shim queue entry points, startup readiness checks, and overlay receipt consumers.
- [ ] Step 3: Classify every proposed edit as canonical source, embedded overlay source, test, documentation, or generated adapter; prohibit edits to generated surfaces without their canonical source update.
- [ ] Step 4: Run `py -3 -m pytest tests/test_9router_cgw_overlay.py tests/test_9router_global_install.py tests/test_skill_cgw_runtime_operations.py tests/test_herdr_main_launcher.py -q` and record the baseline result without fixing unrelated failures.

**Verification:**
- [ ] `git status --short --branch` and `git diff --name-only 558a73ae809af857400ce74efc0b8ffbdb17b728`
- Expected: unrelated user edits remain identified and no CGW implementation files are modified before Task 2.
- [ ] `rg -n "_shared_web_runtime_lock|_submit_codex_prompt|CGW execution queue is full|Test-ThreeWayApply|20128|20129" scripts tools tests`
- Expected: every matching production path is assigned to one owner in the task evidence.

**Exit Criteria:**
- Base, preserved changes, canonical sources, shared write surfaces, baseline
  test output, and ownership assignments are recorded in the task evidence.
### Task 2: Carry one absolute deadline through Herdr CGW admission

**Purpose:**
- Prevent a shared-lock wait from receiving the full attempt duration again for
  prompt submission or idle completion, while preserving fail-fast pane
  ownership.

**Task Function:**
- Attempt-budget and cross-process lock contract correction.

**Template Profile:**
- Controller-selected: `review-1`
- Selection basis: `shared launcher semantics have high blast radius; resolve profile after Task 1 inventory`

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: `independent validation must cover timing and cross-process behavior rather than source shape alone`

**Specification Coverage:**
- One monotonic attempt deadline covers lock acquisition, assignment, and
  `agent wait --until idle`; lock contention is bounded by remaining budget;
  pane lock remains nonblocking; lock retries do not mask unrelated OS errors.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-cgw-runtime-operations`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_exclusive_file_lock`, `_shared_web_runtime_lock`, `_submit_codex_prompt`, `_wait_for_shared_web_runtime_turn`, and the attempt caller around line 3997
- Modify: `tests/test_herdr_main_launcher.py:shared runtime lock and web prompt tests`
- Verify: `scripts/herdr_parallel_dispatch.py` only if the shared attempt-deadline contract is consumed there; do not add a second deadline owner

**Dependencies:**
- Task 1 complete; preserve the existing `attempt_deadline` source and avoid introducing a parallel timeout registry.

**Authority:**
- Preauthorized local actions: `edit the named Herdr helpers and focused tests, run deterministic timing tests, and use disposable lock files or child processes for contention proof`
- Stop for: `the existing attempt contract cannot provide one absolute deadline, pane-lock behavior would change, or a fix requires a new scheduler/retry loop`

**Steps:**
- [ ] Step 1: Replace duration reuse with a deadline-aware helper that computes remaining monotonic seconds at each phase and treats expired budget as blocked/uncertain according to the existing attempt result contract.
- [ ] Step 2: Pass the deadline through `_shared_web_runtime_lock`, prompt submission, and `_wait_for_shared_web_runtime_turn`; preserve the lock across acknowledged submission and idle completion only for shared CGW web turns.
- [ ] Step 3: Keep `_pane_ownership_lock` fail-fast and narrow `_exclusive_file_lock` retry handling to recognized lock-contention errors, allowing unrelated `OSError` failures to surface immediately.
- [ ] Step 4: Add regression cases for lock release before deadline, total lock-plus-submit-plus-wait wall-clock bound, cross-process contention, timeout settlement, and pane-lock fail-fast behavior.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
+- Expected: all existing Herdr tests pass and new tests show the total elapsed time never exceeds the attempt budget except for the test harness tolerance.
- [ ] A disposable child-process contention test using the same lock path
- Expected: the second process waits only within remaining budget, then reports blocked/uncertain without submitting a duplicate turn.

**Exit Criteria:**
- Herdr has one end-to-end deadline, pane ownership remains fail-fast, and
  focused tests prove no duplicate admission or budget reset under contention.

### Task 3: Replace text-only queue saturation with a structured local-capacity contract

**Purpose:**
- Stop the shim's local queue boundary from being mistaken for provider quota
  exhaustion or an ordinary provider rate limit.

**Task Function:**
- Cross-boundary error contract and consumer classification migration.

**Template Profile:**
- Controller-selected: `review-1`
- Selection basis: `the canonical contract spans the embedded shim, 9Router fallback, and overlay tests`

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: `provider-scoped negative cases are required to prevent false CGW classification`

**Specification Coverage:**
- Queue saturation retains HTTP `429` at the local boundary but emits a stable
  code such as `cgw_queue_full` plus local-capacity metadata; 9Router uses the
  code and provider/route context rather than English message text; no account
  fallback, quota backoff, or combo fallback occurs for that local boundary;
  identical prose from a non-CGW provider remains ordinary provider handling.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-central-config-layer`
- `skill-cgw-runtime-operations`

**Files And Symbols:**
- Modify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:tools/cgw-codex-shim/server.js:WorkQueue and requestHandler error response`
- Modify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:open-sse/services/accountFallback.js:checkFallbackError`
- Modify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:tests/unit/account-fallback-cgw-queue.test.js`
- Verify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:src/app/api/models/test/ping.js and src/sse/services/model.js` for unrelated envelope, API-key, runtime lookup, and ambiguity changes
- Modify: `tests/test_9router_cgw_overlay.py` only for source-contract assertions that cannot be exercised in the disposable 9Router checkout

**Dependencies:**
- Task 1 ownership map; use the shim patch as the canonical source for the
  downstream 9Router runtime and do not add a second local-capacity schema in
  the repository.

**Authority:**
- Preauthorized local actions: `edit the embedded overlay contract and its downstream unit tests, generate disposable patched-runtime fixtures, and run Node and Python contract checks`
- Stop for: `the downstream 9Router error envelope cannot carry a stable code, provider context is unavailable at the classification boundary, or the change requires altering non-CGW provider semantics`

**Steps:**
- [ ] Step 1: Define the local-capacity error shape, including stable code, owner/scope metadata, HTTP status, and whether the request is eligible for one Herdr-controlled retry without account substitution.
- [ ] Step 2: Emit that shape from `WorkQueue` saturation and preserve the code through the shim's JSON error response and any 9Router transport wrapper.
- [ ] Step 3: Change `checkFallbackError` and combo fallback handling to branch on structured code plus CGW/provider context; remove the English-message-only decision path.
- [ ] Step 4: Review the same overlay hunk's `ping.js` and `model.js` changes. Keep only behavior required for CGW model identity/inference; split or remove unrelated provider-envelope, API-key-selection, runtime-lookup, and ambiguity changes from the overlay if they are not required by the CGW contract.
- [ ] Step 5: Add positive and negative tests for CGW queue saturation, provider `429`, identical prose from a non-CGW provider, account fallback, quota backoff, and combo branching.

**Verification:**
- [ ] Patched checkout Node test command for the overlay's `tests/unit/account-fallback-cgw-queue.test.js`
- Expected: local `cgw_queue_full` stops fallback/backoff/branching while ordinary provider `429` behavior remains unchanged.
- [ ] `py -3 -m pytest tests/test_9router_cgw_overlay.py tests/test_9router_global_install.py -q`
- Expected: the repository validates the structured contract and no assertion depends only on the old English message.

**Exit Criteria:**
- The local queue boundary has one stable error contract, 9Router consumes it
  only in the CGW context, and unrelated provider behavior is covered by a
  negative regression case.

### Task 4: Harden the shim queue without making it the scheduler

**Purpose:**
- Ensure canceled or stale queued requests release defensive capacity and do
  not create a second hidden admission/retry system.

**Task Function:**
- Bounded queue lifecycle and cancellation correctness.

**Template Profile:**
- Controller-selected: `review-1`
- Selection basis: `queue lifecycle is local and bounded, but cancellation races require focused backend reasoning`

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: `validator must exercise abort-before-start, expiry, and active-request cancellation paths`

**Specification Coverage:**
- Keep one active request plus the configured defensive queue; queued entries
  carry cancellation state and a queue-age or request-deadline bound; detached
  clients are removed or rejected before execution; no second scheduler,
  reconciliation loop, or unbounded queue is introduced.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-cgw-runtime-operations`

**Files And Symbols:**
- Modify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:tools/cgw-codex-shim/server.js:WorkQueue and requestHandler abort wiring`
- Modify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:tools/cgw-codex-shim/http.js and config limits only when required by the queue contract`
- Modify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:tests/unit/cgw-shim-queue.test.js`
- Modify: `tools/local-patch-hub/overlays/9router-cgw/87a74e1b/9router-cgw.patch:README.md` queue semantics and operational guidance

**Dependencies:**
- Task 3 structured local-capacity error contract; queue expiry must use the same
  owner/scope and must not invent a second error taxonomy.

**Authority:**
- Preauthorized local actions: `edit the embedded shim queue and focused Node tests, run deterministic abort/expiry tests, and document the defensive-only queue role`
- Stop for: `queue lifecycle changes require a second scheduler, a persistent queue store, a default-capacity reduction without measurements, or retry behavior outside Herdr`

**Steps:**
- [ ] Step 1: Add an item state that can be canceled while queued and ensure a canceled item is skipped without incrementing active execution or invoking `executeTurn`.
- [ ] Step 2: Add one queue-age or request-deadline check at dequeue time and return a structured local-capacity/expiration failure without requeueing.
- [ ] Step 3: Keep active request cancellation wired to the existing `AbortController`; ensure shutdown and client disconnect paths cannot leave active controllers or queued promises retained indefinitely.
- [ ] Step 4: Preserve the one-plus-eight default until a measured test demonstrates a capacity problem; document that Herdr's single-flight admission should keep normal queue depth near zero.
- [ ] Step 5: Add tests for canceled queued removal, queue-age expiry, active cancellation, shutdown cleanup, FIFO among live entries, and one active `executeTurn` call at a time.

**Verification:**
- [ ] Patched checkout Node test command for `tests/unit/cgw-shim-queue.test.js`
- Expected: canceled/expired entries never reach `executeTurn`; queue depth returns to zero; active concurrency never exceeds one.
- [ ] A bounded stress fixture with ten simultaneous requests
- Expected: only the configured active plus queued capacity is admitted, and local saturation returns `cgw_queue_full` without duplicate execution.

**Exit Criteria:**
- The shim queue is cancellable, age-bounded, FIFO for live work, and still a
  defensive boundary rather than a normal scheduler.

### Task 5: Simplify readiness and derive runtime identity from configuration

**Purpose:**
- Remove misleading readiness claims and hard-coded shared-runtime identity while
  avoiding a per-request inference probe or another retry layer.

**Task Function:**
- Readiness contract and central runtime-identity configuration.

**Template Profile:**
- Controller-selected: `review-1`
- Selection basis: `configuration spans launcher, startup, documentation, and tests; centralization prevents port drift`

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: `validator must distinguish listener reachability from authenticated inference`

**Specification Coverage:**
- Normal Herdr admission uses cheap listener/configuration readiness and labels
  it accordingly; startup/install acceptance and explicit diagnostics use one
  authenticated minimal inference contract; no per-request probe is added;
  router, shim, upstream, and lock identity come from resolved configuration.

**Required Skills:**
- `skill-central-config-layer`
- `skill-backend-verification`
- `skill-cgw-runtime-operations`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_CGW_SHIM_PREFLIGHT_URL`, `_SHARED_WEB_RUNTIME_LOCK_NAME`, `_preflight_profile_runtime`, and configuration-resolution helpers
- Modify: `tests/test_herdr_main_launcher.py:preflight and runtime identity tests`
- Modify: `tools/local-patch-hub/Start-9RouterCodexCombo.ps1:startup port, shim readiness, and authenticated acceptance checks`
- Modify: `tools/local-patch-hub/README.md:readiness and port/configuration contract`
- Modify: `docs/operating_system/tooling/runtime-tool-resolution.md:CGW readiness and single-flight wording`
- Verify: `tests/test_9router_global_install.py` for startup/receipt compatibility

**Dependencies:**
- Tasks 2-4 define the deadline and local-capacity contracts that readiness and
  runtime identity must reference; resolve canonical values from existing
  configuration rather than introducing a new config file.

**Authority:**
- Preauthorized local actions: `edit launcher/startup configuration plumbing, focused readiness tests, and maintained CGW documentation without changing credentials or permanent provider settings`
- Stop for: `the canonical runtime configuration cannot supply stable identity, authenticated inference would become a per-request probe, or a readiness change would claim inference success from HTTP 200/401 alone`

**Steps:**
- [ ] Step 1: Identify the existing canonical source for router port, shim port, upstream URL, model alias, and lock identity; add one resolver used by Herdr and startup rather than duplicating constants.
- [ ] Step 2: Rename or reshape Herdr preflight evidence to distinguish `listener_ready`/`configuration_ready` from `inference_ready`; preserve the current cheap admission latency and do not accept `401` as authenticated inference proof.
- [ ] Step 3: Make startup/install acceptance perform the authenticated minimal inference probe once, verify returned model identity and CGW transport, and reserve the same probe for explicit diagnostics.
- [ ] Step 4: Derive the shared lock filename from resolved runtime identity so unrelated CGW instances do not serialize, while preserving one lock for the same router/shim/upstream tuple.
- [ ] Step 5: Update tests and docs to assert one readiness contract and to reject hard-coded identity drift.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_9router_global_install.py -q`
- Expected: listener-only Herdr preflight accepts only the documented readiness statuses, authenticated startup acceptance checks model/transport identity, and lock keys differ for unrelated configured runtimes.
- [ ] Static search for duplicated literal runtime identities in launcher/startup/docs
- Expected: identity values are read from the canonical resolver or explicitly documented external CGW upstream configuration.

**Exit Criteria:**
- Readiness claims are truthful, authenticated inference is not repeated per
  request, and shared-lock serialization is limited to the resolved runtime
  identity.

### Task 6: Make overlay application exact-base and receipt-bound

**Purpose:**
- Prevent an older overlay from being treated as current merely because it
  reverse-applies or has a compatible package version.

**Task Function:**
- Patch selection, installation idempotency, and rollback-boundary hardening.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `PowerShell installer behavior has migration and rollback risk; exact receipt proof is required`

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: `validator must exercise exact-base, already-applied, stale-receipt, and rebase-diagnostic branches`

**Specification Coverage:**
- Mutation requires exact manifest base equals current HEAD, manifest target
  version equals package version, and any active receipt agrees on overlay ID,
  overlay version, base, target version, package version, and source HEAD.
  3-way apply remains diagnostic-only and never installs or validates an older
  base as current. Existing tracked-change protection and idempotency remain.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-cgw-runtime-operations`

**Files And Symbols:**
- Modify: `tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1:Get-OverlayRecords`, exact-base selection, reverse-check, receipt validation, and VerifyOnly/apply branches
- Modify: `tests/test_9router_cgw_overlay.py:manifest and installer contract tests`
- Modify: `tests/test_9router_global_install.py:receipt/install compatibility tests`
- Verify: `tools/local-patch-hub/Install-9RouterGlobal.ps1:receipt persistence and rollback behavior`

**Dependencies:**
- Task 1 canonical overlay inventory; Task 5 runtime identity/readiness changes
  must not be hidden inside installer selection logic.

**Authority:**
- Preauthorized local actions: `edit the overlay installer and focused disposable Git fixture tests, inspect receipt handling, and run VerifyOnly without global installation`
- Stop for: `exact base, package version, or receipt ownership cannot be proven; a change would mutate a global runtime; or 3-way application is required for installation rather than diagnosis`

**Steps:**
- [ ] Step 1: Select overlays only by exact current HEAD for mutation and reject multiple active reverse-applying overlays before any receipt or installation action.
- [ ] Step 2: Validate the active receipt against manifest ID/version/base/target version, current HEAD, and installed package version; reject stale or mismatched receipts instead of repairing them implicitly.
- [ ] Step 3: Keep direct apply as the only installation path; retain 3-way checks only as an explicit VerifyOnly rebase diagnostic that instructs registration of a new exact-base overlay.
- [ ] Step 4: Add fixture cases for exact-base selection, wrong package version, stale receipt, multiple reverse-applying overlays, direct apply, already-applied idempotency, and rebase candidate reporting.

**Verification:**
- [ ] `py -3 -m pytest tests/test_9router_cgw_overlay.py tests/test_9router_global_install.py -q`
- Expected: stale/older overlays cannot be selected for mutation, exact-base overlays remain idempotent, and VerifyOnly distinguishes rebase diagnostics from installed verification.
- [ ] Disposable Git fixture invoking `Apply-9RouterCgwOverlay.ps1 -VerifyOnly`
- Expected: no global package, receipt, or target checkout mutation occurs during verification-only paths.

**Exit Criteria:**
- Overlay selection and receipts have one exact-base truth source, installation
  is idempotent and fail-closed, and rebase logic cannot mask drift.

### Task 7: Prove the integrated path and reconcile documentation

**Purpose:**
- Verify that the combined changes remove duplicate attempts and unnecessary
  branching under realistic local contention without claiming unavailable live
  provider evidence.

**Task Function:**
- Cross-surface integration, backend boundary proof, and final reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `final fan-in and acceptance require controller authority over all task evidence`

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: `independent final review is required for cross-surface ownership and regression gaps`

**Specification Coverage:**
- Run actual patched 9Router unit tests and shim tests after applying the pinned
  overlay; prove one Herdr admission, one active shim execution, no account or
  combo fallback on local saturation, no duplicate attempt, and truthful final
  evidence. Reconcile docs, generated surfaces, and plan ledger.

**Required Skills:**
- `skill-backend-verification`
- `skill-cgw-runtime-operations`
- `skill-verification-before-completion`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Modify: `.github/workflows/runtime-contracts.yml` only if the disposable overlay integration job is absent and the canonical workflow owner accepts the addition
- Modify: `tests/test_9router_cgw_overlay.py` for the repository-level integration harness
- Verify: `scripts/herdr_main_launcher.py`, `tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1`, `tools/local-patch-hub/Start-9RouterCodexCombo.ps1`, the overlay patch, all focused tests, and maintained docs
- Verify: live process inspection and authenticated inference only when the configured endpoint and credential contract are available

**Dependencies:**
- Tasks 2-6 complete with task-local proof; all shared overlay edits are merged
  into the single patch before the disposable integration run.

**Authority:**
- Preauthorized local actions: `apply the pinned overlay to a disposable checkout, run the declared Python/Node/PowerShell integration checks, inspect local process ownership, and reconcile plan evidence and docs`
- Stop for: `live credentials or endpoints are unavailable, native execution is observed for a CGW attempt, duplicate execution cannot be disproven, or any required task proof is missing or contradictory`

**Steps:**
- [ ] Step 1: Add or update a disposable fixture harness that applies the exact manifest-selected overlay and runs the actual patched 9Router fallback tests plus shim Node tests.
- [ ] Step 2: Run the focused Python suites: `tests/test_herdr_main_launcher.py`, `tests/test_9router_cgw_overlay.py`, `tests/test_9router_global_install.py`, and `tests/test_skill_cgw_runtime_operations.py`.
- [ ] Step 3: Run the repository contract suite and workflow-local checks; include overlay application and patched-runtime tests in CI only through the canonical workflow owner.
- [ ] Step 4: If live runtime evidence is available, perform one bounded authenticated CGW probe and record resolved model, CGW transport, unchanged native quota, process ownership, and no-native-process evidence. If unavailable, record `blocked` for live evidence without adding retries or changing credentials.
- [ ] Step 5: Run `skill-plan-document-reviewer`, reconcile every task ledger row and deviation, and leave the plan proposed/active until `skill-verification-before-completion` returns `verified`.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_9router_cgw_overlay.py tests/test_9router_global_install.py tests/test_skill_cgw_runtime_operations.py -q`
- Expected: focused Python regression suite passes with new timing, ownership, readiness, and installer assertions.
- [ ] Patched 9Router command: actual overlay unit tests plus `node --test` shim queue tests
- Expected: structured local saturation stops fallback/duplicate execution; cancellation and expiry release capacity; one active CGW execution is observed.
- [ ] `python scripts/validate_repo_contracts.py`
- Expected: repository contracts and generated agent surfaces remain valid; unrelated user edits are not overwritten.

**Exit Criteria:**
- All implementation outcomes and task proofs are reconciled, no ownership or
  retry duplication remains, CI exercises runtime behavior rather than patch
  text alone, and any unavailable live proof is explicitly recorded as blocked.

## Verification

- `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_9router_cgw_overlay.py tests/test_9router_global_install.py tests/test_skill_cgw_runtime_operations.py -q`
- `python scripts/validate_repo_contracts.py`
- Disposable exact-base overlay application followed by the actual patched 9Router fallback suite and shim queue `node --test` suite
- `skill-plan-document-reviewer` review of ownership, task dependencies, and no-new-scheduler constraints
- `skill-verification-before-completion` fresh final verification of source, tests, docs, generated surfaces, and recorded live-evidence status

## Completion Criteria

The plan is ready for completion verification when:

1. Herdr uses one absolute attempt deadline across shared CGW lock, prompt
   submission, and idle completion, while pane ownership remains fail-fast.
2. The shim and 9Router share one structured, provider-scoped local-capacity
   contract and local saturation cannot trigger account or combo fallback.
3. The shim queue is bounded, cancellation-aware, age/deadline-aware, and not a
   second scheduler or retry owner.
4. Readiness distinguishes listener/configuration from authenticated inference;
   authenticated inference is used only by startup/install acceptance or explicit
   diagnostics, not every request.
5. Runtime identity is configuration-derived and unrelated CGW instances are not
   unnecessarily serialized.
6. The overlay installer is exact-base and receipt-bound; 3-way apply cannot
   silently install or validate an older overlay as current.
7. The actual patched 9Router and shim runtime tests run in CI or a reproducible
   disposable harness, not only patch-text assertions.
8. Every task-local proof passes, unrelated user edits remain preserved, docs and
   generated surfaces match canonical sources, and all live-evidence limitations
   are recorded.

The plan may be marked `completed` only after `skill-verification-before-completion`
runs fresh final verification, confirms these criteria against repository
evidence, finds no unresolved required task or unrecorded deviation, and returns
`verified`.
