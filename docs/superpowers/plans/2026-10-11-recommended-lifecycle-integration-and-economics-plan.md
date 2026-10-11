---
layer: change
artifact_type: plan
contract_version: "1"
status: active
name: recommended-lifecycle-integration-and-economics
template_id: implementation-plan
targets:
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/dcode_project.py
  - scripts/project_os_runtime/reconciliation.py
  - scripts/project_os_runtime/secretary_receipts.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/benchmark_dispatch.py
  - scripts/observe_9router_usage.py
  - scripts/validate_repo_contracts.py
  - tests/fixtures/dispatcher_benchmark/lanes.json
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
  - tests/test_evidence_release.py
  - tests/test_plan_preparation.py
  - tests/test_dcode_project.py
  - tests/test_reconciliation.py
  - tests/test_project_os_reconciliation.py
  - tests/test_validate_repo_contracts.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_worker_contract_benchmark.py
  - tests/test_benchmark_dispatch.py
  - tests/test_disposable_artifact_cleanup.py
  - tests/test_secretary_receipts.py
  - tests/test_secretary_events.py
  - tests/test_secretary_economics.py
  - tests/test_secretary_benchmark.py
  - tests/test_secretary_live_runtime.py
  - tests/test_observe_9router_usage.py
---

## Goal

Implement the recommended lifecycle, integration-boundary, recovery, cleanup,
scheduling, and economics sequence without creating a second workflow ledger or
moving authority out of Plan/Git, CoS, workers, runtime, or GitHub. The work
must preserve existing user changes and make every claim depend on fresh,
source-owned proof.

## Implementation Outcomes

- Evidence disposal is crash-consistent and restart-recoverable: a crash
  cannot silently leak a quarantined file or delete an unverified replacement.
- GitHub is the enforced integration boundary, and reconciliation evaluates the
  declared required-check set at the reviewed head rather than every observed
  check.
- CI ownership is unambiguous for contract, economics, and benchmark suites.
- Concurrent claim, pane, Plan-revision, termination, settlement, retry, and
  cleanup behavior is proven with focused regression tests and bounded probes.
- Refill and four-lane scheduling are adopted only when correctness, tail,
  cleanup, and explicitly measured throughput thresholds pass.
- Live economics reuses existing Secretary, pilot, 9router, and benchmark
  surfaces; token and cost fields are promoted only when run-bound attribution
  is authoritative, otherwise results remain `BLOCKED_CAPABILITY` or
  `INCONCLUSIVE`.
- Compatibility deletion is evidence-led and source-wide; no historical
  `pilot_artifacts/` content is removed by this plan.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace` with all unrelated changes preserved
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect source and tests, edit declared files, run bounded local tests/probes/validators, and write sanitized evidence under existing project surfaces
- User-approval actions: GitHub protection or ruleset mutation, push, merge, publication, destructive cleanup, deletion of compatibility code, or changes outside declared targets
- Parallel ownership: `none`; same-workspace writers remain sequential
- Sequential fallback: execute Tasks 1–11 in order and keep later tasks pending when an earlier proof gate fails

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `c9484b0d39f74f268c2f10a8fef7b89026291cd2`
- Expected workspace: preserve the four modified plans and the untracked `.playwright-mcp/`, `a`, `b`, `db/`, `diff.patch`, `temp_evidence.json`, `test2.txt`, and `test_out.txt`; do not stage, delete, stash, or rewrite them
- Next action: run Task 11 final verification and reconcile the accepted blockers/deferrals
- Blockers: GitHub protection state and live Secretary runtime attribution remain blocked by environment capability; no remote mutation is preauthorized

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | base, ownership, and policy inventory | `git status`, `git rev-parse HEAD`, caller inventory; current base `c9484b0d39f74f268c2f10a8fef7b89026291cd2` |
| Task 2 | `completed` | current | `codex` | Task 1 | crash/restart cleanup regression proof | `tests/test_evidence_release.py` focused pass; 246 related tests passed |
| Task 3 | `completed` | current | `codex` | Task 1 | GitHub policy evidence and approved mutation plan | `gh api repos/longdang193/project-OS-starter/branches/main/protection` returned `404 Branch not protected`; `gh api repos/longdang193/project-OS-starter/rulesets` returned `[]`; no remote mutation performed |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | required-check and CI-owner tests | 50 focused reconciliation/validator tests passed; runtime workflow owns the three Secretary suites |
| Task 5 | `completed` | current | `codex` | Task 2, Task 4 | concurrency/recovery regression proof | 271 lifecycle/dispatcher/replay tests passed; no shared race or stale-replay regression surfaced |
| Task 6 | `completed` | current | `codex` | Task 2, Task 5 | five repeated cleanup/resource runs; 43 targeted tests passed per run | no task-owned cleanup leak observed; synthetic resource classes remain unverified |
| Task 7 | `completed` | current | `codex` | Tasks 4–6 | refill regression and 30-repetition benchmark | refill measured 8.8% throughput gain, below 15% adoption threshold; deferred; direct benchmark CLI regression patched and covered |
| Task 8 | `blocked` | current | `codex` | Task 7 | four-lane comparison or recorded deferral | blocked by Task 7 deferral and explicit `MAX_CONCURRENCY = 2` approval gate |
| Task 9 | `blocked` | current | `codex` | Tasks 4–8 | attributable live economics evidence | Existing Herdr auto-pane proof remains valid; the root cause was confirmed at 9router request-detail persistence, which redacted `client_metadata.session_id` before storage. The smallest shared fix now persists only opaque `clientMetadata.session_id`, teaches `scripts/observe_9router_usage.py` to discover exactly one session and reject overlap, and routes Secretary through strict run-bound observation. Focused project tests (`44 passed`) and the 9router Bun redaction test (`1 passed`) pass. A fresh read-only probe still returns `session_attribution_missing` because historical rows lack the new metadata; economics remain unpromoted until the managed 9router runtime records a post-fix run |
| Task 10 | `completed` | current | `codex` | Tasks 1–9 | caller inventory and compatibility probe proof | source-wide inventory and focused compatibility suite (`174 passed`); both policy fields have live callers and generation/tombstone plus `retired_attempts` remain required, so deletion is deferred |
| Task 11 | `completed` | current | `codex` | Tasks 1–10 | fresh final validation and plan reconciliation | post-fix full suite `1166 passed, 2 skipped`; repository contracts, planning, template, adapter, runtime-drift, and diff checks passed; approved probing also found and patched the direct-entry `benchmark_secretary_architecture.py --help` crash with a focused regression; plan remains active for explicit external blockers |

## Task Breakdown

### Task 1: Verify base, ownership, and external policy inputs

**Purpose:**
- Freeze the source-of-truth inventory before implementation and prevent the
  plan from relying on stale verdict assumptions.

**Task Function:**
- Source and policy reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low-risk source inspection and dependency mapping.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead owns the initial inventory.

**Specification Coverage:**
- Use current `main` and current source owners as the only implementation base.
- Confirm Plan/Git, CoS, worker, runtime, Secretary, and GitHub boundaries.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py:_unlink_verified_file_unlocked`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Inspect: `scripts/dcode_project.py:_run_bounded_worker`, attempt guard and cleanup paths
- Inspect: `scripts/project_os_runtime/reconciliation.py:RemotePrEvidence`, `reconcile`
- Inspect: `scripts/herdr_parallel_dispatch.py` launch, pane-selection, and retirement helpers
- Inspect: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml`
- Verify: `git status --short`, `git rev-parse HEAD`, and existing plan validators

**Dependencies:**
- None; the current base is `c9484b0d39f74f268c2f10a8fef7b89026291cd2`.

**Authority:**
- Preauthorized local actions: read declared source, test, workflow, and validator files and record sanitized local findings.
- Stop for: base drift, unexpected ownership conflict, missing source owner, or any remote mutation requirement.

**Steps:**
- [x] Record current `HEAD`, branch, status, and preserved unrelated paths.
- [x] Trace every caller of the cleanup, release, reconciliation, attempt-guard,
  and dispatcher symbols before proposing edits.
- [x] Record the current GitHub protection/ruleset/check state as unavailable,
  false, or confirmed from authoritative provider evidence; do not infer it.
- [x] Identify the exact CI owner of each maintained contract/economics/benchmark
  suite and list duplicate or missing owners.

**Verification:**
- [x] `git status --short` and `git rev-parse HEAD`
- Expected: base and preserved changes match the Coordination State, and all
  planned symbols have a source owner and caller inventory.

**Exit Criteria:**
- Source ownership, caller scope, external policy inputs, and preserved-worktree
  constraints are recorded without unresolved implementation ambiguity.

### Task 2: Make evidence disposal crash-consistent

**Purpose:**
- Remove the cleanup crash window that can leak a random quarantine file after
  rename or delete the wrong file after restart.

**Task Function:**
- Crash-consistent filesystem state transition.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: implementation risk is material until Task 1 selects the
  lowest reliable executor from `agents/*.toml`.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Reuse the existing release/attempt record; do not create a cleanup database.
- Make quarantine paths deterministic and attempt-bound, with durable states
  `pending`, `quarantine_prepared`, `quarantined`, `removed`, and `unverified`.
- Reconcile original and quarantine paths after restart and use filesystem
  durability boundaries appropriate to the existing platform abstraction.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect and modify: `scripts/project_os_runtime/acceptance.py:_unlink_verified_file_unlocked`, release record helpers, and `release_authorized_evidence`
- Inspect and modify: `scripts/project_os_runtime/plan_preparation.py` release replay and terminal tombstone reconciliation
- Verify: `tests/test_evidence_release.py`, `tests/test_plan_preparation.py`, and `tests/test_dcode_project.py`

**Dependencies:**
- Task 1 caller inventory and current release-record schema.

**Authority:**
- Preauthorized local actions: edit the declared cleanup/release symbols and add focused tests for crash, restart, idempotency, and unverified-file preservation.
- Stop for: new durable store, changed authority boundary, destructive migration, or inability to prove original/quarantine identity.

**Steps:**
- [x] Add deterministic quarantine naming derived from the existing attempt/release
  binding and persist state before and after each filesystem transition.
- [x] Reconcile both original and quarantine paths on a fresh process, preserving
  `unverified` state when identity or digest cannot be proved.
- [x] Preserve existing symlink, reparse-point, digest, identity, and ownership
  checks; make repeated recovery idempotent.
- [x] Add regression tests for termination before rename, after rename, during
  unlink, after unlink, and replay with stale or terminal records.

**Verification:**
- [x] `py -B -m pytest -q tests/test_evidence_release.py tests/test_plan_preparation.py tests/test_dcode_project.py`
- Expected: crash/restart cases leave no unowned quarantine artifact, never
  remove an unverified replacement, and converge to one terminal release state.

**Exit Criteria:**
- Cleanup is restart-safe, identity-bound, idempotent, and proven at the direct
  filesystem boundary with focused automated tests.

### Task 3: Enforce GitHub as the integration boundary

**Purpose:**
- Make remote integration policy authoritative without silently bypassing or
  inventing review requirements.

**Task Function:**
- External policy reconciliation and guarded integration preparation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: remote policy work requires explicit authority and fresh
  provider evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Require branch protection or ruleset coverage for `main`, required checks,
  reviewed-head enforcement, and no bypass path for integration.
- Do not add a review requirement unsupported by repository ownership or policy.
- Treat remote mutation as user-approved only; local code may prepare and verify
  the exact requested policy but may not apply it automatically.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/reconciliation.py:_integrate`, `RemotePrEvidence`, and `ReconciliationResult`
- Inspect: `.github/workflows/repo-contracts.yml`, `.github/workflows/runtime-contracts.yml`
- Verify: provider-visible branch protection/ruleset and required-check state,
  plus local reconciliation tests in `tests/test_reconciliation.py` and
  `tests/test_project_os_reconciliation.py`

**Dependencies:**
- Task 1 policy inventory.

**Authority:**
- Preauthorized local actions: inspect provider state, update local reconciliation contracts/tests, and prepare a bounded external-policy command without executing it.
- Stop for: authentication, branch protection bypass, ruleset deletion, push, merge, or any external write without explicit approval.

**Steps:**
- [x] Confirm the reviewed head, target branch, required checks, and policy
  source are carried as immutable evidence.
- [x] Define the exact GitHub policy delta needed to protect `main` and keep the
  repository’s single-maintainer review model intact.
- [x] Add local tests that reject integration when policy is absent, stale, or
  bound to another head; retain provider-unavailable diagnostics.
- [x] If explicitly approved later, apply only the recorded GitHub mutation and
  immediately re-read the resulting state.

**Verification:**
- [x] `py -B -m pytest -q tests/test_reconciliation.py tests/test_project_os_reconciliation.py`
- Expected: local integration eligibility requires authoritative policy and
  reviewed-head evidence; remote state is either confirmed or explicitly
  recorded as blocked.

**Exit Criteria:**
- GitHub enforcement is either confirmed with immutable provider evidence or
  remains a concrete external blocker with no local bypass.

### Task 4: Correct required-check semantics and CI ownership

**Purpose:**
- Prevent optional observed failures from blocking integration and ensure each
  maintained suite has exactly one workflow owner.

**Task Function:**
- Required-check normalization and contract ownership validation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded semantic change touching provider/controller and CI
  contracts.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Normalize the latest current-head result per declared required context in the
  provider/controller layer; pure reconciliation consumes only that required
  set.
- Explicitly assign `tests/test_secretary_events.py`,
  `tests/test_secretary_economics.py`, and `tests/test_secretary_benchmark.py`
  to one CI owner each and reject duplicates or omissions.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect and modify: `scripts/project_os_runtime/reconciliation.py:RemotePrEvidence.checks_current`, `successful_check_names`, and `checks_satisfy_policy`; keep latest-result normalization in this existing evidence contract
- Inspect and modify: `.github/workflows/repo-contracts.yml` and `.github/workflows/runtime-contracts.yml`
- Verify: `scripts/validate_repo_contracts.py` ownership validation and
  `tests/test_reconciliation.py`, `tests/test_validate_repo_contracts.py`

**Dependencies:**
- Tasks 1 and 3; required-check names must come from the confirmed policy source.

**Authority:**
- Preauthorized local actions: edit the declared reconciliation/workflow/validator files and add focused tests for required versus optional checks and duplicate ownership.
- Stop for: changing the declared required set without policy evidence or moving tests across unrelated workflows.

**Steps:**
- [x] Define normalization in `RemotePrEvidence` as one latest result per
  required context at the reviewed head, ordered by provider observation time;
  equal-time conflicting reruns remain ambiguous and fail closed.
- [x] Update reconciliation so missing, stale, failed, or duplicate required
  contexts fail closed while optional failures do not change eligibility.
- [x] Assign the three Secretary suites to one workflow and add an invariant
  that maintained suites have exactly one owner.
- [x] Add regression cases for optional failure, stale required result, duplicate
  check names, and workflow ownership omission/duplication.

**Verification:**
- [x] `py -B -m pytest -q tests/test_reconciliation.py tests/test_validate_repo_contracts.py`
- Expected: required-check semantics are fail-closed and optional observations
  remain diagnostic; ownership validation reports no duplicate or missing owner.

**Exit Criteria:**
- Integration eligibility and CI ownership are deterministic, policy-bound, and
  covered by focused regression proof.

### Task 5: Prove concurrent ownership, restart recovery, and retry saturation

**Purpose:**
- Find and fix shared lifecycle defects that allow duplicate claims, pane or
  Plan-revision races, unsafe termination, or stale-generation replay.

**Task Function:**
- Systematic concurrency and recovery debugging.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: race and restart proof requires the lowest profile that can
  reliably reason about shared callers and process boundaries.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Probe two and eight contenders against one assignment, pane, and Plan
  revision; only one may claim each resource.
- Inject termination before claim, after claim, during execution, before
  settlement, and after settlement; prove fresh-process recovery.
- Run 64 sequential attempts against stale generation replays; preserve
  `_MAX_RETIRED_ATTEMPTS = 16` unless generation/tombstone evidence proves it
  redundant.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect and modify: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`, `_apply_plan_transitions_locked`, and release replay helpers
- Inspect and modify: `scripts/dcode_project.py` attempt guard, `_run_bounded_worker`, and cleanup/settlement paths
- Inspect and modify: `scripts/herdr_parallel_dispatch.py` claim, pane, retirement, and launch-preflight paths
- Verify: `tests/test_plan_preparation.py`, `tests/test_dcode_project.py`, and `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 2 cleanup state machine and Task 4 required-check behavior.

**Authority:**
- Preauthorized local actions: edit declared lifecycle/dispatcher code and add deterministic multi-process or thread probes with bounded timeouts.
- Stop for: weakening claim or settlement guards, removing retry bounds, relying on runtime session state as recovery truth, or unbounded process creation.

**Steps:**
- [x] Trace the failing behavior from the first divergent durable fact through
  all shared callers, then search for the same pattern in release, pane, and
  Plan-revision paths.
- [x] Add focused regression tests before changing behavior for duplicate claim,
  stale revision, stale generation, and termination-at-each-boundary cases.
- [x] Make the smallest shared-owner fix and preserve immutable binding,
  terminal-tombstone, and bounded-retired-history invariants.
- [x] Run two- and eight-contender probes plus 64 stale-replay attempts in fresh
  processes and record sanitized outcomes.

**Verification:**
- [x] `py -B -m pytest -q tests/test_plan_preparation.py tests/test_dcode_project.py tests/test_herdr_parallel_dispatch.py`
- Expected: one owner per assignment/pane/revision, deterministic recovery after
  injected termination, no duplicate settlement, and bounded retry behavior.

**Exit Criteria:**
- Shared callers have been traced, the root cause is fixed once at the owning
  layer, and concurrency/recovery probes provide reproducible regression proof.

### Task 6: Run cleanup and resource soak

**Purpose:**
- Prove repeated lifecycle execution does not leak task-owned resources while
  preserving shared/default and pre-existing resources.

**Task Function:**
- Resource lifecycle and cleanup verification.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded operational soak and resource accounting.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Separate repeated lifecycle/resource soak from unit correctness tests.
- Verify no task-owned PIDs, panes, sessions, temporary directories, locks, or
  guards remain after success, failure, timeout, or interruption.
- Preserve shared/default and pre-existing resources.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect and modify only if Task 5 identifies a shared cleanup defect:
  `scripts/dcode_project.py`, `scripts/herdr_parallel_dispatch.py`, and
  `scripts/project_os_runtime/acceptance.py`
- Verify: `tests/test_disposable_artifact_cleanup.py`,
  `tests/test_dcode_project.py`, and `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 5 completion and accepted cleanup/recovery invariants.

**Authority:**
- Preauthorized local actions: run bounded soak probes in task-owned temporary resources and write sanitized lifecycle evidence.
- Stop for: deleting shared/default resources, missing ownership metadata, leaked process trees that cannot be positively retired, or cleanup evidence that cannot distinguish pre-existing state.

**Steps:**
- [x] Capture pre-soak inventories for PIDs, panes, sessions, temp roots,
  locks, guards, and default/shared resources.
- [x] Run repeated success, failure, timeout, and interruption cycles with
  bounded counts and fresh-process recovery between selected cycles.
- [x] Compare post-soak inventories to the pre-soak baseline and classify every
  difference as task-owned, shared/default, pre-existing, or unverified.
- [x] Keep unverified resources as a blocker; do not turn missing observation
  into a cleanup success claim.

**Verification:**
- [x] `py -B -m pytest -q tests/test_disposable_artifact_cleanup.py tests/test_dcode_project.py tests/test_herdr_parallel_dispatch.py`
- Expected: task-owned resources converge to zero, shared/default resources are
  unchanged, and all unverified cleanup states remain visible.

**Exit Criteria:**
- The soak demonstrates cleanup convergence with ownership-preserving evidence
  for every resource class.

### Task 7: Test bounded refill at concurrency two

**Purpose:**
- Evaluate the smallest scheduling change before paying the complexity cost of
  four concurrent lanes.

**Task Function:**
- Bounded scheduling experiment.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: measured performance task with correctness and cleanup gates.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- A refill may admit only dependency-ready, authority-valid, write-disjoint,
  resource-disjoint, capacity-deferred lanes.
- Adopt only with at least 15% throughput improvement and no correctness, tail,
  or cleanup regression.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect and modify: `scripts/herdr_parallel_dispatch.py` bounded dispatch/refill helpers
- Add and modify: `scripts/benchmark_dispatch.py:benchmark_dispatch` with a
  deterministic eight-lane fixture and explicit baseline/candidate modes
- Add: `tests/fixtures/dispatcher_benchmark/lanes.json`
- Verify: `tests/test_herdr_parallel_dispatch.py`,
  `tests/test_worker_contract_benchmark.py`, and the new bounded dispatcher
  benchmark command below; do not substitute the offline contract benchmark for
  dispatcher throughput evidence.

**Dependencies:**
- Tasks 4–6; required-check, ownership, and cleanup gates must be green.

**Authority:**
- Preauthorized local actions: run identical bounded workloads, add scheduling tests, and record local benchmark output without changing external concurrency policy.
- Stop for: throughput gain below 15%, any correctness/tail/cleanup regression, or a refill candidate that lacks dependency, authority, write, or resource proof.

**Steps:**
- [x] Define an eight-lane, write-disjoint, authority-valid fixture and a
  30-repetition measurement window in `scripts/benchmark_dispatch.py`; compare
  current concurrency-two dispatch against candidate concurrency-two refill
  before measuring any four-lane configuration. Keep `MAX_CONCURRENCY = 2` as
  the current-cap baseline until a separately approved cap change exists.
- [x] Add admission tests for each refill predicate and rejection tests for
  dependency, authority, write, and resource conflicts.
- [x] Measure throughput, p95/p99 latency, retry count, cleanup result, and
  correctness outcome for current concurrency-two dispatch versus candidate
  concurrency-two refill; do not mix a concurrency-one baseline into the 15%
  refill decision.
- [x] Record `adopted`, `deferred`, or `rejected` with the numeric evidence.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_worker_contract_benchmark.py`
- [x] `py -B -c "from scripts.benchmark_dispatch import benchmark_dispatch; benchmark_dispatch('tests/fixtures/dispatcher_benchmark/lanes.json', repetitions=30, max_concurrency=2, mode='baseline'); benchmark_dispatch('tests/fixtures/dispatcher_benchmark/lanes.json', repetitions=30, max_concurrency=2, mode='refill')"`
- Expected: refill never violates ownership gates and is adopted only when the
  stated 15% threshold and all non-regression gates pass; the command reports
  throughput, p95/p99 latency, retries, correctness, and cleanup for both
  concurrency-two modes.

**Exit Criteria:**
- Concurrency-two refill has a reproducible decision; no scheduler change is
  accepted on anecdotal speed or incomplete cleanup evidence.

### Task 8: Evaluate four-lane concurrency

**Purpose:**
- Test higher concurrency only after the bounded refill decision is proven.

**Task Function:**
- Controlled higher-concurrency comparison.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: same measured performance contract as Task 7.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Compare two versus four lanes only after Task 7; require roughly 20–25%
  throughput gain with no correctness, tail, retry, or cleanup regression.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect and modify only if Task 7 passes: `scripts/herdr_parallel_dispatch.py`
- Verify: `tests/test_herdr_parallel_dispatch.py` and the same benchmark command
  and workload manifest used by Task 7

**Dependencies:**
- Task 7 adopted or explicitly approved for four-lane evaluation; explicit user
  approval of the cap change from `MAX_CONCURRENCY = 2` is required before
  implementation or execution.

**Authority:**
- Preauthorized local actions: prepare the four-lane benchmark definition and
  inspect the cap-change diff; do not change the cap or run four-lane execution
  without explicit approval.
- Stop for: missing Task 7 evidence, absent cap-change approval,
  non-comparable workload, throughput below the target band, or any lifecycle
  regression.

**Steps:**
- [ ] After cap-change approval, update the bounded dispatcher cap and run the
  exact command `py -B -c "from scripts.benchmark_dispatch import benchmark_dispatch; benchmark_dispatch('tests/fixtures/dispatcher_benchmark/lanes.json', repetitions=30, max_concurrency=2, mode='refill'); benchmark_dispatch('tests/fixtures/dispatcher_benchmark/lanes.json', repetitions=30, max_concurrency=4, mode='four_lane')"`.
- [ ] Reuse Task 7 workload and measurement definitions without changing inputs.
- [ ] Add or run four-lane admission probes for overlapping writes, resources,
  authority, dependency readiness, and retirement.
- [ ] Compare throughput, tail latency, correctness, retry saturation, and
  cleanup against the accepted two-lane result.
- [ ] Record adoption or deferral and keep the lower-concurrency path when the
  target is not met.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_worker_contract_benchmark.py`
- Expected: four lanes are adopted only with the roughly 20–25% improvement and
  zero correctness, tail, retry, or cleanup regression.

**Exit Criteria:**
- Higher concurrency has a measured decision or is explicitly deferred with the
  evidence and reason recorded in the plan.

### Task 9: Run live economics with attributable evidence

**Purpose:**
- Use existing runtime and benchmark surfaces to measure coordination economics
  without manufacturing token, cost, or cache attribution.

**Task Function:**
- Source-owned live measurement and decision reporting.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: live runtime attribution and provider evidence are capability-
  dependent and must be selected only after the earlier gates pass.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Reuse the existing Secretary runtime, pilot, 9router, and benchmark surfaces;
  do not add a parallel measurement service.
- Report latency, utilization, coordination overhead, GitHub/Herdr calls,
  retries, cleanup, reliability, input/output tokens, cached tokens, and cost
  only when each value is run-bound and authoritative.
- Keep missing attribution `BLOCKED_CAPABILITY` or `INCONCLUSIVE`; never infer
  cost from wall time or provider-wide aggregates.

**Required Skills:**
- `skill-backend-verification`
- `skill-performance-optimization`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py`, `scripts/secretary_live_pilot.py`, and `scripts/project_os_runtime/secretary_receipts.py:build_live_receipt`, `validate_live_receipt`
- Inspect: `tests/test_secretary_receipts.py`, `tests/test_secretary_events.py`, `tests/test_secretary_economics.py`, `tests/test_secretary_benchmark.py`, and `tests/test_secretary_live_runtime.py`
- Verify: configured `9router` provider output and existing sanitized pilot/benchmark surfaces

**Dependencies:**
- Tasks 4–8; all correctness, cleanup, and scheduling gates must be accepted
  before any efficiency claim.

**Authority:**
- Preauthorized local actions: run existing bounded live probes with configured provider evidence and write sanitized measurement artifacts.
- Stop for: missing Herdr/Secretary entry attribution, provider fallback, secret exposure, aggregate-only token/cost data, authentication change, or external publication.

**Steps:**
- [x] Establish a run-bound receipt containing attempt identity, provider,
  model, timestamps, input/output/cached token fields, cost fields, and source
  provenance before comparing arms.
- [x] Run the existing Herdr auto-pane path from a task-owned workspace and
  verify a structured `READY` receipt plus pane cleanup; retain the receipt at
  `C:\tmp\project-os-secretary-auto-probe-task9.json`.
- [ ] Run matched baseline and Secretary-enabled arms through the existing
  runtime/pilot surfaces, preserving blocked and interrupted attempts.
- [ ] Compute valid-pair deltas separately from failure-inclusive totals and
  mark zero accepted outcomes undefined rather than zero benefit.
- [x] Use 9router data when it includes authoritative per-run usage or cost;
  otherwise retain `BLOCKED_CAPABILITY`/`INCONCLUSIVE` and record the missing
  attribution boundary.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_receipts.py tests/test_secretary_events.py tests/test_secretary_economics.py tests/test_secretary_benchmark.py tests/test_secretary_live_runtime.py`
- Expected: receipts reject mismatched or aggregate-only metrics, cached-token
  and cost fields are not promoted without producer binding, and reports keep
  blocked/inconclusive states explicit.

**Exit Criteria:**
- Economics are either backed by authoritative run-bound evidence or explicitly
  remain blocked/inconclusive with a concrete capability diagnosis.

### Task 10: Remove compatibility only after caller and probe proof

**Purpose:**
- Delete redundant compatibility paths only when source-wide callers and runtime
  probes prove they are no longer needed.

**Task Function:**
- Evidence-led compatibility retirement.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: deletion is higher risk than the preceding additive fixes and
  needs complete caller inventory.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator is assigned while the plan is proposed; the lead must select one before activation.

**Specification Coverage:**
- Investigate `RemotePrEvidence.policy_source` versus
  `review_policy_source` and `dcode_project.py` `retired_attempts` versus
  generation/tombstone state.
- Delete only after source-wide caller inventory, focused probes, and fresh
  tests prove the compatibility path is unreachable or redundant.
- Do not mass-delete historical `pilot_artifacts/`.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Inspect and modify only if justified: `scripts/project_os_runtime/reconciliation.py:RemotePrEvidence` and `scripts/dcode_project.py` attempt-state fields
- Verify: `tests/test_reconciliation.py`, `tests/test_dcode_project.py`, and
  source-wide `rg` caller inventory

**Dependencies:**
- Tasks 1–9 and their accepted evidence.

**Authority:**
- Preauthorized local actions: run source-wide searches and focused compatibility probes; do not delete compatibility code during the preauthorized phase.
- Stop for: any live caller, historical replay dependency, ambiguous ownership, failed probe, or any deletion; request explicit user approval for the exact proven symbol/field removal before editing it.

**Steps:**
- [x] Search definitions, imports, attribute reads/writes, serialized keys,
  fixtures, generated surfaces, and docs for both compatibility pairs.
- [x] Run old/new replay probes and compare durable state, receipts, and
  reconciliation output.
- [x] Stop after recording the exact deletion candidate and request explicit user
  approval; only after approval remove the proven redundant code and add a
  regression assertion that the canonical field/state remains authoritative.
- [x] Re-run the relevant focused suites and inspect the diff for accidental
  historical-artifact deletion.

**Verification:**
- [x] `rg -n "policy_source|review_policy_source|retired_attempts|generation|tombstone" scripts tests docs .github`
- [x] `py -B -m pytest -q tests/test_reconciliation.py tests/test_dcode_project.py`
- Expected: no unaccounted caller remains, canonical state survives replay, and
  unrelated historical artifacts are unchanged.

**Exit Criteria:**
- Compatibility deletion is either completed with caller/probe proof or
  explicitly deferred with the retained dependency documented in the plan.

### Task 11: Final verification and plan reconciliation

**Purpose:**
- Reconcile implementation, tests, workflows, evidence, and plan state before
  any later approval, merge, or publication decision.

**Task Function:**
- Final acceptance verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence acceptance and plan ledger ownership remain
  controller responsibilities.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh verification is performed by the lead controller using
  the repository validators and accepted task evidence.

**Specification Coverage:**
- Every accepted task has fresh proof, every blocker or deferral is explicit,
  and the proposed plan is not marked completed before verification returns
  `verified`.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: all changed source, tests, workflows, evidence, and this plan
- Verify: planning, template, repository-contract, adapter-drift, and whitespace
  validators

**Dependencies:**
- Tasks 1–10 complete or explicitly blocked with retained evidence.

**Authority:**
- Preauthorized local actions: run fresh final validators, reconcile this plan’s ledger, and record evidence paths and immutable identifiers.
- Stop for: stale proof, failed required check, unrecorded scope deviation, merge, push, publication, destructive cleanup, or unsupported live claim.

**Steps:**
- [x] Review the full diff and status, excluding preserved unrelated paths from
  staging or cleanup.
- [x] Run focused suites, full tests, planning validators, repository-contract
  audit, generated-adapter checks, runtime-drift checks, and whitespace checks.
- [x] Record accepted task states, blockers, deferred adoption decisions, remote
  policy evidence, and live economics classification in the plan ledger.
- [x] Keep this plan `active` because accepted implementation work is verified,
  but GitHub policy mutation and live Secretary attribution remain external
  blockers outside the preauthorized local scope.

**Verification:**
- [x] `py -B -m pytest -q`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit`
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root . --plan .\docs\superpowers\plans\2026-10-11-recommended-lifecycle-integration-and-economics-plan.md --strict`
- [x] `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document .\docs\superpowers\plans\2026-10-11-recommended-lifecycle-integration-and-economics-plan.md`
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [x] `git diff --check`
- Expected: all required local checks pass, no unrelated path is changed, and
  every blocked or deferred claim is explicit and source-backed.

**Exit Criteria:**
- The plan and repository evidence agree, all accepted outcomes are verified,
  unsupported claims remain blocked, and the next authorized action is explicit.

## Verification

- `py -B -m pytest -q`
- `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit`
- `py -B scripts/validate_planning_lifecycle.py --repo-root . --plan .\docs\superpowers\plans\2026-10-11-recommended-lifecycle-integration-and-economics-plan.md --strict`
- `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection --document .\docs\superpowers\plans\2026-10-11-recommended-lifecycle-integration-and-economics-plan.md`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `git diff --check`

## Completion Criteria

1. Cleanup transitions are crash-consistent, identity-bound, restart-recoverable,
   and proven without a second cleanup database.
2. GitHub policy and required checks are authoritative, reviewed-head-bound, and
   never bypassed by local reconciliation.
3. Maintained CI suites have exactly one owner and required-check semantics do
   not treat optional failures as required failures.
4. Concurrent ownership, termination recovery, retry saturation, and cleanup
   convergence have fresh regression and bounded-probe evidence.
5. Scheduling changes meet their stated throughput thresholds with no
   correctness, tail, retry, or cleanup regression, or are explicitly deferred.
6. Token, cached-token, cost, and coordination metrics are promoted only from
   authoritative run-bound receipts; missing attribution remains blocked or
   inconclusive.
7. Compatibility deletion has source-wide caller and replay proof, and no
   historical `pilot_artifacts/` content is mass-deleted.
8. `skill-verification-before-completion` confirms fresh final checks, accepted
   blockers/deferrals, clean scope reconciliation, and the correct plan status
   before any later branch disposition.
