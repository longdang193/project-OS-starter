---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
parent_spec: none
name: streamline-plan-to-dispatch-coordination
targets:
  - scripts/__init__.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - tests/test_plan_preparation.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - scripts/validate_planning_lifecycle.py
  - tests/test_validate_planning_lifecycle.py
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Streamline Plan-to-Dispatch Coordination

## Verdict Review

All three supplied verdicts support one bounded vertical slice: prepare selected approved tasks directly from the canonical Git-tracked plan plus runtime inputs already resolved by the controller, then reuse existing admission, dispatch, and structured results.

Corrections applied here:

- `612ebd6` is current `HEAD`; reported parser defects must be reproduced at baseline, not assumed from the verdict.
- Current source clearly owns lane normalization, admission, dispatch, and lifecycle evidence, but no shared plan-preparation consumer is obvious.
- Local `scripts` package boundary is required so repository modules are not shadowed by shared runtime namespace during full collection.
- Live dispatch probe: current plan rows use `codex` and are correctly rejected by DeepAgents-only admission; synthetic `deepagents` plan admitted and completed through existing dispatch.
- Plan-derived inputs and runtime-resolved inputs are different contracts.
- Preparation collects reusable facts once; fresh checks remain only at real mutable-state or execution boundaries.
- Completion changes are conditional on a demonstrated redundant read or reconstruction step. Existing result output may be sufficient.
- Required measurement is proportionate: fewer preparation operations, fewer manually assembled descriptor fields, before/after preparation timing, and focused contract proof. Broader outcomes are reported, not assumed.

## Goal

Extend existing coordinated DeepAgents dispatch workflow so selected approved tasks reach existing lane preparation without manual descriptor assembly, while preserving plan ownership, authority, admission, settlement, recovery, and acceptance boundaries.

Do not create second task ledger, persistent DAG, scheduler, universal dispatcher, acceptance authority, retry policy, or mandatory workflow.

## Implementation Outcomes

### Dependency correctness

Execution-eligible plans use one deterministic dependency parser and complete whole-graph validation. Canonical dependency declarations are task-ledger fields under plan task rows; supported syntax is a comma-separated list of task IDs, with only the range form recorded by Task 1 allowed. Parser must consume complete field, reject trailing or unparsed input, and validate every node and edge before readiness. Duplicate IDs, missing references, self-dependencies, cycles, unsupported syntax, and partial parses fail closed. Historical plans remain compatible under existing validator policy unless explicitly selected for automated preparation; supported historical fixtures pass, while ambiguous or malformed declarations require explicit modernization.

### Plan-derived preparation

Controller can obtain selected task identity, dependencies, recorded prerequisite state, explicit evidence and artifact references, required proof, bounded worker brief, and concrete missing prerequisites without repeating source reads. Projection is disposable, on demand, and never mutates plan state or infers technical acceptance.

### Existing dispatch reuse

Prepared facts feed existing `PreparedLane`, `_prepare_admission`, `load_lane_descriptors_from_items`, and `run_parallel` paths. Existing executor/profile resolution, worktree and write-set ownership, runtime grants, capacity, and `ADMITTED`/`DEFERRED`/`BLOCKED`/`REJECTED` semantics remain authoritative. Codex, Tura, direct execution, and explicit CoS paths remain unchanged.

### Reconciliation reuse

Current controller consumes existing structured lifecycle evidence. Delivery, execution, observation, task result, cleanup, verification, and acceptance stay distinct. Settled runtime never means accepted task. If current result output already removes redundant inspection, no completion production change is needed.

### Measured improvement

Before/after evidence uses fixed equivalent fixtures and proves at least one fewer counted controller preparation operation or manually assembled descriptor field per selected task. Run each deterministic fixture at least 10 times; report median preparation time and require no more than 10 percent median regression. End-to-end latency, tokens, interventions, missing-context requests, and rework are measured when available and reported inconclusive otherwise.

## Execution Approach

- Mode: `subagent-ready`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace` for planning; clean implementation worktree before execution
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named source, tests, canonical runtime documentation, and this plan; run listed local tests, validators, and read-only probes; preserve unrelated workspace state
- User-approval actions: commits, pushes, merges, publication, authentication, external writes, destructive cleanup, and edits outside named targets
- Parallel ownership: review-only agents may inspect this plan concurrently; implementation stays sequential until disjoint ownership is proven
- Sequential fallback: baseline and parser contract, then preparation, then dispatch integration, then conditional reconciliation, then measurement

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `612ebd6ae77ceed9695ac5eb8920e354ab0df7d3`
- Expected workspace: preserve unrelated untracked `.playwright-mcp/`, `db/`, and existing plan files; do not stage, delete, or rewrite them
- Next action: resolve preparation timing gate or record approved inconclusive telemetry
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | clean implementation worktree | `codex` | none | baseline and integration contract | 268 focused tests; 9 runtime tests; planning validator passed; no parser or plan-to-dispatch consumer at HEAD; dispatcher accepts descriptor inputs only |
| Task 2 | `completed` | clean implementation worktree | `codex` | Task 1 | parser and graph regressions | `82 passed` focused suite; strict dependency, duplicate, missing, self, cycle, and partial-parse checks pass |
| Task 3 | `completed` | clean implementation worktree | `codex` | Task 2 | readiness and brief regressions | `82 passed` focused suite; readiness stays separate from evidence and unresolved prerequisites remain explicit |
| Task 4 | `completed` | clean implementation worktree | `codex` | Task 3 | lane/admission/dispatch regressions | `82 passed` focused suite; `run_parallel_from_plan` reuses existing admission and dispatch; no grant or concurrency changes; live `deepagents` task admitted; `codex` task rejected with `unsupported executor: codex`; executor boundary preserved. |
| Task 5 | `completed` | clean implementation worktree | `codex` | Task 4 | conditional reconciliation proof | `220 passed` launcher/result/lifecycle suite; existing structured result fields sufficient, no reconciliation production change |
| Task 6 | `active` | clean implementation worktree | `codex` | Tasks 1-5 | measurement and final validation | `814 passed, 1 skipped`; all validators pass; import-boundary live probe passes across dispatcher, launcher, runtime, and contract callers; synthetic 10-run preparation median `0.1993 ms -> 0.4347 ms` exceeds 10% threshold, so completion gate remains open |

## Task Breakdown

### Task 1: Establish baseline and integration contract

**Template Profile:**
- Controller-selected: `normal`
- Task function: `baseline and contract mapping`

**Skills:** `skill-systematic-debugging`, `skill-backend-verification`

**Files and Symbols:**
- Inspect `scripts/validate_planning_lifecycle.py` and `scripts/planning_artifact_schema.py`.
- Inspect `scripts/project_os_runtime/lane.py:prepare_lane` and `scripts/project_os_runtime/admission.py:classify_admission`.
- Inspect `scripts/herdr_parallel_dispatch.py:_prepare_admission`, `load_lane_descriptors_from_items`, and `run_parallel`.
- Inspect `scripts/herdr_main_launcher.py:_build_assignment_result` and `_classify_deepagents_outcome`.
- Inspect current plan ledger examples under `docs/superpowers/plans/`.

**Dependencies:** none.

**Authority:**
- Preauthorized local actions: read source/tests, run baseline commands, create disposable fixtures, and record exact consumer ownership in this plan.
- Stop for: unproven defect, missing consumer seam, unexpected mutation, or preserved-workspace conflict.

**Steps:**
1. Record `HEAD`, branch, status, and preserved unrelated paths.
2. Reproduce or falsify duplicate IDs, missing references, cycles, self-reference, multiple dependencies, ranges, partial parses, and active-task cases. Record exact accepted dependency syntax and complete-consumption behavior.
3. Map canonical ledger fields and supported dependency grammar. Task prose is explanatory; ledger state owns dependencies.
4. Trace one coordinated DeepAgents path from lane input through admission, launcher result, receipt, and controller reconciliation.
5. Record manual operation to remove: controller assembly of lane fields already present in plan and resolved runtime inputs.
6. Capture baseline preparation operations and timing using existing evidence or deterministic fixtures. Mark unavailable telemetry unavailable.

**Verification:**
- `py -3 -m pytest -q tests/test_validate_planning_lifecycle.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `git diff --check` and read-only `git status --short`.

**Exit Criteria:** grammar, source ownership, consumer seam, replaced manual operation, scenarios, and baseline evidence are recorded before code changes.

### Task 2: Implement strict dependency parsing and graph validation

**Template Profile:**
- Controller-selected: `normal`
- Task function: `dependency correctness`

**Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files and Symbols:**
- Modify parser owner identified by Task 1. Use new `scripts/project_os_runtime/plan_preparation.py` only if no current owner exists.
- Reuse `scripts/planning_artifact_schema.py` for artifact metadata.
- Add focused `tests/test_plan_preparation.py`; extend planning lifecycle tests only for a proven validator gap.

**Dependencies:** Task 1.

**Authority:**
- Preauthorized local actions: edit named parser/tests and add minimum data representation required by existing consumers.
- Stop for: persistent graph state, natural-language dependency inference, historical rewrite, or changed admission semantics.

**Steps:**
1. Parse canonical task-ledger dependency fields only. Accept task IDs separated by commas and exact range form recorded by Task 1; reject all other syntax.
2. Require complete parser consumption; reject trailing tokens, empty items, unsupported tokens, and partial parses.
3. Validate every task node and dependency edge for duplicate IDs, missing references, self-dependencies, and cycles before readiness.
4. Preserve historical artifact validation. Define automated-preparation eligibility as an explicitly selected plan whose dependency fields satisfy supported grammar; supported historical fixtures pass, ambiguous or malformed fixtures require modernization.
5. Keep output disposable and reconstructible. Add no DAG file, registry, or cache.

**Verification:** valid sequential and independent branches pass; all listed invalid forms fail; supported historical, ambiguous historical, and malformed historical fixtures prove eligibility policy; planning lifecycle suite remains green.

**Exit Criteria:** one parser owner, complete-graph validation, and explicit historical policy are proven.

### Task 3: Derive bounded readiness and worker brief

**Template Profile:**
- Controller-selected: `normal`
- Task function: `plan-derived preparation`

**Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files and Symbols:**
- Modify Task 2 preparation owner and exact existing controller entry point found by Task 1.
- Add focused tests in `tests/test_plan_preparation.py`.

**Dependencies:** Task 2.

**Authority:**
- Preauthorized local actions: add on-demand readiness and brief projection, update focused tests, and run plan/lifecycle checks.
- Stop for: plan mutation, second ledger, inferred acceptance, invented authority, or full-conversation injection.

**Input Mapping:**

| Input | Source |
| --- | --- |
| Task, dependencies, executor, selected profile | Canonical plan |
| Purpose, constraints, required proof | Task contract and explicit shared references |
| Worktree, branch, base, HEAD | Existing workspace resolution and Git inspection |
| Runtime grant, MCP selection, remaining allowance | Existing controller/runtime resolution |
| Session and pane selectors | Existing launcher selection |
| Accepted prerequisite evidence | Existing controller decision and referenced records |

**Steps:**
1. Expose task identity, dependencies, recorded prerequisite state, explicit evidence/artifact refs, required proof, and unresolved prerequisites.
2. Keep structural readiness, evidence sufficiency, artifact availability, and execution admission separate.
3. Build bounded brief from approved contract, plan-wide requirements, shared contracts, explicit refs, authority constraints, and required proof.
4. Resolve missing choices once through existing workflow; do not require plans to carry runtime details solely for this helper.
5. Reuse facts within preparation. Keep fresh checks only at mutable-state and launch boundaries. Add no cache or validation framework.

**Verification:** pending prerequisite stays unready; missing or superseded evidence stays explicit; unavailable artifact prevents authorization; simple direct task needs no projection; no prose claim becomes acceptance.

**Exit Criteria:** approved plan plus selected task IDs plus resolved runtime inputs produce bounded worker inputs without repeated source reconstruction.

### Task 4: Project into existing DeepAgents dispatch

**Template Profile:**
- Controller-selected: `normal`
- Task function: `runtime integration`

**Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files and Symbols:**
- Modify `scripts/herdr_parallel_dispatch.py` only at consumer established by Task 1.
- Reuse `prepare_lane`, `classify_admission`, `load_lane_descriptors_from_items`, and `run_parallel`.
- Extend `tests/test_herdr_parallel_dispatch.py` and `tests/test_project_os_runtime.py` only for changed contracts.

**Dependencies:** Task 3.

**Authority:**
- Preauthorized local actions: map validated facts into existing lane inputs, add focused regressions, and run bounded dispatch tests.
- Stop for: universal dispatcher, changed concurrency ceiling, new grant, automatic retry/continuation, or bypassed launch checks.

**Steps:**
1. Derive plan-owned fields: task, dependencies, executor, profile, purpose, proof, fixed contracts, and explicit evidence refs.
2. Accept runtime-owned fields once resolved: worktree, branch/base/HEAD, grant, MCP selection, remaining allowance, session, pane, and capabilities.
3. Preserve `PreparedLane` validation and existing resolution for missing data.
4. Recheck plan revision, task identity, Git bindings, evidence/artifact bindings, ownership, prior attempt settlement, grant, and capabilities at launch boundaries.
5. Preserve independent eligible lanes, conflict `BLOCKED`, capacity `DEFERRED`, valid `ADMITTED`, and invalid-input `REJECTED`.

**Verification:** existing lane/admission tests pass; add stale-plan, stale-evidence, unavailable-artifact, unresolved-attempt, independent-lane, conflict, capacity, and direct-path regressions; run fixture-backed dispatch.

**Exit Criteria:** controller no longer manually assembles descriptor fields already available from plan plus resolved runtime inputs.

### Task 5: Consume completion evidence only where needed

**Template Profile:**
- Controller-selected: `normal`
- Task function: `reconciliation integration`

**Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files and Symbols:**
- Inspect `scripts/herdr_main_launcher.py:_build_assignment_result` and current controller consumer first.
- Modify those files only if Task 1 identifies extra read, parse, or status reconstruction that current output cannot remove.
- Reuse tests in `tests/test_herdr_main_launcher.py` and `tests/test_deepagents_result_contract.py`.

**Dependencies:** Task 4.

**Authority:**
- Preauthorized local actions: add only demonstrated completion-context wiring or fields and focused proof.
- Stop for: second acceptance authority, state-machine fork, receipt schema fork, retry, or settled-runtime-as-accepted behavior.

**Steps:**
1. Confirm result fields already separate delivery, execution, observation, task result, cleanup, performance, verification, and acceptance.
2. If sufficient, consume directly and make no production change.
3. Otherwise add smallest derived context at existing result boundary; preserve legacy fields and source evidence.
4. Prove unknown, unverified, cleanup-uncertain, failed, reported-complete, and acceptance-pending cases remain distinguishable.

**Verification:** launcher and result-contract tests prove no false acceptance; recovery behavior remains unchanged.

**Exit Criteria:** redundant reconciliation work is removed only where measured; no duplicate authority exists.

### Task 6: Measure and close

**Template Profile:**
- Controller-selected: `normal`
- Task function: `outcome verification`

**Skills:** `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`

**Files and Symbols:** verify all changed files, this plan, and affected canonical runtime docs. Preserve unrelated workspace paths.

**Dependencies:** Task 1, Task 2, Task 3, Task 4, Task 5.

**Authority:**
- Preauthorized local actions: run listed tests, validators, deterministic fixtures, measurement comparison, documentation checks, and Git inspection.
- Stop for: failed proof, unavailable required baseline, stale generated surface, unexpected file, or unapproved Git disposition.

**Steps:**
1. Compare before/after serial, independent, conflict, failed, and recovery fixtures under equivalent inputs.
2. Count controller preparation calls, plan/evidence reads, and manually assembled lane fields at selected-task boundary. Run fixed fixtures at least 10 times; require one fewer counted operation or field and no more than 10 percent median preparation-time regression.
3. Report end-to-end latency, tokens, interventions, missing context, and rework when available; do not claim unsupported savings.
4. Run final tests, validators, adapter check, diff check, and workspace review.

**Verification:**
```powershell
py -3 -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_project_os_runtime.py tests/test_validate_planning_lifecycle.py
py -3 -m pytest -q
py -3 scripts/validate_planning_lifecycle.py --repo-root .
py -3 scripts/validate_repo_contracts.py --repo-root . --fast
py -3 scripts/sync_agent_adapters.py --all-platforms --check
git diff --check
git status --short
```

**Exit Criteria:** correctness, fewer preparation operations, existing dispatch execution, acceptance boundaries, compatibility, and measurement evidence are accepted. Review leaves plan `proposed`; execution approval changes it to `active` under lead controller, and completion changes it only after all task proof and final verification are recorded. Failed or blocked proof leaves plan non-complete and records blocker.

## Verification

- Focused suite and full suite above.
- Planning lifecycle, repository contract, adapter drift, and diff checks above.
- Deterministic before/after workflow evidence with unavailable telemetry marked.
- No persistent DAG, scheduler, universal dispatcher, duplicate ledger, automatic retry, or false-acceptance shortcut.

## Completion Criteria

- Dependency parser rejects reproduced defects and preserves valid supported and historical artifacts under stated policy.
- Approved plan plus selected task IDs plus resolved runtime inputs reach existing DeepAgents dispatch without manual descriptor assembly.
- Admission, grants, ownership, settlement, recovery, direct execution, and executor-specific paths remain valid.
- Completion handling changes only when a redundant operation is identified.
- Required evidence shows fewer preparation operations without unacceptable correctness regressions.

## Deliberate Deferrals

Persistent DAG storage, scheduler daemon, universal dispatcher, learned routing, critical-path optimization, experience replay, semantic evidence ranking, candidate cross-verification, automatic retry/continuation, cross-runtime parity, and new mandatory CLI remain outside scope.

## Self-Review

- Verdict claims are inputs to scope, not proof.
- Current `HEAD` and exact consumer seam gate implementation.
- Plan-owned and runtime-owned lane inputs are explicit.
- Structural readiness never substitutes for evidence, artifact, admission, or acceptance.
- New code is conditional on demonstrated missing ownership or consumer need.
- Review agents must return severity, evidence, and exact corrections; lead controller applies only justified findings.


- Dependency grammar consumes complete input and historical eligibility has fixtures.
- Measurement has fixed fixtures, counting boundaries, repeat count, and threshold.
- Lifecycle status ownership is explicit.
