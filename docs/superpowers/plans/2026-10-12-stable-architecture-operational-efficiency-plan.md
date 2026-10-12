---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: stable-architecture-operational-efficiency
targets:
  - artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline.jsonl
  - artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline-summary.json
  - artifacts/runtime-observation/2026-10-12-stable-architecture-pane-dry-run-baseline.jsonl
  - artifacts/runtime-observation/2026-10-12-stable-architecture-pane-dry-run-candidate.jsonl
  - artifacts/runtime-observation/2026-10-12-stable-architecture-pane-dry-run-comparison.json
  - artifacts/runtime-observation/2026-10-12-stable-architecture-pane-live-smoke.json
  - .github/workflows/repo-contracts.yml
  - .github/workflows/runtime-contracts.yml
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - docs/superpowers/plans/2026-10-12-stable-architecture-operational-efficiency-plan.md
---

# Stable Architecture Operational Efficiency

## Goal

Make the converged Project OS runtime cheaper to operate without reopening its
coordination architecture. The review of `c179fe6` is accepted with one source
correction: the implementation candidate is local
`7196983549392a5780f80b060daba5b05dd04d10`, based on
`origin/main=c179fe6408980b4b7081c806c72f256413a8c3f7`; it is not yet a
published remote-main commit. All new measurement and implementation decisions
must use that candidate source, not the older revision.

The plan admits only two immediate changes: fresh operational evidence and
dependency caching in required GitHub Actions jobs. A runtime change is
conditional: remove only the redundant unlocked pane validation when current
evidence proves it is a material recurring cost. The final lock-bound pane
validation, atomic evidence writes, MCP least-privilege discovery, launch
freshness checks, dormant managed-Codex capability gate, and concurrency cap
remain unchanged unless a separate approved plan reopens them.

## Implementation Outcomes

### Current operational baseline and decision record

Capture 10–20 ordinary, authorized read-only or normal-development attempts on
the current checkout using the existing launcher performance evidence. Preserve
raw JSONL and a summary containing phase medians/p95 values, total and
non-worker duration, subprocess counts by executable, retries, diagnostics,
receipt checks, cleanup/reconciliation outcomes, and an explicit retain/freeze/
optimize decision. Do not add telemetry infrastructure or present blocked live
probes as performance evidence.

### Lower-cost CI dependency setup

Configure `actions/setup-python@v5` pip caching in all maintained contract and
benchmark jobs. Use `requirements.txt` for repository and runtime jobs, and
both `requirements.txt` and `requirements-benchmark.txt` for the benchmark job.
Preserve the Windows matrix, required checks, immutable candidate checkout, and
workflow path behavior.

### Conditional pane-validation reduction

Only when the baseline identifies target discovery or launch preparation as a
recurring material cost, thread the already validated selected pane state from
`_resolve_target_selector()` through the ordinary auto-target launch path so the
selected auto pane is not validated a second time before launch. Keep
`_run_with_pane_ownership(..., verify=True)` as the one authoritative fresh
validation under the ownership lock. Exact-target launches and the exceptional
Codex retry/reconciliation path retain their current validation behavior, and
pane state remains local rather than entering the serialized result schema.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-performance-optimization`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `one dedicated task-owned worktree created before Task 1 from local candidate 7196983549392a5780f80b060daba5b05dd04d10`; keep the same worktree and source lineage through Task 4
- Commit policy: `no commits during execution`; the lead may create one later checkpoint only after fresh verification and explicit Git authorization
- Preauthorized local actions: `read declared repository sources and artifacts, run bounded local validation and authorized live probes, write the named plan/evidence/workflow/test files, and make the conditional launcher/test edit only after the baseline admission gate passes`
- User-approval actions: `credentials or provider installation, external writes, push, merge, destructive recovery, discard, cleanup outside task-owned paths, or changing protected GitHub settings`
- Parallel ownership: `none; baseline, CI edits, conditional runtime edits, and final verification share decision and validation ordering`
- Sequential fallback: `source/base reconciliation → baseline capture and decision → CI cache edit → conditional pane edit/tests → final validation and plan reconciliation`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/stable-architecture-efficiency`
- Base commit: `7196983549392a5780f80b060daba5b05dd04d10`
- Expected workspace: `dedicated worktree clean before Task 1; this plan is copied into that worktree before activation; candidate is local 7196983 based on origin/main c179fe6; no mid-plan worktree migration`
- Next action: `No further implementation action; branch disposition remains unchanged pending explicit Git authorization`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated worktree | `codex` | none | current baseline JSONL and summary | `artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline.jsonl; artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline-summary.json; 20 homogeneous managed rows, all reported_completed/deepagents-worker, worker_exit_code=0, cleanup=removed, retirement proven, reconciliation_required=false; prior blocked sample retained as *-blocked-publication artifacts` |
| Task 2 | `completed` | dedicated worktree | `codex` | Task 1 | workflow diff plus repository-contract validation | `.github/workflows/repo-contracts.yml; .github/workflows/runtime-contracts.yml; CACHE_CONFIG_VERIFIED; python scripts/validate_repo_contracts.py passed; YAML parse passed; CACHE_RUNTIME_OBSERVED=NOT YET MEASURED` |
| Task 3 | `completed` | dedicated worktree | `codex` | Task 1, Task 2 | cost-gated decision and unchanged lock-bound safety proof | `Explicitly deferred after measured baseline: target discovery median 85.772 ms and launch preparation median 47.026 ms, versus observation median 69,290.148 ms; no material non-worker cost. No launcher/test runtime patch made.` |
| Task 4 | `completed` | dedicated worktree | `codex` | Task 1, Task 2, Task 3 | final validators, focused tests, diff check, reconciled plan | `Fresh verification passed: 372 focused tests, 38 planning-lifecycle tests, repository-contract validation, planning validation, JSON parse, and git diff check` |

## Task Breakdown

### Task 1: Refresh the operational baseline

**Purpose:**
- Replace the September-era mixed-revision observation with current evidence before changing runtime behavior.

**Task Function:**
- Bounded operational measurement and source reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-first inspection and a bounded evidence refresh with no new runtime owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead owns the measurement admission decision.

**Specification Coverage:**
- Use candidate source at `7196983549392a5780f80b060daba5b05dd04d10`, and record its relationship to `origin/main=c179fe6408980b4b7081c806c72f256413a8c3f7`.
- Use a primary sample of 20 managed DeepAgents runs with valid assignment/attempt bindings. Any standalone/direct launcher runs are optional secondary evidence and must be reported separately, never aggregated with the managed sample.
- Measure end-to-end duration, separately attributable worker/provider duration, preflight, target discovery, launch preparation, delivery, observation, retirement, subprocess totals and executable breakdown, receipt checks, retries, diagnostics, cleanup, reconciliation, and manual intervention only when explicitly observable.
- Report count, median, max, and descriptive p95; do not use this small sample as an SLO or production tail-reliability claim.
- Admit runtime optimization only when a recurring non-worker phase is material and the paired proof in Task 3 passes its explicit reduction and correctness gates.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_new_performance_evidence`
- Inspect: `scripts/herdr_main_launcher.py:_record_performance_phase`
- Inspect: `scripts/herdr_main_launcher.py:_metrics_snapshot`
- Inspect: `scripts/herdr_main_launcher.py:_finalize_performance`
- Inspect: `artifacts/runtime-observation/representative-work-summary.json`
- Write: `artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline.jsonl`
- Write: `artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline-summary.json`

**Dependencies:**
- None; existing launcher performance evidence and the prior observation artifact are available.

**Authority:**
- Preauthorized local actions: `inspect the named source/artifact files, run 10–20 bounded authorized launcher attempts with existing local capabilities, and write the two named evidence artifacts`
- Stop for: `missing credentials/provider capability, workspace or base drift, cleanup outside task-owned paths, or any request to substitute synthetic data for unavailable live evidence`

**Steps:**
- [x] Step 1: Dedicated worktree and candidate identity were recorded before measurement: branch `codex/stable-architecture-efficiency`, `HEAD=7196983549392a5780f80b060daba5b05dd04d10`, candidate based on `origin/main=c179fe6408980b4b7081c806c72f256413a8c3f7`.
- [x] Step 2: Run 20 homogeneous managed DeepAgents probes through the documented direct launcher boundary with valid assignment/attempt bindings, unique names, the existing `--session auto --pane auto` path, and a 120-second runtime grant; preserve parsed performance and lifecycle evidence in the canonical JSONL. All 20 published valid `deepagents-worker` results.
- [x] Step 3: No standalone/direct runs were aggregated; the primary sample contains only the 20 managed DeepAgents rows.
- [x] Step 4: Record the measured sample and decision without fabricating worker/provider timing. The summary reports count, median, max, descriptive p95, phase stats, subprocess totals, lifecycle outcomes, and `worker_provider_duration_ms.status=unavailable`.
- [x] Step 5: Freeze runtime optimization on measured evidence: observation dominates total duration, while target discovery and launch preparation are sub-0.2-second phases; the pane-validation hypothesis is explicitly deferred.

**Verification:**
- [x] `python -m json.tool artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline-summary.json`
- Expected: the 20-row homogeneous sample, measured phase statistics, unavailable worker/provider attribution, and freeze decision are parseable; no synthetic or mixed-revision result is presented as current performance evidence.

**Exit Criteria:**
- Current baseline and decision record exist, are parseable, contain 20 homogeneous managed rows, and freeze runtime changes with an evidence-backed cost-gate decision recorded.

### Task 2: Cache CI dependencies without changing required coverage

**Purpose:**
- Reduce repeated package download and setup cost while preserving all current correctness and platform checks.

**Task Function:**
- Minimal workflow configuration optimization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded YAML-only change with a direct, low-risk operational benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing repository-contract validation owns workflow consistency.

**Specification Coverage:**
- Add `cache: pip` to the three maintained setup-python paths.
- Use `cache-dependency-path: requirements.txt` for `repo-contracts` and the runtime matrix.
- Use both `requirements.txt` and `requirements-benchmark.txt` for the benchmark job.
- Do not reduce Windows coverage, remove required jobs, add path filters, or alter checkout/ref assertions.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect/Modify: `.github/workflows/repo-contracts.yml:jobs.validate.steps[setup-python]`
- Inspect/Modify: `.github/workflows/runtime-contracts.yml:jobs.runtime.steps[setup-python]`
- Inspect/Modify: `.github/workflows/runtime-contracts.yml:jobs.benchmark.steps[setup-python]`
- Verify: `.github/workflows/repo-contracts.yml`
- Verify: `.github/workflows/runtime-contracts.yml`

**Dependencies:**
- Task 1 records the current baseline; no runtime change is required for this task.

**Authority:**
- Preauthorized local actions: `edit only the two named workflow files and run the declared repository-contract and YAML-adjacent validation commands`
- Stop for: `a workflow parser/validator reports changed required-job semantics, cache dependency paths do not match install inputs, or any protected GitHub setting must change`

**Steps:**
- [x] Step 1: Add pip caching and dependency paths to the repository and runtime setup-python steps.
- [x] Step 2: Add both dependency files to the benchmark cache path while leaving its two-file install command unchanged.
- [x] Step 3: Inspect the diff to confirm no matrix, permissions, concurrency, checkout, required test, or path behavior changed.

**Verification:**
- [x] `python scripts/validate_repo_contracts.py`
- Expected: repository-contract validation passes, the workflow diff contains only the intended setup-python cache fields, and local evidence is recorded as `CACHE_CONFIG_VERIFIED`; no CI latency improvement is claimed locally.

**Exit Criteria:**
- All three CI dependency-install paths use the correct pip cache key inputs and preserve existing required coverage. Warm-cache runtime improvement is `NOT YET MEASURED` unless an authorized exact-SHA PR run supplies remote evidence.

### Task 3: Apply the cost-gated pane-validation reduction

**Purpose:**
- Remove one redundant unlocked Herdr pane/process validation only when Task 1 proves it is worth the added internal handoff complexity.

**Task Function:**
- Narrow runtime overhead reduction with lock-bound safety preservation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the measured baseline does not show a material recurring non-worker cost; no runtime edit is admitted.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead validates the lock-bound safety invariant through focused tests.

**Specification Coverage:**
- Reuse the selected `_herdr_pane()` result produced during auto-target discovery instead of re-running it immediately in the launch-preparation path.
- Keep `_run_with_pane_ownership(..., verify=True)` unchanged as the authoritative fresh validation after ownership acquisition and before launch.
- Preserve exact-target behavior, Codex retry/reconciliation behavior, pane cwd/process evidence, rejection reasons, result schemas, atomic receipts, and ambiguous-delivery protection. Do not optimize the retry path; if a return-contract adjustment requires compatibility code there, retain its existing fresh `_herdr_pane()` validation.
- If Task 1 does not pass the admission gate, mark this task explicitly deferred and make no runtime code change.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Inspect/Modify: `scripts/herdr_main_launcher.py:_resolve_target_selector`
- Inspect/Modify: `scripts/herdr_main_launcher.py:resolve_launch`
- Inspect/Modify: `scripts/herdr_main_launcher.py:_run_with_pane_ownership`
- Inspect: `scripts/herdr_main_launcher.py:_main_body` retry path; preserve its existing fresh pane validation
- Verify/Modify: `tests/test_herdr_main_launcher.py` target-selection, launch, retry, and pane-ownership tests
- Write: `artifacts/runtime-observation/2026-10-12-stable-architecture-pane-dry-run-baseline.jsonl`
- Write: `artifacts/runtime-observation/2026-10-12-stable-architecture-pane-dry-run-candidate.jsonl`
- Write: `artifacts/runtime-observation/2026-10-12-stable-architecture-pane-dry-run-comparison.json`
- Write: `artifacts/runtime-observation/2026-10-12-stable-architecture-pane-live-smoke.json`

**Dependencies:**
- Task 1 must explicitly admit the hypothesis.
- Task 2 must be complete so the runtime diff remains isolated from workflow changes.

**Disposition:**
- Deferred. Task 1 now proves valid managed publication and shows that observation dominates the measured cost; the pane-validation admission gate fails the material-cost criterion. No launcher or test change is authorized in this execution.

**Authority:**
- Preauthorized local actions: `modify only the named launcher/test symbols after admission, thread selected pane state as an internal non-serialized handoff for the ordinary auto-target path, run paired dry-run trials and one bounded live smoke, and run focused tests`
- Stop for: `the required fresh lock-bound validation would be weakened, exact-target or retry semantics diverge, result schema changes, or the measured improvement fails the declared threshold`

**Steps:**
- [x] Step 1: Confirm the runtime change is not admitted after the measured baseline; do not start paired dry-runs or modify launcher code when the non-worker cost is immaterial.
- [x] Step 2: Deferred with Task 3; no dry-run artifacts are claimed.
- [x] Step 3: Not applicable; no runtime patch is made.
- [x] Step 4: Not applicable; no runtime patch is made.
- [x] Step 5: Preserved by making no runtime change; existing lock-bound and retry behavior remain untouched.
- [x] Step 6: Deferred; no candidate exists to compare.
- [x] Step 7: The 20 managed rows prove worker-owned result publication, cleanup, descendant retirement, and `reconciliation_required=false`; no pane optimization candidate is needed.
- [x] Step 8: No candidate was created; the deferral is recorded rather than adding a second optimization.

**Verification:**
- [x] No focused runtime test run is required because Task 3 made no runtime change; the publication guidance patch is covered by `py -B -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py -q` (`372 passed`).
- Expected: no launcher diff exists; lock-bound verification, retry validation, and serialized result schemas remain unchanged.

**Exit Criteria:**
- Either the admitted optimization passes paired dry-run, focused-test, and one-live-smoke gates with unchanged safety/lifecycle outcomes, or the task is explicitly deferred with the evidence and no runtime patch.

### Task 4: Final verification and plan reconciliation

**Purpose:**
- Prove the accepted changes as a coherent, minimal patch and record any conditional deferral honestly.

**Task Function:**
- Final artifact verification and coordination reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and source-of-truth reconciliation require controller authority.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is owned by the lead controller.

**Specification Coverage:**
- Confirm only measurement artifacts, pip-cache workflow fields, and—if admitted—the bounded pane handoff changed.
- Confirm the protected non-goals remained untouched: no new runtime manager, daemon, registry, workflow database, result/receipt schema, generic cache service, automatic fallback, persistent telemetry, MCP bypass, fsync weakening, launch-freshness merge, or concurrency increase.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-backend-verification`

**Files And Symbols:**
- Verify: all plan targets and `git diff --stat`
- Verify: `scripts/herdr_main_launcher.py:_codex_runtime_mcp_servers`
- Verify: `scripts/herdr_main_launcher.py:_run_with_pane_ownership`
- Verify: `scripts/secretary_live_runtime.py:_normal_managed_result_capability_available`
- Verify: `scripts/herdr_parallel_dispatch.py:MAX_CONCURRENCY`
- Modify: this plan’s task ledger, evidence, next action, and accepted deferral/decision text

**Dependencies:**
- Task 1, Task 2, and Task 3 complete or explicitly recorded as deferred/blocked with evidence.

**Authority:**
- Preauthorized local actions: `run final local validators/tests, inspect the complete diff, and update this plan with accepted evidence and deviations`
- Stop for: `failed required proof, stale base/workspace identity, unrecorded scope changes, unresolved cleanup/resource use, or any need for push/merge/protected-setting mutation`

**Steps:**
- [x] Step 1: Run the focused publication/launcher tests and the workflow, planning, and artifact validators required by the accepted scope.
- [x] Step 2: Run `python scripts/validate_repo_contracts.py`, `python scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-12-stable-architecture-operational-efficiency-plan.md`, and `git diff --check`.
- [x] Step 3: Review the complete diff and reconcile the task ledger with exact evidence paths, the publication root cause and regression, the 20-row managed baseline, and the deferred runtime optimization.
- [x] Step 4: Record local workflow proof as `CACHE_CONFIG_VERIFIED`; warm-cache runtime evidence remains `NOT YET MEASURED` because no authorized exact-SHA PR run exists.
- [x] Step 5: Mark the plan `completed` after fresh final verification returned `verified`; completion does not authorize commit, push, merge, or PR publication.

**Verification:**
- [x] `python scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-12-stable-architecture-operational-efficiency-plan.md`
- [x] `git diff --check`
- [x] `py -B -m pytest tests/test_dcode_project.py tests/test_herdr_main_launcher.py -q` (`372 passed`)
- [x] `py -B -m pytest tests/test_validate_planning_lifecycle.py -q` (`38 passed`)
- [x] `py -B scripts/validate_repo_contracts.py` (`Env gitignore contract validation passed`)
- [x] `py -B -m json.tool artifacts/runtime-observation/2026-10-12-stable-architecture-operational-baseline-summary.json` (valid JSON)
- Expected: the plan validates, the diff is whitespace-clean, and every admitted/deferred outcome is backed by an exact artifact, test, remote CI result, or command result.

**Exit Criteria:**
- The plan is executable without inventing file ownership or proof, and its completion gate distinguishes accepted CI savings, proven runtime savings, and an evidence-backed deferral.

## Verification

Use the final verification set appropriate to the admitted scope:

- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-12-stable-architecture-operational-efficiency-plan.md`
- `python -m pytest tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py -q` when Task 3 changes runtime code
- `python -m pytest tests/test_validate_planning_lifecycle.py -q`
- `git diff --check`

For the runtime optimization, require the paired dry-run comparison artifact
and one live managed smoke in addition to focused tests. For CI caching, local
verification proves only `CACHE_CONFIG_VERIFIED`; claim `CACHE_RUNTIME_OBSERVED`
only from an authorized exact-SHA GitHub run with warm-cache setup/install
timings. Do not claim live performance improvement unless the same candidate
workload has before/after evidence, the worker/provider portion is separated,
the subprocess breakdown is present, and lifecycle, cleanup, reconciliation,
and ambiguous-delivery outcomes remain unchanged.

## Completion Criteria

The plan is ready for completion verification when:

1. The current revision and workspace identity are recorded before measurement.
2. The primary baseline contains 20 homogeneous managed attempts, with standalone evidence separate, and reports count, median, max, and descriptive-only p95 with unavailable or blocked live fields explicit.
3. CI pip caching is structurally verified for all three maintained dependency-install paths without reducing required coverage; warm-cache runtime improvement is separately marked `CACHE_RUNTIME_OBSERVED` or `NOT YET MEASURED`.
4. The pane-validation change is either proven by paired dry-runs, focused tests, and one live managed smoke against the two-dimensional cost/correctness gate or explicitly deferred with no runtime patch.
5. The final diff contains no new runtime manager, daemon, registry, workflow database, result/receipt schema, generic cache service, fallback, persistent telemetry, fsync weakening, MCP least-privilege regression, launch-freshness collapse, retry-path optimization, or concurrency increase.
6. All required task and final verification evidence is recorded in this plan, including deviations, remote-proof status, and blockers.
7. `skill-verification-before-completion` runs fresh final verification and returns `verified` before any later status transition to `completed`.

The following remain out of scope: managed Codex result-adapter implementation,
dormant-path deletion/quarantine, concurrency changes above `MAX_CONCURRENCY = 2`,
new persistent telemetry, GitHub ruleset administration, and any external
publication or merge action.
