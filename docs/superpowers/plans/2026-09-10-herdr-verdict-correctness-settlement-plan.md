---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: herdr-verdict-correctness-settlement
targets:
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - scripts/deepagents_result_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
---

# Herdr Verdict Correctness And Settlement Plan

## Goal

Close remaining lifecycle evidence defects after commit
`1f4cfcdfee89491cb7b49603508346358394f5d3`, then simplify DeepAgents
settlement without weakening uncertainty reporting or MCP isolation.

Keep existing lifecycle owners, legacy output compatibility, role-view locking,
attempt correlation, and unrelated workspace changes. Do not add a watcher,
cache service, reservation registry, heartbeat, or orchestration layer.

Preserve supported output field names and shapes. Correct values may change when
current evidence was wrong; document those semantic corrections in tests and
the final implementation record. Do not force Codex and DeepAgents into one
identical lifecycle model.

## Implementation Outcomes

### Consistent terminal outcome

`_main_body()` prints and returns one classified result. JSON `launcher_exit_code`,
`failure_kind`, `reconciliation_required`, status, and legacy exit behavior agree
for success, worker failure, missing receipt, malformed receipt, and uncertain
cleanup.

### Trustworthy lifecycle receipt

Receipt encoding and parsing share one payload validator. Invalid types and
cross-field contradictions return structured `unknown` evidence instead of
raising or producing false confirmation.

### Producer-owned evidence

`dcode-project` reports cleanup, worker, and descendant facts established by its
own execution path. Missing ownership evidence remains `unverified`; retained
role views remain attributable for recovery.

### One settlement owner

DeepAgents uses one receipt-aware observation deadline. Receipt reads stay cheap,
pane/process fallback stays bounded, and result emission does not sleep or poll.

### Accurate MCP evidence

Configuration distinguishes available capabilities, requested selection, effective
direct selection, and MCP mode. Default no-MCP execution remains isolated and
skips unnecessary capability projection.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared launcher, worker, receipt-contract, MCP-reporting, and test files; run focused tests, repository validators, adapter checks, and bounded task-owned probes without authentication, destructive cleanup, or external writes
- User-approval actions: commits, pushes, merges, authentication, external configuration writes, process termination outside task-owned probes, destructive cleanup, and edits outside declared targets
- Parallel ownership: none; launcher, worker, receipt contract, and tests share one lifecycle contract
- Sequential fallback: baseline and regression locks, receipt contract, canonical outcomes and producer evidence, settlement and timing, MCP semantics, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `1f4cfcdfee89491cb7b49603508346358394f5d3`
- Expected workspace: preserve unrelated modifications in `scripts/validate_planning_lifecycle.py`, `tests/test_validate_planning_lifecycle.py`, `.playwright-mcp/`, and `db/`; do not stage, delete, or rewrite them
- Next action: complete — verification recorded
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | defect matrix and focused failing tests | baseline `215 passed`; regression matrix implemented |
| Task 2 | `completed` | current | `codex` | Task 1 | shared validator and malformed-receipt tests | `115 passed`; deployed shared scripts refreshed |
| Task 3 | `completed` | current | `codex` | Tasks 1–2 | return-code, cleanup, and producer-fact tests | `219 passed`; production-path exit parity and lifecycle exception facts covered |
| Task 4 | `completed` | current | `codex` | Task 3 | one-deadline observer tests and comparable timing evidence | `108 passed`; receipt-first, deadline, slow-pane, and Codex timing cases |
| Task 5 | `completed` | current | `codex` | Task 2 | MCP field semantics and no-MCP projection tests | `119 passed`; canonical selection state and lazy default projection |
| Task 6 | `completed` | current | `codex` | Tasks 1–5 | final focused, contract, config, drift, and diff checks | `245 passed`; all mandatory validators and diff checks passed |

## Task Breakdown

### Task 1: Lock defect matrix and baseline

**Purpose:**
- Convert reviewed verdicts into executable regression cases before changing lifecycle code.

**Task Function:**
- Establish source-to-test mapping and capture behavior at commit `1f4cfcd`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded Python control-flow and test-matrix work with known files and moderate integration risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check that each demonstrated verdict defect has a regression assertion.

**Specification Coverage:**
- Single-source terminal result.
- Structured uncertainty for missing or malformed receipts.
- Conservative cleanup and process evidence.
- One settlement deadline.
- MCP requested-versus-effective evidence.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_main_body`, `emit_assignment`, `_classify_deepagents_outcome`
- Inspect: `scripts/deepagents_result_contract.py:encode_result_receipt`, `parse_result_receipt`
- Inspect: `scripts/dcode_project.py:_remove_role_views`, `_run_bounded_worker`, `_parse_mcp_selection`
- Modify: `tests/test_herdr_main_launcher.py`, `tests/test_dcode_project.py`
- Verify: `git status --short`, existing focused test commands

**Dependencies:**
- Current source at base commit `1f4cfcdfee89491cb7b49603508346358394f5d3`.

**Authority:**
- Preauthorized local actions: inspect declared source and test files, add focused regression tests, and run focused tests without changing unrelated workspace paths.
- Stop for: source behavior differs materially from reviewed defects, an existing test contract conflicts with the approved scope, or unrelated files change.

**Steps:**
- [x] Record baseline `git status --short --branch` and preserve all pre-existing changes.
- [x] Add tests covering classifier exit code versus `_main_body()` return code, legacy `exit_code` parity, failure/reconciliation consistency, malformed receipt state types, missing cleanup marker, and worker exception lifecycle facts.
- [x] Add a worker-exit-zero plus explicitly failed-report case; define expected execution, task-result, acceptance, launcher-return, and reconciliation fields from existing classifier rules.
- [x] Add tests covering receipt-first observation behavior and MCP config fields without asserting speculative latency gains.
- [x] Add a Codex acknowledgement-and-return regression assertion; preserve confirmed prompt acceptance even when completion remains uncertain.
- [x] Run focused tests and retain failures as task evidence until Tasks 2–5 fix them.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- Expected: test collection succeeds; new regression failures are limited to defects assigned to Tasks 2–5 and do not block Task 1; unrelated failures are recorded separately.

**Exit Criteria:**
- Every reviewed correctness claim has one named regression assertion.
- Baseline workspace state is recorded and unrelated paths remain untouched.

### Task 2: Harden shared receipt contract

**Purpose:**
- Make receipt validation total, non-throwing at parse boundaries, and shared by encoding and parsing.

**Task Function:**
- Implement minimal payload validation around the existing contract module.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: small shared-module change with explicit type and invariant rules.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent validation of schema behavior and compatibility with current producer payloads.

**Specification Coverage:**
- Type checks precede enum membership.
- Exited workers require integer exit codes.
- Descendant state uses the vocabulary already emitted by `dcode-project`.
- Removed cleanup cannot claim remaining owned paths.
- Parser returns structured `unknown` for malformed payloads.
- Encoder rejects invalid producer payloads explicitly and never publishes a fabricated `unknown` receipt.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/deepagents_result_contract.py:WORKER_STATES`, `CLEANUP_STATES`, `encode_result_receipt`, `parse_result_receipt`
- Modify: `scripts/deepagents_result_contract.py`
- Verify: `tests/test_dcode_project.py` receipt tests

**Dependencies:**
- Task 1 regression cases exist.

**Authority:**
- Preauthorized local actions: edit the shared receipt contract and its focused tests; run Python tests and import checks without changing producer semantics outside declared invariants.
- Stop for: a required invariant would reject an existing valid producer payload, require a schema version bump, or require edits outside declared targets.

**Steps:**
- [x] Add one internal payload validator used by `encode_result_receipt` and `parse_result_receipt`.
- [x] Validate object and scalar types before membership checks; reject booleans where integers are required.
- [x] Validate descendant states using the current emitted vocabulary: `terminated`, `not_started`, and `unknown`.
- [x] Enforce exit-code and cleanup-path invariants without making parsing block or invoke subprocesses.
- [x] Map parser validation failures to stable `unknown` detail strings and preserve valid receipt projection fields.
- [x] Let encoder validation raise an explicit publication error to its producer; do not convert producer bugs into success-shaped or fabricated `unknown` receipts.
- [x] Handle malformed nested structures and supported decoding failures at the parser boundary without a blanket exception handler that hides programming errors.
- [x] Extend focused tests for list-valued states, invalid exit codes, invalid descendants, contradictory cleanup, invalid encoder payloads, and valid producer receipts.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py -q`
- Expected: malformed receipts return structured `unknown`; valid receipts remain `confirmed`; no uncaught `TypeError` reaches callers.

**Exit Criteria:**
- Encoding and parsing use one validator.
- Producer-generated receipt payloads pass validation.
- Parser remains bounded local I/O only.

### Task 3: Make outcome and producer evidence canonical

**Purpose:**
- Remove competing terminal decisions and report cleanup/process facts from the owner that observed them.

**Task Function:**
- Reconcile launcher classification with process return behavior and worker receipt production.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: cross-file lifecycle change with direct regression coverage and high false-success risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent outcome-matrix and failure-path review.

**Specification Coverage:**
- `_main_body()` returns classified `launcher_exit_code`.
- `failure_kind` and `reconciliation_required` derive from final classification.
- Missing ownership marker yields `unverified`, not `removed`.
- Preserved role views retain ownership and recovery evidence.
- Worker owner supplies process-start, exit, and descendant facts.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:emit_assignment`, `_classify_deepagents_outcome`, `_main_body`
- Inspect: `scripts/dcode_project.py:_remove_role_views`, `_run_bounded_worker`, `_run_deepagents_worker`, `_run_tura_worker`, `_publish_result_receipt`
- Modify: `scripts/herdr_main_launcher.py`, `scripts/dcode_project.py`
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_dcode_project.py`

**Dependencies:**
- Task 2 contract validator is complete.
- Task 1 outcome matrix is present.

**Authority:**
- Preauthorized local actions: edit declared launcher and worker lifecycle functions plus focused tests; run mocked failure probes and bounded task-owned worker tests without destructive cleanup.
- Stop for: removing supported output fields or shapes, weakening uncertainty, changing role-view lock ownership, or requiring external process control.

**Steps:**
- [x] Remove the older marker-based terminal return decision from `_main_body()`.
- [x] Construct one classified result, serialize it, and return its `launcher_exit_code` on every terminal path.
- [x] Derive failure and reconciliation fields from that same classified result; remove provisional duplicate calculations. Assert JSON `launcher_exit_code`, legacy `exit_code`, and actual function return parity.
- [x] Preserve confirmed prompt acceptance when completion or task-result evidence remains uncertain.
- [x] Preserve current invocation ownership facts before cleanup and return `unverified` when marker absence or cleanup failure prevents proof of removal.
- [x] Return or attach bounded-worker lifecycle facts through `_run_bounded_worker()`, `_run_deepagents_worker()`, and `_run_tura_worker()` so post-start errors are not relabeled as `not_started`.
- [x] Distinguish failure before process creation, error after process creation, known parent exit with uncertain descendants, timeout with confirmed termination, and unproven termination. Unknown lifetime must not permit cleanup that assumes the worker stopped.
- [x] Keep retained paths and marker state in published receipts for recovery.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- Expected: serialized exit code equals `_main_body()` return; malformed or missing evidence cannot produce false successful completion; cleanup and worker states match established facts.

**Exit Criteria:**
- No terminal branch has an independent exit-code decision.
- All reviewed false-success, parser-crash, cleanup, and process-evidence regressions pass.

### Task 4: Collapse settlement into one observer

**Purpose:**
- Replace split pane observation and post-emission receipt waiting with one receipt-aware deadline.

**Task Function:**
- Simplify observation while preserving uncertainty and required report evidence.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded control-flow refactor with measurable subprocess and latency effects.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check that optimization does not treat `pane run` success as wrapper termination proof.

**Specification Coverage:**
- One observer owns receipt and pane evidence collection.
- Receipt reads precede expensive pane/process commands.
- One deadline governs settlement; no additive five-second claim.
- Classifier runs after observation; emitter does not sleep.
- Report/diagnostic observation remains separate where required.
- Performance phases preserve preparation intervals and use current monotonic finalization time.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:emit_assignment`, `_deepagents_completion_snapshot`, `_deepagents_completion_evidence`, `_record_performance_phase`, `_finalize_performance`
- Modify: `scripts/herdr_main_launcher.py`
- Verify: `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 3 canonical outcome and producer facts are complete.

**Authority:**
- Preauthorized local actions: edit declared observation and performance helpers, add deterministic clock/subprocess-count tests, and run bounded local probes without claiming live Herdr ordering not proven by evidence.
- Stop for: need for a second watcher, unsupported lifecycle claim, or required change to worker ownership. Preserve uncertainty when `pane run` acknowledgement semantics are unknown.

**Steps:**
- [x] Define one settlement deadline from the existing observation budget; do not extend it after exhaustion.
- [x] Poll the local receipt cheaply before invoking pane/process observation.
- [x] When receipt is confirmed, collect only required final pane/process/report evidence and stop redundant lifecycle polling.
- [x] When receipt is absent, use sparse existing pane/process fallback until the same deadline, then classify uncertainty.
- [x] Move all waiting out of `emit_assignment()`; make emission serialize already-collected evidence only.
- [x] Reuse immediately collected pane evidence instead of rereading it during classification.
- [x] Preserve preparation intervals and finalization timestamps in performance output.
- [x] Correct Codex delivery timing and test it through `_main_body()`, including initial evidence serialization.
- [x] Require one common remaining budget for every subprocess timeout and sleep.
- [x] Add deterministic cases for receipt-before-first-pane-command, receipt-between-polls, receipt deadline expiry, slow pane commands consuming the remaining budget, and terminal receipt with missing or contradictory report evidence.
- [x] Treat one settlement owner as mandatory. Make reduced observation frequency and measured latency improvement conditional on preserved evidence; do not claim improvement without identical before/after workloads.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: one deadline, no post-deadline receipt extension, no emitter sleep, receipt-first ordering, preserved uncertain fallback, accurate timing fields, and correct Codex delivery timing through `_main_body()`.

**Exit Criteria:**
- Observer owns waiting and evidence collection.
- No code path assumes successful `pane run` proves wrapper exit.
- Any performance claim has comparable before/after evidence.

### Task 5: Correct MCP evidence and lazy projection

**Purpose:**
- Make MCP reporting describe actual launch behavior without changing default isolation.

**Task Function:**
- Separate capability discovery from requested and effective direct MCP selection.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: localized configuration/reporting change with compatibility checks.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check that handoff provenance remains separate from direct MCP access.

**Specification Coverage:**
- Empty selection is not reported as all available capabilities.
- Default DeepAgents path reports direct MCP disabled and passes `--no-mcp`.
- Capability projection occurs only for explicit selection, handoff validation, or config inspection.
- Handoff facts remain provenance, not permission grants.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_parse_mcp_selection`, `_controller_options`, config-print path, `_direct_mcp_runtime`
- Modify: `scripts/dcode_project.py`
- Verify: `tests/test_dcode_project.py`, any direct config consumers found by repository search

**Dependencies:**
- Task 2 receipt contract is complete; Tasks 3–4 may proceed independently but must not change MCP ownership semantics.

**Authority:**
- Preauthorized local actions: edit declared MCP selection/reporting code and focused tests; run config-print and no-MCP worker argument tests without authentication or external MCP writes.
- Stop for: an external consumer depends on the old `selected_mcp` meaning, handoff provenance would become direct tool access, or project MCP config must be modified.

**Steps:**
- [x] Search production callers and tests for `selected_mcp` before changing its meaning.
- [x] Represent `available_mcp`, `requested_mcp`, `effective_mcp`, and `mcp_mode` from one canonical selection decision.
- [x] Retain `selected_mcp` only as a documented derived alias when compatibility requires it; otherwise migrate every discovered consumer. Never calculate it independently.
- [x] Keep default empty selection as `requested_mcp=[]`, `effective_mcp=[]`, and `mcp_mode="disabled"`.
- [x] Resolve capabilities lazily only when explicit MCP selection, handoff validation, or configuration inspection requires it.
- [x] Preserve `--no-mcp` on default DeepAgents launches and existing direct-runtime cleanup.
- [x] Add handoff tests for no direct MCP selection with valid provenance and explicit selection restricted to allowed handoff sources.
- [x] Update config and selection tests to prove reporting accuracy and default isolation.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py -q`
- Expected: empty selection no longer expands to all available capabilities; default launch remains no-MCP; explicit selection still produces the required runtime configuration; handoff provenance never grants direct MCP access.

**Exit Criteria:**
- MCP evidence has one canonical source.
- Default no-MCP path avoids unnecessary capability projection.
- Handoff provenance and direct MCP permission remain separate.

### Task 6: Final verification and handoff

**Purpose:**
- Reconcile implementation, tests, repository validators, generated surfaces, and preserved workspace state.

**Task Function:**
- Execute final verification and record deviations without changing scope.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: deterministic repository verification after cross-file lifecycle changes.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent final plan and evidence review.

**Specification Coverage:**
- All implementation outcomes and task-local proof.
- No unrelated workspace changes.
- No generated-surface drift.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all declared targets and `git diff`
- Verify: repository tests, validators, adapter checks, and workspace state

**Dependencies:**
- Tasks 1–5 complete; Task 4 must not claim performance improvement without comparable evidence.

**Authority:**
- Preauthorized local actions: run final checks, inspect diff/status, confirm preserved unrelated paths, and update this plan ledger after accepted proof.
- Stop for: failed mandatory proof, generated drift, unexpected file changes, stale plan status, commit, push, merge, or destructive cleanup.

**Steps:**
- [x] Run focused lifecycle tests.
- [x] Run repository contract and config validators.
- [x] Run agent-runtime drift and adapter sync checks.
- [x] Run `git diff --check` and confirm unrelated paths remain unchanged.
- [x] Separate pre-existing validator/test failures from regressions introduced by this plan using the Task 1 baseline and unchanged-file status.
- [x] Have `skill-plan-document-reviewer` inspect scope, ownership, and proof.
- [x] Set plan status to `completed` only after `skill-verification-before-completion` returns `verified`.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py tests/test_starter_lifecycle_contract.py -q` (`245 passed`)
- [x] `py scripts/validate_repo_contracts.py --repo-root . --fast` (passed)
- [x] `py scripts/validate_repo_config.py --repo-root .` (passed)
- [x] `py scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check` (passed)
- [x] `py scripts/sync_agent_adapters.py --all-platforms --check` (passed)
- [x] `git diff --check` (passed)
- [x] `git status --short --branch` (only declared implementation files, plan, and preserved unrelated paths)
- Expected: all mandatory checks pass; only declared implementation files and pre-existing unrelated workspace paths remain.

**Exit Criteria:**
- Fresh verification passes.
- No task remains pending, active, or blocked.
- Every deviation, deferral, and performance limitation is recorded in this plan.

## Verification Record

- Verified on `main` at `1f4cfcdfee89491cb7b49603508346358394f5d3`; no commits, pushes, merges, or cleanup performed.
- Preserved unrelated workspace state: `scripts/validate_planning_lifecycle.py`, `tests/test_validate_planning_lifecycle.py`, `.playwright-mcp/`, and `db/`.
- Shared runtime redeployed with `py scripts/deploy_agent_runtime.py --target all`; runtime drift and adapter checks pass.
- Live DeepAgents smoke: explicit MCP selection passed; documented no-MCP command passed with `--json --max-turns 4 --timeout 120` and returned `DEEPAGENTS_UPGRADE_OK`.
- Failed smoke attempts were procedural, not product defects: wrapper rejects caller-supplied `--executor`; first no-MCP attempt omitted documented turn bounds and hit its 45-second timeout. Missing `TAVILY_API_KEY` warning is expected and disables web search per runtime procedure.

## Deferred Follow-Up

- Profile digest binding: plan separately after lifecycle correctness; verify digest against the same loaded profile object used to launch the worker.
- `[delegation].default_executor` removal: audit all production callers first; do not remove fallback solely because two sources exist.
- `validate_repo_contracts --fast` reuse: defer until repeated validation cost is measured and invalidation covers uncommitted files, configuration, and contracts.
- Git query consolidation: defer until existing subprocess evidence shows material Windows startup cost.
- Stale MCP janitor deletion and tutorial extraction: maintenance-only follow-up after consumer search; no latency claim without measurement.

## Non-Goals

- No new runtime service, cache database, watcher, scheduler, heartbeat, reservation registry, or orchestration framework.
- No schema version bump unless current producer payloads cannot satisfy the validator without changing contract semantics.
- No change to Codex acknowledge-and-return behavior.
- No change to role-view locking, direct MCP runtime cleanup, attempt correlation, legacy output fields, or project MCP configuration.
- No destructive cleanup of existing user files or unrelated workspace artifacts.

## Verification

Use focused lifecycle tests, repository contract/config validators, agent-runtime drift and adapter checks, `git diff --check`, preserved-workspace inspection, and comparable mocked observation evidence. Live Herdr proof is supplemental; source and tests remain authoritative when live pane ordering cannot be proven.

## Completion Criteria

1. `_main_body()` return code, JSON `launcher_exit_code`, and supported legacy `exit_code` equal the classified result on every terminal path.
2. Receipt parsing never raises on malformed lifecycle field types and rejects relied-upon contradictions.
3. Missing cleanup ownership evidence cannot become confirmed removal.
4. Worker receipts report established process and descendant facts.
5. One settlement observer owns receipt/pane waiting under one deadline.
6. Timing output preserves preparation and finalization boundaries, including corrected Codex delivery timing through `_main_body()`.
7. MCP reporting distinguishes available, requested, effective, and mode; default no-MCP isolation remains intact.
8. Focused tests and mandatory repository checks pass with fresh output.
9. Unrelated tracked and untracked workspace state remains preserved.
10. The plan is marked `completed` only after `skill-verification-before-completion` returns `verified`.
