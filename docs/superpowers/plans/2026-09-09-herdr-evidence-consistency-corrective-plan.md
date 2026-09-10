---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: herdr-evidence-consistency-corrective
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
---

# Herdr Evidence Consistency Corrective Plan

## Goal

Fix remaining Herdr evidence defects found after `befaf744a819c84fcf5ad97162c43331ee3c1fe1` without reopening or editing earlier plans. Make delivery, execution, observation, task result, cleanup, and performance evidence independent and truthful. Preserve Codex ACK-and-return, DeepAgents MCP isolation, final pane validation, fresh MCP discovery, and unrelated workspace state.

This plan is new. Earlier plans `2026-09-09-launcher-reliability-performance-hardening-plan.md` and `2026-09-09-starter-verdict-follow-up-plan.md` remain historical and are not edited.

## Implementation Outcomes

- Terminal assignment results expose independent lifecycle facts and finalized performance data.
- DeepAgents markers correlate output but cannot prove worker exit or cleanup alone.
- Observer expiry stays observation evidence; execution timeout requires runtime enforcement proof.
- Performance phase names match measured boundaries; skipped phases are explicit.
- Canonical CoS/runtime instructions match launcher behavior and generated surfaces remain synchronized.
- Focused tests and bounded Windows/Herdr proof establish behavior or leave this plan blocked. Tool-call, streaming, and delegation behavior remain outside this corrective scope.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-receiving-code-review`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared launcher, tests, canonical docs, and managed generated surfaces; run focused tests, validators, sync checks, and bounded task-owned Windows/Herdr probes without authentication or external writes
- User-approval actions: commits, pushes, merges, authentication, external configuration writes, process termination outside task-owned probes, destructive cleanup, and edits outside declared targets
- Parallel ownership: none; launcher, tests, and docs share one evidence contract
- Sequential fallback: baseline, lifecycle correction, metrics publication, SSOT sync, runtime proof, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `befaf744a819c84fcf5ad97162c43331ee3c1fe1`
- Expected workspace: tracked tree clean; preserve every pre-existing unrelated tracked and untracked change; do not stage, delete, or rewrite unrelated state. Current known untracked paths include `.playwright-mcp/` and `db/`.
- Next action: none; plan complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline and contract map | `89 passed`; response/legacy field map recorded; all pre-existing paths preserved |
| Task 2 | `completed` | current | `codex` | Task 1 | lifecycle boundary tests | `92 passed`; independent lifecycle output and marker/live-worker regression coverage |
| Task 3 | `completed` | current | `codex` | Task 2 | final metrics tests and measurements | structured phase values, total duration, retry attribution, failure-output metrics verified |
| Task 4 | `completed` | current | `codex` | Tasks 1, 3 | canonical/generated parity | canonical docs updated; adapter sync and runtime drift checks passed |
| Task 5 | `completed` | current | `codex` | Tasks 2–4 | focused and bounded runtime proof | `herdr api snapshot` and bounded auto-target probe passed; six mocked boundary cases covered |
| Task 6 | `completed` | current | `codex` | Task 5 | final verification and preservation proof | final tests/validators passed; historical plans and unrelated paths preserved |

Only lead controller updates ledger. A checked item records accepted proof, not intent.

## Task Breakdown

### Task 1: Establish current contract

**Purpose:** Capture current source, tests, docs, and workspace state before edits.

**Files And Symbols:** Inspect `scripts/herdr_main_launcher.py:_deepagents_task_state`, `_deepagents_completion_evidence`, `_classify_codex_prompt_result`, `_main_body`; `tests/test_herdr_main_launcher.py`; `.agents/skills/skill-chief-of-staff/SKILL.md`; `docs/operating_system/planning/planning-dispatch.md`; `docs/operating_system/runtime/runtime-surfaces.md`; `docs/operating_system/procedures/runtime-adapter-procedure.md`. Do not edit earlier plans.

**Task Function:** Execute bounded repository work and verification for this task.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded single-lane change with direct tests and deterministic verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract and evidence review.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: read declared files, run baseline tests, inspect Git state, and record evidence in this plan.
- Stop for: unsafe workspace identity, unexpected tracked changes, missing base commit, or a request to edit historical plans.

**Steps:**
- [x] Confirm `HEAD` is `befaf744a819c84fcf5ad97162c43331ee3c1fe1` or reconcile base.
- [x] Snapshot every pre-existing tracked, unstaged, staged, and untracked path; preserve all unrelated state.
- [x] Run `py -3 -m pytest tests/test_herdr_main_launcher.py -q`.
- [x] Map every assignment JSON path and evidence owner.
- [x] Establish installed Herdr response semantics: rejection, acceptance, and uncertainty for `agent prompt` and `pane run`.
- [x] List compatibility fields affected by the result builder: `prompt_accepted`, `task_accepted`, `status`, `completion`, and `exit_code`; distinguish launcher exit code from worker exit code.
- [x] Identify canonical/generated ownership before doc edits.

**Verification:** `py -3 -m pytest tests/test_herdr_main_launcher.py -q`; `git status --short --branch`.

**Exit Criteria:** Baseline, response matrix, legacy-field map, and complete preservation snapshot recorded; earlier plans and unrelated state unchanged.

### Task 2: Separate lifecycle evidence

**Purpose:** Remove false implications between delivery, completion, execution, observation, and cleanup.

**Files And Symbols:** Modify `scripts/herdr_main_launcher.py:_main_body`, `_deepagents_task_state`, `_deepagents_completion_snapshot`, `_deepagents_completion_evidence`, and only required parts of `_classify_codex_prompt_result`; update lifecycle tests in `tests/test_herdr_main_launcher.py`.

**Task Function:** Execute bounded repository work and verification for this task.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded single-lane change with direct tests and deterministic verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract and evidence review.

**Dependencies:** Task 1 accepted.

**Authority:**
- Preauthorized local actions: edit launcher lifecycle code and focused tests; run mocked boundary tests.
- Stop for: generic cleanup, retry after uncertain ownership, unrelated pane termination, MCP policy changes, or Codex ACK-and-return changes.

**Contract:**
- One result builder emits independent `delivery`, `execution`, `observation`, `task_result`, and `cleanup` sections for success, rejection, uncertainty, timeout, failure, and cleanup uncertainty.
- Expected marker proves only that worker reported completion. Attributable worker exit proves execution terminated, with worker exit status only when available. Task-specific verification proves task result. Runtime cleanup proof proves descendant cleanup. Missing exit, verification, or cleanup evidence stays `unknown`.
- Marker is correlation evidence. Marker plus a live non-shell process, or marker plus an empty foreground list, cannot prove worker exit, task result, or cleanup.
- Nonzero `pane run` is `not_delivered` only on established rejection; otherwise delivery is `unknown` with reconciliation.
- Observation expiry never rewrites confirmed delivery or claims execution timeout without enforcement proof.
- Preserve compatible fields only when derived from these facts. `dispatch_id` stays constant for one dispatch operation; every actual launch attempt gets its own `attempt_id`. Observation, reconciliation, and retirement reference their attempt. A replacement attempt cannot overwrite prior attempt evidence.
- Executor-specific classifiers interpret Herdr responses; the common builder formats established facts. Launcher `exit_code` is not worker exit status.

**Steps:**
- [x] Add common result construction for all terminal paths and define derivation/removal of `prompt_accepted`, `task_accepted`, `status`, `completion`, and `exit_code`.
- [x] Preserve `last_observed_state` on failed or expired reads.
- [x] Record marker, attributable worker exit, task verification, and runtime cleanup as separate facts; never infer missing facts from an empty process list.
- [x] Keep cleanup `unknown`/`unverified` when runtime does not prove descendant exit.
- [x] Add tests for accepted long task, rejection, ambiguous acknowledgement, unavailable observation, marker/process conflict, worker exit without task verification, observer expiry, possible post-submit command failure, cleanup uncertainty, retry identity, and retry metric attribution.

**Verification:** `py -3 -m pytest tests/test_herdr_main_launcher.py -q` plus direct mocked success/failure boundary proof.

**Exit Criteria:** Lifecycle facts remain independent; no uncertain replay; MCP isolation and ACK-and-return remain unchanged.

### Task 3: Publish final performance evidence

**Purpose:** Make existing invocation-scoped metrics complete and usable without new infrastructure.

**Files And Symbols:** Modify `scripts/herdr_main_launcher.py:_metrics_snapshot`, `resolve_launch`, and `_main_body` only as required; update performance tests and `docs/operating_system/runtime/runtime-surfaces.md`.

**Task Function:** Execute bounded repository work and verification for this task.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded single-lane change with direct tests and deterministic verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract and evidence review.

**Dependencies:** Task 2 accepted.

**Authority:**
- Preauthorized local actions: edit existing metrics and tests, update metric contract docs, and run comparable local measurements.
- Stop for: persistent metrics storage, descendant accounting, unsupported thresholds, or polling optimization before baseline evidence.

**Contract:**
- Every terminal assignment, including preflight and target-resolution failure, includes finalized `performance` or explicit unavailable evidence. Dry-run output is identified as preparation evidence.
- Phase keys are `preflight`, `target_discovery`, `worker_initialization`, `delivery`, `observation`, and `retirement`.
- `delivery` excludes observation; `retirement` means launcher-owned retirement, not runtime cleanup.
- Each phase uses `{ "status": "measured|not_attempted|unavailable", "duration_ms": number|null }`; measured zero is valid, skipped phases use `duration_ms: null`.
- `worker_initialization` measures actual start/readiness operations, not argv preparation. Version probes and other preparation belong to a named phase. `delivery` excludes startup and observation; `observation` covers observer work only; `retirement` covers launcher retirement only.
- Include total invocation duration, retry aggregation, and per-attempt attribution. Counts are launcher command invocations, excluding worker, MCP, browser, and other descendants.

**Steps:**
- [x] Replace ambiguous acknowledgement timing with delivery and observation timings, and define version/preparation placement.
- [x] Finalize performance before every result, including preflight and target-resolution failures.
- [x] Preserve `ContextVar` metrics; add no parallel store.
- [x] Test success, rejection, uncertainty, timeout, and failure outputs.
- [x] Record comparable Codex/DeepAgents command counts, retry aggregation, total duration, and phase values without claiming a win.

**Verification:** `py -3 -m pytest tests/test_herdr_main_launcher.py -q`.

**Exit Criteria:** Final output carries truthful metrics; later optimization remains deferred unless identical workloads prove material benefit.

### Task 4: Align canonical runtime instructions

**Purpose:** Remove SSOT drift without editing historical plans.

**Files And Symbols:** Modify `.agents/skills/skill-chief-of-staff/SKILL.md`, `docs/operating_system/planning/planning-dispatch.md`, and metric wording in `docs/operating_system/runtime/runtime-surfaces.md` and `docs/operating_system/procedures/runtime-adapter-procedure.md`. Regenerate and explicitly authorize managed outputs selected by `scripts/sync_agent_adapters.py`. Do not edit earlier plans; this plan’s status and evidence may be updated.

**Task Function:** Execute bounded repository work and verification for this task.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded single-lane change with direct tests and deterministic verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract and evidence review.

**Dependencies:** Task 1 ownership map and Task 3 terminology.

**Authority:**
- Preauthorized local actions: edit canonical docs, run sync/drift checks, and inspect generated diffs.
- Stop for: manual generated-file edits, provider configuration changes, credentials, or historical-plan edits.

**Contract:** Numeric Codex wall-clock grants fail closed unless a named runtime owner proves interruption and cleanup enforcement. No unsupported `outer-watchdog` claim remains. Native Codex and existing DeepAgents numeric bounds remain supported. Generated outputs corresponding to changed canonical sources are in scope and must match those sources.

**Verification:** `py scripts/sync_agent_adapters.py --all-platforms --check`; `py scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`.

**Exit Criteria:** One canonical rule governs numeric Codex wall-clock support; no generated drift; old plans untouched.

### Task 5: Run focused and bounded proof

**Purpose:** Prove direct boundaries and supported Windows/Herdr behavior.

**Files And Symbols:** Inspect Task 2–4 diffs. Modify only tests for in-scope proof failures. Preserve earlier plans, every pre-existing unrelated tracked/untracked path, `.playwright-mcp/`, `db/`, external adapter files, credentials, and provider config.

**Task Function:** Execute bounded repository work and verification for this task.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded single-lane change with direct tests and deterministic verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract and evidence review.

**Dependencies:** Tasks 2–4 accepted.

**Authority:**
- Preauthorized local actions: run tests, validators, sync checks, generated-kit checks when affected, and bounded task-owned Windows/Herdr probes without authentication or destructive cleanup.
- Stop for: unavailable mandatory runtime evidence, shared-daemon termination, out-of-scope process termination, unrelated failure, or scope deviation.

**Probe Matrix:** Run bounded probes with expected outcomes: (1) Codex acknowledgement returns before observation; (2) observer expiry preserves confirmed delivery; (3) marker appears while worker remains live; (4) worker exits without sufficient task-result evidence; (5) command response is ambiguous after possible submission; (6) final metrics appear on success and failure. Use mocked responses for destructive or difficult faults, plus bounded live proof of the actual Herdr boundary. Tool-call, streaming, and delegation behavior are outside this corrective scope.

**Verification:**

```powershell
py -3 -m pytest tests/test_herdr_main_launcher.py -q
py scripts/validate_repo_contracts.py --repo-root . --fast
py scripts/validate_repo_config.py --repo-root .
py scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check
py scripts/sync_agent_adapters.py --all-platforms --check
git diff --check
```

**Exit Criteria:** Fresh automated checks pass and probe matrix evidence is recorded. Missing required Herdr-boundary proof leaves Task 5 `blocked`, not completed.

### Task 6: Final verification and handoff

**Purpose:** Reconcile source, tests, docs, generated surfaces, runtime proof, and Git state.

**Task Function:** Execute bounded repository work and verification for this task.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded single-lane change with direct tests and deterministic verification.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract and evidence review.

**Dependencies:** Task 5 complete and not blocked.

**Authority:**
- Preauthorized local actions: run final checks, inspect diff/status, confirm preserved artifacts, and update this plan ledger after accepted proof.
- Stop for: failed mandatory proof, stale status, unexpected tracked changes, generated drift, commit, push, merge, or destructive cleanup.

**Steps:**
- [x] Confirm fresh task-local proof and final assignment/performance output.
- [x] Confirm canonical/generated parity and untouched earlier plans.
- [x] Confirm every pre-existing unrelated path remains unchanged.
- [x] Run final checks once against unchanged candidate; rerun only checks invalidated by later edits.
- [x] Set this plan `status: completed` only after `skill-verification-before-completion` returns `verified`.

**Verification:** Run Task 5 commands plus `git status --short --branch`.

**Exit Criteria:** All criteria have fresh evidence; no task is pending, active, or blocked; no unrelated state changed.

## Non-Goals

- No edits to the earlier September 9 plans named in this document.
- No metrics service, cache, watcher, scheduler, janitor, or orchestration framework.
- No generic cleanup, uncertain replay, Codex watchdog implementation, or MCP/credential/provider changes.
- No polling optimization until finalized metrics and comparable baseline prove material benefit.
- No claim that source tests prove live Herdr behavior; tool-call, streaming, and delegation behavior are outside this corrective scope.

## Verification

Use focused launcher tests, repository contract/config validators, adapter sync/drift checks, `git diff --check`, and the six bounded Windows/Herdr probes. Mock destructive or difficult faults; prove the actual Herdr boundary separately. Preserve every pre-existing unrelated path.

## Completion Criteria

1. Terminal results independently report delivery, execution, observation, task result, cleanup, and final performance.
2. DeepAgents marker cannot prove cleanup while worker remains live.
3. Observation expiry does not become execution timeout without enforcement proof.
4. Possible post-submit `pane run` failure remains uncertain, not false rejection.
5. Performance phases match work; skipped phases are explicit; counts mean launcher invocations.
6. Numeric Codex wall-clock grants fail closed without named enforcement owner; no unsupported watchdog claim.
7. Canonical and generated instructions show no drift.
8. Focused, validator, sync, and mandatory Herdr-boundary proof pass; otherwise Task 5 is blocked.
9. Earlier plans and every pre-existing unrelated tracked/untracked path remain unchanged.
