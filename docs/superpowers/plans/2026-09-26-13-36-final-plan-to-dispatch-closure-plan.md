---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: final-plan-to-dispatch-closure
targets:
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/herdr_parallel_dispatch.py
  - tests/test_plan_preparation.py
  - tests/test_herdr_parallel_dispatch.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-09-26-13-36-final-plan-to-dispatch-closure-plan.md
---

# Final Plan-to-Dispatch Closure

## Verdict Review

The supplied verdict is supported by merged `origin/main` at `bc60466`.
Architecture is converged; four closure gaps remain:

- `prepare_task()` derives dependency readiness but does not gate selected-task
  execution by recorded task state.
- `main()` treats only `unresolved=True` as runtime failure, so safely retired
  launch failures can return exit code `0`.
- `_bounded_task_text()` removes task-local `Verification` and `Exit Criteria`
  content before the launcher receives `--task`.
- The prior optimization claim has no durable, inspectable before/after counts.

Plan direction is correct: make one small closure patch, preserve the existing
preparation/admission/launcher/lifecycle/acceptance boundaries, and defer
intra-invocation deduplication until closure evidence exists. No scheduler,
persistent DAG, memory layer, retry authority, lifecycle enum, acceptance layer,
runtime, or CI workflow belongs in this plan.

## Goal

Close behavioral and evidence gaps in the existing plan-to-dispatch path so
selected task eligibility, CLI failure status, worker handoff completeness, and
the optimization outcome are correct and inspectable without changing
orchestration ownership.

## Implementation Outcomes

### Selected-task eligibility

`prepare_task()` distinguishes selected-task execution eligibility from
dependency readiness. `pending` and `active` remain ordinary execution-eligible
states. `blocked` and `completed` fail before lane construction with an explicit
reason. Controller-owned reopening or continuation remains unchanged.

### Accurate command status

CLI status reports nonzero when any result has unresolved ownership or a
non-null failure kind. Safely retired failures keep `unresolved=False` and
retired capacity. Admission and deferred-capacity behavior remain unchanged.

### Complete deterministic worker contract

The launcher receives the complete selected task section through `Verification`
and `Exit Criteria`, bounded only by the next task heading or peer `##` section.
The payload includes plan goal, accepted prerequisite identities, required proof
when it adds information, and deterministic explicit shared requirements once.
It excludes later tasks, unrelated sections, histories, and duplicate task
Purpose/Authority text.

### Inspectable outcome evidence

One fake-launcher comparison records actual manual-descriptor versus plan-input
fields, preparation operations, plan/evidence reads, dispatch commands, model
calls, launcher subprocesses, context requests, recovery paths, semantic
equivalence, and preparation-through-launch-check timing. The completed plan
records those observed values and final verification evidence; it does not
invent targets or numbers.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `clean managed worktree rooted at origin/main`
- Commit policy: `no commits during execution; commit only after verification returns verified and user authorizes Git disposition`
- Preauthorized local actions: `inspect and edit listed source/tests/docs/plan files, create the named clean worktree, run listed local checks, and record measured evidence in this plan`
- User-approval actions: `commit, push, pull request, merge, external authentication, destructive cleanup, discard, and edits outside listed targets`
- Parallel ownership: `none; tasks share preparation, dispatch, tests, and plan evidence`
- Sequential fallback: `Task 1, then Task 2 and Task 3 in order, then Task 4 and final verification`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/final-plan-to-dispatch-closure`
- Base commit: `bc60466d558193579053153265ba1183f77c2ce8`
- Expected workspace: `clean managed worktree from origin/main; preserve current checkout untracked artifacts and do not delete or rewrite them`
- Next action: `finish Git disposition: commit, push, PR review, and merge`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated worktree | `codex` | none | eligibility and dependency-readiness regressions pass | `python -m pytest -q tests/test_plan_preparation.py` — 17 passed |
| Task 2 | `completed` | same worktree | `codex` | Task 1 | CLI returns nonzero for known failed dispatch and preserves lifecycle facts | `python -m pytest -q tests/test_herdr_parallel_dispatch.py` — 70 passed |
| Task 3 | `completed` | same worktree | `codex` | Task 1 | final launcher `--task` contains complete bounded contract without duplication | `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py` — 88 passed |
| Task 4 | `completed` | same worktree | `codex` | Tasks 1–3 | measured comparison, documentation reconciliation, and final checks pass | all checks pass after approved runtime sync |

Only the lead controller updates this ledger. A checked item records accepted
proof, not activity.

## Scope Boundaries

Preserve one preparation owner, existing admission states, existing dispatcher,
existing launcher, existing lifecycle/settlement/recovery contracts, controller
acceptance, descriptor-file compatibility, direct execution, and current
concurrency limits.

Do not implement the later optimization order in this plan: readiness/brief
deduplication, duplicate plan-load removal, runtime-fact reuse, Git subprocess
consolidation, runtime-binding reduction, ready-task projections, task-relevant
freshness, experience handoff, topology-aware execution, persistent scheduling,
learned routing, or general memory. Record those as follow-up work only after
the closure evidence is accepted.

## Task Breakdown

### Task 1: Restore selected-task execution eligibility

**Purpose:**
- Prevent `blocked` and `completed` selected tasks from reaching ordinary dispatch while keeping dependency readiness independently observable.

**Task Function:**
- Correct the canonical plan-preparation projection and add focused state regressions without changing admission ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small shared-runtime behavior change with direct lifecycle and dispatch impact.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused regression tests and final backend verification cover this bounded change.

**Specification Coverage:**
- Selected-task eligibility is separate from predecessor completion.
- `pending` and `active` follow existing ordinary execution policy.
- `blocked` and `completed` do not auto-dispatch.
- Reopening and continuation remain controller-owned.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:PreparedTask`, `prepare_task`, `_prepare_plan_lanes`
- Inspect: `scripts/project_os_runtime/admission.py:classify_admission`
- Modify: `scripts/project_os_runtime/plan_preparation.py:PreparedTask`, `prepare_task`, `_prepare_plan_lanes`
- Modify: `tests/test_plan_preparation.py` state and readiness regressions
- Verify: `scripts/project_os_runtime/lane.py:prepare_lane` remains compatible with descriptor-file input

**Dependencies:**
- `origin/main` at `bc60466d558193579053153265ba1183f77c2ce8`
- Existing task-state meanings in `parse_plan()` and `validate_planning_lifecycle.py`

**Authority:**
- Preauthorized local actions: inspect and edit `plan_preparation.py` and `test_plan_preparation.py`, run focused tests, and preserve descriptor-file behavior
- Stop for: any need to add a lifecycle state, reopen a task in preparation, change admission ownership, or modify files outside listed targets

**Steps:**
- [x] Step 1: Add one explicit execution-eligibility projection using existing states `pending` and `active`; do not add a lifecycle enum or new persisted state.
- [x] Step 2: Keep `structurally_ready` derived only from declared predecessor completion, calculate combined `dependency_ready` from eligibility plus structural readiness, and fail selected ineligible tasks before lane construction with `selected task is not execution-eligible: blocked` or `selected task is not execution-eligible: completed`.
- [x] Step 3: Add tests proving `pending` and `active` remain eligible, `blocked` and `completed` fail before launch, and a pending predecessor still leaves structural/dependency readiness false for an otherwise eligible task.

**Verification:**
- [x] `python -m pytest -q tests/test_plan_preparation.py` — 17 passed
- Expected: new eligibility regressions pass; existing dependency, identity, binding, and digest tests pass; no launcher is invoked for an ineligible selected task.

**Exit Criteria:**
- Canonical plan preparation cannot admit ordinary execution for `blocked` or `completed` selected tasks, and structural dependency readiness remains a separate fact.

### Task 2: Make CLI status reflect failed dispatch

**Purpose:**
- Return nonzero when requested execution fails even when ownership is safely settled.

**Task Function:**
- Extend the existing CLI result interpretation without changing result schema or lifecycle facts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one dispatcher boundary with low ambiguity and direct automation impact.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused CLI and stale-binding regressions provide direct proof.

**Specification Coverage:**
- `failure_kind` communicates failed execution independently from `unresolved` ownership uncertainty.
- `unresolved=False` and `capacity=retired` remain valid for pre-launch failures.
- Successful execution returns `0`; failed dispatch, command exit, preparation failure, and unresolved transport return nonzero.
- `DEFERRED` behavior stays unchanged.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:main`, `run_lane`, `run_parallel`
- Modify: `scripts/herdr_parallel_dispatch.py:main`
- Modify: `tests/test_herdr_parallel_dispatch.py` CLI-result and stale-binding regressions

**Dependencies:**
- Task 1 complete
- Existing failure result fields from `run_lane()` and existing admission result handling

**Authority:**
- Preauthorized local actions: edit dispatcher result interpretation and focused tests, run the dispatcher test module, and preserve existing result fields
- Stop for: any proposal to rewrite `unresolved`, capacity settlement, admission states, or launcher result schemas

**Steps:**
- [x] Step 1: Change the CLI runtime-failure predicate to treat `unresolved is True` or `failure_kind is not None` as failure; retain existing admission-failure handling.
- [x] Step 2: Add a direct `main()` regression with a safely retired `launch_binding_stale` result and assert nonzero status while asserting `unresolved=False` and `capacity=retired` remain unchanged at the result-producing seam.
- [x] Step 3: Retain success, command-exit, transport-timeout, admission-blocked, and deferred-capacity expectations through focused tests.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_parallel_dispatch.py` — 70 passed
- Expected: stale launch failure returns nonzero; successful execution returns `0`; unresolved ownership remains nonzero; deferred capacity keeps current behavior.

**Exit Criteria:**
- Command callers can trust exit status as execution outcome while lifecycle consumers can still trust independent ownership and capacity fields.

### Task 3: Preserve the complete worker handoff contract

**Purpose:**
- Deliver complete task-local instructions and deterministic plan context to the actual launcher without duplicate or unrelated text.

**Task Function:**
- Correct structural task-section extraction and final worker-brief composition at the existing plan-preparation owner.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic text-boundary change with an existing launcher capture seam.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final `--task` assertions prove the externally delivered contract.

**Specification Coverage:**
- Verification and Exit Criteria survive.
- Plan objective, accepted prerequisite identities, required proof, and deterministic shared requirements reach the worker.
- Later tasks, unrelated peer sections, histories, arbitrary summaries, and duplicate Purpose/Authority text stay excluded.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:_bounded_task_text`, `_contract_section`, `_worker_brief`, `prepare_plan_lanes`
- Inspect: `scripts/herdr_parallel_dispatch.py:_launcher_command`, `run_lane`
- Modify: `scripts/project_os_runtime/plan_preparation.py:_bounded_task_text`, `_worker_brief`
- Modify: `tests/test_plan_preparation.py` and `tests/test_herdr_parallel_dispatch.py` final launcher-payload coverage

**Dependencies:**
- Task 1 complete
- Existing canonical `PlanGraph.goal`, `PlanGraph.required_skills`, accepted prerequisite bindings, and `run_lane(..., popen_factory=...)` seam

**Authority:**
- Preauthorized local actions: edit worker-brief composition and focused payload tests, run fake-launcher checks, and preserve existing plan/runtime field ownership
- Stop for: semantic plan-prose search, arbitrary history retrieval, live model benchmarking, or a new context/memory service

**Steps:**
- [x] Step 1: Change `_bounded_task_text()` to stop only at the next `### Task N` heading, next peer `##` section, or end of document; retain internal Verification and Exit Criteria subsections.
- [x] Step 2: Compose one deterministic worker payload with plan goal, complete selected task contract, accepted prerequisite identities, required proof only when not already represented, and explicit plan-wide requirements only when canonical and nonempty. Do not append task Purpose, Authority, Verification, or Exit Criteria a second time.
- [x] Step 3: Capture the final `--task` argument through the existing fake `Popen` seam and assert included/excluded content, including Task N+1 and unrelated following `##` sections.

**Verification:**
- [x] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py` — 88 passed
- Expected: final launcher task text contains plan goal, complete selected task contract, Verification, Exit Criteria, prerequisite identities, and applicable proof/constraints exactly once; unrelated sections are absent.

**Exit Criteria:**
- Worker receives complete, bounded, deterministic selected-task instructions through the existing launcher command without avoidable duplication.

### Task 4: Record outcome evidence and reconcile the closure

**Purpose:**
- Prove the optimization outcome with one reproducible fixture, update the runtime contract documentation, and reconcile this plan with measured evidence.

**Task Function:**
- Run equivalent manual-descriptor and canonical-plan dispatches through one fake launcher, record actual counters and timing, then complete documentation and plan evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: evidence task crosses implementation surfaces and owns the final plan/documentation reconciliation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification commands and CI provide independent contract proof.

**Specification Coverage:**
- Manual descriptor and plan input preserve equivalent semantic execution inputs.
- Plan input reduces manually assembled plan-owned preparation work.
- No extra controller round trip, model call, launcher subprocess, missing-context request, or recovery/reconciliation path appears in the fixed fixture.
- Timing is descriptive, not a sub-millisecond acceptance gate.
- Runtime documentation states the final eligibility and command-status boundaries.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel_from_plan`, `run_parallel`, `run_lane`
- Inspect: `tests/test_plan_preparation.py` existing plan/binding fixtures and `tests/test_herdr_parallel_dispatch.py` fake launcher seams
- Modify: `tests/test_plan_preparation.py` one reproducible manual-versus-plan evidence test or fixture
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:DeepAgents Boundary Contract`
- Modify: `docs/superpowers/plans/2026-09-26-13-36-final-plan-to-dispatch-closure-plan.md` evidence, ledger, and final reconciliation only after proof

**Dependencies:**
- Tasks 1–3 complete
- `origin/main` remains the base for the implementation worktree
- Existing fake launcher seam is sufficient; no live model call or new instrumentation service is permitted

**Authority:**
- Preauthorized local actions: add one bounded evidence fixture, update the listed runtime contract paragraph, run all listed checks, and record actual outputs in this plan
- Stop for: missing semantic equivalence, invented measurements, live-model dependency, new CI workflow, unrelated cleanup, or any architecture change

**Steps:**
- [x] Step 1: Build one logical task fixture with equivalent manual lane fields and plan-plus-runtime-binding inputs. Run both through the same fake launcher and capture final semantic inputs.
- [x] Step 2: Record actual caller-supplied fields, plan-owned fields manually transcribed, preparation operations, plan reads, evidence/reference reads, dispatch commands, model calls, launcher subprocesses, missing-context requests, recovery/reconciliation paths, and preparation-through-launch-check timing.
- [x] Step 3: Assert semantic equivalence for task contract, runtime grant, remaining authority, deadline, capabilities, write scope, fixed contracts, mutable resources, accepted prerequisites, required proof, and worker-facing instructions. Assert stale-binding fixture invokes no worker and returns nonzero CLI status.
- [x] Step 4: Update `runtime-surfaces.md` to state selected-task eligibility and execution-outcome status without duplicating lifecycle ownership. Record actual comparison values, deltas, fixture commands, and deviations in this plan.

### Task 4 Evidence

Fixture command: `python -m pytest -q tests/test_plan_preparation.py::test_manual_and_plan_inputs_record_equivalent_dispatch_evidence`.

Observed comparison on 2026-09-26:

| Measure | Manual descriptor | Canonical plan input |
| --- | ---: | ---: |
| Caller plan selectors | 0 | 2 |
| Caller runtime-binding field groups | 13 | 13 |
| Caller plan-derived execution fields | 8 | 0 |
| Raw caller input fields | 24 | 15 |
| Plan/source preparation operations | 0 | `source_parts=1`, `parse_plan=1`, `prepare_task=1` |
| Dispatch commands | 1 | 1 |
| Launcher subprocesses | 1 | 1 |
| Fake fixture model calls | 0 | 0 |
| Fake fixture missing-context events | 0 | 0 |
| Fake fixture recovery paths | 0 | 0 |
| Preparation-through-launch-check time | 3.364 ms | 103.628 ms |

Task contract, runtime grant, remaining authority, deadline, capabilities, write
scope, fixed contracts, mutable resources, accepted prerequisites, required
proof, and worker-facing instructions were semantically equivalent. Canonical
plan input removed 8 explicitly identified plan-derived caller fields from this
fixture. Raw input-field totals are not a savings claim because manual grant
fields are flattened while plan runtime bindings are nested. Fake zeroes are
fixture invariants: the comparison introduced no additional modeled launcher,
model, context, or recovery step. Timing is descriptive, not an apples-to-
apples latency comparison; plan parsing and freshness validation made this
fixture slower than direct descriptor input. The stale-binding regression
invokes no worker and returns nonzero while preserving `unresolved=False` and
`capacity=retired`.

**Verification:**
- [x] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_validate_planning_lifecycle.py` — 132 passed
- [x] `python scripts/validate_planning_lifecycle.py --repo-root . --strict` — passed
- [x] `python scripts/validate_repo_contracts.py --repo-root .` — passed
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check` — passed
- [x] `python scripts/validate_agent_runtime_drift.py --all-platforms` — passed after approved runtime sync
- [x] `python scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check` — passed
- [x] `git diff --check` — passed
- Expected: evidence is reproducible, semantic inputs remain equivalent, measured plan-owned preparation work decreases, fixed no-extra-work invariants hold, and all validators pass without generated-surface drift.

Verification deviation resolved: approved runtime synchronization updated stale
user-global bundles, including deployed `plan_preparation.py`; the full drift
check now passes.

**Exit Criteria:**
- Actual evidence is written into this plan, runtime documentation matches source behavior, and no required closure claim depends on an unchecked assertion or an invented number.

## Verification

Use existing local and CI checks. Do not add a workflow.

- `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_validate_planning_lifecycle.py`
- `python -m pytest -q`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`
- Existing `repo-contracts.yml` and `runtime-contracts.yml` checks on Ubuntu and Windows

## Completion Criteria

The plan is ready for completion verification when:

1. Task eligibility, CLI status, worker payload, and evidence outcomes all pass their task-local proof.
2. `blocked` and `completed` selected tasks cannot enter ordinary dispatch; controller reopening remains external to preparation.
3. Known dispatch failures return nonzero without rewriting `unresolved` or capacity facts.
4. Final launcher `--task` preserves the complete selected task contract and excludes unrelated plan content.
5. Manual-versus-plan evidence records actual values and proves semantic equivalence plus reduced plan-owned preparation work.
6. Runtime documentation, tests, validators, and this plan agree with `origin/main` plus the closure patch.
7. No P1 optimization, new orchestration layer, new runtime, or new CI workflow entered scope.
8. `skill-verification-before-completion` returns `verified`; verified on 2026-09-26 before changing frontmatter to `status: completed`.
