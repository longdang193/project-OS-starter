---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: completion-monitoring-convergence
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - scripts/benchmark_completion_monitoring.py
  - artifacts/completion-monitoring/next-convergence-evidence.json
  - docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md
  - docs/superpowers/plans/2026-09-27-completion-monitoring-convergence-plan.md
---

# Completion Monitoring Convergence

## Verdict Review

The verdict correctly moves the next optimization into completion monitoring.
PR #49 remains retained. Dispatch contracts, prompt compression, runtime-binding
reduction, selected-pane changes, worker changes, and plan-preparation changes
remain frozen because current evidence does not justify reopening them.

Current source evidence at `d797028` confirms two defects:

- `detection_delay_ms` is `receipt_observed_at - monitoring_started_at`; it is
  time to receipt, not receipt detection latency.
- `_deepagents_completion_snapshot()` runs synchronous `process-info` and
  `pane read` commands. Each can inherit `_HERDR_COMMAND_TIMEOUT` (`30.0s`),
  so receipt polling cannot run while either command blocks.

The next change must bound optional diagnostics, recheck authoritative receipt
state between diagnostic phases, and preserve lifecycle, settlement, cleanup,
reconciliation, fallback, and stale-attempt behavior.

## Goal

Reduce receipt-blocking completion-monitoring latency without changing worker
lifecycle classification, receipt authority, settlement deadlines, cleanup,
reconciliation, or stale-attempt protection. Correct monitoring evidence so
future optimization decisions use truthful duration names and monotonic
elapsed-time calculations.

## Implementation Outcomes

### Bounded receipt-first monitoring

`_deepagents_completion_evidence()` gives each optional diagnostic command a
small completion-specific timeout, capped by remaining observation deadline.
The global `_HERDR_COMMAND_TIMEOUT` remains unchanged. Receipt is checked after
each diagnostic phase; once confirmed, later pane diagnostics are skipped and
receipt-derived lifecycle state wins.

### Truthful timing evidence

Monitoring evidence replaces `detection_delay_ms` with `time_to_receipt_ms` and
adds `receipt_to_completion_return_ms`. Duration values use `time.monotonic()`.
Human-readable wall-clock fields remain only where needed for artifact review.
No synthetic receipt-publication timestamp or production
`receipt_detection_delay_ms` is added.

### Regression and comparison proof

Focused tests reproduce stalled `process-info` and `pane read` behavior,
prove timeout capping and receipt rechecks, and prove unchanged fallback and
settlement semantics. A deterministic before/after evidence artifact records
fixed cadence, command budgets, subprocess counts, receipt timing, lifecycle,
cleanup, reconciliation, and mismatch results.

### Historical plan SSOT

The completed worker-contract experiment plan no longer appears actionable.
It is marked `superseded` and points to this plan plus its canonical evidence,
without rewriting historical results.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-performance-optimization`, `skill-backend-verification`, `skill-writing-plans`, `skill-verification-before-completion`
- Isolation: current workspace; temporary baseline module loading uses `tempfile.TemporaryDirectory()` and does not mutate Git state
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect and edit the named launcher, benchmark runner, focused test, evidence artifact, and historical plan; update this plan ledger; resolve `unresolved` profiles through Planning Dispatch before activation; run declared local tests, probes, validators, and read-only Git commands; preserve unrelated untracked files
- User-approval actions: push, merge, publication, branch retargeting, destructive recovery, discard, cleanup, external worker runs, and changes outside listed targets
- Parallel ownership: none; launcher and focused tests share one behavioral contract
- Sequential fallback: baseline and root-cause proof, then runtime patch, then focused regression proof, then deterministic comparison evidence, then SSOT cleanup, then final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `d797028fc00d022b9541ddf1e612e4b2e223f25e`
- Expected workspace: `main` clean except preserved untracked `.playwright-mcp/`, `db/`, and `docs/superpowers/plans/2026-09-27-completion-monitoring-convergence-plan.md`
- Next action: build deterministic baseline/candidate convergence evidence
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline launcher tests and source/caller map | `182 passed`; HEAD `d797028`; shared callers mapped; preserved untracked files unchanged |
| Task 2 | `completed` | current | `codex` | Task 1 | bounded diagnostic commands, receipt-first ordering, monotonic metrics | `186 passed`; stalled receipt path fixed after root-cause trace; global timeout and cadence unchanged |
| Task 3 | `completed` | current | `codex` | Task 2 | focused stalled-diagnostic and fallback regressions | `python -m pytest -q tests/test_herdr_main_launcher.py`; `186 passed`; red/green proof recorded in test history |
| Task 4 | `completed` | current | `codex` | Task 3 | deterministic before/after monitoring evidence | 36 rows; zero lifecycle/cleanup/reconciliation mismatches; candidate receipt-case max `0.65s` vs baseline `2.1s` |
| Task 5 | `completed` | current | `codex` | Task 4 | historical plan marked `superseded` with canonical pointer | old plan superseded; pointer and both evidence artifacts recorded |
| Task 6 | `completed` | current | `codex` | Task 5 | full focused suite, repository validators, diff hygiene | `315 passed`; planning, repo-contract, adapter, runtime-drift, JSON, and diff checks passed |

## Task Breakdown

### Task 1: Freeze baseline and confirm shared root cause

**Purpose:**
- Record current test and workspace state before runtime edits.
- Confirm every caller and test seam for `_deepagents_completion_snapshot()` and `_deepagents_completion_evidence()`.

**Task Function:**
- Establish source-of-truth baseline and diagnostic control-flow map.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: direct source inspection and bounded local verification; no delegation needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: baseline is source-first and command-verifiable.

**Specification Coverage:**
- Verdict root cause: synchronous diagnostic commands block receipt observation.
- Scope boundary: completion monitoring only; no dispatcher, worker, or runtime-binding redesign.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_run`, `_deepagents_completion_snapshot`, `_deepagents_completion_evidence`, `_read_deepagents_receipt`
- Inspect: `tests/test_herdr_main_launcher.py` completion snapshot/evidence tests and receipt assertions
- Verify: `git status --short --branch`, `git show -s --format='%H %s' HEAD`

**Dependencies:**
- Repository remains at `main` on `d797028` with unrelated `.playwright-mcp/` and `db/` untracked files preserved.

**Authority:**
- Preauthorized local actions: read named source/tests, run baseline tests and read-only Git commands, and record findings in this plan
- Stop for: dirty tracked files, changed base commit, missing test command, or any requested scope outside completion monitoring

**Steps:**
- [x] Step 1: Run `git status --short --branch` and confirm only `.playwright-mcp/`, `db/`, and this proposed plan are untracked.
- [x] Step 2: Run `python -m pytest -q tests/test_herdr_main_launcher.py` and record the baseline result.
- [x] Step 3: Trace all source and test callers with `rg -n "_deepagents_completion_snapshot|_deepagents_completion_evidence|detection_delay_ms" scripts tests`.
- [x] Step 4: Record the current diagnostic order: receipt read, synchronous diagnostic snapshot, next receipt read; record `_HERDR_COMMAND_TIMEOUT = 30.0` and fixed cadence values `0.1s` receipt polling and `2.0s` diagnostics.
- [x] Step 5: Record the baseline revision as `d797028`; Task 4 will load this revision through `git show` into a temporary module so baseline and candidate use one deterministic harness after the runtime patch.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: baseline suite passes; no tracked workspace changes exist before Task 2.

**Exit Criteria:**
- Baseline result, exact shared callers, current metric fields, timeout constants, and preserved workspace state are recorded.

### Task 2: Bound diagnostics and correct monitoring metrics

**Purpose:**
- Make optional diagnostics unable to block observation for the global Herdr command timeout.
- Ensure receipt authority is checked between expensive diagnostic phases.
- Replace misleading elapsed-time naming and wall-clock duration arithmetic.

**Task Function:**
- Patch the shared completion-monitoring owner without changing lifecycle or settlement contracts.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: one shared runtime owner, one sequential behavior change, high correctness sensitivity.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: Task 3 owns independent regression proof.

**Specification Coverage:**
- Add `_DEEPAGENTS_DIAGNOSTIC_COMMAND_TIMEOUT = 0.5` beside completion-monitoring constants.
- Pass `min(_DEEPAGENTS_DIAGNOSTIC_COMMAND_TIMEOUT, remaining observation deadline)` to each `process-info` and `pane read` command.
- Do not change `_HERDR_COMMAND_TIMEOUT` or worker/attempt deadlines.
- Split or phase the existing snapshot flow so `_deepagents_completion_evidence()` checks receipt before diagnostics, after `process-info`, and before `pane read`; confirmed receipt skips remaining diagnostics.
- Keep diagnostic timeout as observer-unavailable evidence, never worker failure. Expired deadlines skip commands rather than passing zero or negative timeouts.
- Preserve missing-receipt fallback, terminal-process evidence, settlement grace, cleanup, reconciliation, and stale-attempt checks.
- Replace `detection_delay_ms` with `time_to_receipt_ms` and calculate it from monotonic elapsed time.
- Add `receipt_to_completion_return_ms`, also monotonic; retain only explicitly needed wall-clock timestamps as `monitoring_started_at`, `receipt_observed_at`, and `completion_returned_at`.
- Do not add `receipt_detection_delay_ms` without a receipt-contract publication timestamp.
- Keep `_deepagents_completion_snapshot()` callable with its current positional/keyword contract and preserve its monkeypatch seam; optional phase support must default to existing all-phase behavior and `_deepagents_completion_evidence()` must not bypass the seam.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`
- Modify: `scripts/herdr_main_launcher.py:_DEEPAGENTS_DIAGNOSTIC_COMMAND_TIMEOUT` and monitoring evidence construction
- Verify: `scripts/herdr_main_launcher.py:_read_deepagents_receipt`, `_deepagents_receipt_observation`, settlement callers

**Dependencies:**
- Task 1 confirms current source shape and no tracked workspace drift.

**Authority:**
- Preauthorized local actions: edit only the named launcher symbols and constants; run focused launcher tests; preserve all existing receipt, cleanup, reconciliation, and settlement branches; record task evidence and update the ledger in this plan
- Stop for: required change to attempt contracts, dispatcher, worker wrapper, global Herdr timeout, generated adapters, persistent state, background thread, or unrelated launcher path

**Steps:**
- [x] Step 1: Add the completion-specific `0.5s` diagnostic budget without changing shared command defaults.
- [x] Step 2: Refactor only enough of `_deepagents_completion_snapshot()` to apply the budget independently to `process-info` and `pane read`, preserving existing observation-error classification.
- [x] Step 3: Reorder `_deepagents_completion_evidence()` diagnostic phases so receipt is read after process-info and before pane read; return authoritative receipt observation immediately when confirmed.
- [x] Step 4: Replace wall-clock subtraction for durations with monotonic start/receipt/return markers and emit `time_to_receipt_ms` plus `receipt_to_completion_return_ms`.
- [x] Step 5: Update `test_deepagents_completion_records_receipt_detection_delay` in the same task to assert `time_to_receipt_ms` and `receipt_to_completion_return_ms`; keep Task 2 green before Task 3 starts.
- [x] Step 6: Keep `0.1s` receipt polling and `2.0s` diagnostic cadence unchanged.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py -k "completion or snapshot"`
- Expected: focused completion tests pass with renamed metric assertions; diagnostic timeout remains observer-only and lifecycle branches remain reachable.

**Exit Criteria:**
- Runtime path has bounded per-command diagnostics, receipt recheck between phases, unchanged global timeout/cadence, and truthful monotonic metrics.

### Task 3: Add focused regression proof

**Purpose:**
- Prove the reproduced stalled-diagnostic defect is fixed and sibling fallback paths remain unchanged.

**Task Function:**
- Build deterministic regression seams for command timeouts, receipt availability, ordering, and metric semantics.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: tests share launcher seams and must be authored against Task 2 behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification owns broad validation after focused proof.

**Specification Coverage:**
- Test receipt arriving while `process-info` is stalled; receipt wins within the bounded diagnostic budget plus `0.1s` poll tolerance.
- Test receipt recheck after `process-info` prevents a following `pane read` when receipt is confirmed; separately test receipt becoming available during a bounded `pane read` timeout and assert bounded return.
- Test `pane read` stall and both-diagnostic timeout paths without receipt.
- Test diagnostic error followed by valid receipt, normal successful diagnostics, and terminal process evidence without receipt.
- Test timeout passed to each command is capped by both `0.5s` diagnostic budget and remaining observation deadline; test deadline expiry between phases skips the next command.
- Verify the Task 2 metric assertion and add monotonic-duration coverage despite wall-clock changes.
- Assert cleanup, reconciliation, stale-attempt protection, and receipt-authoritative classification remain unchanged through existing tests.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `tests/test_herdr_main_launcher.py` completion snapshot/evidence tests near existing timeout, delayed receipt, fallback, and metric cases
- Verify: `tests/test_herdr_attempt_contract.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_project_os_runtime.py`

**Dependencies:**
- Task 2 runtime behavior exists.

**Authority:**
- Preauthorized local actions: add or update focused tests in `tests/test_herdr_main_launcher.py`, run named test modules, and record task evidence/update the ledger in this plan
- Stop for: production behavior requiring changes outside Task 2, test-only weakening of lifecycle assertions, or removal of stale-attempt/cleanup coverage

**Steps:**
- [x] Step 1: Add the failing stalled-`process-info` test before finalizing runtime assertions; use monkeypatched `_run`, receipt reads, monotonic clock, and sleep, never a real wall-clock hang.
- [x] Step 2: Add ordering and timeout-cap tests using the existing monkeypatched `_run`, receipt, clock, and sleep seams.
- [x] Step 3: Add metric assertions that patch `time.monotonic()` and `time.time()` independently.
- [x] Step 4: Run `python -m pytest -q tests/test_herdr_main_launcher.py`.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: all launcher tests pass; stalled diagnostics never force a second diagnostic before a receipt check; missing-receipt and terminal fallback results match expected lifecycle.

**Exit Criteria:**
- Focused tests fail on the old blocking behavior, pass on the patched behavior, and cover every changed branch plus unchanged lifecycle safeguards.

### Task 4: Produce deterministic convergence evidence

**Purpose:**
- Measure before/after monitoring behavior with fixed cadence and controlled stalled-command cases.

**Task Function:**
- Run identical deterministic fake-Herdr cases and record reviewable evidence.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded local performance experiment with no external dependency.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification checks artifact shape and claims.

**Specification Coverage:**
- Write `artifacts/completion-monitoring/next-convergence-evidence.json` with schema `completion-monitoring-evidence/v2`.
- Keep receipt polling at `0.1s` and diagnostics at `2.0s` for both sides.
- Record Python version, OS, repository revision, harness identity, fixed budgets, case, repetition, command counts, timeout counts, receipt checks, diagnostic probes, `time_to_receipt_ms`, `receipt_to_completion_return_ms`, lifecycle, cleanup, reconciliation, and outcome match.
- Cases: `process_info_stall_receipt`, `pane_read_stall_receipt`, `both_diagnostics_timeout_no_receipt`, `diagnostic_error_late_receipt`, `normal_success`, `terminal_process_without_receipt`.
- Label injected receipt availability as harness control data, not production receipt-publication evidence.
- Retain the change only when lifecycle, cleanup, reconciliation, stale-attempt behavior, and subprocess overhead do not regress; stalled-command receipt return is bounded by the `0.5s` diagnostic budget plus polling tolerance and removes the tens-of-seconds tail.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/benchmark_completion_monitoring.py` as a standard-library deterministic baseline/candidate runner
- Modify: `artifacts/completion-monitoring/next-convergence-evidence.json`
- Inspect: `tests/test_herdr_main_launcher.py` deterministic fake-Herdr seams and current `artifacts/completion-monitoring/task3-fake-herdr-evidence.json`
- Verify: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`

**Dependencies:**
- Task 3 focused tests pass.

**Authority:**
- Preauthorized local actions: edit `scripts/benchmark_completion_monitoring.py`, run deterministic local fake-Herdr probes, write the named evidence artifact, and update the ledger in this plan; do not start external workers or alter cadence
- Stop for: missing reproducible baseline, lifecycle mismatch, cleanup/reconciliation mismatch, stale-attempt regression, material subprocess regression, or evidence that only changes metric names without removing blocking

**Steps:**
- [x] Step 1: Run `python scripts/benchmark_completion_monitoring.py --baseline-revision d797028 --repetitions 3 --output artifacts/completion-monitoring/next-convergence-evidence.json`; runner loads baseline launcher source with `git show d797028:scripts/herdr_main_launcher.py` into a temporary module and candidate source from the current worktree.
- [x] Step 2: Use one deterministic fake-Herdr command seam for both modules; inject receipt availability and command stalls without real subprocess waits or real wall-clock sleeps.
- [x] Step 3: Validate every row has matching expected lifecycle, cleanup, and reconciliation values.
- [x] Step 4: Summarize median and p95 subprocess totals, time to receipt, receipt-to-return time, timeout counts, and lifecycle mismatches; write exact baseline and candidate revisions plus harness digest.
- [x] Step 5: Do not tune receipt cadence or diagnostic cadence in this experiment.

**Verification:**
- [x] `python scripts/benchmark_completion_monitoring.py --baseline-revision d797028 --repetitions 3 --output artifacts/completion-monitoring/next-convergence-evidence.json`
- [x] Inspect `artifacts/completion-monitoring/next-convergence-evidence.json` with `python -m json.tool artifacts/completion-monitoring/next-convergence-evidence.json`
- Expected: valid JSON, six cases, three repetitions per side, zero lifecycle/cleanup/reconciliation mismatches, and no tens-of-seconds receipt-blocking row in the candidate.

**Exit Criteria:**
- Evidence supports retain/revert decision with identical workload, fixed cadence, named metrics, and correctness gates.

### Task 5: Reconcile historical plan state

**Purpose:**
- Prevent completed benchmark work from appearing actionable in future planning.

**Task Function:**
- Apply minimal documentation SSOT correction after runtime evidence is accepted.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: one historical plan, one status transition, no runtime coupling.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: metadata and pointer inspection are sufficient.

**Specification Coverage:**
- Change `docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md` from `status: active` to `status: superseded`.
- Add a short historical note pointing to `2026-09-27-completion-monitoring-convergence-plan.md`, `artifacts/completion-monitoring/task3-fake-herdr-evidence.json`, and `artifacts/completion-monitoring/next-convergence-evidence.json`.
- Do not reset tasks, rewrite historical evidence, or mark the old plan completed.

**Required Skills:**
- `skill-writing-plans`

**Files And Symbols:**
- Modify: `docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md` frontmatter and verdict note
- Verify: `docs/superpowers/plans/2026-09-27-completion-monitoring-convergence-plan.md`

**Dependencies:**
- Task 4 evidence passes retain gate.

**Authority:**
- Preauthorized local actions: edit only the named historical plan metadata and pointer note, and update the ledger in this plan
- Stop for: any request to rewrite historical benchmark evidence or change unrelated plan lifecycle state

**Steps:**
- [x] Step 1: Set old plan status to `superseded`.
- [x] Step 2: Add pointer to this plan and both canonical completion-monitoring evidence artifacts.
- [x] Step 3: Run `python scripts/validate_planning_lifecycle.py --repo-root . --strict`.

**Verification:**
- [x] `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- Expected: plan lifecycle validation passes and old benchmark work is not actionable.

**Exit Criteria:**
- Historical plan state reflects repository truth without changing historical task evidence.

### Task 6: Final verification and reconciliation

**Purpose:**
- Prove changed runtime, tests, evidence, planning metadata, and repository adapters are consistent.

**Task Function:**
- Execute fresh final verification and reconcile all required artifacts.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: final acceptance requires one lead-owned proof set.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `skill-verification-before-completion` owns final verification.

**Specification Coverage:**
- All implementation outcomes, task-local proof, scope boundaries, and artifact claims are reconciled against source and tests.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-performance-optimization`

**Files And Symbols:**
- Verify: `scripts/herdr_main_launcher.py`
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_herdr_attempt_contract.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_project_os_runtime.py`
- Verify: `artifacts/completion-monitoring/next-convergence-evidence.json`
- Verify: all files changed by this plan with `git diff --check`

**Dependencies:**
- Tasks 1–5 complete and accepted.

**Authority:**
- Preauthorized local actions: run named validators and read-only diff/status checks; update this plan’s task evidence and completion state only after fresh proof
- Stop for: failed required check, unresolved lifecycle mismatch, unrecorded scope deviation, changed base, or any request for push/merge

**Steps:**
- [x] Step 1: Run `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py`.
- [x] Step 2: Run `python scripts/validate_planning_lifecycle.py --repo-root . --strict`.
- [x] Step 3: Run `python scripts/validate_repo_contracts.py --repo-root .`.
- [x] Step 4: Run `python scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Step 5: Run `python scripts/validate_agent_runtime_drift.py --all-platforms`.
- [x] Step 6: Run `git diff --check` and `git status --short --branch`.
- [x] Step 7: Apply `skill-verification-before-completion`; plan status is `active` during execution and transitions to `completed` only after verification returns `verified`.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py`
- [x] `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- [x] `python scripts/validate_repo_contracts.py --repo-root .`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `python scripts/validate_agent_runtime_drift.py --all-platforms`
- [x] `git diff --check`
- Expected: all commands pass; tracked changes are limited to plan targets; preserved untracked `.playwright-mcp/`, `db/`, and this plan remain untouched except for declared plan edits.

**Exit Criteria:**
- Fresh verification returns `verified`; all required evidence is recorded; no scope deviation or blocker remains; plan can then transition to `completed` by the lead controller.

## Verification

- `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `python -m json.tool artifacts/completion-monitoring/next-convergence-evidence.json`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. `_deepagents_completion_evidence()` checks receipt before diagnostics and between bounded diagnostic phases.
2. `process-info` and `pane read` use the explicit `0.5s` completion-specific timeout capped by remaining observation deadline; expired deadlines skip commands.
3. `detection_delay_ms` is gone from current monitoring output and replaced by monotonic `time_to_receipt_ms` plus `receipt_to_completion_return_ms`.
4. Lifecycle classification, receipt authority, settlement grace, cleanup, reconciliation, missing-receipt fallback, and stale-attempt protection remain unchanged under focused tests.
5. Deterministic evidence records fixed-cadence before/after cases with zero correctness mismatches and no tens-of-seconds candidate receipt-blocking tail.
6. Historical worker-contract plan state is `superseded` and points to canonical current evidence.
7. Final validators pass, unrelated untracked files remain untouched, and all deviations/blockers are recorded in this plan.
8. Plan status changes to `completed` only after `skill-verification-before-completion` returns `verified`.
