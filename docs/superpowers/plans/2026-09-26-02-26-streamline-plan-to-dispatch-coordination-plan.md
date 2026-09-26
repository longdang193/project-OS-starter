---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
parent_spec: none
name: streamline-plan-to-dispatch-coordination
targets:
  - scripts/planning_dependencies.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/lane.py
  - scripts/project_os_runtime/attempt.py
  - scripts/herdr_parallel_dispatch.py
  - tests/test_plan_preparation.py
  - tests/test_project_os_runtime.py
  - tests/test_herdr_parallel_dispatch.py
  - scripts/validate_planning_lifecycle.py
  - tests/test_validate_planning_lifecycle.py
  - .github/workflows/runtime-contracts.yml
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Streamline Plan-to-Dispatch Coordination

## Verdict Review

The supplied verdict supports one bounded vertical slice: prepare selected approved tasks directly from the canonical Git-tracked plan plus runtime inputs already resolved by the controller, then reuse existing admission, dispatch, and structured results.

Corrections applied here:

- `612ebd6` is current `HEAD`; source and tests show no durable `plan_preparation.py`, `test_plan_preparation.py`, or plan-input dispatcher path. Prior completion claims are not implementation evidence in this checkout.
- Existing source owns lane normalization, admission, dispatch, and lifecycle evidence. New preparation must bridge into those owners, not replace them.
- `scripts/__init__.py` is not required for current imports; adding it would change standalone-script package resolution, so it is removed from scope.
- Existing dispatcher CLI requires `--lanes-file`; plan mode must be added to that command while preserving descriptor-file behavior.
- Plan-derived inputs and runtime-resolved inputs are different contracts.
- Preparation collects reusable facts once; fresh checks remain only at real mutable-state or execution boundaries.
- Completion changes are conditional on a demonstrated redundant read or reconstruction step. Existing result output may be sufficient.
- Operation-count and real workflow reduction are primary evidence. Micro-benchmark timing is reported with absolute and relative deltas, not used as a 10% hard gate.

New verdict review:

- The verdict's `2902ee6` baseline and claim that preparation already exists do not match local Git/source truth; retain `612ebd6ae77ceed9695ac5eb8920e354ab0df7d3` and this proposed pending ledger.
- Accepted: dependency semantics need a dedicated pure owner, artifact availability must derive from verifiable identity at launch, identity needs an `execution_binding_digest`, worker inputs must come from deterministic fields, CLI/runtime-binding shapes must be exact, and one launch-bound verifier must own freshness checks.
- Accepted: measurement gates use operational invariants instead of vague end-to-end wording.
- Rejected: preserving Tasks 1–5 as completed or converting this into an amendment to an absent PR #40 implementation.

## Review Findings

Two review agents inspected this plan against the verdict, repository source, and planning contracts. Accepted corrections:

- Make plan status and ledger truthful for this checkout: proposed draft with pending tasks; no source-backed completion evidence exists.
- Define existing-command plan invocation, selected task inputs, descriptor-file compatibility, and one admission/dispatch path.
- Define transient accepted prerequisite bindings: structural readiness, controller-accepted evidence, and artifact availability must all pass before `dependency_ready` can pass.
- Require one shared dependency grammar and graph-validation owner consumed by both lifecycle validation and preparation.
- Bound final task extraction at the next peer-level section and assert on actual worker-facing task text.
- Add stable plan identity versus mutable plan revision/freshness checks, existing cross-platform CI, and exact file/symbol ownership.
- Remove the synthetic 10% timing gate; require reduced controller preparation work and fixed operational invariants instead: no additional controller round trip, model call, launch subprocess, missing-context request, or recovery/reconciliation path.

Rejected suggestion: add `scripts/__init__.py`. Current namespace imports work without it, and changing package resolution is unrelated scope.

## Goal

Extend existing coordinated DeepAgents dispatch workflow so selected approved tasks reach existing lane preparation without manual descriptor assembly, while preserving plan ownership, authority, admission, settlement, recovery, and acceptance boundaries.

Do not create second task ledger, persistent DAG, scheduler, universal dispatcher, acceptance authority, retry policy, or mandatory workflow.

## Implementation Outcomes

### Dependency correctness

Execution-eligible plans use one deterministic dependency parser and complete whole-graph validation in `scripts/planning_dependencies.py`. Canonical dependency declarations are task-ledger fields under plan task rows; supported syntax is a comma-separated list of task IDs, with only the range form recorded by Task 1 allowed. Parser must consume complete field, reject trailing or unparsed input, and validate every node and edge before readiness. Duplicate IDs, missing references, self-dependencies, cycles, unsupported syntax, and partial parses fail closed. Historical plans remain compatible under existing validator policy unless explicitly selected for automated preparation; supported historical fixtures pass, while ambiguous or malformed declarations require explicit modernization.

### Plan-derived preparation

Controller can obtain selected task identity, dependencies, recorded prerequisite state, explicit evidence and artifact references, required proof, bounded worker brief, and concrete missing prerequisites without repeating source reads. Projection consumes deterministic task, ledger, binding, and explicit-reference fields only; it never performs arbitrary semantic extraction, mutates plan state, or infers technical acceptance.

### Existing dispatch reuse

Prepared facts feed existing `PreparedLane`, `_prepare_admission`, `load_lane_descriptors_from_items`, and `run_parallel` paths. Existing executor/profile resolution, worktree and write-set ownership, runtime grants, capacity, and `ADMITTED`/`DEFERRED`/`BLOCKED`/`REJECTED` semantics remain authoritative. Codex, Tura, direct execution, and explicit CoS paths remain unchanged.

### Reconciliation reuse

Current controller consumes existing structured lifecycle evidence. Delivery, execution, observation, task result, cleanup, verification, and acceptance stay distinct. Settled runtime never means accepted task. If current result output already removes redundant inspection, no completion production change is needed.

### Measured improvement

Before/after evidence uses fixed equivalent fixtures and proves at least one fewer counted controller preparation operation or manually assembled descriptor field per selected task. Run deterministic fixtures at least 10 times when timing is available; report median preparation time with absolute and relative deltas, but do not gate completion on sub-millisecond timing noise. Gate completion on reduced controller work, no additional controller round trip, no additional model call, no additional launch subprocess, no additional missing-context request in fixed fixtures, and no new recovery/reconciliation path. Tokens, interventions, and rework are measured when available and reported inconclusive otherwise.

## Execution Approach

- Mode: `subagent-ready`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace` for planning; clean implementation worktree before execution
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named source, tests, canonical runtime documentation, and this plan; run listed local tests, validators, and read-only probes; preserve unrelated workspace state
- User-approval actions: commits, pushes, merges, publication, authentication, external writes, destructive cleanup, and edits outside named targets
- Parallel ownership: review-only agents may inspect this plan concurrently; implementation stays sequential until disjoint ownership is proven
- Sequential fallback: baseline and parser contract, then preparation and worker payload, then identity/freshness, then dispatcher integration, then conditional reconciliation, then CI and measurement

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `612ebd6ae77ceed9695ac5eb8920e354ab0df7d3`
- Expected workspace: preserve unrelated untracked `.playwright-mcp/`, `db/`, and existing plan files; do not stage, delete, or rewrite them
- Next action: none; execution complete and evidence recorded
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | clean implementation worktree | `codex` | none | baseline and integration contract | 268 baseline tests passed; current dispatcher requires `--lanes-file`; no plan-preparation module or consumer exists |
| Task 2 | `completed` | clean implementation worktree | `codex` | Task 1 | shared grammar and graph regressions | strict parser, graph validation, lifecycle suite 33 passed, preparation suite 5 passed |
| Task 3 | `completed` | clean implementation worktree | `codex` | Task 2 | readiness, prerequisite binding, and worker payload regressions | plan projection and preparation suite 6 passed |
| Task 4 | `completed` | clean implementation worktree | `codex` | Tasks 2-3 | stable identity and mutable-binding regressions | launch freshness and digest suite 80 passed |
| Task 5 | `completed` | clean implementation worktree | `codex` | Tasks 3-4 | existing-command dispatch and compatibility regressions | plan CLI, descriptor compatibility, and shared-path suite 73 passed |
| Task 6 | `completed` | clean implementation worktree | `codex` | Tasks 1-5 | CI, measurement, and final validation | 813 tests passed, 1 skipped; validators, adapter check, diff check passed; 10-run median preparation 0.354 ms; no additional controller round trip, model call, launch subprocess, missing-context request, or recovery path |

## Task Breakdown

### Task 1: Establish baseline and integration contract

**Purpose:**
- Prove current parser, lane, admission, dispatcher, CI, and documentation owners before implementation.

**Task Function:**
- Baseline and contract mapping.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: Codex controller owns baseline mapping and direct source/test evidence; no delegated execution needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead controller runs baseline validation directly.

**Specification Coverage:**
- Direct approved scope: Plan-to-Dispatch Coordination Completion verdict; preserve existing authority, admission, lifecycle, and acceptance owners.

**Required Skills:** `skill-systematic-debugging`, `skill-backend-verification`

**Files And Symbols:**
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
- [x] Step 1: Record `HEAD`, branch, status, and preserved unrelated paths.
- [x] Step 2: Reproduce or falsify duplicate IDs, missing references, cycles, self-reference, multiple dependencies, ranges, partial parses, and active-task cases. Record exact accepted dependency syntax and complete-consumption behavior.
- [x] Step 3: Map canonical ledger fields and supported dependency grammar. Task prose is explanatory; ledger state owns dependencies.
- [x] Step 4: Trace one coordinated DeepAgents path from lane input through admission, launcher result, receipt, and controller reconciliation.
- [x] Step 5: Record manual operation to remove: controller assembly of lane fields already present in plan and resolved runtime inputs.
- [x] Step 6: Capture baseline preparation operations and timing using existing evidence or deterministic fixtures. Mark unavailable telemetry unavailable.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_validate_planning_lifecycle.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `git diff --check` and read-only `git status --short`.
- Expected: baseline commands pass; current plan path accepts descriptor input only; no plan-preparation consumer exists in checkout.

**Exit Criteria:**
- Grammar, source ownership, consumer seam, replaced manual operation, scenarios, and baseline evidence are recorded before code changes.

### Task 2: Implement strict dependency parsing and graph validation

**Purpose:**
- Give lifecycle validation and plan preparation one complete-consumption dependency contract.

**Task Function:**
- Dependency contract implementation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: Codex controller owns preparation projection and focused boundary tests; no delegated execution needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task proof uses existing lifecycle tests and repository validators.

**Specification Coverage:**
- One dependency grammar and graph-validation owner; no duplicate parser, persistent DAG, natural-language inference, or historical rewrite.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Create `scripts/planning_dependencies.py:parse_task_id`, `parse_dependency_field`, `validate_dependency_graph`.
- Inspect `scripts/planning_artifact_schema.py` only for artifact metadata ownership; do not add dependency semantics there.
- Modify `scripts/validate_planning_lifecycle.py:_coordination_dependencies` to consume `planning_dependencies`; do not retain a second regex parser.
- Modify `scripts/project_os_runtime/plan_preparation.py` to consume `planning_dependencies` when plan preparation exists.
- Add focused parser/preparation coverage in `tests/test_plan_preparation.py` and lifecycle compatibility coverage in `tests/test_validate_planning_lifecycle.py`.

**Dependencies:** Task 1.

**Authority:**
- Preauthorized local actions: edit named parser/tests and add minimum data representation required by existing consumers.
- Stop for: persistent graph state, natural-language dependency inference, historical rewrite, or changed admission semantics.

**Steps:**
- [x] Step 1: Define one complete-consumption parser for canonical task-ledger dependency fields. Accept task IDs separated by commas and the exact range form recorded by Task 1; reject all other syntax.
- [x] Step 2: Expose graph validation from the same owner and require both lifecycle validation and preparation to call it.
- [x] Step 3: Validate every task node and dependency edge for duplicate IDs, missing references, self-dependencies, and cycles before readiness.
- [x] Step 4: Preserve historical artifact validation. Define automated-preparation eligibility as an explicitly selected plan whose dependency fields satisfy supported grammar; supported historical fixtures pass, ambiguous or malformed fixtures require modernization.
- [x] Step 5: Keep output disposable and reconstructible. Add no DAG file, registry, or cache.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_validate_planning_lifecycle.py tests/test_plan_preparation.py`
- Expected: valid sequential and independent branches pass; all listed invalid forms fail; historical eligibility policy is covered; lifecycle validation remains green.

**Exit Criteria:**
- One parser owner, complete-graph validation, and explicit historical policy are proven.

### Task 3: Derive bounded readiness and worker brief

**Purpose:**
- Project selected approved tasks into complete worker inputs without repeated plan or evidence reconstruction.

**Task Function:**
- Plan-derived preparation and worker-contract projection.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: Codex controller owns runtime identity and launch-bound freshness checks; no delegated execution needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused preparation tests prove contract and boundary behavior.

**Specification Coverage:**
- Separate structural readiness, accepted dependency evidence, artifact availability, admission, and acceptance; render bounded proof, constraints, authority, and unresolved concerns into actual worker task text.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Create `scripts/project_os_runtime/plan_preparation.py` for disposable plan-to-lane projection.
- Modify `scripts/project_os_runtime/lane.py:PreparedLane` for transient binding and revision fields proven by Task 1 contract mapping.
- Add focused tests in `tests/test_plan_preparation.py` and assert final worker text through the existing launcher/dispatch test seam.

**Dependencies:** Task 2.

**Authority:**
- Preauthorized local actions: add on-demand readiness and brief projection, update focused tests, and run plan/lifecycle checks.
- Stop for: plan mutation, second ledger, inferred acceptance, invented authority, or full-conversation injection.

**Input Mapping:**

| Input | Source |
| --- | --- |
| Task, dependencies, executor, selected profile | Canonical plan |
| Purpose, constraints, required proof | Selected Task N fields and ledger Required Proof |
| Worktree, branch, base, HEAD | Existing workspace resolution and Git inspection |
| Runtime grant, MCP selection, remaining allowance | Existing controller/runtime resolution |
| Session and pane selectors | Existing launcher selection |
| Accepted prerequisite evidence | Existing controller decision and explicit task references |

**Transient prerequisite binding:**

```text
source_task
accepted_revision
evidence_ref
artifact_ref
```

For this first version, `accepted_revision` and `artifact_ref` are Git-bound identities. The controller owns acceptance. Preparation derives `structurally_ready` from declared task state and graph facts, then verifies accepted bindings exist and match dependencies. One launch-bound verifier derives dispatcher-facing `dependency_ready` only when `structurally_ready`, accepted bindings, and expected prerequisite revisions reachable from consumer execution state all pass. Preparation never trusts an earlier `artifact_available` boolean.

**Steps:**
- [x] Step 1: Expose task identity, dependencies, recorded prerequisite state, explicit evidence/artifact refs, required proof, and unresolved prerequisites.
- [x] Step 2: Validate transient prerequisite bindings and derive `structurally_ready`; leave dispatcher-facing `dependency_ready` to the launch-bound verifier.
- [x] Step 3: Build bounded brief from selected Task N fields, ledger Required Proof, dependency identities, accepted prerequisite bindings, known canonical execution fields, and explicit contract/reference fields already present in Task N.
- [x] Step 4: Stop task extraction at the next peer-level section outside the task breakdown. Exclude trailing `## Verification`, notes, decisions, and complete upstream histories.
- [x] Step 5: Resolve missing choices once through existing workflow; plans carry no mutable runtime state for this helper.
- [x] Step 6: Reuse facts within preparation. Keep fresh checks only at mutable-state and launch boundaries. Add no cache or validation framework.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py`
- Expected: pending, missing, superseded, or unavailable prerequisites remain unready; actual worker text excludes trailing sections and histories; prose never becomes acceptance.

**Exit Criteria:**
- Approved plan plus selected task IDs plus resolved runtime inputs produce bounded worker inputs without repeated source reconstruction.

### Task 4: Separate stable identity and revalidate mutable bindings

**Purpose:**
- Prevent assignment churn from unrelated plan edits and stale mutable state from reaching worker invocation.

**Task Function:**
- Freshness and assignment-identity enforcement.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: Codex controller owns final verification, fixed-fixture comparison, and plan reconciliation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: runtime contract tests prove stale-state rejection and identity stability.

**Specification Coverage:**
- Stable `plan_identity` and task identity remain separate from full-plan `plan_revision` and selected-task `execution_binding_digest`; launch revalidates plan, Git, evidence, ownership, settlement, grant, and capabilities.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect `scripts/project_os_runtime/lane.py:PreparedLane` and `scripts/project_os_runtime/attempt.py:assignment_id`.
- Modify `scripts/project_os_runtime/lane.py:PreparedLane` and `scripts/project_os_runtime/attempt.py:assignment_id` for stable identity and binding digest fields.
- Add `scripts/herdr_parallel_dispatch.py:verify_launch_bindings` as sole coordinator-owned freshness verifier.
- Modify `scripts/herdr_parallel_dispatch.py:_prepare_admission` to consume verifier result, and `_launcher_command`/`run_lane` to consume verified `PreparedLane` without re-parsing plan semantics.
- Verify `scripts/herdr_main_launcher.py` existing coordinated launch contract through current launcher tests; keep launcher production code unchanged.
- Extend `tests/test_project_os_runtime.py` and `tests/test_herdr_parallel_dispatch.py` for changed contracts.

**Dependencies:** Tasks 2-3.

**Authority:**
- Preauthorized local actions: map validated facts into existing lane inputs, add focused regressions, and run bounded dispatch tests.
- Stop for: universal dispatcher, changed concurrency ceiling, new grant, automatic retry/continuation, or bypassed launch checks.

**Steps:**
- [x] Step 1: Keep stable `plan_identity`, repository identity, task identity, parsed graph, and task contract separate from full-plan `plan_revision` and selected-task `execution_binding_digest`.
- [x] Step 2: Compute `execution_binding_digest` from selected task identity, task contract, dependencies, executor/profile, required proof, applicable shared requirements, accepted prerequisite refs, and authority-relevant inputs.
- [x] Step 3: Ensure unrelated progress or evidence edits do not churn assignment identity or selected-task binding digest; relevant task-binding changes fail freshness checks.
- [x] Step 4: Make `verify_launch_bindings` revalidate task binding, accepted prerequisite revisions, expected Git reachability, worktree/branch/base/HEAD, ownership, prior settlement, grant, capabilities, and `execution_binding_digest` immediately before invocation.
- [x] Step 5: Reuse `PreparedLane`, `prepare_lane`, `classify_admission`, and existing launcher Git/runtime checks. Add no retry, scheduler, cache, or new state owner.
- [x] Step 6: Preserve independent eligible lanes, conflict `BLOCKED`, capacity `DEFERRED`, valid `ADMITTED`, and invalid-input `REJECTED`.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py`
- Expected: assignment identity and `execution_binding_digest` stay stable across unrelated plan edits; stale bindings fail closed; no launch bypasses final checks.

**Exit Criteria:**
- Mutable bindings are checked at launch, stable identity does not churn, and existing admission/lifecycle semantics remain authoritative.

### Task 5: Integrate plan input into existing dispatcher

**Purpose:**
- Make canonical plan/task input the normal coordinated command path while preserving descriptor-file compatibility.

**Task Function:**
- Existing dispatcher integration.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: Codex controller owns dispatcher integration and compatibility proof; no delegated execution needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: command and dispatch tests prove both input modes share one path.

**Specification Coverage:**
- Existing dispatcher gains `--plan-file`, repeatable `--task`, and `--runtime-bindings`; `--lanes-file` remains compatible and mutually exclusive with plan mode; one admission and `run_parallel()` path remains authoritative.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify `scripts/herdr_parallel_dispatch.py:build_parser`, `main`, `load_lane_descriptors_from_items`, and `run_parallel`.
- Add plan mode with canonical plan path plus selected task IDs and resolved runtime bindings; preserve `--lanes-file` compatibility.
- `--runtime-bindings <runtime.json>` accepts JSON keyed by selected task ID. Each value contains runtime-owned fields only: `repository_identity`, `worktree`, `expected_base`, `session`, `pane`, `runtime_grant`, and `accepted_prerequisites`; it is not a second lane descriptor.
- Reuse `scripts/project_os_runtime/plan_preparation.py`, `prepare_lane`, `_prepare_admission`, and `run_parallel`.
- Extend `tests/test_herdr_parallel_dispatch.py` and `tests/test_plan_preparation.py`; update `docs/operating_system/runtime/runtime-surfaces.md` with one canonical invocation.

**Dependencies:** Tasks 3-4.

**Authority:**
- Preauthorized local actions: wire plan inputs through existing dispatcher/admission/launch paths, preserve descriptor compatibility, update focused tests and runtime guidance.
- Stop for: second dispatcher, changed concurrency ceiling, new grant, automatic retry/continuation, bypassed launch checks, or settled-runtime-as-accepted behavior.

**Steps:**
- [x] Step 1: Add plan-derived mode to the existing command with exact flags `--plan-file <plan.md>`, repeatable `--task <task-id>`, and `--runtime-bindings <runtime.json>`; reject ambiguous mode combinations and reject mixing plan mode with `--lanes-file`.
- [x] Step 2: Route descriptor-file mode and plan mode through the same admission, capacity, conflict, launcher, settlement, and event paths.
- [x] Step 3: Derive plan-owned fields from the canonical plan and accept only controller-resolved runtime-owned bindings matching the keyed JSON shape; reject plan-owned fields duplicated in runtime bindings.
- [x] Step 4: Prove selected sequential and independent tasks reach the existing `run_parallel()` path; invalid executor, missing binding, conflict, and capacity outcomes retain existing classifications.
- [x] Step 5: Preserve delivery, execution, observation, task result, cleanup, performance, verification, and acceptance distinctions; keep completion production code unchanged.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_plan_preparation.py`
- Expected: actual command invocation accepts plan mode; descriptor mode remains compatible; both modes share one dispatch path; no false acceptance occurs.

**Exit Criteria:**
- Normal coordinated execution accepts canonical plan/task inputs without manual plan-owned descriptor assembly, while descriptor compatibility and existing lifecycle authority remain intact.

### Task 6: Measure and close

**Purpose:**
- Prove operational reduction and reconcile final documentation, CI, and lifecycle evidence.

**Task Function:**
- Outcome verification and plan reconciliation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: Codex controller owns final verification, fixed-fixture comparison, and plan reconciliation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification skill owns fresh completion evidence.

**Specification Coverage:**
- Existing cross-platform runtime CI covers preparation; completion handling remains unchanged; completion requires reduced controller work and no lifecycle regressions.

**Required Skills:** `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`

**Files And Symbols:**
- Verify: all changed files, this plan, and affected canonical runtime docs.
- Preserve: unrelated workspace paths.

**Dependencies:** Task 1, Task 2, Task 3, Task 4, Task 5.

**Authority:**
- Preauthorized local actions: run listed tests, validators, deterministic fixtures, measurement comparison, documentation checks, and Git inspection.
- Stop for: failed proof, unavailable required baseline, stale generated surface, unexpected file, or unapproved Git disposition.

**Steps:**
- [x] Step 1: Compare before/after serial, independent, conflict, failed, and recovery fixtures under equivalent inputs.
- [x] Step 2: Confirm existing structured completion evidence separates delivery, execution, observation, task result, cleanup, performance, verification, and acceptance; keep result production code unchanged.
- [x] Step 3: Count controller preparation calls, plan/evidence reads, manually assembled lane fields, commands required to dispatch, and eligibility-to-delivery time at the selected-task boundary. Run fixed fixtures at least 10 times; require no additional controller round trip, model call, launch subprocess, missing-context request, or recovery/reconciliation path; report timing without a micro-benchmark hard gate.
- [x] Step 4: Report absolute and relative timing deltas, tokens, interventions, missing context, and rework; mark unavailable telemetry inconclusive.
- [x] Step 5: Update `.github/workflows/runtime-contracts.yml` to include preparation tests in its existing Windows/Linux matrix. Add no workflow.
- [x] Step 6: Run final tests, validators, adapter check, diff check, and workspace review.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_validate_planning_lifecycle.py`
- [x] `py -3 -m pytest -q`
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `git diff --check`
- [x] `git status --short`
- Expected: all required checks pass; controller preparation work decreases; fixed fixtures show no additional controller round trip, model call, launch subprocess, missing-context request, or recovery/reconciliation path; ownership, lifecycle, and acceptance remain unchanged.

**Exit Criteria:**
- Correctness, fewer preparation operations, existing dispatch execution, acceptance boundaries, compatibility, CI coverage, and measurement evidence are accepted.
- This plan is `completed` after approval, task proof, final verification, and evidence reconciliation.
- Failed or blocked proof leaves plan non-complete and records blocker.

## Verification

- `py -3 -m pytest -q tests/test_plan_preparation.py tests/test_project_os_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_validate_planning_lifecycle.py`
- `py -3 -m pytest -q`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- Deterministic before/after workflow evidence records unavailable telemetry as inconclusive.
- No persistent DAG, scheduler, universal dispatcher, duplicate ledger, automatic retry, or false-acceptance shortcut.

## Completion Criteria

- Dependency parser rejects reproduced defects and preserves valid supported and historical artifacts under stated policy.
- Approved plan plus selected task IDs plus resolved runtime inputs reach existing DeepAgents dispatch without manual descriptor assembly.
- Admission, grants, ownership, settlement, recovery, direct execution, and executor-specific paths remain valid.
- Completion handling changes only when a redundant operation is identified.
- Required evidence shows fewer preparation operations, no additional controller round trip, model call, launch subprocess, missing-context request, or recovery/reconciliation path, and no ownership, lifecycle, or acceptance regressions.
- Required evidence proves selected-task `execution_binding_digest` remains stable across unrelated edits and rejects stale launch bindings.

## Deliberate Deferrals

Persistent DAG storage, scheduler daemon, universal dispatcher, learned routing, critical-path optimization, experience replay, semantic evidence ranking, candidate cross-verification, automatic retry/continuation, cross-runtime parity, and a new executable remain outside scope. The existing dispatcher CLI may gain plan-input flags.

## Self-Review

- Verdict claims are inputs to scope, not proof.
- Current `HEAD` and exact consumer seam gate implementation.
- Plan-owned and runtime-owned lane inputs are explicit.
- Structural readiness never substitutes for evidence, artifact, admission, or acceptance.
- New code has one named owner and one focused consumer path.
- Review agents returned severity, evidence, and exact corrections; accepted findings are recorded above and rejected packaging scope is explicit.
- Dependency grammar consumes complete input and historical eligibility has fixtures.
- Measurement has fixed fixtures and counting boundaries; timing is descriptive, not a micro-benchmark completion gate.
- Lifecycle status ownership is explicit.
