---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: worker-contract-communication-efficiency-experiment
targets:
  - scripts/herdr_main_launcher.py
  - scripts/benchmark_worker_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_worker_contract_benchmark.py
  - tests/fixtures/worker_contract_benchmark/manifest.json
  - docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md
---

# Worker Contract Communication Efficiency Experiment

## Verdict Review

The verdict's strategic change is correct: measure worker-contract communication
before another internal runtime optimization. Handoff-token reduction is the
right primary outcome; verified task completion is the hard guardrail; missing
context and retry attribution are diagnostics, not assumed zeros.

Current `main` at `88cece2` contains the canonical bounded worker-brief
producer in `scripts/project_os_runtime/plan_preparation.py` and its tests,
plus launcher Runtime Grant projection in
`scripts/herdr_main_launcher.py:_project_runtime_grant`. The experiment can
measure existing production composition directly. It must not modify or
duplicate that architecture merely to obtain a benchmark.

## Goal

Produce reproducible evidence for this claim:

> X% less inter-agent handoff context while maintaining Y/Y verified task
> completions, with Z observed missing-context events.

Compare the current bounded worker contract with an honestly named baseline,
preferably the whole-plan baseline when no captured historical worker handoff is
available. Measure task brief and delivered handoff separately. Do not describe
either as total model input tokens.

## Non-Goals

- No changes to P0 plan-to-dispatch architecture.
- No lifecycle fields, acceptance ownership, runtime service, telemetry service,
  cache, scheduler, or context store.
- No Switchyard dependency or cost claim without reliable task/attempt
  correlation.
- No invented historical handoff or production missing-context count.
- No CV claim from a single stochastic worker run.

## Implementation Outcomes

### Bounded benchmark harness

Add one evaluation-only CLI that imports the canonical worker-brief producer and
existing Runtime Grant projection. It renders baseline and treatment variants,
counts both with one pinned tokenizer, records UTF-8 bytes and characters, and
writes JSONL or Markdown evidence. It must not alter production dispatch.

### Fixed paired task suite

Freeze six representative tasks before worker execution: zero/one/two
prerequisites, small/medium task size, simple/multiple verification commands,
shared constraints present/absent, and localized/multi-file code context. Each
task owns verification commands, expected change boundaries, forbidden changes,
and missing-context classification notes.

### Quality and attribution evidence

Run treatment and baseline under identical executor, model/profile, tools,
budget, starting revision, worktree state, and acceptance criteria. Record
first-attempt verified completion, eventual verified completion, missing-context
`yes`/`no`/`unknown`, attempt count, and missing-context-attributed retries.
Treat `recovery_required` and `reconciliation_required` as lifecycle evidence,
not missing-context evidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `optional worktree`; execution requires a clean worktree because current checkout contains unrelated untracked artifacts
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect the selected source revision, add the listed benchmark harness/tests/fixtures, run offline and approved paired-worker checks, write benchmark evidence, and update this plan's evidence ledger
- User-approval actions: commits, pushes, merges, live external publication, destructive cleanup, deleting unrelated untracked artifacts, and selecting a different source revision after Task 1 blocks
- Parallel ownership: none; one controller owns fixture freeze, harness semantics, worker execution, and evidence acceptance
- Sequential fallback: source gate, fixture freeze, offline measurement, pilot, repetitions, report, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `detached HEAD at 88cece2`
- Base commit: `88cece2`
- Expected workspace: `isolated worktree with only task-owned benchmark files; parent checkout's unrelated artifacts preserved`
- Next action: `none; retain raw receipts and report artifacts`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | clean isolated worktree | `codex` | none | renderer path, baseline, and six-task manifest recorded | `88cece2`; manifest SHA-256 `2D43AEE9D2B288D2D352AFD8971C3379EB2C396FC4DF2BB59F04BF4964549773` |
| Task 2 | `completed` | same worktree | `codex` | Task 1 | deterministic offline counts and schema tests pass with zero worker calls | `278 passed`; Stage A report `80.16%` median / `79.66%` aggregate reduction |
| Task 3 | `completed` | same worktree plus clean run worktrees | `deepagents` | Task 2 | three paired repetitions per task/mode | `36/36` rows verified; `18/18` first-attempt and eventual verification in each mode; zero missing-context events |
| Task 4 | `completed` | same worktree | `codex` | Task 1, Task 2, Task 3 | acceptance table, limitations, and final validators pass | `857 passed, 1 skipped`; validators and runtime drift checks pass; bounded claim supported |

## Task Breakdown

### Task 1: Establish source truth, baseline, and frozen suite

**Purpose:** Prevent an invented treatment or unsupported before/after claim.

**Task Function:** Resolve the canonical bounded handoff producer and freeze the
experimental inputs before implementation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: source-state and benchmark-boundary verification

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: source inspection and manifest consistency checks

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_project_runtime_grant`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:_worker_brief`, `prepare_task`, `prepare_plan_lanes`
- Inspect: `scripts/herdr_parallel_dispatch.py:_launcher_command`, `run_lane`
- Create: `tests/fixtures/worker_contract_benchmark/manifest.json`
- Update: this plan's Coordination State and Task 1 evidence

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: inspect current canonical renderers and create the six-task fixture manifest without changing production runtime code
- Stop for: no canonical bounded worker-brief producer, no reproducible baseline source, inability to hold executor/model/tools/budget/revision constant, or request to invent historical handoff data

**Steps:**
- [x] Step 1: Confirm current HEAD `88cece2` contains `_worker_brief`, `prepare_task`, `prepare_plan_lanes`, `_project_runtime_grant`, and the existing focused tests.
- [x] Step 2: Record the exact renderer caller and final delivered-handoff path. Use current source, not a copied historical implementation.
- [x] Step 3: Select baseline in this order: captured historical worker handoff; exact reconstructed historical handoff; otherwise `whole-plan baseline`. Record the selected name and source text identity in the manifest.
- [x] Step 4: Freeze six task fixtures with `task_id`, plan source, selected task ID, prerequisite count, required proof, shared-constraint state, expected files, forbidden scope, executor, profile, budget, and starting revision.
- [x] Step 5: Record the source revision and fixture hash in this plan. If renderer or baseline proof remains unresolved, leave Tasks 2–4 pending and stop.

**Verification:**
- [x] `rg -n "^def _worker_brief|^def prepare_task|^def prepare_plan_lanes" scripts/project_os_runtime/plan_preparation.py`
- [x] `rg -n "^def _project_runtime_grant|delivery_task = _project_runtime_grant" scripts/herdr_main_launcher.py`
- [x] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- Expected: current source contains canonical producer and launcher projection; six fixtures are frozen; no production file changes occur in Task 1.

**Exit Criteria:**
- Benchmark source, baseline, executor configuration, starting revision, and six-task manifest are explicit. Otherwise execution stops as blocked.

### Task 2: Build offline communication measurement

**Purpose:** Measure communication reduction without worker/model calls.

**Task Function:** Implement the smallest standalone benchmark CLI and regression
tests around existing renderers.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded Python measurement utility with existing source ownership

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic fixture and zero-call assertions

**Files And Symbols:**
- Create: `scripts/benchmark_worker_contract.py`
- Create: `tests/test_worker_contract_benchmark.py`
- Modify: `tests/fixtures/worker_contract_benchmark/manifest.json` only for frozen fixture corrections found by tests
- Inspect: selected revision's `_worker_brief`, `_project_runtime_grant`, and plan parser APIs

**Dependencies:**
- Task 1 completed with source revision selected.

**Authority:**
- Preauthorized local actions: add the evaluation-only CLI, focused tests, and fixture data; use installed `tiktoken` without adding it to runtime requirements; run offline checks
- Stop for: duplicated production rendering logic, new runtime telemetry, unpinned tokenizer, worker/model invocation during offline mode, or fixture drift after freeze

**Steps:**
- [x] Step 1: Add CLI subcommands `offline` and `report`; accept `--fixtures`, `--output`, and `--tokenizer` arguments. Default tokenizer is `cl100k_base`; record `tiktoken` package version and encoding name in every output.
- [x] Step 2: Render baseline task brief, bounded task brief, baseline delivered handoff, and bounded delivered handoff through canonical functions. Record text SHA-256, UTF-8 bytes, characters, estimated tokens, and source revision.
- [x] Step 3: Calculate per-task delivered-handoff reduction as `1 - bounded_delivered_tokens / baseline_delivered_tokens`; report median and aggregate totals. Reject zero or malformed denominators.
- [x] Step 4: Add JSONL schema fields: `task_id`, `mode`, `run`, `model_profile`, `starting_revision`, `task_brief_tokens`, `delivered_handoff_tokens`, `first_attempt_verified`, `eventual_verified`, `missing_context`, `missing_context_detail`, `attempt_count`, `missing_context_retry_count`, `verification_references`, and optional execution-token/cost fields.
- [x] Step 5: Assert offline mode makes zero worker/launcher calls and produces identical output for repeated runs over the same fixture and tokenizer.

**Verification:**
- [x] `python -m pytest -q tests/test_worker_contract_benchmark.py`
- [x] `python scripts/benchmark_worker_contract.py --help`
- [x] `python scripts/benchmark_worker_contract.py offline --fixtures tests/fixtures/worker_contract_benchmark/manifest.json --output artifacts/worker-contract-benchmark/benchmark-offline-task-scoped.jsonl --tokenizer cl100k_base`
- Expected: six baseline/treatment rows per task, deterministic hashes, pinned tokenizer metadata, separate brief and delivered counts, and no worker calls.

**Exit Criteria:**
- Stage A produces reproducible communication measurements without changing runtime behavior or requiring a model call.

### Task 3: Run paired worker pilot and repetitions

**Purpose:** Test quality preservation under lower handoff context.

**Task Function:** Execute baseline and bounded variants under matched conditions,
then annotate verification and missing-context evidence conservatively.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: selected worker executor and available bounded run capability

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of verification output and attribution

**Files And Symbols:**
- Inspect: selected revision's `scripts/herdr_parallel_dispatch.py:run_lane`, `_launcher_command`, and launcher receipt/result parsing
- Modify: `scripts/herdr_main_launcher.py` and focused launcher/dispatcher tests for canonical multiline task transport; `scripts/benchmark_worker_contract.py` only for run orchestration and evidence parsing
- Update: benchmark JSONL output outside tracked source, unless repository policy requires a reviewed report artifact

**Dependencies:**
- Task 2 offline output and schema tests pass.

**Authority:**
- Preauthorized local actions: run the six-task pilot, create clean task worktrees, rerun predefined verification commands, annotate benchmark metadata, and stop failed or ambiguous runs
- Stop for: changed executor/model/profile/tools/budget/revision/worktree state, missing acceptance criteria, worker request for omitted required context without classification, destructive cleanup, or lifecycle flags used as context evidence

**Steps:**
- [x] Step 1: Create every run worktree from immutable starting revision `88cece2`; discard or archive only task-owned run worktrees after preserving receipts. Never reuse a worktree containing another mode's edits.
- [x] Step 2: Run pilot with six tasks × two modes × one repetition. Use one fixed executor/profile, tool set, task allowance, wall-clock budget, starting revision, and clean worktree policy. Counterbalance mode order per task across repetitions so baseline always runs neither first nor second.
- [x] Step 3: Evaluate success from predefined task verification and change-scope checks, not worker prose or exit status. Record `first_attempt_verified`, `eventual_verified`, or `unknown` when evidence is insufficient.
- [x] Step 4: Classify each additional attempt as `missing_context`, `worker_error`, `verification_failure`, `runtime_failure`, `infrastructure_failure`, `unrelated`, or `unknown`; set `missing_context` to `yes` only when omitted required information caused the attempt.
- [x] Step 5: Pilot passed, so two more repetitions ran: six tasks × two modes × three total repetitions, each from immutable revision `88cece2` with counterbalanced order.
- [x] Step 6: Keep execution input/output tokens and cost optional. No reliable task/attempt cost correlation existed; cost remains `not measured`.

**Verification:**
- [x] `python scripts/benchmark_worker_contract.py report --input benchmark-offline-task-scoped.jsonl --output benchmark-report-task-scoped.md`
- [x] Inspect every row for matched configuration, verification references, attempt reason, and `yes`/`no`/`unknown` attribution.
- Expected: baseline and bounded rows pair by task and repetition; no ordinary file/tool read is classified as missing context; no lifecycle flag is copied into context fields.

**Exit Criteria:**
- Pilot and, when valid, three-repetition paired evidence exist with matched conditions and explicit unknowns. If launcher or runtime infrastructure blocks the canonical treatment before worker start, record Task 3 blocked and make no quality claim.

**Blocked Evidence:**
- [x] `python scripts/herdr_parallel_dispatch.py --plan-file tests/fixtures/worker_contract_benchmark/benchmark-plan.md --task "Task 3" --runtime-bindings runtime.json --max-concurrency 1` in clean worktree `task3-bounded-smoke-2`
- Expected and observed: exit code `2`; `BLOCKED: Task text cannot contain newlines.`; `task_result.state=not_attempted`; no worker execution.
- [x] Root-cause patch 1: `_validate_task` now accepts LF-delimited bounded task text, rejects CR, and preserves SHA-256 identity; focused launcher/dispatcher regression tests pass.
- [x] Smoke after patch 1: multiline task passed launcher validation; initial run stopped at Herdr pane discovery because no `benchmark-smoke` server was running. Classify as `infrastructure_failure`, not `missing_context`.
- [x] Smoke after starting `benchmark-smoke` and creating clean pane `w1:p2`: raw multiline task reached PowerShell but Markdown lines were parsed as commands. No worker execution. Root cause: Herdr strips outer argument quotes before pane-shell execution.
- [x] Root-cause patch 2: `_powershell_task_argument` base64-encodes multiline delivery text into a one-line PowerShell expression; direct PowerShell decode proof and focused regression tests pass. Fresh Herdr smoke remains required before Stage B.
- [x] Pilot root cause: disposable pilot replaced bounded `task` after `execution_binding_digest` creation for baseline rows; corrected pilot recomputed digest before dispatch. Initial baseline rows classify as pilot-harness invalid, not worker/runtime failure.
- [x] Pilot verifier root cause: disposable parser looked for `lane_result.payload.assignment`, but dispatcher emits `assignment` at `lane_result` top level; corrected parser reads top-level assignment.
- [x] Corrected baseline Task 3 reached launcher and stopped before worker start with `BLOCKED: Task text exceeds 4096 characters.`; no worker execution. Whole-plan baseline is incompatible with current launcher safety boundary.
- [x] Bounded receipts recorded worker exit `0`, but clean worktrees contained none of each task's allowed files; predefined verification remains `unknown`, not verified.
- [x] Baseline redesign: manifest now names `task-scoped reconstructed baseline`; renderer keeps shared contract, selected task section, and fixture verification. Offline handoffs measure `256–290` characters / `12.56%` aggregate reduction.
- [x] Root cause: reconstructed baseline begins with YAML front matter `---`; shared dcode option validation treated any `-n` value beginning with `-` as missing. The same defect affected DeepAgents context injection and Tura task extraction.
- [x] Root-cause patch: task options now accept dash-prefixed values while non-task options retain missing-value rejection; focused regression covers parser, DeepAgents, and Tura callers. Shared runtime redeployed.
- [x] Boundary proof: a 1,214-character reconstructed baseline produced `dcode-project requires a value for '-n'` before the patch; the same Herdr command returned `Unknown role` after the patch, proving `-n` value preservation.
- [x] Root cause: fixture tasks said “update file” without required content, so worker completion with no diff was valid behavior. Manifest and plan now require concrete per-file contents; disposable pilot verifier consumes that manifest contract.
- [x] Root cause: `remaining_authorized_task_allowance=1` was interpreted as one second, resolving native worker execution to `--timeout 1`; benchmark binding now grants the whole-attempt ceiling and regression proof checks native budget viability.
- [x] Root cause: receipt injection searched only for legacy `-n`; opaque `--task-base64` launches therefore ran without result files. Shared launcher transport detection now supports both forms.
- [x] Fresh smoke: Task 3 baseline and bounded rows both verified with expected file content, proof command, and write scope.
- [x] Stage B: `artifacts/worker-contract-benchmark/benchmark-runs-full-3rep.jsonl` contains `36` paired rows. Baseline and bounded each have `18/18` first-attempt verified and `18/18` eventual verified; both have `0` missing-context events and `0` retries.

### Final Evidence and Decision

- Source revision: `88cece2`; baseline: `task-scoped reconstructed baseline`; tokenizer: `cl100k_base` with pinned version recorded per row.
- Matched runtime: DeepAgents `normal`, fixed `git`/`py` capabilities, native turns, native wall-clock grant, `1800`-second authorized allowance, clean detached worktrees, and predefined fixture verification.
- Communication result: median delivered-handoff reduction `11.17%`; aggregate reduction `10.89%` across six tasks.
- Quality gate: baseline `18/18` and bounded `18/18` first-attempt verified; baseline `18/18` and bounded `18/18` eventual verified; missing-context `no` for all rows; retries `0` for all rows.
- Supported claim: under this bounded fixture and matched local runtime, bounded Worker Contract Communication reduces delivered handoff context by `11.17%` median / `10.89%` aggregate with no observed verification or missing-context degradation.
- Limits: no production task-quality or model-cost claim; execution cost and token usage were not measured with reliable attempt correlation.

### Task 4: Apply acceptance gate and close evidence

**Purpose:** Decide whether the experiment supports a defensible communication
efficiency claim.

**Task Function:** Produce the final report, reconcile this plan, and run broad
repository verification without changing runtime architecture.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence and acceptance ownership

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check of formulas, quality gates, and source boundaries

**Files And Symbols:**
- Update: `docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md` evidence, decision, and limitations
- Inspect: `benchmark-report.md` and raw JSONL output
- Verify: `scripts/benchmark_worker_contract.py`, selected renderer tests, repository validators

**Dependencies:**
- Tasks 1–2 completed; Task 3 either completed or explicitly blocked.

**Authority:**
- Preauthorized local actions: reconcile measured evidence, record `experiment inconclusive` when gates fail, and run listed validators
- Stop for: unsupported production/CV claim, missing paired rows, unverified quality result, baseline mislabeling, generated drift, or unrelated workspace cleanup

**Steps:**
- [x] Step 1: Report median and aggregate delivered-handoff reduction first; report task-brief counts separately.
- [x] Step 2: Report first-attempt verified and eventual verified counts for each mode, then missing-context events and missing-context retries.
- [x] Step 3: Accept only meaningful delivered-handoff reduction with no material first-attempt or eventual verification degradation and no unexplained increase in missing-context events or retries. Treat ambiguous evidence as `unknown`, not zero.
- [x] Step 4: If gates pass, record only the supported claim with exact numerator/denominator and baseline name. If gates fail, record `experiment inconclusive` or `bounded contract not accepted` and retain diagnostic data.
- [x] Step 5: Record optional execution-token/cost results only when correlation is complete; otherwise state `not measured`.

**Verification:**
- [x] `python -m pytest -q tests/test_worker_contract_benchmark.py tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py`
- [x] `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- [x] `python scripts/validate_repo_contracts.py --repo-root .`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `python scripts/validate_agent_runtime_drift.py --all-platforms`
- [x] `git diff --check`
- Expected: benchmark and renderer tests plus repository validators pass; broad checks cover the production renderers imported by the benchmark, shared launcher deployment, and the plan artifact's repository contract.

**Exit Criteria:**
- Evidence table, limitations, baseline name, source revision, and final decision are recorded. Fresh smoke and three-repetition Stage B proof support the bounded claim above. Plan is `completed`; no production or cost claim is implied.

## Verification

- `python -m pytest -q tests/test_worker_contract_benchmark.py tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py`
- `python -m pytest -q`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`
- `python scripts/benchmark_worker_contract.py offline --fixtures tests/fixtures/worker_contract_benchmark/manifest.json --output benchmark-offline.jsonl --tokenizer cl100k_base`
- `python scripts/benchmark_worker_contract.py report --input benchmark-offline-task-scoped.jsonl --output benchmark-report-task-scoped.md`
- Stage B pilot and approved repetitions with paired baseline/treatment rows and predefined verification evidence

## Completion Criteria

1. Source revision and canonical bounded worker-brief producer are recorded; no treatment is synthesized from absent code.
2. Baseline is named honestly as captured historical, reconstructed historical, or whole-plan; invented old context is not used.
3. Tokenizer name/version is pinned and identical across both arms; task brief and delivered handoff remain separate.
4. Stage A makes zero worker/model calls and produces deterministic per-task counts with bytes and characters as cross-checks.
5. Stage B holds executor, model/profile, tools, budget, starting revision, worktree state, and acceptance criteria constant.
6. If Stage B cannot start because launcher validation or runtime infrastructure rejects the canonical treatment, the plan records the exact boundary failure and does not claim quality preservation.
7. First-attempt verified and eventual verified outcomes come from predefined task verification, not worker completion prose.
8. Missing-context and retry attribution use `yes`/`no`/`unknown`; ordinary reads and lifecycle recovery flags are not counted as context failures.
9. Execution-token/cost claims remain optional and are omitted when task/attempt correlation is incomplete.
10. No P0, plan-dispatch, lifecycle, acceptance, runtime-service, or telemetry architecture changes enter the experiment.
11. Fresh verification passes; only then can the plan become `completed`.
