---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
parent_spec: none
name: plan-to-dispatch-contract-convergence
targets:
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/lane.py
  - scripts/project_os_runtime/attempt.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/planning_dependencies.py
  - scripts/validate_planning_lifecycle.py
  - tests/test_plan_preparation.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_validate_planning_lifecycle.py
  - docs/superpowers/plans/2026-09-26-02-26-streamline-plan-to-dispatch-coordination-plan.md
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Plan-to-Dispatch Contract Convergence

## Verdict Review

The supplied verdict is directionally correct. PR #41 completed operational
integration but left contract convergence open: CLI plan mode calls
`prepare_plan_lanes`, while `run_parallel_from_plan` still calls the weaker
`prepare_lane_inputs` path. Runtime authority is also partly recreated inside
plan preparation, accepted Git revisions are not yet proven contained by the
consumer checkout, and launch freshness is checked before the final launcher
boundary.

Accepted requirements:

- one authoritative execution-eligible preparation contract for CLI and Python
  plan entry points;
- descriptor-file compatibility remains separate and unchanged;
- plan preparation derives plan-owned facts only;
- runtime bindings preserve resolved authority, grants, capabilities, resources,
  deadlines, and write scope;
- Git-backed prerequisites use revisions contained in the consumer checkout;
- one freshness verifier runs at the actual launcher boundary;
- worker payload contains deterministic task, objective, prerequisite, proof, and
  explicit constraint context;
- lifecycle validation passes original task rows to shared dependency validation;
- completed-plan history and final evidence reconcile with Git;
- operational invariants prove reduced controller preparation work without using
  sub-millisecond timing as a hard gate.

Adjustments:

- retain `prepare_lane_inputs` only as an explicit compatibility adapter that
  delegates to the authoritative contract; do not preserve weaker readiness or
  identity semantics under that name;
- keep `artifact_ref` only for demonstrated non-Git artifacts; Git-backed
  dependencies use `accepted_revision` as canonical identity;
- execute from a clean worktree based on `origin/main` at merged PR #41
  (`e5e6630`), not from the current checkout, which is behind and contains
  unrelated untracked files;
- require operation counts and fixed workflow invariants as gates; report timing
  deltas descriptively.

Rejected scope:

- no scheduler, persistent DAG, memory store, semantic evidence engine, learned
  router, retry controller, new runtime, acceptance authority, or mandatory
  workflow;
- no broad runtime-binding reduction in this plan; record it as the next
  optimization after convergence.

## Goal

Make plan input have one authoritative interpretation, preserve all resolved
execution semantics, reach workers with sufficient deterministic context, and
remove controller preparation work without weakening admission, lifecycle,
settlement, recovery, or acceptance boundaries.

## Current Baseline

- PR #40 merged at `2902ee6` and introduced the first plan-preparation path.
- PR #41 merged at `e5e6630` and added stricter CLI preparation, binding digest,
  accepted prerequisites, launch verification, and CI coverage.
- Current `origin/main` is the source of truth for execution.
- Existing descriptor input `--lanes-file` remains a supported compatibility path.

## Implementation Outcomes

### Single preparation owner

`prepare_plan_lanes` becomes the only execution-eligible plan projection. CLI
plan mode and `run_parallel_from_plan` call it with the same source, selected
task IDs, and resolved runtime-binding shape. `prepare_lane_inputs` remains only
as a compatibility adapter with no independent readiness, identity, dependency,
or runtime-default logic.

### Runtime authority preservation

Plan preparation derives task identity, bounded task text, dependencies, required
proof, executor/profile decisions, explicit plan constraints, and structural
readiness. Runtime bindings provide repository/worktree/base, session/pane,
runtime grant, remaining allowance, deadline, capabilities, fixed contracts,
mutable resources, effective write scope, accepted prerequisites, and optional
launcher-owned fields. Missing runtime authority fails closed; preparation does
not restore defaults or invent `mutable_resources`, `fixed_contracts`,
`local_capabilities`, deadlines, allowances, or write scope.

### Dependency freshness

Git-backed prerequisite readiness requires recorded completion, an accepted
revision, and `git merge-base --is-ancestor <accepted_revision> HEAD` inside the
consumer worktree. A separate artifact reference exists only for a non-Git
artifact contract. The same verifier checks plan binding, prerequisite revisions,
artifact availability, worktree/base/HEAD, ownership, settlement, grants, and
capabilities immediately before launcher invocation.

### Complete worker handoff

Worker task text contains only deterministic canonical inputs: selected task
section, applicable objective, accepted prerequisite identities, required proof,
and explicit execution constraints. It excludes histories, arbitrary summaries,
and unrelated plan sections. Tests inspect the final `--task` launcher argument.

### Durable evidence and measurement

The earlier completed plan records the PR #40 baseline and PR #41 reconciliation
without rewriting history. A fixed before/after comparison proves fewer manually
assembled preparation fields and no added controller round trip, model call,
launcher subprocess, missing-context request, or recovery/reconciliation path.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Base: clean implementation worktree from `origin/main` at `e5e6630`
- Required skills: `skill-executing-plans`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`,
  `skill-performance-optimization`, `skill-verification-before-completion`,
  `skill-finishing-a-development-branch`
- Commit policy: no commits during execution; lead creates commit only after
  verification accepts all task proof
- Shared-write rule: all tasks touch the preparation/dispatch contract or its
  evidence, so execute sequentially; no parallel writer lane
- Preauthorized local actions: inspect and edit listed source/tests/docs,
  create the clean worktree, run listed local checks, and record evidence in the
  plan; preserve unrelated checkout files
- User-approval actions: commit, push, PR, merge, destructive cleanup, external
  authentication, and edits outside listed targets
- Stop for: source/API conflict, missing runtime owner, stale base, failed
  required proof, unexpected dirty worktree, or any need for new orchestration

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/plan-to-dispatch-contract-convergence`
- Base commit: `e5e6630d20b4c69eee50707733526c97b5e57439`
- Expected workspace: clean managed worktree based on `origin/main`
- Next action: execute Task 1 after approval
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | isolated worktree | `codex` | none | unified contract tests and owner map | pending |
| Task 2 | `pending` | same worktree | `codex` | Task 1 | runtime authority preserved; no synthesized fields | pending |
| Task 3 | `pending` | same worktree | `codex` | Task 2 | Git-bound prerequisite and launch-bound freshness tests | pending |
| Task 4 | `pending` | same worktree | `codex` | Task 2 | final worker payload and launcher-argument proof | pending |
| Task 5 | `pending` | same worktree | `codex` | Task 1 | duplicate-row and shared-validator proof | pending |
| Task 6 | `pending` | same worktree | `codex` | Tasks 3–5 | reconciled evidence and operational comparison | pending |

Only the lead controller updates this ledger. A checked item records accepted
proof, not activity.

## Task Breakdown

### Task 1: Converge execution-eligible preparation entry points

**Purpose:**
- Make CLI plan mode and `run_parallel_from_plan` use one preparation owner while preserving descriptor-file mode.

**Task Function:**
- Refactor shared plan preparation and migrate its direct callers without changing admission or launcher ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared API ownership and compatibility decisions require controller review.

**Specification Coverage:**
- Single preparation owner; descriptor-file compatibility; no weaker plan interpretation.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel_from_plan`, `main`, `run_parallel`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:prepare_lane_inputs`, `prepare_plan_lanes`
- Modify: `scripts/herdr_parallel_dispatch.py:run_parallel_from_plan`
- Modify: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`, `prepare_lane_inputs`
- Modify: `tests/test_herdr_parallel_dispatch.py:test_run_parallel_from_plan_reuses_existing_admission`
- Modify: `tests/test_plan_preparation.py`

**Dependencies:**
- Clean worktree based on `origin/main` at `e5e6630`.
- Existing plan and descriptor callers are inventoried before edits.

**Authority:**
- Preauthorized local actions: change listed preparation callers and focused tests.
- Stop for: an external caller requires a different runtime contract, descriptor mode changes, or a second preparation owner.

**Steps:**
- [ ] Step 1: Record current CLI/API outputs and all in-repository callers of both preparation functions.
- [ ] Step 2: Define one exact execution-binding input shape and make `prepare_plan_lanes` accept the canonical plan source plus selected task IDs plus resolved runtime bindings.
- [ ] Step 3: Make `run_parallel_from_plan` delegate to `prepare_plan_lanes`; retain `prepare_lane_inputs` only as a named compatibility adapter that delegates to the same owner and rejects weaker plan-derived/runtime overrides.
- [ ] Step 4: Keep `--lanes-file` parsing and descriptor admission unchanged; assert both modes converge at `PreparedLane`.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py`
- Expected: CLI and Python plan paths produce equivalent plan-owned fields and reuse existing admission; descriptor mode tests remain green.

**Exit Criteria:**
- No execution-eligible caller uses independent preparation semantics.
- Compatibility adapter has no readiness or runtime-default logic of its own.

### Task 2: Preserve resolved runtime authority and resource bindings

**Purpose:**
- Stop plan preparation from inventing runtime authority, grants, capabilities, deadlines, contracts, resources, or effective write scope.

**Task Function:**
- Align runtime-binding validation with existing `PreparedLane` and attempt contracts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: backend contract preservation and trust-boundary validation require direct source review.

**Specification Coverage:**
- Runtime authority ownership; no default restoration; conflict/resource correctness.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/lane.py:PreparedLane`, `prepare_lane`
- Inspect: `scripts/project_os_runtime/attempt.py:normalize_runtime_grant`, `resolve_attempt_budget`
- Modify: `scripts/project_os_runtime/plan_preparation.py:_BINDING_FIELDS`, `_runtime_grant`, `prepare_plan_lanes`
- Modify: `scripts/project_os_runtime/lane.py:PreparedLane` only for provenance fields required by launch freshness
- Modify: `tests/test_plan_preparation.py`
- Modify: `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 1 defines the single binding contract.
- Existing runtime owner remains authoritative for grant, capability, resource, deadline, and write-scope values.

**Authority:**
- Preauthorized local actions: pass through and validate existing resolved fields; update focused tests.
- Stop for: no owning resolver exists for a required runtime field, or a safe default would need to be invented.

**Steps:**
- [ ] Step 1: Enumerate every field required by `PreparedLane`, launcher command construction, admission, and settlement; classify each as plan-owned or runtime-owned.
- [ ] Step 2: Expand runtime bindings to carry resolved `remaining_authorized_task_allowance`, `attempt_deadline`, `local_capabilities`, `fixed_contracts`, `mutable_resources`, `allowed_write_set`, and accepted prerequisite data where the existing owner supplies them.
- [ ] Step 3: Remove preparation defaults for `1800`-second allowance, current-time deadline, default capabilities, synthetic contracts, task-ID resources, and heuristic/fallback write scope.
- [ ] Step 4: Reject plan-owned runtime overrides and missing runtime authority before admission; preserve optional launcher fields without changing their existing defaults.
- [ ] Step 5: Add tests for shared mutable resources, exhausted allowance, finite deadline, explicit capabilities, and unresolved write scope.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py`
- Expected: resolved values reach `PreparedLane` unchanged; missing or conflicting authority fails closed; descriptor mode behavior remains unchanged.

**Exit Criteria:**
- Plan preparation derives no runtime-owned authority.
- Every execution-eligible lane carries the resolved runtime contract or is rejected before launch.

### Task 3: Bind prerequisite artifacts and freshness to launch

**Purpose:**
- Make accepted Git revisions meaningful and close the admission-to-launch freshness gap.

**Task Function:**
- Harden one existing verifier and invoke it immediately before launcher command execution.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: trust-boundary and failure-path verification require direct backend ownership.

**Specification Coverage:**
- Consumer-contained revisions; mutable plan binding; launch-bound verification; settlement and ownership preservation.

**Required Skills:**
- `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:verify_launch_bindings`, `_prepare_admission`, `run_lane`, `_launcher_command`
- Inspect: `scripts/project_os_runtime/lane.py:PreparedLane`
- Modify: `scripts/herdr_parallel_dispatch.py:verify_launch_bindings`, `run_lane`, `_prepare_admission`
- Modify: `scripts/project_os_runtime/lane.py:PreparedLane` provenance mapping
- Modify: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`
- Modify: `tests/test_plan_preparation.py`, `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 2 provides complete runtime bindings and provenance.
- Git-backed prerequisite identity is `accepted_revision`; separate artifact references require a distinct non-Git contract.

**Authority:**
- Preauthorized local actions: change one verifier and its direct call sites; add failure-path tests.
- Stop for: artifact ownership cannot be proven, verifier would require a second subsystem, or stale state could launch a worker.

**Steps:**
- [ ] Step 1: Store canonical plan source, plan revision, selected task identity, and execution-binding digest in the prepared lane provenance.
- [ ] Step 2: Replace Git object existence checks with `git merge-base --is-ancestor <accepted_revision> HEAD` in the consumer worktree; retain explicit non-Git artifact validation only where tested.
- [ ] Step 3: Re-read only the selected task’s current plan binding immediately before `_launcher_command`; compare task eligibility, relevant plan revision, dependencies, executor/profile, required proof, and digest.
- [ ] Step 4: Move the authoritative `verify_launch_bindings` call to the final `run_lane` launch boundary; keep admission checks cheap and non-launching.
- [ ] Step 5: Return structured settled failure evidence when freshness fails; do not start subprocess, alter acceptance, or add retry/recovery behavior.
- [ ] Step 6: Test stale plan edits after admission, unreachable accepted revisions, missing artifacts, invalid base/worktree, grant mismatch, and successful contained revisions.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: stale bindings fail before `subprocess.Popen`; contained revisions pass; descriptor lanes without plan provenance preserve existing behavior.

**Exit Criteria:**
- One verifier owns freshness semantics.
- No worker starts after a relevant plan, dependency, artifact, ownership, grant, or capability binding becomes stale.

### Task 4: Complete deterministic worker handoff

**Purpose:**
- Give workers enough accepted context to execute without controller rereads while excluding unrelated history and prose.

**Task Function:**
- Build and verify final worker-facing task text from canonical plan and accepted runtime facts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic payload design crosses plan and launcher boundaries but needs no new subsystem.

**Specification Coverage:**
- Bounded worker brief; required proof; accepted prerequisite identities; explicit constraints; no unrelated sections.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:_bounded_task_text`, `prepare_plan_lanes`
- Inspect: `scripts/herdr_parallel_dispatch.py:_launcher_command`, `run_lane`
- Modify: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`
- Modify: `scripts/herdr_parallel_dispatch.py:_launcher_command` only if required to preserve final payload
- Modify: `tests/test_plan_preparation.py`, `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Tasks 1–3 define the authoritative task and prerequisite contract.

**Authority:**
- Preauthorized local actions: modify deterministic payload construction and tests.
- Stop for: worker context would require history search, semantic evidence ranking, or inferred constraints.

**Steps:**
- [ ] Step 1: Build payload sections in fixed order: selected task section, applicable objective, accepted prerequisites, required proof, and explicit execution constraints.
- [ ] Step 2: Include accepted revision identities and non-Git artifact references only when supplied by the runtime binding owner.
- [ ] Step 3: Exclude trailing verification sections, upstream conversations, worker histories, and unrelated plan-wide prose.
- [ ] Step 4: Assert the final `--task` argument passed by `_launcher_command` contains required sections and excludes forbidden content.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py`
- Expected: worker-facing payload is deterministic, bounded, and sufficient for proof-aware execution without an added context request.

**Exit Criteria:**
- Final launcher input carries all required deterministic context exactly once.

### Task 5: Finish shared dependency validation and durable evidence

**Purpose:**
- Remove duplicate graph validation and reconcile the completed predecessor plan with actual Git and verification evidence.

**Task Function:**
- Consolidate validation ownership and update durable operational records without rewriting history.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: validator and plan-document ownership require source-first reconciliation.

**Specification Coverage:**
- Duplicate-row detection; one graph owner; historical reconciliation; truthful completion evidence.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/planning_dependencies.py:validate_dependency_graph`
- Inspect: `scripts/validate_planning_lifecycle.py:validate_git_coordination`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:parse_plan`
- Modify: `scripts/validate_planning_lifecycle.py:validate_git_coordination`
- Modify: `scripts/project_os_runtime/plan_preparation.py:parse_plan`
- Modify: `docs/superpowers/plans/2026-09-26-02-26-streamline-plan-to-dispatch-coordination-plan.md`
- Modify: `tests/test_validate_planning_lifecycle.py`, `tests/test_plan_preparation.py`

**Dependencies:**
- Task 1 establishes the shared preparation contract.
- Tasks 2–4 preserve the fields and evidence referenced by the completed plan.

**Authority:**
- Preauthorized local actions: remove redundant local traversal after shared equivalence tests; update historical evidence text.
- Stop for: historical evidence cannot be reconciled from Git, or validator compatibility requires undocumented policy.

**Steps:**
- [ ] Step 1: Pass the original row sequence to `validate_dependency_graph` so duplicate task IDs remain visible; do not build a dictionary before validation.
- [ ] Step 2: Remove redundant local dependency traversal/checks from `parse_plan` after shared-validator tests cover missing references, self-dependencies, cycles, duplicate IDs, and supported historical syntax.
- [ ] Step 3: Reconcile the completed plan narrative with `612ebd6`, `2902ee6`, and `e5e6630`; distinguish task-focused and full-suite evidence when counts differ.
- [ ] Step 4: Preserve completed status only when final verification evidence is current; record deviations and deferrals in the plan.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_validate_planning_lifecycle.py tests/test_plan_preparation.py`
- [ ] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- Expected: duplicate rows fail validation, historical valid plans remain accepted, and durable evidence matches Git history.

**Exit Criteria:**
- Shared dependency module is sole graph-validation owner.
- Completed plan contains no contradictory history or suite claims.

### Task 6: Prove operational improvement and close

**Purpose:**
- Produce reproducible before/after evidence through existing dispatcher paths and complete final verification.

**Task Function:**
- Measure fixed equivalent workflows, reconcile plan state, and prepare verified branch handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence and acceptance require controller authority.

**Specification Coverage:**
- Reduced preparation work; preserved operational invariants; final completion proof.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel`, `run_parallel_from_plan`
- Modify: `tests/test_herdr_parallel_dispatch.py` or `tests/test_plan_preparation.py` only for one reproducible comparison
- Modify: `docs/superpowers/plans/2026-09-26-12-34-plan-to-dispatch-contract-convergence-plan.md`
- Verify: `.github/workflows/runtime-contracts.yml`

**Dependencies:**
- Tasks 1–5 complete and accepted.
- Clean worktree and exact `origin/main` base are recorded.

**Authority:**
- Preauthorized local actions: run deterministic tests/probes, record evidence, and update this plan’s ledger.
- Stop for: unavailable telemetry, added operational path, failed semantic equivalence, or any required Git publication action.

**Steps:**
- [ ] Step 1: Run equivalent manual descriptor and plan-input dispatch fixtures with a safe fake launcher/worker target; count controller preparation reads, manually supplied fields, model calls, launch subprocesses, missing-context requests, and recovery/reconciliation paths.
- [ ] Step 2: Require plan input to use fewer manually assembled fields and no additional operational invariant; report timing, token, intervention, and rework deltas descriptively.
- [ ] Step 3: Run focused tests, full suite, planning lifecycle validation, repo-contract validation, adapter sync/drift checks, and `git diff --check`.
- [ ] Step 4: Reconcile all task evidence and completion criteria; invoke `skill-verification-before-completion` before marking this plan completed.

**Verification:**
- [ ] `py -3 -m pytest -q`
- [ ] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- [ ] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `git diff --check`
- Expected: all checks pass; plan/API semantic equivalence holds; operational invariants show no added controller or launch work and reduced preparation assembly.

**Exit Criteria:**
- One preparation contract is authoritative.
- Runtime authority and accepted dependency evidence remain intact.
- Worker receives deterministic sufficient context.
- Durable history and measurement evidence are reconciled.
- Final verification returns `verified` before plan status changes to `completed`.

## Verification

- `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_validate_planning_lifecycle.py`
- `py -3 -m pytest -q`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- Fixed before/after dispatcher comparison with operational invariant counts.
- No new scheduler, DAG, retry controller, acceptance authority, runtime, or persistent memory layer.

## Completion Criteria

1. CLI and Python plan entry points use one authoritative preparation contract.
2. Compatibility adapters cannot bypass plan-derived readiness, identity, or runtime-binding validation.
3. Plan preparation preserves resolved runtime authority and rejects missing/conflicting bindings.
4. Accepted Git revisions are proven contained in the consumer checkout before launch.
5. One verifier checks mutable plan/dependency/artifact/runtime facts at the launcher boundary.
6. Final worker payload includes deterministic task, objective, accepted prerequisites, required proof, and explicit constraints.
7. Shared dependency validation detects duplicate rows and owns graph checks without duplicate traversal.
8. Completed-plan evidence matches Git history and verification counts.
9. Fixed comparison proves reduced preparation work without added controller round trips, model calls, launch subprocesses, missing-context requests, or recovery paths.
10. `skill-verification-before-completion` returns `verified` before status becomes `completed`.

## Deliberate Deferrals

Runtime-binding surface reduction, duplicate Git/process-read elimination beyond
this launch-boundary fix, topology-aware execution, candidate cross-verification,
learned routing, persistent scheduling, general experience memory, and
cross-runtime orchestration remain outside this plan.

## Self-Review

- Verdict requirements map to Tasks 1–6.
- Current callers, symbols, tests, and validators are named.
- Shared preparation and dependency owners are explicit.
- Runtime values are passed through existing owners rather than synthesized.
- Descriptor-file compatibility remains separate.
- Launch freshness, worker payload, history reconciliation, and operational proof
  have explicit task-local gates.
- Current checkout dirtiness and stale base are called out; execution must use a
  clean worktree from `origin/main`.
