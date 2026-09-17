---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: deepagents-runtime-boundary-completion
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/dcode_project.py
  - scripts/deepagents_result_contract.py
  - scripts/herdr_attempt_contract.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - scripts/validate_repo_contracts.py
  - scripts/validate_planning_lifecycle.py
  - scripts/deploy_agent_runtime.py
  - tests/test_dcode_project.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_deploy_agent_runtime.py
  - .github/workflows/runtime-contracts.yml
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/superpowers/plans/2026-09-15-herdr-autonomy-predictability-update-plan.md
---

# Complete DeepAgents Runtime Boundaries

## Goal

Reconcile the parent dispatch specification, then complete existing DeepAgents
attempt, budget, result, scheduling, and guidance contracts without adding a
scheduler service, heartbeat store, runtime ledger, or concurrency beyond the
current limit of two lanes.

## Implementation Outcomes

### Transactional attempt ownership

Assignment claim, recovery, settlement, and settled-attempt replacement use one
assignment-scoped short-lived lock. Worker execution and role-view ownership
remain separately locked. Concurrent claims produce one owner and no replay.

### One bounded budget model

Durable allowances, requested numeric grants, and effective worker budgets use
integer seconds. Monotonic clocks remain fractional internally. One attempt
deadline starts at launcher invocation and reserves settlement time; preflight
cost reduces effective worker time before launch, and dispatcher waits are
bounded by that same deadline.

### One semantic decision contract

The shared attempt contract owns lifecycle, admission, settlement, budget, and
eligibility meaning. Launcher, dispatcher, and wrapper consume one reducer
instead of rebuilding state combinations locally. Runtime guidance validates
structural ownership invariants rather than copied prose.

### Separate lifecycle and task-result evidence

Lifecycle receipts continue to prove process, descendant, cleanup, and recovery
facts. A bound `TaskResult` record reports progress and references checkpoint,
remaining-work, verification, and continuation evidence; it does not prove
that verification or acceptance succeeded. Pane text remains fallback
diagnostics, not normal completion transport or acceptance authority.

### Bounded ready-queue scheduling

Dispatcher admission distinguishes `READY`, `DEFERRED`, and `BLOCKED` lanes.
Only temporary capacity or explicitly shareable resource contention defers
work. Dependency-awaiting-acceptance, overlapping write ownership, duplicate
assignment, and uncertain prior ownership remain blocked or return to CoS.
Current `MAX_CONCURRENCY = 2` remains unchanged.

### Operational proof

Focused runtime suites run in CI on Linux and Windows before broader scheduling
work lands. Shared runtime deployment uses staged validation and an atomic
version selection before switching the deployed projection. Historical plan
metadata cannot remain `active` after all tasks and verification are complete.

## Review Basis

Verification against `main` at `7fe01a3df73f3597b39e45444e4def6b1ae0dd92` supports
these findings:

- **P1 assignment race confirmed:** `scripts/dcode_project.py:_claim_attempt`
  performs guard read, reconciliation, decision, and atomic replacement without
  an assignment-scoped critical section. The existing role-view lock is keyed by
  worktree, so it cannot serialize claims for the same assignment across
  worktrees. Existing claim coverage is sequential only.
- **P1 budget/deadline mismatch confirmed:**
  `scripts/herdr_attempt_contract.py:resolve_attempt_budget` can return `100.0`
  for a valid float allowance, while
  `scripts/herdr_parallel_dispatch.py:_effective_budget_is_contained` rejects
  non-`int` effective values. `resolve_launch` resolves budget before later
  preflight work, and `run_lane(..., timeout_seconds=None)` passes an unbounded
  wait to `process.communicate` when callers omit the value.
- **P2 shared-contract consumption confirmed:**
  `derive_lifecycle_state` and `eligibility_action` have no production callers;
  `_claim_attempt` reconstructs lifecycle/admission combinations. The boundary
  validator checks `_ADMISSION_RESULTS` but wrapper fallback code defines
  unprefixed `ADMISSION_RESULTS`, and it still requires stale ownership prose.
- **P2 structured-result direction confirmed:**
  `task_result_path` already exists in the attempt guard, while the canonical
  guidance already defines progress, remaining work, requested increase, reason,
  and checkpoint fields. The durable channel is incomplete, not absent.
- **P2 scheduling and CI gaps confirmed:** `_invalidate_wave` clears prior
  admissions on later conflict, capacity overflow is rejected, and
  `run_parallel` exposes results only after pool shutdown. The current CI job
  invokes only validator/configuration suites; it omits runtime contract suites
  and has no Windows job.
- **P2 lifecycle metadata issue confirmed:**
  `2026-09-15-herdr-autonomy-predictability-update-plan.md` remains `active`
  despite completed task rows, recorded verification, `Next action: none`, and
  no blockers.
- **P3 deployment hardening supported:** `scripts/deploy_agent_runtime.py`
  writes deployed files destination-by-destination. Staged deployment is useful,
  but follows correctness work and must not change ownership or authority.

## Required Specification Delta

Task 1 must update
`docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md` before
runtime implementation begins. The delta must reconcile these contracts without
weakening existing safety rules:

- A wave is validated for unsafe ownership before launch. `DEFERRED` is only a
  scheduler state for temporary capacity or explicitly shareable resource
  contention; it is not partial acceptance of an unsafe wave.
- Dependencies awaiting CoS acceptance, overlapping write ownership, duplicate
  assignments, and uncertain prior process ownership do not auto-refill.
- The 1,800-second attempt ceiling includes worker execution, output draining,
  descendant retirement, cleanup, and settlement. Any collection allowance is
  reserved inside that ceiling and cannot extend worker execution or authorize
  replay.
- `TaskResult` reports progress and references evidence. Lifecycle receipts
  prove process/resource facts. Neither record grants CoS acceptance authority.
- `CONTINUATION_ELIGIBLE` is a fact consumed by CoS; dispatcher and worker
  cannot authorize continuation or replay.

## Non-Goals And Deferrals

- No new coordinator, scheduler daemon, heartbeat, event bus, or persistent
  runtime registry.
- No increase above `MAX_CONCURRENCY = 2`.
- No hot mutation of deadlines, child-spend accounting, or provider retry-policy
  tuning before ownership and deadline proof exists.
- No CAS revision field unless a deterministic stale-controller test still finds
  a gap after the assignment lock is implemented; mutual exclusion plus current
  binding validation is the smallest safe baseline.
- No external credentials, MCP authorization, or provider configuration changes
  in implementation or CI. External provider probes remain bounded and
  read-only.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: fresh native Git worktree on a new `codex/` branch from the base commit; preserve current main and unrelated untracked paths
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, test, validator, workflow, canonical guidance, and plan files; run focused/full checks, bounded local probes, adapter synchronization, and staged deployment tests without credentials
- User-approval actions: external provider authentication or configuration, destructive cleanup, commit, push, merge, publication, and runtime deployment to user-global targets
- Parallel ownership: `none`; shared contract and scheduler changes are sequential
- Sequential fallback: keep the same task order and run all tasks in one Codex workspace when worktree or executor independence cannot be proven

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/deepagents-runtime-boundary`
- Base commit: `7fe01a3df73f3597b39e45444e4def6b1ae0dd92`
- Expected workspace: fresh worktree `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-deepagents-runtime-boundary` at base; unrelated main-worktree untracked files remain preserved
- Next action: none; implementation and verification complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | parent-spec delta and contract proof | verified |
| Task 2 | `completed` | current | `codex` | Task 1 | concurrent claim and settlement proof | verified; Windows race fixed with blocking assignment lock |
| Task 3 | `completed` | current | `codex` | Task 2 | integer budget and one-deadline proof | verified |
| Task 4 | `completed` | current | `codex` | Task 3 | reducer, validator, and plan-lifecycle proof | verified |
| Task 5 | `completed` | current | `codex` | Task 3 | Linux/Windows runtime CI proof | workflow added and local Windows checks passed |
| Task 6 | `completed` | current | `codex` | Task 4 | structured task-result and continuation proof | verified |
| Task 7 | `completed` | current | `codex` | Task 6 | ready-queue, deferred-conflict, and bounded-result proof | verified |
| Task 8 | `completed` | current | `codex` | Task 7 | staged-deployment and atomic-reader proof | verified |

## Task Breakdown

### Task 1: Reconcile parent specification

**Purpose:**
- Reconcile ownership, continuation, budget, evidence, and queue semantics before runtime implementation.

**Task Function:**
- Convert confirmed runtime findings into one executable contract without adding a coordinator or registry.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: specification ownership and safety-boundary reconciliation require lead-controller review.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: existing planning and repository contract validators prove structural consistency.

**Specification Coverage:**
- Parent spec defines admission, resource occupancy, task outcome, continuation authority, deadline ceiling, evidence ownership, and deferred/blocked semantics.

**Required Skills:**
- `skill-systematic-debugging`, `skill-plan-document-reviewer`, `skill-writing-plans`

**Files And Symbols:**
- Inspect: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`, `scripts/validate_planning_lifecycle.py`, `scripts/validate_repo_contracts.py`
- Modify: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`, `scripts/validate_planning_lifecycle.py`, `tests/test_validate_planning_lifecycle.py`, `tests/test_validate_repo_contracts.py`

**Dependencies:**
- None; source behavior and current tests remain authoritative for resolving contradictions.

**Authority:**
- Preauthorized local actions: edit parent specification and targeted validator fixtures/tests only.
- Stop for: changing runtime behavior, adding persistent coordination state, or weakening ownership and acceptance rules.

**Steps:**
- [x] Step 1: Add red fixtures for temporary capacity deferral versus unsafe ownership conflict, continuation eligibility versus dispatch permission, and resource state versus task outcome.
- [x] Step 2: Update parent spec with one 1,800-second end-to-end deadline, one charge per attempt including interruption, settled prior ownership plus new worktree binding for fresh attempts, `CONTINUATION_ELIGIBLE` as a CoS-consumed fact, and independent lifecycle/task-result evidence.
- [x] Step 3: Define missing, malformed, stale, or contradictory evidence as reconciliation or escalation; it never authorizes acceptance, replay, or capacity release.
- [x] Step 4: Make historical-plan terminal-state validation an explicit validator-backed decision, not prose-only cleanup.

**Verification:**
- [x] `py -m pytest tests/test_validate_planning_lifecycle.py tests/test_validate_repo_contracts.py -q`
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- Expected: fixtures reject unsafe auto-refill and unauthorized continuation; canonical documents pass.

**Exit Criteria:**
- Parent specification is internally consistent and executable by Tasks 2–8.

### Task 2: Serialize assignment claim and settlement

**Purpose:**
- Close the cross-worktree read/decide/write race without holding a lock during worker execution.

**Task Function:**
- Establish deterministic concurrent ownership proof and implement the smallest assignment transaction boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared-state correctness and platform-sensitive file locking require controller-owned integration.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: task-local concurrent regression is sufficient.

**Specification Coverage:**
- One assignment has at most one active owner. Same binding is idempotent. Competing binding blocks. Settled replacement is serialized. Unknown evidence never authorizes replay.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_role_views_lock`, `_claim_attempt`, `_reconcile_attempt`, `_settle_attempt`
- Modify: `scripts/dcode_project.py:_attempt_lock_path`, `_claim_attempt`, `_reconcile_attempt`, `_settle_attempt`
- Modify: `tests/test_dcode_project.py` concurrent claim, reconciliation, settlement, and replacement cases

**Dependencies:**
- Task 1 complete; current guard schema and binding validation remain authoritative.

**Authority:**
- Preauthorized local actions: add assignment-scoped lock and deterministic concurrent regression tests in listed files.
- Stop for: stale-controller safety that cannot be proven by lock plus current binding, cross-repository coordination, or destructive recovery.

**Steps:**
- [x] Step 1: Add failing real multi-process tests on Linux and Windows using one shared guard root and one assignment with two distinct attempts; assert exactly one admission and no worker launch for the competitor.
- [x] Step 2: Add a lock path derived from `SHA256(assignment_id)` under the existing temporary lock parent. Acquire it around claim, reconciliation transition, settlement, and settled replacement only; retain the worktree role-view lock separately.
- [x] Step 3: Refactor nested reconciliation/settlement calls so one transaction does not reacquire a non-reentrant platform lock.
- [x] Step 4: Add interruption and same-binding tests proving idempotency, correlated evidence recovery, mismatched evidence blocking, and no replay after settled replacement.

**Verification:**
- [x] `py -m pytest tests/test_dcode_project.py -q`
- Expected: concurrent ownership, idempotency, recovery, and settlement tests pass on Linux and Windows without holding assignment lock during worker execution.

**Exit Criteria:**
- Cross-worktree claims serialize; active ownership remains blocking; proven settlement permits replacement; uncertain ownership remains recovery-required.

### Task 3: Normalize integer budgets and one attempt deadline

**Purpose:**
- Remove float containment drift and stop preflight or dispatcher waits from escaping the attempt budget.

**Task Function:**
- Align contract resolution, launcher projection, wrapper timeout, and dispatcher reaping to one monotonic deadline.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deadline ownership crosses contract, launcher, dispatcher, and wrapper boundaries.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused boundary and fake-clock tests cover conversion and expiry.

**Specification Coverage:**
- Integer durable seconds, floor-only conversion, minimum one-second worker budget, settlement reserve, and bounded outer waits.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_attempt_contract.py:resolve_attempt_budget`, `remaining_attempt_seconds`
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`, `_main_body`, `_run_deepagents_worker`
- Inspect: `scripts/herdr_parallel_dispatch.py:_effective_budget_is_contained`, `run_lane`
- Modify: same symbols and their focused tests

**Dependencies:**
- Task 2 complete; attempt ownership must not be changed while budget tests run.

**Authority:**
- Preauthorized local actions: modify numeric normalization, deadline propagation, dispatcher wait bounds, and named tests.
- Stop for: provider retry-policy changes, hot deadline mutation, or budget semantics that expand plan Authority.

**Steps:**
- [x] Step 1: Add red tests for `100.0` remaining allowance, fractional remaining time, zero-after-reserve, explicit `600`, and numeric grants exceeding remaining authority.
- [x] Step 2: Make `resolve_attempt_budget` return positive integer seconds by flooring finite fractional availability; reject results below one second and preserve `native` sentinel semantics.
- [x] Step 3: Keep `_main_body` invocation deadline as authority. Defer final DeepAgents effective timeout calculation until mandatory preflight completes, then project one effective integer timeout immediately before worker launch.
- [x] Step 4: Derive `run_lane` outer `communicate` timeout from the same attempt deadline plus only bounded reaping allowance; reject omitted or expired values instead of passing `None`.
- [x] Step 5: Create the original deadline at launcher invocation and carry it through wrapper setup, locks, MCP setup, transport, worker execution, output drain, descendant retirement, cleanup, and settlement; keep reaping reserve inside the 1,800-second ceiling.
- [x] Step 6: Record one plan-owned charge per attempt, including interruption. Compute remaining allowance from recorded charges; require settled prior ownership and a newly validated worktree binding before any fresh attempt; stop or escalate when authority is exhausted.
- [x] Step 7: Add fake-clock coverage proving wrapper setup consumes remaining worker allowance, coordinated launches reject missing remaining authority, and observation timeout cannot authorize replacement or extend the deadline.

**Verification:**
- [x] `py -m pytest tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py -q`
- Expected: resolver, containment, fake-clock, launcher, timeout, and reaping tests pass with integer effective budgets and no unbounded wait.

**Exit Criteria:**
- Every DeepAgents attempt has one deadline, one effective worker budget, preserved settlement reserve, and bounded dispatcher collection.

### Task 4: Make attempt decisions and guidance structurally canonical

**Purpose:**
- Make one pure semantic reducer authoritative and repair validators and historical lifecycle metadata that still encode old ownership.

**Task Function:**
- Replace duplicated state mapping with shared decisions and enforce source ownership through structural checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract and canonical guidance changes require serialized integration.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: repository validator tests provide direct negative fixtures.

**Specification Coverage:**
- Attempt meaning belongs to shared contract; wrapper records facts; Herdr observes and transports; generated surfaces mirror canonical inputs.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `scripts/herdr_attempt_contract.py:derive_lifecycle_state`, `eligibility_action`, `terminal_settlement_proven`
- Modify: `scripts/herdr_attempt_contract.py` pure `AttemptDecision` reducer and compatibility callers
- Modify: `scripts/dcode_project.py:_claim_attempt`, `_reconcile_attempt`
- Modify: `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py` production consumers
- Modify: `scripts/validate_repo_contracts.py:validate_runtime_boundary_guidance`
- Modify: `tests/test_herdr_attempt_contract.py`, `tests/test_dcode_project.py`, `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_validate_repo_contracts.py`
- Modify: `docs/superpowers/plans/2026-09-15-herdr-autonomy-predictability-update-plan.md`

**Dependencies:**
- Tasks 1–3 complete; decision fields must reflect final lock and budget semantics.

**Authority:**
- Preauthorized local actions: add reducer, move production callers, replace stale structural checks, and close the named historical plan when validator evidence supports completion.
- Stop for: changing CoS acceptance authority, generated files without canonical sync, or broad prose rewrites unrelated to runtime ownership.

**Steps:**
- [x] Step 1: Add red reducer matrix covering unclaimed, active, settled, recovery-required, same-binding, competing-binding, and proven/unknown settlement cases.
- [x] Step 2: Implement one `AttemptDecision` result with lifecycle, admission, eligibility, settlement, recovery, and reason; make existing helper functions delegate or remove them only after production callers move.
- [x] Step 3: Make wrapper and dispatcher consume reducer output; remove inline admission/lifecycle combinations and fallback taxonomy duplication.
- [x] Step 4: Replace English substring checks with structural checks for shared imports, duplicate taxonomies, production consumers, and Herdr observation-only ownership.
- [x] Step 5: Change `2026-09-15-herdr-autonomy-predictability-update-plan.md` to terminal status only after task rows, evidence, blockers, and verification satisfy lifecycle rules.

**Verification:**
- [x] `py -m pytest tests/test_herdr_attempt_contract.py tests/test_dcode_project.py tests/test_validate_repo_contracts.py tests/test_validate_planning_lifecycle.py -q`
- Expected: reducer matrix passes; stale private taxonomy and stale plan fixtures fail; current canonical sources pass.

**Exit Criteria:**
- Production callers use one semantic decision contract; validators detect structural drift; no completed plan remains falsely active.

### Task 5: Add runtime CI

**Purpose:**
- Make runtime-contract regressions visible on both supported operating systems before scheduling and deployment work lands.

**Task Function:**
- Add focused CI proof for ownership, budget, wrapper, launcher, dispatcher, and validator behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: runtime CI protects correctness work and must land before broader scheduling or deployment changes.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: workflow syntax and local workflow-equivalent checks cover scope.

**Specification Coverage:**
- Runtime contract suites are first-class CI evidence on Linux and Windows.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `.github/workflows/repo-contracts.yml`, `scripts/validate_repo_contracts.py`
- Modify: `.github/workflows/runtime-contracts.yml`
- Verify: runtime contract tests and repository validators

**Dependencies:**
- Tasks 2–4 complete; runtime schemas are stable enough for focused CI.

**Authority:**
- Preauthorized local actions: add CI workflow and local workflow-equivalent validation.
- Stop for: deployment changes, credential changes, or CI jobs requiring external provider secrets.

**Steps:**
- [x] Step 1: Add a focused runtime-contract workflow matrix for `ubuntu-latest` and `windows-latest` covering attempt contract, wrapper, launcher, dispatcher, process cleanup, and runtime validators.
- [x] Step 2: Run local workflow-equivalent commands and inspect generated adapter/kit drift.

**Verification:**
- [x] `py -m pytest tests/test_herdr_attempt_contract.py tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_validate_repo_contracts.py -q`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- Expected: local checks pass and CI workflow covers both OS families before Task 6 or Task 7 proceeds.

**Exit Criteria:**
- Runtime suites run in CI on Linux and Windows.

### Task 6: Complete bound structured `TaskResult` and continuation

**Purpose:**
- Separate task progress and continuation evidence from lifecycle receipt and pane diagnostics.

**Task Function:**
- Complete the existing task-result path without adding another result registry or acceptance layer.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: durable schema and continuation semantics require contract ownership.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: schema and integration tests cover direct boundary behavior.

**Specification Coverage:**
- Lifecycle receipt proves process/resource facts. Task result reports progress and references checkpoint facts. CoS alone accepts work and authorizes continuation.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/deepagents_result_contract.py:_validate_payload`, `parse_result_receipt`
- Inspect: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`, `_build_assignment_result`
- Inspect: `scripts/dcode_project.py:_claim_attempt`, `_publish_result_receipt`
- Modify: `scripts/deepagents_result_contract.py` task-result schema/parser
- Modify: `scripts/dcode_project.py` task-result publication and guard binding
- Modify: `scripts/herdr_main_launcher.py` result composition and continuation handoff
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md`, `.agents/skills/skill-deepagents-executing-plans/SKILL.md`, and canonical runtime guidance
- Modify: focused result and continuation tests

**Dependencies:**
- Tasks 4–5 reducer, canonical ownership, and runtime CI are complete.

**Authority:**
- Preauthorized local actions: extend existing result contract, wrapper publication, launcher parsing, continuation guidance, and focused regression tests.
- Stop for: automatic acceptance, replay without settled ownership, raw pane text as authoritative result, or new persistent orchestration state.

**Steps:**
- [x] Step 1: Add failing schema tests binding `assignment_id`, `attempt_id`, `task_sha256`, and `grant_digest` to `progress`, `checkpoint`, `remaining_work`, verification references, continuation request, producer identity, schema version, outcome status, and bounded size.
- [x] Step 2: Make wrapper create the controller-selected absolute result path; define worker publication as bounded JSON written to a temporary sibling and atomically renamed only after identity/schema validation.
- [x] Step 3: Preserve lifecycle receipt independently. Keep result references and settlement evidence when deleting disposable receipts; result-file deletion must not erase recovery facts.
- [x] Step 4: Make launcher and dispatcher consume task-result evidence first; retain pane observation only as explicitly non-authoritative fallback diagnostics. Valid result identity reports progress and references evidence; it does not prove verification or acceptance.
- [x] Step 5: Add deterministic continuation reducer: prior settled ownership, valid checkpoint reference, unchanged identity/ownership/dependencies/capabilities, and request within cumulative authority yield `CONTINUATION_ELIGIBLE`; authority change, missing proof, or unsettled lifecycle yields reconciliation or `ESCALATE`.
- [x] Step 6: Prove valid task result with unsettled lifecycle, settled lifecycle with missing/malformed result, claimed verification contradicted by evidence, and publication failure without loss of lifecycle receipt or settlement evidence.

**Verification:**
- [x] `py -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_skill_chief_of_staff.py tests/test_skill_deepagents_executing_plans.py -q`
- Expected: lifecycle and task-result evidence remain independent; continuation is mechanical only inside unchanged durable authority.

**Exit Criteria:**
- Structured task result replaces normal pane completion transport; acceptance and continuation ownership remain with CoS.

### Task 7: Replace wave invalidation with bounded ready/deferred scheduling

**Purpose:**
- Preserve valid admissions, defer capacity/resource/dependency waits, and expose settled lane results in completion order while keeping concurrency capped at two.

**Task Function:**
- Repair dispatcher scheduling semantics without introducing a separate scheduler service.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: scheduler behavior shares admission, dependency, and result contracts.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: deterministic fake workers and bounded queue tests are sufficient.

**Specification Coverage:**
- Invalid lanes are blocked; capacity, conflicts, and pending dependencies are deferred; admitted work is not invalidated by later candidates; `MAX_CONCURRENCY = 2` remains fixed.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:_admit_lanes`, `_invalidate_wave`, `run_lane`, `run_parallel`
- Modify: same symbols and result-shape compatibility fields
- Modify: `tests/test_herdr_parallel_dispatch.py` capacity, conflict, dependency, refill, and completion-order cases

**Dependencies:**
- Tasks 1–6 complete; lane decisions and result evidence are stable.

**Authority:**
- Preauthorized local actions: change dispatcher classification and bounded refill behavior in listed files; keep concurrency at two.
- Stop for: increasing concurrency, persistent queue state, cross-repository scheduling, or changing CoS acceptance semantics.

**Steps:**
- [x] Step 1: Add red tests proving later conflicts do not clear earlier ready lanes and capacity overflow does not invalidate valid work.
- [x] Step 2: Replace `_invalidate_wave` behavior with explicit `READY`, `DEFERRED`, and `BLOCKED` classification; retain invalid-lane reasons.
- [x] Step 3: Classify full capacity and explicitly shareable-resource contention as `DEFERRED`; classify dependency awaiting CoS acceptance as return-to-CoS without auto-refill; classify overlapping writes, duplicate assignment, and uncertain ownership as `BLOCKED` or reconciliation.
- [x] Step 4: Run up to two ready lanes, consume each future as it settles, emit completion-order evidence through the existing result boundary, and refill only deferred lanes whose dependencies/resources are now ready.
- [x] Step 5: Keep unresolved process ownership occupied; only proven cleanup and settlement release capacity. If all lanes are deferred and no running attempt can unblock one, return a bounded deferred result instead of spinning or replaying.
- [x] Step 6: Preserve CLI and JSON compatibility or record an explicit schema update in the task evidence.

**Verification:**
- [x] `py -m pytest tests/test_herdr_parallel_dispatch.py -q`
- Expected: no valid lane is invalidated, capacity is bounded, deferred work refills safely, and unresolved lanes never authorize replacement.

**Exit Criteria:**
- Dispatcher behaves as a bounded ready queue with current two-lane capacity and no hidden retry or acceptance authority.

### Task 8: Add staged deployment hardening

**Purpose:**
- Prevent partial shared-runtime publication after correctness contracts and CI are green.

**Task Function:**
- Stage marker-owned output, validate it, and switch one immutable runtime version atomically.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deployment migration is separate from runtime correctness and requires serialized final validation.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: deployment tests and local dry-run proof cover scope.

**Specification Coverage:**
- Shared runtime is staged and validated before current projection changes; readers retain one version for each attempt.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/deploy_agent_runtime.py:main`, `_plan_deploy`, `tests/test_deploy_agent_runtime.py`
- Modify: `scripts/deploy_agent_runtime.py`, `tests/test_deploy_agent_runtime.py`
- Verify: `scripts/validate_agent_runtime_drift.py`, adapter and starter-kit validators

**Dependencies:**
- Tasks 1–7 complete and runtime CI is green.

**Authority:**
- Preauthorized local actions: add staged deployment logic, dry-run/rollback tests, and local validation.
- Stop for: user-global deployment, credential changes, force replacement of unowned files, or incompatible entry-point changes.

**Steps:**
- [x] Step 1: Add a failing deployment test showing destination-by-destination writes can expose partial state.
- [x] Step 2: Implement marker-owned immutable digest/version output and an atomic current-pointer activation; readers resolve one version before an attempt and retain that binding through completion.
- [x] Step 3: Preserve backups, unowned-file collision checks, dry-run behavior, active old readers, and rollback on failed validation.
- [x] Step 4: Add Windows reader-during-activation coverage proving each reader observes one complete runtime version, never a mixed projection.
- [x] Step 5: Run adapter synchronization before `--check`, then run local staged deployment validation without changing user-global runtime.

**Verification:**
- [x] `py -m pytest tests/test_deploy_agent_runtime.py tests/test_validate_agent_runtime_drift.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- Expected: staged deployment never exposes partial state, preserves unowned files, and supports rollback.

**Exit Criteria:**
- Deployment switches one complete immutable runtime version without changing ownership or acceptance authority.

## Verification

Final artifact verification runs serialized by lead controller:

- `py -m pytest -q`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- `py -B scripts/sync_agent_adapters.py --all-platforms`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `py -B scripts/validate_starter_kit.py`
- `py -B scripts/validate_generated_header_format.py`
- `py -B scripts/validate_repo_config.py --repo-root .`
- `py -m compileall scripts tests`
- `git diff --check`
- bounded Windows and Linux claim-race probes with unique temporary roots
- bounded read-only DeepAgents provider probe when configured; identify runtime
  revision exercised and record claim, completion, release, controller-call,
  and manual-reconciliation metrics

## Final Evidence

- `py -m pytest -q`: `746 passed, 1 skipped`.
- Runtime-focused suite: `422 passed`.
- Windows cross-process claim probe: one `ADMITTED`, one `BLOCKED`, one guard
  record; competing process now waits for claim transaction and returns JSON.
- Starter kit built and validated at
  `generated_exports/project-OS-starter-kit`.
- Repository contracts, planning lifecycle, adapter sync/check, runtime drift,
  generated headers, repo config, compile, and diff checks passed.
- Read-only provider probe attempted on September 17, 2026; local DeepAgents
  CLI exited without model execution because no supported provider credential
  was configured. External completion/release/controller metrics remain
  unavailable; no authentication or configuration change was made.

## Completion Criteria

The plan is ready for completion verification when:

1. concurrent claims cannot double-admit one assignment
2. settlement and replacement remain idempotent and evidence-bound
3. effective worker budgets are positive integers bounded by one attempt deadline,
   remaining authority, and settlement reserve
4. dispatcher collection is bounded and cannot treat observation timeout as
   settlement or replacement authority
5. production callers consume one shared attempt decision contract
6. lifecycle receipts and task results remain separate and independently bound
7. continuation stays within unchanged durable authority or escalates
8. ready/deferred/blocked scheduling preserves valid work and keeps capacity at
   two
9. canonical guidance, validators, generated adapters, and historical plan
   metadata agree with source behavior
10. runtime contract CI covers Linux and Windows
11. staged deployment tests prove no partial switch and preserve unowned files
12. fresh final verification returns `verified`

Plan completed after fresh verification returned `verified`.
