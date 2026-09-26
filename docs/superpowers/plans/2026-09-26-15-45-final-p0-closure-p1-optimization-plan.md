---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
name: final-p0-closure-p1-optimization
targets:
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - tests/test_plan_preparation.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-09-26-15-45-final-p0-closure-p1-optimization-plan.md
---

# Final P0 Closure and P1 Optimization

## Verdict Review

The supplied verdict is substantively correct against `origin/main` at
`57f4faf`:

- `_shared_constraints()` captures only the physical line containing each
  allowlisted bullet, so wrapped continuation text is lost.
- `prepare_task()` builds `PreparedTask.brief`, then `_worker_brief()` builds
  the execution text again.
- The canonical path already reads, parses, and prepares once in the measured
  fixture; no broad P0 refactor is justified.
- Dispatcher and launcher perform multiple Git subprocess checks before worker
  execution; this is a valid P1 measurement target.
- The timing comparison between manual and canonical fixtures is descriptive,
  not an apples-to-apples latency claim.

Current local `main` is `612ebd6`; current `origin/main` is `57f4faf`.
Execution must use a clean worktree based on `origin/main` `57f4faf`, not the
older local branch tip.

The launcher regression should target the existing command-building seam:
`tests/test_plan_preparation.py:test_launcher_task_argument_contains_complete_selected_contract`.
Capture the `--task` argument from `dispatcher._launcher_command()` instead of
starting a real worker process. This proves the final worker payload without
adding flaky runtime dependency.

## Goal

Close the last P0 handoff defect by preserving wrapped canonical execution
constraints, then reduce measured plan-dispatch overhead without changing
authority, admission, freshness, prerequisite proof, lifecycle, settlement,
recovery, acceptance, or worker semantics.

## Implementation Outcomes

### Complete P0 shared-constraint handoff

`_shared_constraints()` parses only these four exact labels from the extracted
`Execution Approach` section, in fixed order:

1. `Required skills`
2. `Preauthorized local actions`
3. `User-approval actions`
4. `Parallel ownership`

For each matching bullet, capture the first-line value and indented
continuation lines until the next peer bullet, heading, section boundary, or
end of section. Join continuation lines with single spaces. Preserve the
allowlist and exclude arbitrary prose, historical aliases, planning metadata,
and review commentary.

The final launcher task text contains each selected shared constraint once,
with complete logical content. Existing selected-task, goal, prerequisite,
proof, exclusion, and non-duplication contracts remain unchanged.

### Measure before changing P1 behavior

Use existing test seams and scoped timing wrappers in one clean worktree, with
the same Python executable, temporary fixture shape, and repository state for
before/after runs. Record, for dispatches with zero, one, and two
prerequisites:

- plan source-read and parse counts;
- task-preparation count;
- execution-brief render count;
- Git subprocess command, count, and duration;
- total Git-process duration;
- preparation-to-launch-check duration;
- worker command and task-text equality;
- stale-binding failure behavior;
- admission and lifecycle outcomes.

Do not add permanent telemetry or a new state owner.

The lead controller owns the retention threshold. Removing at least one
counted duplicate operation qualifies as a maintainability optimization. A
latency-only change qualifies only when median protected
preparation-to-launch-check time improves by at least 10% across five repeated
runs for the same representative workload, with unchanged semantics.

### Apply only evidence-backed P1 optimization

Remove competing execution-brief construction only if repository search and
tests confirm no supported production consumer needs `PreparedTask.brief`.
Otherwise retain it as a diagnostic projection and keep `_worker_brief()` as
the sole worker-handoff renderer.

Keep `prepare_lane_inputs()` as a compatibility adapter. Thin it only where
measured duplicate preparation and supported-caller evidence justify the
change. Do not remove external compatibility based only on absence of local
callers.

Consolidate stable invocation facts only within one dispatch call. Keep fresh
checks for `HEAD`, expected-base ancestry, accepted prerequisite ancestry,
plan contents, deadlines, attempt ownership, and process state.

### Preserve bounded evidence claims

Retain the corrected fixture claim: canonical plan input eliminates eight
identified plan-derived caller fields while preserving compared execution
semantics. Do not claim production token savings, production latency savings,
fewer real-world interventions, or fewer production recovery events.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-writing-plans`, `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `clean managed worktree rooted at origin/main`
- Commit policy: `no commits during execution; commit only after verification returns verified and user authorizes Git disposition`
- Preauthorized local actions: inspect and edit listed source/tests/docs/plan files, run listed local checks, collect scoped benchmark evidence, and update this plan's ledger/evidence
- User-approval actions: commit, push, pull request, merge, external authentication, destructive cleanup, discard, and changes outside listed targets
- Parallel ownership: `none`; P0, measurement, optimization, and final verification are sequential
- Sequential fallback: complete P0 and its proof, then baseline P1, then apply only measured P1 changes, then run final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/final-p0-closure-p1-optimization`
- Base commit: `57f4faf` (`origin/main`)
- Expected workspace: `clean isolated worktree`; current checkout contains unrelated untracked artifacts and is not the execution target
- Next action: activate Task 1 after approval and fresh base verification
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | isolated worktree | `unresolved` | none | wrapped constraints reach `--task` payload without duplication | pending |
| Task 2 | `pending` | same worktree | `unresolved` | Task 1 | baseline counts and Git timings recorded for 0/1/2 prerequisites | pending |
| Task 3 | `pending` | same worktree | `unresolved` | Task 2 | only measured duplicate work removed; semantic and freshness checks unchanged | pending |
| Task 4 | `pending` | same worktree | `unresolved` | Task 3 | focused/full tests and repository validators pass | pending |

## Scope Boundaries

Do not change `PreparedLane` ownership, admission states, launch freshness,
lifecycle, settlement, recovery, acceptance, descriptor compatibility,
concurrency limits, direct execution, CLI modes, dependency graph semantics,
runtime authority, worker grant semantics, or full-plan freshness.

Do not add a scheduler, cache service, persistent runtime registry, semantic
parser, worker-context service, new process for bookkeeping, or general memory
layer.

## Task Breakdown

### Task 1: Preserve wrapped shared constraints

**Purpose:**
- Fix the P0 parser defect and prove complete values reach the launcher task payload.

**Task Function:**
- Correct bounded Markdown-list extraction and strengthen the existing external launcher seam regression.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through Planning Dispatch from required reasoning depth, ambiguity, scope, risk, and cost.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: independently validate parser boundaries and final payload exclusions.

**Specification Coverage:**
- Four-label allowlist remains unchanged.
- Wrapped continuation lines normalize into one logical value.
- Complete shared constraints reach `--task`.
- Unrelated plan content and duplicate task-local sections remain excluded.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:_shared_constraints`, `scripts/project_os_runtime/plan_preparation.py:parse_plan`, `scripts/project_os_runtime/plan_preparation.py:_worker_brief`
- Modify: `scripts/project_os_runtime/plan_preparation.py:_shared_constraints`, `tests/test_plan_preparation.py:_active_plan`, `tests/test_plan_preparation.py:test_launcher_task_argument_contains_complete_selected_contract`
- Verify: `scripts/herdr_parallel_dispatch.py:_launcher_command`, `tests/test_plan_preparation.py`

**Dependencies:**
- Clean worktree based on `origin/main` `57f4faf`.
- Existing fixture and command-builder seam remain available.

**Authority:**
- Preauthorized local actions: edit the listed parser and test symbols; run focused tests.
- Stop for: changed allowlist, changed worker contract, missing launcher seam, or any source outside listed targets.

**Steps:**
- [ ] Step 1: Replace physical-line lookup with continuation-aware parsing bounded to `_section(text, "Execution Approach")` and `_SHARED_CONSTRAINT_LABELS`.
- [ ] Step 2: Wrap at least `Required skills` and `User-approval actions` across physical lines in the active fixture; include all four allowlisted labels and unrelated planning metadata.
- [ ] Step 3: Extract the `--task` argument from `dispatcher._launcher_command()` and assert complete normalized values, exact-once section labels, complete selected contract, goal, accepted prerequisite identity, and required proof.
- [ ] Step 4: Assert absence of `Mode`, `Coordination`, `Isolation`, `Commit policy`, later task sections, unrelated peer sections, and duplicate `Purpose`, `Authority`, `Verification`, and `Exit Criteria` sections.

**Verification:**
- [ ] `python -m pytest -q tests/test_plan_preparation.py::test_launcher_task_argument_contains_complete_selected_contract tests/test_plan_preparation.py::test_prepare_task_keeps_readiness_separate_from_evidence`
- Expected: both tests pass; wrapped values appear fully and normalized in the final `--task` argument.

**Exit Criteria:**
- P0 parser and launcher-payload regression pass without changing parser allowlist or unrelated dispatch behavior.

### Task 2: Establish P1 baseline and consumer evidence

**Purpose:**
- Measure current canonical invocation work before any optimization and decide whether `PreparedTask.brief` or compatibility preparation is removable.

**Task Function:**
- Build a reproducible scoped probe from existing test seams and record baseline evidence.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through Planning Dispatch from performance scope and measurement risk.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: independently confirm counters, command identity, and semantic equivalence.

**Specification Coverage:**
- Read/parse/preparation counts stay measured rather than assumed.
- Git preflight cost is measured for zero, one, and two prerequisites.
- Timing remains descriptive and uses identical workloads and environment for before/after comparisons.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:PreparedTask`, `scripts/project_os_runtime/plan_preparation.py:prepare_task`, `scripts/project_os_runtime/plan_preparation.py:prepare_lane_inputs`, `scripts/project_os_runtime/plan_preparation.py:_worker_brief`, `scripts/herdr_parallel_dispatch.py:verify_launch_bindings`, `scripts/herdr_parallel_dispatch.py:_launcher_command`, `scripts/herdr_main_launcher.py:_git_identity`, `scripts/herdr_main_launcher.py:_run`
- Modify: `tests/test_plan_preparation.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`; modify production instrumentation only if existing test seams cannot expose required counts without changing behavior
- Verify: `tests/test_plan_preparation.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 complete.
- No production optimization is allowed before baseline evidence is recorded.

**Authority:**
- Preauthorized local actions: add scoped test probes and inspect consumers of named symbols.
- Stop for: permanent telemetry, persistent state, changed freshness behavior, or benchmark workload mismatch.

**Steps:**
- [ ] Step 1: Search all repository consumers of `PreparedTask.brief`, `prepare_lane_inputs()`, and `_worker_brief()`; classify each as production, compatibility, diagnostic, or test-only.
- [ ] Step 2: Instrument existing test seams with scoped wrappers that record operation counts and durations without adding runtime state.
- [ ] Step 3: Run representative canonical dispatches with zero, one, and two prerequisites; record plan-read, parse, preparation, render, Git command, Git count, Git duration, total preparation-to-launch-check duration, worker command equality, and failure-path outcomes. Repeat each latency workload five times.
- [ ] Step 4: Record whether duplicate brief construction or duplicate compatibility preparation is demonstrated, and identify the exact owner that can be simplified without weakening trust boundaries.

**Verification:**
- [ ] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: baseline probe passes; evidence identifies measured duplicate work or records `no optimization justified`.

**Exit Criteria:**
- P1 change decision is evidence-backed, reproducible, and bounded to existing invocation owners.

### Task 3: Apply measured P1 optimization

**Purpose:**
- Remove only proven duplicate local work while preserving all authority and freshness boundaries.

**Task Function:**
- Simplify execution-brief ownership and, only when proven, reuse stable invocation facts within one dispatch.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through Planning Dispatch from measured scope and regression risk.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: independently validate worker command, admission, freshness, lifecycle, and failure semantics.

**Specification Coverage:**
- One worker-handoff renderer owns final execution text.
- Compatibility adapter remains supported or is explicitly preserved as thin normalization.
- Mutable execution facts remain fresh at their trust boundaries.
- No new persistent state or orchestration layer appears.

**Required Skills:**
- `skill-code-standards`, `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:PreparedTask`, `scripts/project_os_runtime/plan_preparation.py:prepare_task`, `scripts/project_os_runtime/plan_preparation.py:prepare_lane_inputs`, `scripts/project_os_runtime/plan_preparation.py:_worker_brief`, `scripts/herdr_parallel_dispatch.py:verify_launch_bindings`, `scripts/herdr_main_launcher.py:_git_identity`
- Modify: only the named production symbols whose duplicate work Task 2 proves; update their focused tests in `tests/test_plan_preparation.py`, `tests/test_herdr_parallel_dispatch.py`, and `tests/test_herdr_main_launcher.py`
- Verify: same symbols and tests plus `docs/operating_system/runtime/runtime-surfaces.md` when the retained runtime contract is missing or inaccurate

**Dependencies:**
- Task 2 identifies a concrete duplicate and an owner-safe simplification.
- If no measurable duplicate is found, record `no optimization justified` and make no production change in this task.

**Authority:**
- Preauthorized local actions: edit named production/test symbols, run baseline and after probes, and update runtime wording when source behavior changed.
- Stop for: weaker prerequisite proof, stale mutable facts, changed acceptance/lifecycle semantics, new persistent state, or no measurable reduction.

**Steps:**
- [ ] Step 1: If `PreparedTask.brief` has no supported production consumer, remove competing execution rendering or retain it explicitly as a diagnostic projection while keeping `_worker_brief()` as the handoff owner.
- [ ] Step 2: If measured compatibility duplication is supported and safe, normalize legacy input once and delegate to `prepare_plan_lanes()`; otherwise leave compatibility behavior unchanged.
- [ ] Step 3: Re-run identical zero/one/two-prerequisite probes and compare operation counts, Git process count/duration, protected preparation-to-launch-check duration, worker command equality, stale-binding rejection, admission, and lifecycle outcomes.
- [ ] Step 4: Keep any change only when it removes at least one counted duplicate operation, or when latency-only work improves median protected preparation-to-launch-check time by at least 10% across five identical runs; preserve correctness evidence in both cases.

**Verification:**
- [ ] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: all focused tests pass; before/after evidence uses identical workloads and records either one removed duplicate operation, a median latency reduction of at least 10% across five runs, or `no optimization justified`.

**Exit Criteria:**
- P1 contains no speculative refactor. Mutable checks, authority, admission, freshness, lifecycle, and worker semantics remain unchanged.

### Task 4: Final verification and plan reconciliation

**Purpose:**
- Prove P0 closure, reconcile P1 evidence, and leave durable plan state for handoff.

**Task Function:**
- Run final repository proof and update this plan only after fresh verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: sequential fan-in verification owned by the lead controller.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository validators and focused tests provide independent evidence.

**Specification Coverage:**
- P0 payload contract, P1 measurement/optimization contract, documentation, and generated surfaces agree with source.
- No unrelated untracked artifact enters scope.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all Task 1–3 targets, `origin/main` history, and final Git diff
- Modify: `docs/superpowers/plans/2026-09-26-15-45-final-p0-closure-p1-optimization-plan.md` ledger, evidence, and status only after verification
- Verify: repository validators and diff checks

**Dependencies:**
- Tasks 1–3 complete.
- Final verification runs from the same clean execution worktree.

**Authority:**
- Preauthorized local actions: run listed checks, inspect changed-file scope, record evidence, and reconcile this plan.
- Stop for: failed required check, stale generated output, unrelated dirty change, source/plan disagreement, or unrecorded scope expansion.

**Steps:**
- [ ] Step 1: Run focused tests and full test suite.
- [ ] Step 2: Run planning lifecycle, repository-contract, adapter-sync, runtime-drift, and diff checks.
- [ ] Step 3: Confirm no unresolved template markers, no new management layer, exact P0 claim, bounded P1 claim, and one canonical owner per changed behavior.
- [ ] Step 4: Record exact outputs and deviations; mark tasks and plan `completed` only after `skill-verification-before-completion` returns `verified`.

**Verification:**
- [ ] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- [ ] `python -m pytest -q`
- [ ] `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- [ ] `python scripts/validate_repo_contracts.py --repo-root .`
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `python scripts/validate_agent_runtime_drift.py --all-platforms`
- [ ] `git diff --check`
- Expected: all required checks pass; no generated drift; no new workflow or unrelated file scope.

**Exit Criteria:**
- P0 is permanently closed after complete wrapped constraints reach the launcher payload.
- P1 evidence records retained optimization or `no optimization justified`.
- Plan status changes to `completed` only after fresh verification returns `verified`.

## Verification

- `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- `python -m pytest -q`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`

## Completion Criteria

1. Wrapped continuation lines for all four allowlisted shared constraints reach the actual launcher `--task` payload with normalized whitespace.
2. The allowlist remains exact; arbitrary prose and historical aliases remain excluded.
3. Selected task, goal, accepted prerequisites, required proof, exclusions, and non-duplication assertions pass.
4. Baseline and after P1 evidence use identical workloads and record named metrics.
5. The lead controller applies the P1 threshold: retain a change only after removing one counted duplicate operation or improving median protected preparation-to-launch-check time by at least 10% across five identical runs; freshness, authority, prerequisite proof, admission, lifecycle, settlement, recovery, acceptance, and worker semantics remain unchanged.
6. Required tests, validators, adapter checks, runtime-drift checks, and diff checks pass from the execution worktree.
7. No new persistent state, scheduler, cache service, runtime, worker-context subsystem, or unrelated scope enters the patch.
8. `skill-verification-before-completion` returns `verified` before plan status becomes `completed`.
