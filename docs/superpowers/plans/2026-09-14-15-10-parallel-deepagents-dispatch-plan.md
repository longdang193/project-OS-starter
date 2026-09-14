---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: parallel-deepagents-dispatch
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - scripts/deepagents_result_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_dcode_project.py
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Parallel DeepAgents Dispatch

## Goal

Implement and verify a bounded two-lane DeepAgents dispatch pilot using current Herdr lifecycle evidence, isolated Git worktrees, exclusive pane bindings, and existing `dcode-project` receipts. Keep single-lane behavior unchanged. Do not add a supervisor, second lifecycle schema, durable runtime registry, or optimistic task acceptance path.

## Implementation Outcomes

### Consistent attempt-safe evidence

`_build_assignment_result()` remains the single lane-result composition boundary. Structured lifecycle sections and compatibility fields agree; all facts retain `dispatch_id`, stable task identity, and unique `attempt_id`; stale receipts cannot settle replacement attempts.

### Bounded parallel coordinator

The plan/task coordinator admits at most two dependency-ready lanes only when worktree, pane, write-set, contract, and mutable-resource isolation are proven. `scripts/herdr_parallel_dispatch.py` collects blocking launcher subprocesses and tagged preparation/final evidence without ledger mutation, worker cancellation claims, or persistent runtime state.

### Pilot proof and rollout gate

Mocked lifecycle tests, dry-run resolution, a sequential control, and three paired harmless real trials provide evidence for admission, delivery uncertainty, retry, deferred cancellation, cleanup, receipt attribution, exact combined-revision review, and declared wall-time/model-usage thresholds.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`; use `skill-deepagents-executing-plans` only for bounded approved DeepAgents lanes.
- Isolation: dedicated implementation worktree on `codex/parallel-deepagents-dispatch` for all source/test/docs changes; separate temporary pilot worktrees for real lanes.
- Commit policy: no commits during plan drafting; implementation execution requires one lead-owned checkpoint after accepted task proof; lane commits only when explicitly granted by active task authority.
- Preauthorized local actions: inspect and edit named files in the implementation worktree, run named tests/validators, create declared isolated pilot worktrees, run bounded harmless pilot tasks, and record evidence in this plan.
- User-approval actions: push, merge, publication, destructive recovery, discard, cleanup outside task-owned pilot resources, or any mutation of `.playwright-mcp/` or `db/`.
- Parallel ownership: Task 3 owns plan-side admission validation; Task 4 owns `scripts/herdr_parallel_dispatch.py`, its tests, bounded subprocess coordination, and aggregation; Task 5 owns measurement; Task 7 owns runtime-surface documentation and final integration review; real pilot lanes own separate worktrees and disjoint write sets.
- Sequential fallback: stop new admission when any gate fails; retain starting, running, or uncertain attempts; reconcile plan, Git, process/descendant, pane, receipt, and cleanup evidence; redispatch only tasks proven safe after retirement. Never restart uncertain work merely because launcher observation failed.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/parallel-deepagents-dispatch`
- Base commit: `c086339c08bb396d32be44a2b848b1ab473fa52c`
- Expected workspace: dedicated implementation worktree from `c086339c08bb396d32be44a2b848b1ab473fa52c`; lead workspace preserves untracked `.playwright-mcp/` and `db/`
- Next action: execute Task 2 result derivation and stale-attempt regression work
- Blockers: none for drafting; implementation remains blocked while plan status is `proposed`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | implementation worktree | `codex` | none | focused baseline and contract matrix | `250 passed`; preservation snapshot recorded |
| Task 2 | `active` | implementation worktree | `codex` | Task 1 | builder/receipt tests pass | active |
| Task 3 | `pending` | implementation worktree | `codex` | Task 2 | admission and identity tests pass | pending |
| Task 4 | `pending` | implementation worktree | `codex` | Task 3 | mocked parallel lifecycle tests pass | pending |
| Task 5 | `pending` | implementation worktree | `codex` | Task 4 | measurement and dry-run evidence | pending |
| Task 6 | `pending` | isolated pilot worktrees | `deepagents` | Task 5 | two harmless real lanes and receipts | pending |
| Task 7 | `pending` | implementation/integration worktree | `codex` | Task 6 | docs update, combined-revision review, final verification | pending |

## Task Breakdown

### Task 1: Establish baseline and contract matrix

**Purpose:**
- bind implementation work to current lifecycle behavior, existing tests, and preserved workspace paths before edits.

**Task Function:**
- inspect current launcher, receipt, lock, discovery, dry-run, and plan-coordination boundaries; record expected facts and existing regressions.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source inspection and baseline verification; no delegation benefit.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract review of exact current symbols and test seams.

**Specification Coverage:**
- Current State and Evidence; lane admission; lifecycle evidence composition; ownership invariants.

**Required Skills:**
- `skill-plan-document-reviewer`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_build_assignment_result`, `_classify_deepagents_outcome`, `_deepagents_completion_evidence`, target discovery helpers, dry-run branch.
- Inspect: `scripts/deepagents_result_contract.py:parse_result_receipt`, `encode_result_receipt`.
- Inspect: `scripts/dcode_project.py:_publish_result_receipt`, `_role_views_lock`, `main`.
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_dcode_project.py`, `docs/operating_system/runtime/runtime-surfaces.md`.

**Dependencies:**
- dedicated implementation worktree from base commit and preservation of lead-workspace `.playwright-mcp/` and `db/`.

**Authority:**
- Preauthorized local actions: read named files and run baseline commands; do not edit source or preserved paths.
- Stop for: base drift, missing named symbols, or any required change outside declared targets.

**Steps:**
- [x] Step 1: Capture `git status --short`, `git rev-parse HEAD`, and read-only preservation hashes for `.playwright-mcp/` and `db/`.
- [x] Step 2: Run focused launcher and receipt tests; record counts and failures.
- [x] Step 3: Record contract matrix mapping each lifecycle fact to owner, source, and proof.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- [x] `git status --short`
- Expected: baseline tests pass; only declared untracked preservation paths exist.

**Accepted Evidence:**
- `250 passed in 5.56s`.
- Base `c086339c08bb396d32be44a2b848b1ab473fa52c`; branch `codex/parallel-deepagents-dispatch`; dedicated worktree verified.
- Lead-workspace preservation snapshot: `.playwright-mcp/` 34 files / 624833 bytes / aggregate `89D20F9B915B2C7A50C8052E3280432BC01322747EB6F329B21359B41B925E0A`; `db/` 8 files / 540394 bytes / aggregate `1DEFE73D54AA4DDBA6006E5FA8348B1FAB2F6BE1170C2E6C41F8FE118643B02D`.

**Exit Criteria:**
- baseline evidence and contract matrix identify exact edit/test seams; no unresolved source contradiction remains.

### Task 2: Normalize result derivation and stale-attempt handling

**Purpose:**
- make existing lane evidence internally consistent without creating a second verdict layer.

**Task Function:**
- update shared result derivation and receipt correlation; preserve delivery, execution, observation, task result, cleanup, and performance sections.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: shared lifecycle semantics, retry identity, and failure-state risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of result-field consistency and stale receipt boundaries.

**Specification Coverage:**
- Requirements: Lifecycle evidence composition; Delivery, execution, and acceptance separation; Retry and stale-receipt protection.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_build_assignment_result`, `_classify_deepagents_outcome`, `_read_deepagents_receipt` only where derivation/correlation is inconsistent.
- Modify: `scripts/deepagents_result_contract.py:parse_result_receipt` only if current validation cannot reject stale/malformed attempt evidence.
- Verify: `tests/test_herdr_main_launcher.py` builder, classifier, timeout, receipt, and attempt-identity tests.
- Verify: `tests/test_dcode_project.py` receipt publication and cleanup tests.

**Dependencies:**
- Task 1 baseline and contract matrix complete.

**Authority:**
- Preauthorized local actions: edit only named symbols/files, add focused regression tests, and run named tests.
- Stop for: new lifecycle schema, new `accepted: true` path, changes to runtime ownership, or failing unrelated tests.

**Steps:**
- [ ] Step 1: Add failing tests for compatibility-field agreement, preserved known facts after later errors, and late receipt rejection across attempt IDs.
- [ ] Step 2: Make smallest shared-boundary change so structured sections remain authoritative and compatibility fields derive consistently.
- [ ] Step 3: Verify uncertain delivery reconciles same attempt and confirmed retry uses new attempt identity.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- Expected: new regressions pass; no test permits launcher start or worker completion to claim task acceptance.

**Exit Criteria:**
- one lane result per attempt is internally consistent; stale receipts cannot settle replacements; observation remains explicit.

### Task 3: Add deterministic lane admission and stable identity checks

**Purpose:**
- reject unsafe parallel waves before write-capable launch.

**Task Function:**
- validate plan-side lane descriptors before invoking the foreground coordinator; keep workflow dependencies/write authority with CoS/plan and pane/runtime evidence with Herdr.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: concurrency safety, worktree/write-set conflicts, dependency semantics, and resource ownership.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent challenge of conflict detection and preserved discovery semantics.

**Specification Coverage:**
- Requirement: Lane admission; invariants for worktree, pane, write-set, discovery, and mutable resources.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `docs/superpowers/plans/2026-09-14-15-10-parallel-deepagents-dispatch-plan.md` lane contract only during planning; implementation lane descriptors are consumed by Task 4 and are not interpreted by `_resolve_target_selector`.
- Verify: `scripts/herdr_main_launcher.py:_resolve_target_selector`, `resolve_launch` preserve pane resolution and runtime evidence ownership without workflow dependency logic.
- Verify: `scripts/herdr_main_launcher.py:_resolve_target_selector` preserves full eligible-set reporting.
- Modify: `tests/test_herdr_parallel_dispatch.py` with same-worktree, overlapping-write-set, duplicate-pane, unresolved-dependency, and isolated-lane cases.

**Dependencies:**
- Task 2 complete; plan/task lane input shape is fixed before implementation.

**Authority:**
- Preauthorized local actions: edit named launcher/test files and run focused validation; no worktree deletion or external writes.
- Stop for: missing canonical plan-ledger input, selected-pane-only discovery requirement, or need for a new durable registry.

**Steps:**
- [ ] Step 1: Define lane descriptor fields: plan task/lane ID, task text/hash, executor/profile, repo/worktree, expected base, session/pane, allowed write set, fixed shared contracts, dependency status, and mutable-resource policy.
- [ ] Step 2: Validate separate worktrees, exclusive panes, disjoint write sets, fixed shared contracts, dependency readiness, and mutable-resource isolation; cap admitted lanes at two.
- [ ] Step 3: Return deterministic admitted/rejected records; leave `_resolve_target_selector` responsible only for full eligible-set discovery and pane/runtime evidence.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_parallel_dispatch.py -q`
- Expected: unsafe waves reject before launch; valid two-lane input admits exactly two lanes; single-lane behavior remains unchanged.

**Exit Criteria:**
- admission is deterministic, pre-launch, bounded to two, and backed by focused tests.

### Task 4: Implement bounded parallel coordination and result aggregation

**Purpose:**
- run independent admitted lanes concurrently while preserving per-lane lifecycle facts and explicit batch uncertainty.

**Task Function:**
- implement the repository-owned foreground coordinator `scripts/herdr_parallel_dispatch.py` with standard-library subprocess/threading only; collect lane evidence without ledger mutation, worker cancellation claims, or a persistent registry.

**Template Profile:**
- Controller-selected: `xhigh`
- Selection basis: concurrency, timeout/retry/cancel semantics, sibling preservation, and exact ownership boundaries.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: independent failure-path and aggregation review.

**Specification Coverage:**
- Outcomes: Bounded parallel lifecycle; Safe retry, cancellation, and reconciliation; Final combined-revision acceptance.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`

**Files And Symbols:**
- Add: `scripts/herdr_parallel_dispatch.py:load_lane_descriptors`, `run_lane`, `parse_launcher_records`, `run_parallel`.
- Modify: `tests/test_herdr_parallel_dispatch.py` with deterministic mocked lanes for barrier concurrency, capacity retention, startup failure, late receipt, timeout, deferred cancellation, partial failure, interruption, and sibling preservation.
- Verify: `scripts/herdr_main_launcher.py:_main_body`, `resolve_launch`, `_deepagents_completion_evidence` remain per-lane lifecycle owners.
- Verify: `scripts/dcode_project.py` remains worker/descendant/role-view owner and publishes one receipt per attempt.

**Dependencies:**
- Task 3 admission checks complete.

**Authority:**
- Preauthorized local actions: edit named launcher/test files, run deterministic mocks, and record derived aggregate evidence; no real worker launch yet.
- Stop for: need for atomic Herdr API not present, second supervisor/registry, duplicate polling loop, or cross-lane shared mutable writes.

**Steps:**
- [ ] Step 1: Add a start/release barrier test proving both workers start before either finishes; reject a third launch while two slots are occupied.
- [ ] Step 2: Implement tagged JSONL framing for preparation output, final assignment output, child exit status, stderr diagnostics, occupied capacity, and unresolved conditions.
- [ ] Step 3: Keep slots occupied after launcher exit, transport timeout, observation expiry, or uncertain cleanup until retirement evidence; stop admission on controller interruption.
- [ ] Step 4: Model lane A start plus lane B launch failure, potentially live worker timeout, deferred cancellation racing with completion, and sibling preservation; never claim active worker cancellation.
- [ ] Step 5: Derive batch `PASS`, `FAIL`, or `BLOCKED` only as a CoS consumer decision; `FAIL` requires settled lifecycle, while unresolved state yields `BLOCKED` and preserves known failure.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py -q`
- Expected: barrier proves overlap; capacity, interruption, partial-start, stale-attempt, deferred-cancellation, and mixed-verdict cases pass; no old attempt settles new attempt.

**Exit Criteria:**
- two admitted mocked lanes can complete, fail, timeout, defer cancellation, or remain uncertain without evidence loss, unsafe retry, or false retirement.

### Task 5: Measure probe cost and validate dry-run resolution

**Purpose:**
- prove any observation/discovery optimization reduces cost without weakening semantics.

**Task Function:**
- compare baseline and bounded parallel resolution/observation metrics; change only measured redundant work.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded measurement and documentation; no new runtime abstraction.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check that candidate-set semantics and evidence remain unchanged.

**Specification Coverage:**
- Decision: Separate budgets; validation performance claim; preserved full discovery semantics.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: existing performance counters and phase records in `scripts/herdr_main_launcher.py` and `scripts/herdr_parallel_dispatch.py`; no new metric store.
- Verify: `tests/test_herdr_main_launcher.py` and `tests/test_herdr_parallel_dispatch.py` performance, barrier, capacity, and discovery tests.
- Verify: dry-run branch in `scripts/herdr_main_launcher.py` and emitted resolved JSON.

**Dependencies:**
- Task 4 mocked lifecycle complete.

**Authority:**
- Preauthorized local actions: run dry-run and local benchmarks; make measured changes only in named launcher/test files.
- Stop for: semantic discovery change, unmeasured optimization, or performance regression with no safe explanation.

**Steps:**
- [ ] Step 1: Record the runtime implementation commit, exact launcher path, `dcode-project` wrapper path/version, and deployment parity needed for the pilot.
- [ ] Step 2: Run dry-run resolution and a sequential control using identical harmless-task descriptors, profiles, limits, clean worktrees, and implementation revision.
- [ ] Step 3: Set pilot gates before execution: three paired trials; parallel median wall time at least 20% lower; model usage no more than 110% of sequential control; positive overlap every trial; zero retries, duplicate attempts, and cleanup failures.
- [ ] Step 4: Record wall time, subprocess/probe count, output bytes, model usage, retries, and candidate-set equality; change only demonstrably redundant observation work.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py -q`
- [ ] `py -3 scripts/herdr_main_launcher.py --help`
- Expected: dry-run proves resolution only; candidate sets remain equal; no worker starts during dry-run; thresholds and runtime paths are recorded before real pilot.

**Exit Criteria:**
- dry-run and sequential-control evidence is reproducible; implementation/runtime revisions are pinned; thresholds are recorded before the real pilot.

### Task 6: Run two harmless real DeepAgents lanes

**Purpose:**
- prove real process, receipt, cleanup, worktree, and pane behavior after mocks and dry-run pass.

**Task Function:**
- execute two non-production, disjoint, write-capable tasks in separate worktrees and exclusive panes; collect exact lifecycle evidence.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded harmless runtime execution with low task ambiguity and isolated resources.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: independent evidence review of process ownership, receipts, cleanup, and Git state.

**Specification Coverage:**
- Outcome: Pilot proof and rollout gate; real dependency evidence; worktree and pane invariants.

**Required Skills:**
- `skill-deepagents-executing-plans`, `skill-backend-verification`, `skill-using-git-worktrees`

**Files And Symbols:**
- Verify: `scripts/herdr_parallel_dispatch.py` tagged JSONL coordinator output and capacity evidence.
- Verify: `scripts/herdr_main_launcher.py` emitted preparation and final assignment results.
- Verify: `scripts/dcode_project.py` worker/descendant/role-view receipt.
- Verify: `dcode-project` wrapper path/version resolves to the recorded runtime implementation revision or approved deployed equivalent.
- Verify: Git worktree/branch/base and exact task-owned changes.
- Pilot output paths: `pilot-artifacts/parallel-dispatch/lane-a.txt` and `pilot-artifacts/parallel-dispatch/lane-b.txt` only.
- Do not modify: `.playwright-mcp/`, `db/`, or unrelated repository paths.

**Dependencies:**
- Tasks 1–5 complete; runtime implementation revision and wrapper parity recorded; pilot worktrees, panes, branches, prompts, and thresholds declared in active task authority.

**Authority:**
- Preauthorized local actions: create declared pilot branches/worktrees, run sequential control and two bounded harmless tasks, collect normalized receipts, create exact lane commits for pilot output paths, and remove only task-owned runtime resources after positive retirement proof; defer Git worktree disposal until Task 7.
- Stop for: uncertain process retirement, cleanup ownership, worktree identity, wrapper/runtime mismatch, receipt attribution, unexpected path changes, threshold miss, or any need for destructive recovery.

**Steps:**
- [ ] Step 1: Create `codex/parallel-dispatch-lane-a` and `codex/parallel-dispatch-lane-b` from the recorded runtime implementation revision; bind exclusive Herdr panes.
- [ ] Step 2: Run three sequential-control trials for the exact prompts, then three paired parallel trials with concurrency limit two and separate result files/attempt IDs.
- [ ] Step 3: Lane A creates only `pilot-artifacts/parallel-dispatch/lane-a.txt` with `lane-a complete`; Lane B creates only `pilot-artifacts/parallel-dispatch/lane-b.txt` with `lane-b complete`; no lane touches source, tests, docs, `.playwright-mcp/`, or `db/`.
- [ ] Step 4: Capture tagged preparation/final launcher JSONL, normalized `lifecycle_receipt`, stderr, process/descendant evidence, cleanup state, Git revisions, wrapper path/version, and metrics.
- [ ] Step 5: If any attempt is uncertain, stop new admission and reconcile; never restart same task sequentially until retirement is proven. Keep lane outputs and worktrees through Task 7.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- [ ] read-only Git/worktree inspection, task-owned artifact checks, and three paired-trial threshold comparison
- Expected: both lanes have distinct attempts, overlapping execution intervals, no role-view collision, no stale receipt settlement, positive cleanup proof, and all declared thresholds pass.

**Exit Criteria:**
- real pilot produces complete per-lane normalized evidence, pinned runtime paths, no unresolved ownership or cleanup ambiguity, and threshold evidence for a separate expansion decision.

### Task 7: Review exact combined revision and close verification

**Purpose:**
- prove final acceptance against integrated changes and reconcile docs, tests, generated surfaces, and preserved paths.

**Task Function:**
- create the temporary integration branch from the recorded runtime implementation revision, integrate exact lane commits, update canonical runtime ownership documentation, inspect the combined revision, and record deviations/deferrals without changing plan status prematurely.

**Template Profile:**
- Controller-selected: `review`
- Selection basis: independent final review and evidence reconciliation.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: final verification against exact combined revision and completion criteria.

**Specification Coverage:**
- Outcome: Final combined-revision acceptance; all completion criteria.

**Required Skills:**
- `skill-plan-document-reviewer`, `skill-verification-before-completion`, `skill-backend-verification`, `skill-finishing-a-development-branch`

**Files And Symbols:**
- Modify: `docs/operating_system/runtime/runtime-surfaces.md` to name `scripts/herdr_parallel_dispatch.py` as foreground coordinator, preserve Herdr/dcode/Git ownership, and document deferred active cancellation plus normalized receipt retention.
- Verify: `scripts/herdr_parallel_dispatch.py`, all changed files, and exact combined Git revision.
- Verify: `tests/test_herdr_parallel_dispatch.py` and focused runtime tests.
- Verify: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md` and this plan.

**Dependencies:**
- Task 6 complete with accepted pilot evidence.

**Authority:**
- Preauthorized local actions: create temporary integration branch from recorded runtime revision, cherry-pick exact lane commits, edit named runtime documentation, run final tests/validators/diff checks, perform read-only review, and invoke finishing cleanup only after positive retirement/retention proof.
- Stop for: failed required proof, post-review changes, stale generated surfaces, unresolved plan/Git mismatch, or any unapproved merge/publication/cleanup.

**Steps:**
- [ ] Step 1: Create temporary `codex/parallel-dispatch-integration` from the recorded runtime implementation revision and cherry-pick exact lane commits; do not merge or push.
- [ ] Step 2: Review exact combined revision, including both pilot output paths, not only lane revisions or baseline.
- [ ] Step 3: Update and review `docs/operating_system/runtime/runtime-surfaces.md`; sync/check generated surfaces if canonical skill/runtime ownership requires it.
- [ ] Step 4: Keep lane outputs, normalized evidence, and combined worktree until verification and retention dependencies finish; then use `skill-finishing-a-development-branch` for retirement and worktree disposal.
- [ ] Step 5: Compare preserved `.playwright-mcp/` and `db/` records.
- [ ] Step 6: Run `skill-verification-before-completion`; mark plan `completed` only on `verified`.

**Verification:**
- [ ] `py -3 -m pytest tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_starter_lifecycle_contract.py tests/test_validate_planning_lifecycle.py -q`
- [ ] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- [ ] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `git diff --check`
- Expected: required tests and validators pass; exact combined revision and runtime paths are reviewed; docs match ownership; preserved paths remain byte-identical; plan verification returns `verified`.

**Exit Criteria:**
- every task has accepted proof; no unresolved required blocker or scope deviation remains; concurrency remains capped at two; any expansion is a separate approved decision after thresholds pass.

## Verification

- `py -3 -m pytest tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_starter_lifecycle_contract.py tests/test_validate_planning_lifecycle.py -q`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- read-only preservation comparison for `.playwright-mcp/` and `db/`
- `skill-verification-before-completion` returns `verified` before plan status changes to `completed`

## Completion Criteria

The plan is ready for completion verification when:

1. result construction reuses existing lifecycle sections and compatibility fields remain consistent
2. lane admission proves isolated worktrees, panes, write sets, dependencies, contracts, and mutable resources
3. bounded two-lane coordination preserves per-lane evidence and explicit uncertainty
4. retries, cancellation, timeouts, stale receipts, and cleanup uncertainty have focused regression proof
5. full auto-discovery semantics remain unchanged
6. dry-run is not treated as real worker proof
7. two harmless real lanes produce complete receipt and cleanup evidence
8. final review targets exact combined revision
9. required tests, validators, adapter checks, diff checks, and preservation proof pass
10. no supervisor, second ledger, durable runtime registry, or `accepted: true` shortcut was added
11. concurrency remains capped at two; any broader rollout is a separate approved decision after declared wall-time, cost, overlap, retry, duplicate, and cleanup gates pass
12. `skill-verification-before-completion` returns `verified`
