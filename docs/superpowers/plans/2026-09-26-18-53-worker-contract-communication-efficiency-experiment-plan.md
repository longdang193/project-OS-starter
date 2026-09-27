---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
name: worker-contract-communication-efficiency-experiment
targets:
  - scripts/benchmark_worker_contract.py
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
- Branch: `unresolved until execution approval`
- Base commit: `88cece2`
- Expected workspace: `clean isolated worktree; preserve current checkout's unrelated untracked artifacts`
- Next action: `select and verify benchmark source revision in Task 1`
- Blockers: `bounded worker-brief producer is absent from current HEAD`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | clean isolated worktree | `unresolved` | none | renderer path, baseline, and six-task manifest recorded | pending |
| Task 2 | `pending` | same worktree | `unresolved` | Task 1 | deterministic offline counts and schema tests pass with zero worker calls | pending |
| Task 3 | `pending` | same worktree plus clean run worktrees | `unresolved` | Task 2 | paired pilot and, if retained, three total repetitions per task/mode | pending |
| Task 4 | `pending` | same worktree | `unresolved` | Task 3 | acceptance table, limitations, and final validators pass | pending |

## Task Breakdown

### Task 1: Establish source truth, baseline, and frozen suite

**Purpose:** Prevent an invented treatment or unsupported before/after claim.

**Task Function:** Resolve the canonical bounded handoff producer and freeze the
experimental inputs before implementation.

**Template Profile:**
- Controller-selected: `unresolved`
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
- [ ] Step 1: Confirm current HEAD `88cece2` contains `_worker_brief`, `prepare_task`, `prepare_plan_lanes`, `_project_runtime_grant`, and the existing focused tests.
- [ ] Step 2: Record the exact renderer caller and final delivered-handoff path. Use current source, not a copied historical implementation.
- [ ] Step 3: Select baseline in this order: captured historical worker handoff; exact reconstructed historical handoff; otherwise `whole-plan baseline`. Record the selected name and source text identity in the manifest.
- [ ] Step 4: Freeze six task fixtures with `task_id`, plan source, selected task ID, prerequisite count, required proof, shared-constraint state, expected files, forbidden scope, executor, profile, budget, and starting revision.
- [ ] Step 5: Record the source revision and fixture hash in this plan. If renderer or baseline proof remains unresolved, leave Tasks 2–4 pending and stop.

**Verification:**
- [ ] `rg -n "^def _worker_brief|^def prepare_task|^def prepare_plan_lanes" scripts/project_os_runtime/plan_preparation.py`
- [ ] `rg -n "^def _project_runtime_grant|delivery_task = _project_runtime_grant" scripts/herdr_main_launcher.py`
- [ ] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- Expected: current source contains canonical producer and launcher projection; six fixtures are frozen; no production file changes occur in Task 1.

**Exit Criteria:**
- Benchmark source, baseline, executor configuration, starting revision, and six-task manifest are explicit. Otherwise execution stops as blocked.

### Task 2: Build offline communication measurement

**Purpose:** Measure communication reduction without worker/model calls.

**Task Function:** Implement the smallest standalone benchmark CLI and regression
tests around existing renderers.

**Template Profile:**
- Controller-selected: `unresolved`
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
- [ ] Step 1: Add CLI subcommands `offline` and `report`; accept `--fixtures`, `--output`, and `--tokenizer` arguments. Default tokenizer is `cl100k_base`; record `tiktoken` package version and encoding name in every output.
- [ ] Step 2: Render baseline task brief, bounded task brief, baseline delivered handoff, and bounded delivered handoff through canonical functions. Record text SHA-256, UTF-8 bytes, characters, estimated tokens, and source revision.
- [ ] Step 3: Calculate per-task delivered-handoff reduction as `1 - bounded_delivered_tokens / baseline_delivered_tokens`; report median and aggregate totals. Reject zero or malformed denominators.
- [ ] Step 4: Add JSONL schema fields: `task_id`, `mode`, `run`, `model_profile`, `starting_revision`, `task_brief_tokens`, `delivered_handoff_tokens`, `first_attempt_verified`, `eventual_verified`, `missing_context`, `missing_context_detail`, `attempt_count`, `missing_context_retry_count`, `verification_references`, and optional execution-token/cost fields.
- [ ] Step 5: Assert offline mode makes zero worker/launcher calls and produces identical output for repeated runs over the same fixture and tokenizer.

**Verification:**
- [ ] `python -m pytest -q tests/test_worker_contract_benchmark.py`
- [ ] `python scripts/benchmark_worker_contract.py --help`
- [ ] `python scripts/benchmark_worker_contract.py offline --fixtures tests/fixtures/worker_contract_benchmark/manifest.json --output benchmark-offline.jsonl --tokenizer cl100k_base`
- Expected: six baseline/treatment rows per task, deterministic hashes, pinned tokenizer metadata, separate brief and delivered counts, and no worker calls.

**Exit Criteria:**
- Stage A produces reproducible communication measurements without changing runtime behavior or requiring a model call.

### Task 3: Run paired worker pilot and repetitions

**Purpose:** Test quality preservation under lower handoff context.

**Task Function:** Execute baseline and bounded variants under matched conditions,
then annotate verification and missing-context evidence conservatively.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: selected worker executor and available bounded run capability

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of verification output and attribution

**Files And Symbols:**
- Inspect: selected revision's `scripts/herdr_parallel_dispatch.py:run_lane`, `_launcher_command`, and launcher receipt/result parsing
- Modify: `scripts/benchmark_worker_contract.py` only for run orchestration and evidence parsing
- Update: benchmark JSONL output outside tracked source, unless repository policy requires a reviewed report artifact

**Dependencies:**
- Task 2 offline output and schema tests pass.

**Authority:**
- Preauthorized local actions: run the six-task pilot, create clean task worktrees, rerun predefined verification commands, annotate benchmark metadata, and stop failed or ambiguous runs
- Stop for: changed executor/model/profile/tools/budget/revision/worktree state, missing acceptance criteria, worker request for omitted required context without classification, destructive cleanup, or lifecycle flags used as context evidence

**Steps:**
- [ ] Step 1: Create every run worktree from immutable starting revision `88cece2`; discard or archive only task-owned run worktrees after preserving receipts. Never reuse a worktree containing another mode's edits.
- [ ] Step 2: Run pilot with six tasks × two modes × one repetition. Use one fixed executor/profile, tool set, task allowance, wall-clock budget, starting revision, and clean worktree policy. Counterbalance mode order per task across repetitions so baseline always runs neither first nor second.
- [ ] Step 3: Evaluate success from predefined task verification and change-scope checks, not worker prose or exit status. Record `first_attempt_verified`, `eventual_verified`, or `unknown` when evidence is insufficient.
- [ ] Step 4: Classify each additional attempt as `missing_context`, `worker_error`, `verification_failure`, `runtime_failure`, `infrastructure_failure`, `unrelated`, or `unknown`; set `missing_context` to `yes` only when omitted required information caused the attempt.
- [ ] Step 5: If pilot instrumentation and execution conditions pass, add two more repetitions per task/mode for six tasks × two modes × three total repetitions. Restore each run to the same immutable starting revision and counterbalanced order. Otherwise stop and record pilot failure without a CV claim.
- [ ] Step 5: Keep execution input/output tokens and cost optional. Record them only when one request can be reliably correlated to `task_id`, `attempt_id`, and `mode`.

**Verification:**
- [ ] `python scripts/benchmark_worker_contract.py report --input benchmark-runs.jsonl --output benchmark-report.md`
- [ ] Inspect every row for matched configuration, verification references, attempt reason, and `yes`/`no`/`unknown` attribution.
- Expected: baseline and bounded rows pair by task and repetition; no ordinary file/tool read is classified as missing context; no lifecycle flag is copied into context fields.

**Exit Criteria:**
- Pilot and, when valid, three-repetition paired evidence exist with matched conditions and explicit unknowns. No quality claim is made from worker completion alone.

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
- Tasks 1–3 completed or Task 1 explicitly blocked.

**Authority:**
- Preauthorized local actions: reconcile measured evidence, record `experiment inconclusive` when gates fail, and run listed validators
- Stop for: unsupported production/CV claim, missing paired rows, unverified quality result, baseline mislabeling, generated drift, or unrelated workspace cleanup

**Steps:**
- [ ] Step 1: Report median and aggregate delivered-handoff reduction first; report task-brief counts separately.
- [ ] Step 2: Report first-attempt verified and eventual verified counts for each mode, then missing-context events and missing-context retries.
- [ ] Step 3: Accept only meaningful delivered-handoff reduction with no material first-attempt or eventual verification degradation and no unexplained increase in missing-context events or retries. Treat ambiguous evidence as `unknown`, not zero.
- [ ] Step 4: If gates pass, record only the supported claim with exact numerator/denominator and baseline name. If gates fail, record `experiment inconclusive` or `bounded contract not accepted` and retain diagnostic data.
- [ ] Step 5: Record optional execution-token/cost results only when correlation is complete; otherwise state `not measured`.

**Verification:**
- [ ] `python -m pytest -q tests/test_worker_contract_benchmark.py tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py`
- [ ] `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- [ ] `python scripts/validate_repo_contracts.py --repo-root .`
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `python scripts/validate_agent_runtime_drift.py --all-platforms`
- [ ] `git diff --check`
- Expected: benchmark and renderer tests plus repository validators pass; broad checks cover the production renderers imported by the benchmark and the plan artifact's repository contract. No P0, lifecycle, acceptance, generated-surface, or production runtime ownership changes enter the diff.

**Exit Criteria:**
- Evidence table, limitations, baseline name, source revision, and final decision are recorded. Only `skill-verification-before-completion` may mark this plan `completed` after fresh proof.

## Verification

- `python -m pytest -q tests/test_worker_contract_benchmark.py tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py`
- `python -m pytest -q`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`
- `python scripts/benchmark_worker_contract.py offline --fixtures tests/fixtures/worker_contract_benchmark/manifest.json --output benchmark-offline.jsonl --tokenizer cl100k_base`
- `python scripts/benchmark_worker_contract.py report --input benchmark-runs.jsonl --output benchmark-report.md`
- Stage B pilot and approved repetitions with paired baseline/treatment rows and predefined verification evidence

## Completion Criteria

1. Source revision and canonical bounded worker-brief producer are recorded; no treatment is synthesized from absent code.
2. Baseline is named honestly as captured historical, reconstructed historical, or whole-plan; invented old context is not used.
3. Tokenizer name/version is pinned and identical across both arms; task brief and delivered handoff remain separate.
4. Stage A makes zero worker/model calls and produces deterministic per-task counts with bytes and characters as cross-checks.
5. Stage B holds executor, model/profile, tools, budget, starting revision, worktree state, and acceptance criteria constant.
6. First-attempt verified and eventual verified outcomes come from predefined task verification, not worker completion prose.
7. Missing-context and retry attribution use `yes`/`no`/`unknown`; ordinary reads and lifecycle recovery flags are not counted as context failures.
8. Execution-token/cost claims remain optional and are omitted when task/attempt correlation is incomplete.
9. No P0, plan-dispatch, lifecycle, acceptance, runtime-service, or telemetry architecture changes enter the experiment.
10. Fresh verification passes; only then can the plan become `completed`.
