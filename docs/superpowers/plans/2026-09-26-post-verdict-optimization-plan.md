---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: post-verdict-optimization
targets:
  - scripts/benchmark_worker_contract.py
  - scripts/herdr_main_launcher.py
  - tests/test_worker_contract_benchmark.py
  - tests/test_herdr_main_launcher.py
  - .github/workflows/runtime-contracts.yml
  - requirements-benchmark.txt
  - artifacts/worker-contract-benchmark/
  - artifacts/completion-monitoring/task3-fake-herdr-evidence.json
  - docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md
---

# Post-Verdict Optimization Plan

## Review Summary

The verdict's priority change is correct: harden measurement, then reduce
completion-monitoring subprocesses, then inspect runtime-binding duplication.

Repository evidence:

- `codex/worker-contract-benchmark` at `b420c9f` has the benchmark harness and
  six focused tests; the focused test file passes locally.
- Tokenizer override bug reproduces: `measure_offline(..., "o200k_base")`
  still writes `cl100k_base`.
- Incomplete report input is not rejected cleanly; `_write_report()` reaches
  `StopIteration` after accepting an unmatched row.
- `requirements.txt` has no benchmark-only tokenizer dependency, and
  `.github/workflows/runtime-contracts.yml` does not run the benchmark test.
- `_deepagents_completion_evidence()` calls
  `_deepagents_completion_snapshot()` every completion-poll cycle. Each
  snapshot can issue `pane wait-output`, `pane process-info`, and `pane read`.

Source commit `5803d66` named by the verdict is not present in local Git. Use
`main` at `88cece2` and benchmark branch `b420c9f` as repository evidence. Do
not reopen closed P0 work or claim total latency, total model tokens, or cost
from the current benchmark.

## Goal

Reduce recurring completion-monitoring overhead without changing lifecycle,
settlement, cleanup, recovery, or acceptance semantics. Make benchmark claims
fail closed before using them to select or retain optimization changes.

## Implementation Outcomes

### Trusted benchmark evidence

Benchmark reports validate complete paired rows keyed by `(task_id, run)`, use
resolved tokenizer provenance, preserve `unknown` when evidence is missing, and
keep one canonical tracked evidence set. Benchmark-only dependencies stay out
of runtime installation.

### Receipt-first completion monitoring

Completion checks the authoritative receipt frequently and runs pane diagnostics
on a slower bounded cadence. Missing receipts still receive periodic diagnostic
sampling and existing timeout, grace, failure, cleanup, and reconciliation
behavior remains intact.

### Evidence-backed follow-on scope

Completion candidates are retained only when subprocess reduction and failure
semantics meet the acceptance gate. Runtime-binding simplification starts with
an ownership audit and changes only mechanically derivable fields proven safe.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`
- Isolation: `optional worktree`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect `main` and `b420c9f`, edit named benchmark/launcher/test/workflow surfaces, run declared local checks, and record evidence in this plan
- User-approval actions: carry benchmark commit `b420c9f` into the execution workspace, push, merge, publication, delete any tracked artifact, and external worker runs not covered by task authority
- Parallel ownership: none
- Sequential fallback: complete benchmark hardening before launcher changes; complete launcher tests before any runtime-binding edit

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `88cece2`
- Expected workspace: preserve unrelated untracked `.playwright-mcp/`, `db/`, and existing benchmark experiment plan
- Next action: none; execution and verification complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current workspace | `codex` | none | source and benchmark ownership map | `main@88cece2`, `b420c9f` carried; unrelated untracked files preserved; focused tests passed |
| Task 2 | `completed` | current workspace | `codex` | Task 1 | fail-closed benchmark tests and Linux CI path | `10` benchmark tests passed; canonical artifacts and Ubuntu job recorded |
| Task 3 | `completed` | current workspace | `codex` | Task 2 | cadence tests and six-class monitoring evidence | `310` focused tests passed; `artifacts/completion-monitoring/task3-fake-herdr-evidence.json`; 2s retained |
| Task 4 | `completed` | current workspace | `codex` | Task 3 | runtime-binding ownership decision and final validators | Audit found no mechanically safe reduction; source unchanged |

## Task Breakdown

### Task 1: Reconcile source and freeze optimization boundary

**Purpose:**
- Establish exact source, branch, artifacts, metrics, and non-goals before edits.

**Task Function:**
- Source-first repository mapping and benchmark-boundary review.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded inspection; no delegated implementation needed.

**Validator Profile:**
- Controller-selected: none
- Selection basis: source and test evidence are local and deterministic.

**Specification Coverage:**
- Preserve closed P0 work.
- Use launcher-delivered handoff tokens as benchmark scope.
- Treat missing-context evidence and latency/cost claims as separate metrics.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `scripts/benchmark_worker_contract.py:measure_offline`, `_row`, `_write_report`
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`, `_deepagents_completion_evidence`
- Inspect: `tests/test_worker_contract_benchmark.py`
- Inspect: `docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md`

**Dependencies:**
- None. Existing untracked files remain untouched.

**Authority:**
- Preauthorized local actions: inspect Git history, branch diffs, source, tests, workflows, and benchmark artifacts; update this plan's evidence only.
- Stop for: missing source ownership, changed base commit, or requested scope beyond benchmark and launcher monitoring.

**Steps:**
- [x] Step 1: Confirm `main` at `88cece2` and benchmark branch at `b420c9f`; carry `b420c9f` into the execution workspace or stop with the exact conflict list; record the decision.
- [x] Step 2: Map benchmark inputs, delivered handoff boundary, receipt authority, pane fallback, cleanup, and reconciliation paths.
- [x] Step 3: Freeze non-goals: no scheduler, event bus, persistent cache, telemetry service, broad prompt compression, or total-cost claim.

**Verification:**
- [x] `git status --short` and `git log --oneline -5`
- [x] `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py` (`272 passed` before Task 3 edits)
- Expected: source map is recorded; existing focused production tests pass; unrelated workspace files remain unmodified.

**Exit Criteria:**
- Exact source revision, benchmark baseline, metric boundary, and protected lifecycle semantics are recorded.

### Task 2: Harden benchmark and canonicalize evidence

**Purpose:**
- Make every future comparison reproducible, paired, provenance-correct, and fail closed.

**Task Function:**
- Implement benchmark schema validation, report aggregation, dependency isolation, and evidence cleanup.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small deterministic Python changes with focused tests.

**Validator Profile:**
- Controller-selected: none
- Selection basis: validator commands provide direct proof.

**Specification Coverage:**
- Exact `(task_id, run)` pairing with one `baseline` and one `bounded` row.
- Pair-level invariants for task, run, tokenizer name/version, source revision, baseline identity, model/profile, and manifest/fixture digest.
- Resolved tokenizer override recorded in every row.
- `missing_context=unknown` for offline rows and for live rows lacking auditable worker evidence.
- Benchmark dependency isolated from runtime requirements.
- One canonical tracked evidence set.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/benchmark_worker_contract.py:_row`, `measure_offline`, `_reduction`, `_write_report`, CLI validation
- Modify: `tests/test_worker_contract_benchmark.py`
- Create: `requirements-benchmark.txt` with pinned `tiktoken` version used by accepted evidence
- Modify: `.github/workflows/runtime-contracts.yml` with one Ubuntu-only benchmark job/step
- Modify: `artifacts/worker-contract-benchmark/` to retain only canonical final offline/run/report files
- Update: `docs/superpowers/plans/2026-09-26-18-53-worker-contract-communication-efficiency-experiment-plan.md` evidence and claim limits

**Dependencies:**
- Task 1 source decision.
- `b420c9f` must be carried into the execution workspace before edits; unresolved conflicts block Task 2.

**Authority:**
- Preauthorized local actions: edit named benchmark, test, dependency, workflow, experiment-plan, and three canonical artifact files; run offline benchmark and CI-equivalent local checks.
- Stop for: adding `tiktoken` to `requirements.txt`, deleting or relocating any tracked artifact without separate approval, inventing missing-context evidence, or accepting incomplete rows.

**Steps:**
- [x] Step 1: Add explicit row schema. Require string `task_id`, mode in `{baseline,bounded}`, non-negative integer `run`, tokenizer name/version, starting revision, baseline name, model/profile, manifest digest, fixture digest, and numeric delivered-handoff token count; validate every row before grouping.
- [x] Step 2: Key rows by `(task_id, run)`; reject missing counterparts, duplicates, unknown modes, and invariant mismatches instead of raising incidental `StopIteration` or dropping rows.
- [x] Step 3: Aggregate only validated pairs; reject non-positive baseline token counts.
- [x] Step 4: Pass resolved tokenizer name into `_row`; add override test using `o200k_base` and assert row provenance matches the encoding used.
- [x] Step 5: Add manifest/fixture digest fields. Hash canonical UTF-8 bytes of sorted-key JSON for the manifest and benchmark fixture files in stable relative-path order; require equal digest, source revision, baseline identity, model/profile, and tokenizer name/version within each pair. Replace offline missing-context detail with explicit non-execution `unknown` wording.
- [x] Step 6: Add a separate Ubuntu benchmark CI job with its own Python setup and benchmark dependency installation; do not install benchmark dependencies in the existing `runtime` matrix job.
- [x] Step 7: Designate only `artifacts/worker-contract-benchmark/benchmark-offline-task-scoped.jsonl`, `artifacts/worker-contract-benchmark/benchmark-runs-full-3rep.jsonl`, and `artifacts/worker-contract-benchmark/benchmark-report-task-scoped.md` as canonical final evidence; preserve all other artifacts until separate deletion or relocation approval. Preserve limitations and the scoped term `launcher-delivered handoff tokens`.

**Verification:**
- [x] `python -m pytest -q tests/test_worker_contract_benchmark.py` (`10 passed`)
- [x] `python scripts/benchmark_worker_contract.py offline --fixtures tests/fixtures/worker_contract_benchmark/manifest.json --output <temp>/final-offline.jsonl --tokenizer cl100k_base`
- [x] `python scripts/benchmark_worker_contract.py report --input <temp>/final-runs.jsonl --output <temp>/final-report.md`
- [x] Test missing pair, duplicate pair, tokenizer mismatch, revision mismatch, digest mismatch, unknown mode, and malformed denominator fixtures.
- Expected: valid reports contain only complete pairs; invalid reports fail with actionable validation errors; override provenance is correct; runtime requirements remain unchanged.

**Exit Criteria:**
- Benchmark report cannot produce a result from incomplete or mismatched data, and canonical artifacts have one source of measurement truth.

### Task 3: Make completion monitoring receipt-first

**Purpose:**
- Reduce repeated Herdr pane diagnostics while preserving receipt authority and fallback failure detection.

**Task Function:**
- Refactor the existing completion loop to separate receipt cadence from diagnostic cadence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-risk lifecycle code needs direct source control and focused regression proof.

**Validator Profile:**
- Controller-selected: none
- Selection basis: existing launcher tests plus backend verification cover direct command and fallback behavior.

**Specification Coverage:**
- Frequent cheap receipt reads.
- Slower bounded pane diagnostic probes, initially benchmarked at `1s`, `2s`, and `5s` candidates.
- Immediate confirmed-receipt return.
- Existing attempt deadline, receipt grace, stale/wrong-attempt rejection, terminal/crash detection, missing-receipt fallback, cleanup verification, and reconciliation unchanged.
- No watcher thread, event bus, persistent monitor state, or telemetry framework.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_DEEPAGENTS_*` polling constants, `_deepagents_completion_snapshot`, `_deepagents_completion_evidence`
- Modify: `tests/test_herdr_main_launcher.py` completion, receipt, timeout, and transport-failure tests
- Verify: `scripts/herdr_attempt_contract.py` receipt parsing and attempt identity rules
- Verify: `tests/test_herdr_attempt_contract.py`

**Dependencies:**
- Task 2 complete enough to define measurement output and artifact retention.
- Existing receipt and pane semantics remain canonical.

**Authority:**
- Preauthorized local actions: edit named launcher and launcher/receipt tests; add bounded diagnostic scheduling and performance evidence fields; run mocked and local boundary checks.
- Stop for: changed lifecycle classification, removed pane fallback, new persistent state, altered receipt authority, or unexplained deadline/grace changes.

**Steps:**
- [x] Step 1: Add one diagnostic cadence separate from receipt polling. Keep receipt reads at `0.1s`; benchmark diagnostic intervals at `1s`, `2s`, and `5s`; cap diagnostic interval at the existing attempt-observation budget and reject negative values.
- [x] Step 2: Check receipt before every diagnostic decision; return confirmed receipt without pane commands.
- [x] Step 3: Keep periodic `process-info`/`read` fallback when receipt is absent. Periodic probes pass `wait_for_marker=False` so `pane wait-output` cannot block receipt polling for up to `_HERDR_COMMAND_TIMEOUT`; preserve marker detection from pane reads and existing terminal-state handling.
- [x] Step 4: Record diagnostic probe count, monitoring subprocess counts by command, receipt-observation time, completion-return time, detection delay when derivable, lifecycle classification, cleanup result, and reconciliation result without logging prompts or credentials.
- [x] Step 5: Add deterministic tests for timely receipt, delayed receipt, receipt failure, process termination without receipt, active timeout, diagnostic transport failure, stale receipt, and cadence scheduling.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py` (`310 passed`)
- [x] Compare current cadence against `1s`, `2s`, and `5s` diagnostic candidates using the existing `_deepagents_completion_evidence()` test seam and one fixed local fake-Herdr harness per class; run 3 repetitions per interval and class.
- [x] Record Python version, OS, repository revision, fixture/harness digest, interval, repetition, subprocess counts by command, completion-return time, receipt-observation time when available, detection delay, lifecycle classification, cleanup result, and reconciliation result in `artifacts/completion-monitoring/task3-fake-herdr-evidence.json`.
- Expected: the lead controller owns the gate; retained `2s` candidate has `51.515%` fewer monitoring subprocesses than current `1s`, all `18` candidate rows match expected outcomes, receipt detection delay is `0 ms`, and missing-receipt fallback returns within the `2s` observation budget.

**Exit Criteria:**
- `2s` candidate retained as default diagnostic cadence; no lifecycle, cleanup, reconciliation, or receipt-authority change observed.

### Task 4: Audit runtime bindings and close with evidence

**Purpose:**
- Audit mechanically duplicated controller inputs; implement none unless Task 3 evidence identifies a safe candidate and separate approval is granted.

**Task Function:**
- Build field ownership map, implement one smallest safe derivation if justified, and verify unchanged grants.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: gated follow-on; scope stays small unless evidence identifies a safe duplicate.

**Validator Profile:**
- Controller-selected: none
- Selection basis: existing runtime contract tests and final validators are sufficient.

**Specification Coverage:**
- Keep explicit: `allowed_write_set`, `mutable_resources`, `runtime_grant`, remaining task allowance, accepted prerequisites, and explicitly constrained local capabilities.
- Consider only mechanically derivable identity, pane/session auto-path, or deadline representation after semantic proof.
- Goal is zero duplicated controller inputs, not minimum JSON size.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`, `_resolve_target_selector`, runtime-binding construction
- Inspect: `scripts/herdr_parallel_dispatch.py:_launcher_command`
- Inspect: `scripts/project_os_runtime/attempt.py`
- Modify only if justified: named runtime-binding producer and its focused tests
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_project_os_runtime.py`

**Dependencies:**
- Task 3 retained optimization or explicit `no optimization justified` evidence.

**Authority:**
- Preauthorized local actions: inspect ownership, produce field map, and update plan evidence; no production runtime edit is preauthorized.
- Stop for: any implementation candidate, inferred authority, changed mutable scope, changed grant digest semantics, new runtime state, or missing separate user approval for a runtime-binding edit.

**Steps:**
- [x] Step 1: Build table for each runtime field: canonical owner, controller decision, mechanical fact, validation owner, derivation proof, and manual-operation cost.
- [x] Step 2: Select zero or one candidate; prove source equivalence and request separate approval before editing.
- [x] Step 3: If approved, add focused regression tests for explicit authority fields and derived-field freshness; otherwise keep source unchanged.
- [x] Step 4: Record retained change or `no optimization justified`; do not force a smaller contract.

**Ownership Decision:**

| Field | Canonical owner | Decision |
| --- | --- | --- |
| `assignment_id`, `repository_identity`, `plan_identity` | attempt contract / dispatch | Keep explicit; identity validation and digest binding need controller values. |
| `task`, `task_sha256`, `remaining_authorized_task_allowance` | controller / launcher boundary | Keep explicit; task text and allowance are authority inputs, not derivable facts. |
| `runtime_grant`, `grant_digest` | attempt contract | Keep explicit; launcher recomputes and validates digest rather than deriving authority. |
| `session`, `pane`, `cwd`, `expected_base` | target selector / dispatch | Keep explicit; auto-selection and Git-base checks are separate boundary decisions. |
| `mcp_select`, `local_capabilities` | runtime grant / dispatch | Keep explicit; requested versus effective capability state must remain visible. |
| `pane_cwd`, process IDs, completion evidence | Herdr observation | Derived runtime facts; not controller bindings. |

Result: `no optimization justified`; no runtime-binding source edit made.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py` (`310 passed` with attempt-contract coverage)
- [x] `python scripts/validate_planning_lifecycle.py --repo-root . --strict` (passed)
- Expected: grant, admission, freshness, lifecycle, settlement, recovery, acceptance, and worker semantics remain unchanged.

**Exit Criteria:**
- Ownership decision is explicit, tested, and either removes one proven duplicate or records why no safe reduction exists.

## Verification

- `python -m pytest -q tests/test_worker_contract_benchmark.py tests/test_herdr_main_launcher.py tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py` (`320 passed`)
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict` (passed)
- `python scripts/validate_repo_contracts.py --repo-root .` (passed)
- `python scripts/sync_agent_adapters.py --all-platforms --check` (passed)
- `python scripts/validate_agent_runtime_drift.py --all-platforms` (passed after `deploy_agent_runtime.py --target all`)
- `git diff --check` (passed)

## Completion Criteria

1. Benchmark comparison validation fails closed on incomplete, duplicate, or mismatched pairs.
2. Tokenizer override provenance and benchmark-only dependency path are tested.
3. Canonical benchmark artifacts and claim boundaries are documented; unsupported missing-context, total-latency, total-token, and cost claims are absent.
4. Completion monitoring either reduces monitoring subprocesses by the task gate with unchanged lifecycle outcomes or records `no optimization justified`.
5. Receipt authority, timeout/grace, fallback, cleanup, reconciliation, and stale-attempt protections have fresh regression evidence.
6. Runtime-binding changes are limited to proven mechanical duplication or explicitly deferred.
7. Final validators pass, no unrelated untracked files are changed, and deviations/blockers are recorded here.
8. Plan status changes to `completed` only after `skill-verification-before-completion` returns `verified`.
