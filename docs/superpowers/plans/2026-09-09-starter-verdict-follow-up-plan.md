---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: starter-verdict-follow-up
targets:
  - scripts/setup_hooks.sh
  - scripts/setup_hooks.ps1
  - scripts/validate_repo_contracts.py
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - tools/local-patch-hub/Start-OpenDesignMcp.ps1
  - tests/test_setup_hooks.py
  - tests/test_validate_repo_contracts.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_open_design_local_patch.py
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Starter Verdict Follow-Up

## Goal

Close confirmed reliability defects from the September 9, 2026 verdict review,
make launcher lifecycle evidence truthful, and reduce hot-path work only when
fresh measurements prove benefit. Preserve existing MCP isolation, ownership
checks, generated-surface rules, and unrelated workspace changes.

This plan is a follow-up to
`docs/superpowers/plans/2026-09-09-launcher-reliability-performance-hardening-plan.md`.
It owns only gaps still present at `a17280d`; overlapping pending lifecycle
work in that plan must be reconciled before execution, not implemented twice.

## Implementation Outcomes

### Portable local hooks and validator correctness

Bash and PowerShell hook installers resolve the effective Git hook directory,
work in linked worktrees and configured `core.hooksPath`, and generate hooks
that resolve repository root at invocation time. Tier synchronization runs
without `NameError`. Focused tests cover both defects.

### Truthful launcher lifecycle

Codex dispatch separates delivery acknowledgement from later observation. A
numeric Codex wall-clock grant is either enforced by a named existing owner or
rejected before dispatch; no result claims `outer-watchdog` without proof.
DeepAgents keeps bounded worker and cleanup ownership. Delivery, execution,
observation, and cleanup remain independent evidence fields.

### Bounded startup and measured efficiency

OpenDesign never starts after its readiness deadline. DeepAgents normal launch
does not scan and delete unrelated old runtime directories. Validator scans
avoid known dependency trees and unnecessary full-file reads. Immutable
capability evidence is reused only within one controller turn and only after
baseline evidence supports it.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, tests, canonical docs, and plan state; run focused tests, validators, generated-surface checks, and bounded task-owned runtime probes; preserve unrelated dirty and untracked workspace state
- User-approval actions: authentication, external configuration writes, process termination outside task-owned probes, commits, pushes, merges, destructive cleanup, and edits outside listed targets
- Parallel ownership: none; lifecycle, hook, validator, and generated-doc contracts overlap
- Sequential fallback: baseline and reconciliation, correctness repairs, lifecycle contract, OpenDesign and cleanup guards, measured optimization, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `a17280d`
- Expected workspace: preserve current unrelated changes in `.agents/skills/skill-disposable-artifact-cleanup/SKILL.md`, generated disposable-cleanup adapters, `.playwright-mcp/`, `db/`, and `docs/superpowers/plans/2026-09-09-cleanup-audit-routing-extension-plan.md`; do not stage, delete, or rewrite them
- Next action: run final verification and reconcile accepted evidence
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | requirement mapping and baseline tests | ownership mapping reconciled; unrelated workspace state preserved |
| Task 2 | `completed` | current | `codex` | Task 1 | hook portability, tier-sync, and validator tests | hook/validator suite `21 passed`; `bash -n`, PowerShell parse, and temporary configured-hook-path proof passed |
| Task 3 | `completed` | current | `codex` | Task 2 | lifecycle contract and timeout ownership tests | launcher suite `89 passed`; Codex ACK/observation split and numeric-grant rejection covered |
| Task 4 | `completed` | current | `codex` | Task 3 | OpenDesign deadline and runtime-cleanup tests | OpenDesign/dcode suite `97 passed`; deadline and exact-cleanup behavior covered |
| Task 5 | `completed` | current | `codex` | Tasks 2–4 | measurement and explicit deferrals | no speculative cache/orchestration shipped; deferrals and re-entry gates recorded |
| Task 6 | `completed` | current | `codex` | Task 5 | full focused proof, validators, and diff checks | `462 passed`; repository contract/config/planning/runtime/adapter validators passed; `git diff --check` passed |

## Task Breakdown

### Task 1: Establish baseline and reconcile overlapping plan work

**Purpose:**
- Freeze current source and workspace facts before edits.
- Prevent duplicate implementation against the active launcher-hardening plan.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded task contract with source-first implementation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent proof of task-specific correctness and preserved invariants.

**Files And Symbols:**
- Inspect and update `docs/superpowers/plans/2026-09-09-launcher-reliability-performance-hardening-plan.md`.
- Inspect `scripts/herdr_main_launcher.py` dispatch and observation paths.
- Inspect current Git status and existing focused tests.

**Requirement Ownership Mapping:**

| Requirement | Owning task | Required proof |
| --- | --- | --- |
| Attempt identity spans delivery, observation, reconciliation, and retirement | Task 3 | assignment and observation evidence share one attempt ID; retry creates a new ID |
| Completion evidence is attributable; stale, echoed, idle, or blocked output cannot prove success | Task 3 | focused marker/state tests and one bounded runtime probe |
| Acknowledged delivery and last observed execution facts survive later observation failure | Task 3 | accepted-task plus unavailable-read test preserves both facts |
| Final selected-pane validation remains immediately before launch | Task 3 | launcher tests assert final pane/cwd/process validation before submission |

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: inspect source, plans, Git status, and run baseline focused tests.
- Stop for: request to discard existing changes, unresolved ownership of overlapping plan tasks, or a new required behavior not covered by this plan.

**Steps:**
- [x] Record current `git status --short` and base commit.
- [x] Run the focused baseline suite.
- [x] Compare existing plan Tasks 4–6 with current source.
- [x] Transfer every unfinished requirement through the mapping above into one owning task and required proof.
- [x] Update both plan ledgers only after ownership and proof are recorded; do not supersede requirements by task status alone.
- [x] Record baseline subprocess, dispatch, observation, and cleanup evidence when bounded runtime probes are available; no additional live probe was required for this follow-up.

**Verification:**

```powershell
py -3 -m pytest tests/test_setup_hooks.py tests/test_validate_repo_contracts.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_open_design_local_patch.py -q
```

Expected: baseline result recorded; unrelated workspace state unchanged.

**Exit Criteria:**
- One plan owns each overlapping lifecycle change.
- Baseline evidence and preserved workspace state are recorded.

### Task 2: Repair hook portability and validator defects

**Purpose:**
- Remove confirmed command failures before performance work.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded task contract with source-first implementation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent proof of task-specific correctness and preserved invariants.

**Files And Symbols:**
- Modify `scripts/setup_hooks.sh` and `scripts/setup_hooks.ps1`.
- Modify `scripts/validate_repo_contracts.py:_analyze_metadata_file`, `_iter_files_pruned`, and `sync_starter_kit_distribution_tier`.
- Modify `tests/test_setup_hooks.py` and `tests/test_validate_repo_contracts.py`.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit hook installers, validator, and focused tests; run shell syntax, PowerShell parse, and local temporary-repository checks.
- Stop for: direct edits to generated adapters, hook behavior that bypasses the canonical validator, or inability to test linked-worktree behavior without destructive Git operations.

**Steps:**
- [x] Resolve hook installation path with `git rev-parse --git-path hooks`; stop assuming `.git` is a directory.
- [x] Keep generated hook heredoc self-contained: resolve `repo_root` inside hook invocation.
- [x] Resolve virtual-environment Python paths from `repo_root`, not caller CWD.
- [x] Replace undefined `in_kit` with `distributed_paths`.
- [x] Check metadata-capable suffix before reading files.
- [x] Limit Python metadata reads to the first 30 lines; preserve Markdown front-matter behavior.
- [x] Prune `.venv`, `node_modules`, `.tox`, `.nox`, and other confirmed dependency/runtime trees from repository scans without skipping explicit manifest paths.
- [x] Test explicit manifest paths inside pruned dependency trees remain scanned.
- [x] Add tests for generated-hook variables, effective hook path, tier sync, and scan pruning.

**Verification:**

```powershell
py -3 -m pytest tests/test_setup_hooks.py tests/test_validate_repo_contracts.py -q
sh -n scripts/setup_hooks.sh
```

Also run PowerShell parse validation and a temporary linked-worktree/configured-
`core.hooksPath` installation check when the host supports them.

**Exit Criteria:**
- Hook installation works in normal and linked worktrees.
- Tier sync completes without exception.
- Validator reads only eligible files and preserves classification coverage.

### Task 3: Make lifecycle and timeout evidence truthful

**Purpose:**
- Prevent acknowledged delivery from being confused with completion.
- Remove unsupported Codex watchdog claims.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded task contract with source-first implementation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent proof of task-specific correctness and preserved invariants.

**Files And Symbols:**
- Modify `scripts/herdr_main_launcher.py` runtime-grant normalization, Codex dispatch, completion observation, and lifecycle result construction.
- Modify `tests/test_herdr_main_launcher.py`.
- Update lifecycle ownership text in `docs/operating_system/runtime/runtime-surfaces.md` after reconciling the existing hardening plan.

**Dependencies:**
- Task 1 complete.
- Task 2 may run first but is not technically required.

**Authority:**
- Preauthorized local actions: edit launcher lifecycle fields and tests; run mocked dispatch/observation tests and bounded task-owned pane probes.
- Stop for: claiming strict timeout enforcement without a named owner, automatic replay after uncertain delivery, weakening process/marker validation, or terminating non-owned processes.

**Steps:**
- [x] Define independent `delivery`, `execution`, `observation`, and `cleanup` evidence fields.
- [x] Preserve compatible `prompt_accepted`, `submission`, and `status` fields through one result-construction path; derive them from the independent fields.
- [x] Return successful Codex dispatch after prompt acknowledgement and identity proof; move completion reads to explicit observation.
- [x] Preserve acknowledgement when later observation is unavailable; never convert observation timeout into delivery failure.
- [x] Verify whether an existing runtime owner enforces numeric Codex wall-clock grants.
- [x] If no owner exists, reject non-native strict Codex wall-clock grants before worker creation or prompt submission; never fall back silently to `native` and remove `outer-watchdog` claims.
- [x] Preserve DeepAgents worker timeout and exact cleanup ownership.
- [x] Add tests for accepted long-running tasks, rejected prompts, ambiguous acknowledgement, lost acknowledgement with no replay, unsupported grants with zero launch side effects, observation failure, deadline expiry, and controlled cleanup failure.

**Verification:**

```powershell
py -3 -m pytest tests/test_herdr_main_launcher.py -q
```

Required bounded probes: acknowledged long task, unavailable observation, deadline
expiry, verified cleanup, and controlled cleanup failure. A deadline may produce
`execution: timed_out` with `cleanup: unverified` and
`reconciliation_required: true`; later dispatch or retirement may be blocked
without erasing timeout evidence.

**Exit Criteria:**
- No numeric Codex grant reports `outer-watchdog` without enforcement proof.
- Delivery remains independent from completion and observation.
- No uncertain state triggers replay or unrelated process termination.

### Task 4: Close startup and runtime cleanup gaps

**Purpose:**
- Enforce remaining deadlines and remove destructive age-based work from launch.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded task contract with source-first implementation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent proof of task-specific correctness and preserved invariants.

**Files And Symbols:**
- Modify `tools/local-patch-hub/Start-OpenDesignMcp.ps1` startup lock/start path.
- Modify `scripts/dcode_project.py:_cleanup_stale_direct_mcp_runtimes` call path.
- Modify `tests/test_open_design_local_patch.py` and `tests/test_dcode_project.py`.

**Dependencies:**
- Task 3 complete for shared lifecycle terminology.

**Authority:**
- Preauthorized local actions: edit startup and cleanup code; run PowerShell contract tests and task-owned bounded runtime probes.
- Stop for: killing shared OpenDesign daemons, deleting directories without ownership/liveness evidence, or replacing exact cleanup with a generic janitor.

**Steps:**
- [x] Check remaining readiness budget immediately before `Start-Process`.
- [x] Preserve one monotonic deadline, mutex recheck, warm path, dynamic endpoint discovery, and final handoff timeout.
- [x] Remove age-based stale-runtime sweeping from normal direct-MCP launch.
- [x] Retain exact-attempt cleanup in `finally`.
- [x] Add explicit recovery evidence or a manual recovery path for abandoned runtimes; age alone must not prove abandonment.
- [x] Test deadline exhaustion after mutex wait and preservation of unrelated runtime directories.

**Verification:**

```powershell
py -3 -m pytest tests/test_open_design_local_patch.py tests/test_dcode_project.py -q
```

Run bounded isolated cold/warm startup probes only when shared daemon ownership
is clear. Preserve shared daemons and unrelated runtime directories.

**Exit Criteria:**
- OpenDesign never starts after readiness budget expiry.
- Normal launch performs no generic age-based deletion.
- Exact task-owned cleanup remains verified.

### Task 5: Measure and gate efficiency changes

**Purpose:**
- Avoid speculative caches and orchestration layers.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded task contract with source-first implementation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent proof of task-specific correctness and preserved invariants.

**Files And Symbols:**
- Inspect and, only when justified, modify `scripts/herdr_main_launcher.py:resolve_launch` and validator scan helpers.
- Keep canonical execution-plan and coordination skills outside this follow-up; no context-policy rewrite is justified by current measurements.

**Dependencies:**
- Tasks 2–4 complete.

**Authority:**
- Preauthorized local actions: add existing-evidence timing fields, run comparable probes, and make bounded source/doc changes supported by measurements.
- Stop for: persistent cache databases, watchers, heartbeat services, schedulers, background janitors, or optimization without invalidation and regression proof.

**Baseline Contract:**
- Environment: Windows host, current `main` at `a17280d`, same Herdr/OpenDesign versions, same repository state.
- Workloads: Codex and DeepAgents dispatch; concurrency `1` and `2`; OpenDesign cold and warm; validator clean and dirty trees.
- Metrics: dispatch p50/p95, subprocess count, observation delay, cleanup success, validator wall time, and context bytes/read volume.
- Reliability gate: required behavior and regression proof.
- Deterministic work reduction gate: demonstrably less work with equivalent coverage.
- Caching or polling gate: measured benefit, explicit invalidation, and completion-detection delay within 2 seconds of baseline.
- Capture at least 5 repetitions after 1 warm-up run for each workload; report median and p95.
- No optimization ships when comparable evidence is unavailable; record deferral and re-entry condition.

**Steps:**
- [x] Add phase timings and subprocess counts to existing evidence, not a parallel metrics store.
- [x] Defer turn-scoped capability reuse; no existing invalidation boundary justifies new shared state.
- [x] Keep Git HEAD, worktree, pane, process, lane ownership, delivery, and MCP inventory fresh.
- [x] Defer adaptive observation polling; no measured benefit justifies changing polling semantics.
- [x] Defer progressive plan disclosure and policy deduplication; revisit only if context measurements show material cost.
- [x] Defer context-policy and orchestration deduplication; revisit only after context measurements show material cost and canonical owners are mapped.
- [x] Confirm canonical skills and generated adapters need no changes for this follow-up.
- [x] Record every deferred optimization with reason and required trigger.

**Verification:**

Use identical before/after workloads and report metric, environment, sample,
and threshold. Run focused tests and adapter drift checks for any canonical
skill change.

**Exit Criteria:**
- Every shipped optimization has comparable evidence.
- Unsupported cache or orchestration additions remain absent.
- Deferred work has a measurable re-entry condition.

### Task 6: Final verification and handoff

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification-only task.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: final evidence and preserved workspace state need independent review.


**Purpose:**
- Prove source, tests, docs, generated surfaces, and workspace boundaries agree.

**Dependencies:**
- Tasks 1–5 complete.

**Authority:**
- Preauthorized local actions: run declared tests, validators, adapter checks, bounded probes, and diff inspection; update this plan's evidence and ledger.
- Stop for: failed required proof, stale lifecycle claims, generated drift, unrelated workspace mutation, commits, pushes, merges, or destructive cleanup.

**Steps:**
- [x] Run focused launcher, hook, validator, cleanup, and OpenDesign tests.
- [x] Run repository contract/config/planning validators.
- [x] Run adapter parity checks if canonical skills changed.
- [x] Run generated Starter-kit validation if manifest or distributed metadata changed.
- [x] Run `git diff --check` and confirm unrelated dirty/untracked artifacts remain unchanged.
- [x] Record fresh evidence and promote plan to `completed` after accepted final verification.

**Verification:**

```powershell
py -3 -m pytest tests/test_setup_hooks.py tests/test_validate_repo_contracts.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_open_design_local_patch.py -q
py -3 scripts/validate_repo_contracts.py --repo-root . --fast
py -3 scripts/validate_repo_config.py --repo-root .
py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
py -3 scripts/sync_agent_adapters.py --all-platforms --check
git diff --check
git status --short
```

Expected: focused tests and validators pass; generated surfaces remain aligned;
unrelated existing changes remain preserved.

## Non-Goals

- No new cache database, runtime ledger, watcher, heartbeat service, scheduler,
  reservation service, or background janitor.
- No reopening of completed MCP-isolation architecture or OpenDesign pipe
  discovery without new baseline evidence.
- No automatic retry after uncertain delivery, observation, or cleanup.
- No generic process termination or age-only runtime deletion.
- No live authentication, external configuration writes, commit, push, merge,
  or destructive cleanup.

## Verification

- Baseline and final focused test suites.
- Repository contract/config/planning validation.
- Adapter parity when canonical skills change.
- Bounded OpenDesign and launcher probes where task-owned evidence is available.
- Comparable performance evidence for every shipped optimization.
- `git diff --check` and preserved workspace-state proof.

## Completion Criteria

1. Hook installers support normal repositories, linked worktrees, and configured hook paths.
2. Generated hooks resolve repository root at invocation and use canonical validator.
3. Tier synchronization and validator scan paths complete without known exceptions.
4. Codex delivery, execution, observation, and cleanup evidence remain independent.
5. Numeric Codex wall-clock grants are enforced by a named owner or rejected; no unsupported `outer-watchdog` claim remains.
6. DeepAgents retains bounded worker and exact cleanup ownership.
7. OpenDesign never starts after readiness deadline; warm/cold ownership semantics remain intact.
8. Normal DeepAgents launch performs no generic age-based runtime deletion.
9. Shipped performance changes meet stated measurement threshold or remain explicitly deferred.
10. Canonical docs, generated adapters, tests, validators, and source agree.
11. Existing unrelated workspace changes remain untouched.

The plan is `completed` for this authorized execution. Fresh verification accepted
the source, tests, validators, generated surfaces, and preserved workspace state.
