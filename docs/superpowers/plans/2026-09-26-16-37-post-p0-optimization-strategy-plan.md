---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
name: post-p0-optimization-strategy
targets:
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - docs/superpowers/plans/2026-09-26-16-37-post-p0-optimization-strategy-plan.md
---

# Post-P0 Optimization Strategy

## Verdict Review

The supplied verdict is correct against remote `main` at `d001099`:

- P0 shared-constraint handoff remains closed and must not be reopened for
  naming, abstraction, or historical parser compatibility.
- PR #46 already removed duplicate `PreparedTask.brief` construction and left
  `_worker_brief()` as the sole worker-handoff renderer.
- The remaining measured P1 target is same-boundary Git/preflight process
  startup, especially launcher `_git_identity()`.
- Dispatcher ancestry checks and launcher identity checks are different trust
  boundaries. Sharing observations between them would weaken freshness proof.
- Existing latency numbers are fixture measurements, not production claims.
  Any latency claim needs fresh identical workloads and repeated runs.

This plan therefore scopes one bounded prototype: batch launcher-owned Git
identity facts without adding caching, a Git service, a runtime context store,
task-specific freshness, scheduler state, or another orchestration layer.

## Goal

Reduce protected launch-preflight cost by lowering unnecessary launcher-local
Git process startup while preserving dispatcher freshness checks, launcher
identity verification, failure classifications, worker command construction,
and all existing lifecycle and authority boundaries.

## Implementation Outcomes

### Same-boundary launcher Git batching

`_git_identity()` obtains launcher-owned repository facts through fewer native
Git process invocations while returning the same `worktree`, `repo_root`,
`git_common_dir`, `branch`, `head`, and `expected_base` values. The first
prototype batches only stable `rev-parse` facts that have identical ownership;
`git branch --show-current` and expected-base verification remain separate
until tests prove a combined form preserves detached-head and failure behavior.

### Regression and performance proof

Launcher tests cover exact output parsing, command failure, malformed batched
output, non-root worktrees, detached heads, and invalid expected bases.
Dispatcher tests prove expected-base and accepted-prerequisite ancestry checks
remain unchanged for zero, one, and two prerequisites. Five repeated before /
after measurements record process counts, Git wall time, protected
preparation-to-launch time, failure behavior, and worker-command equality.

### Evidence-based retention

Retain production changes only when they remove a counted launcher Git
operation or deliver a repeatable median protected-latency improvement of at
least 10% across five identical runs, with unchanged semantics. Otherwise
revert the prototype and record `no optimization justified` in this plan.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-performance-optimization`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `optional worktree based on origin/main d001099`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect listed source/tests, create temporary measurement probes outside the repository, edit listed files, run focused tests, full tests, validators, and bounded Windows/Linux-compatible probes
- User-approval actions: commits, pushes, merges, external runtime writes, destructive cleanup, or edits outside listed targets
- Parallel ownership: none; launcher, dispatcher, tests, measurements, and plan evidence share one acceptance boundary
- Sequential fallback: baseline first, then launcher prototype, then cross-boundary regression and repeated benchmark, then final verification and plan reconciliation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `unresolved until plan approval; execution base origin/main d001099`
- Base commit: `d00109926ab474bac66a26ce220df6b5dbad7760`
- Expected workspace: `clean isolated worktree`; current checkout retains unrelated untracked artifacts
- Next action: approve plan and create isolated execution worktree from `origin/main`
- Blockers: none for drafting; execution must not use current dirty checkout

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | isolated worktree | `unresolved` | none | baseline ownership, counts, and five-run measurements recorded | pending approval |
| Task 2 | `pending` | same worktree | `unresolved` | Task 1 | launcher-owned batching passes failure matrix without boundary changes | pending approval |
| Task 3 | `pending` | same worktree | `unresolved` | Task 2 | dispatcher invariants, repeated benchmark, and retain/revert decision recorded | pending approval |

## Scope Boundaries

Do not change:

- P0 plan parsing or shared-constraint allowlists.
- `prepare_plan_lanes()`, `PreparedLane`, runtime grants, admission, or
  settlement ownership.
- Dispatcher `merge-base --is-ancestor` checks for expected base or accepted
  prerequisites.
- Launcher-to-dispatcher trust boundaries or launcher identity requirements.
- Persistent caches, scheduler state, runtime context stores, Git libraries,
  new services, or new orchestration layers.
- Historical parser aliases or old execution artifacts.

## Task Breakdown

### Task 1: Establish Git preflight baseline and ownership map

**Purpose:**
- Prove current launcher and dispatcher Git operations before changing source.
- Separate launcher identity cost from dispatcher freshness cost.

**Task Function:**
- Measure current same-boundary process cost and failure behavior.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: baseline evidence is bounded and low ambiguity; resolve executor at activation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independent validation of command counts and preserved failure classes.

**Specification Coverage:**
- Pasted strategy sections “Optimize Git Launch Preflight”, “Preserve dispatcher freshness checks”, and “Benchmark the candidate correctly”.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_git_value`, `scripts/herdr_main_launcher.py:_git_identity`, `scripts/herdr_main_launcher.py:resolve_launch`
- Inspect: `scripts/herdr_parallel_dispatch.py:verify_launch_bindings`
- Inspect: `tests/test_herdr_main_launcher.py:test_git_identity_rejects_non_root_cwd`
- Inspect: `tests/test_herdr_parallel_dispatch.py` ancestry and stale-binding tests
- Modify: temporary probe outside repository only; no production source change
- Verify: current command sequence, returned identity mapping, failure classes, and zero/one/two-prerequisite counts

**Dependencies:**
- Remote `main` remains at `d001099`.
- Execution uses clean worktree based on `origin/main`.

**Authority:**
- Preauthorized local actions: run read-only inspection and temporary bounded probes against disposable Git fixtures.
- Stop for: base drift, required external access, trust-boundary change, or a probe that mutates repository state.

**Steps:**
- [ ] Step 1: Trace every `_git_identity()` caller and every dispatcher ancestry subprocess without editing source.
- [ ] Step 2: Create temporary probe `$env:TEMP\\post_p0_git_preflight_probe.py` on Windows or `$TMPDIR/post_p0_git_preflight_probe.py` on Linux from the existing test seam, then run identical zero, one, and two accepted-prerequisite workloads five times using the same Python executable and fixture shape; separate launcher and dispatcher command counts.
- [ ] Step 3: Record median Git wall time, protected preparation-to-launch time, returned identity values, worker command, and failure classifications in the Task 1 Evidence column and final verification output.

**Verification:**
- [ ] Temporary probe completes without repository mutation and reports five samples per workload.
- Expected: launcher identity calls and dispatcher ancestry calls are separately attributable; no semantic mismatch appears.

**Exit Criteria:**
- Baseline table and ownership map exist in plan evidence, with no production change justified before measurement.

### Task 2: Prototype launcher-owned `rev-parse` batching

**Purpose:**
- Reduce launcher-local Git process startup without sharing dispatcher observations.

**Task Function:**
- Replace repeated launcher-local `rev-parse` calls with one bounded native Git invocation for stable identity facts, while retaining independent branch and expected-base checks.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: narrow source change with security-sensitive failure semantics; resolve executor at activation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independent review of parser shape, detached-head behavior, and fail-closed errors.

**Specification Coverage:**
- Same-boundary batching only; launcher remains independent verifier.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_run_checked`, `scripts/herdr_main_launcher.py:_git_value`, `scripts/herdr_main_launcher.py:_git_identity`
- Modify: `scripts/herdr_main_launcher.py:_git_identity`; remove `_git_value` only after repository search confirms no remaining consumer
- Modify: `tests/test_herdr_main_launcher.py` Git identity regression tests
- Verify: `scripts/herdr_main_launcher.py:resolve_launch` uses unchanged identity contract

**Dependencies:**
- Task 1 baseline and failure matrix complete.
- No dispatcher result is passed into launcher as trusted input.

**Authority:**
- Preauthorized local actions: edit launcher and launcher tests, run focused tests, and inspect command output.
- Stop for: changed failure classification, detached-head semantic change, root/common-dir normalization change, or any dispatcher ownership change.

**Steps:**
- [ ] Step 1: Add a narrow parser/helper for one native `git rev-parse` invocation returning exactly repository root, common dir, and `HEAD` in fixed order.
- [ ] Step 2: Keep `git branch --show-current` and `git rev-parse --verify expected-base-ref^{commit}` as separate launcher-owned checks for this plan; do not combine them with the batched `rev-parse` call.
- [ ] Step 3: Preserve exact worktree-root rejection and relative `git_common_dir` resolution; fail closed on command failure, empty output, extra output, or malformed output.
- [ ] Step 4: Add tests for normal worktree, linked worktree common dir, detached `HEAD`, non-root cwd, invalid expected base, Git command failure, and malformed batched output.

**Verification:**
- [ ] `python -m pytest -q tests/test_herdr_main_launcher.py -k "git_identity or resolve_launch"`
- Expected: identity mapping and `LaunchBlocked` behavior match baseline; launcher command receives same `head` and expected-base facts.

**Exit Criteria:**
- Prototype reduces launcher-local process count or is reverted before Task 3 retention measurement.

### Task 3: Prove cross-boundary invariants and make retain/revert decision

**Purpose:**
- Demonstrate that batching improves measured cost without weakening freshness, authority, or worker behavior.

**Task Function:**
- Run cross-boundary regressions and identical repeated benchmarks, then retain or revert the prototype.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: evidence synthesis across source, tests, and runtime measurements.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independent acceptance gate for semantics, operation count, and latency claims.

**Specification Coverage:**
- Definition of Done: semantic checks unchanged, ownership unchanged, failure classifications unchanged, worker command unchanged, no persistent state, measured benefit, Windows and Linux contracts pass.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:verify_launch_bindings`, `scripts/herdr_main_launcher.py:resolve_launch`
- Modify: `tests/test_herdr_parallel_dispatch.py` with a focused dispatcher ancestry command-sequence regression
- Modify: this plan’s evidence and decision ledger
- Verify: `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`, focused tests, full suite, and repository validators

**Dependencies:**
- Task 2 focused tests pass.
- No new commit, generated output, or external runtime write exists before final verification.

**Authority:**
- Preauthorized local actions: run five-run probes, add focused regression tests, update plan evidence, and revert task-owned prototype edits when acceptance threshold fails.
- Stop for: any changed dispatcher ancestry result, stale-binding classification, worker command, lifecycle result, or unresolved benchmark variance.

**Steps:**
- [ ] Step 1: Add a dispatcher test that proves expected-base plus zero, one, and two accepted-prerequisite ancestry checks retain command order, count, and failure classification.
- [ ] Step 2: Repeat the exact Task 1 workloads five times before and after prototype with the temporary probe `$env:TEMP\\post_p0_git_preflight_probe.py`, recording launcher count, dispatcher count, total Git count, Git wall time, protected preparation-to-launch median, failure outcomes, and worker-command/task-text equality.
- [ ] Step 3: Run equivalent Linux CI workloads and confirm Windows and Linux contract checks pass.
- [ ] Step 4: Retain only a clear operation-count reduction or at least 10% median protected-latency improvement with unchanged semantics; otherwise revert production prototype and record `no optimization justified` in the Task 3 Evidence column.

**Verification:**
- [ ] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_plan_preparation.py`
- [ ] Windows: `python $env:TEMP\\post_p0_git_preflight_probe.py --runs 5 --prerequisites 0,1,2`
- [ ] Linux: `python $TMPDIR/post_p0_git_preflight_probe.py --runs 5 --prerequisites 0,1,2`
- Expected: dispatcher checks remain unchanged; launcher operation count drops or protected median improves by at least 10%; no failure or worker-command drift.

**Exit Criteria:**
- Production change is retained only with evidence-backed benefit; plan records exact measurements, deviations, and residual risks.

## Verification

- `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_plan_preparation.py`
- `python -m pytest -q`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`
- Windows and Linux five-run zero/one/two-prerequisite benchmark with recorded operation counts and medians

## Completion Criteria

1. P0 remains closed; no P0 parser or plan-to-dispatch architecture changes enter this scope.
2. Dispatcher expected-base and accepted-prerequisite ancestry checks remain independent and semantically unchanged.
3. Launcher `_git_identity()` preserves root, common-dir, branch, `HEAD`, expected-base, detached-head, and failure behavior.
4. No dispatcher observations cross the launcher trust boundary.
5. No persistent cache, service, scheduler, runtime context store, task-specific freshness, or new orchestration layer enters the patch.
6. Five repeated identical workloads record launcher, dispatcher, and total Git process counts plus protected latency for zero, one, and two prerequisites.
7. The production change is retained only after operation-count or latency threshold proof; otherwise `no optimization justified` is recorded and current behavior remains.
8. Focused tests, full suite, planning validator, repository-contract validator, adapter sync, runtime drift, diff check, and Windows/Linux contract checks pass.
9. `skill-verification-before-completion` returns `verified` before this plan becomes `completed`.
