---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: representative-work-observation-and-cost-gated-optimization
targets:
  - artifacts/runtime-observation/representative-work.jsonl
  - artifacts/runtime-observation/representative-work-summary.json
  - artifacts/completion-monitoring/next-convergence-evidence.json
  - docs/superpowers/plans/2026-09-27-completion-monitoring-convergence-plan.md
---

# Representative Work Observation And Cost-Gated Optimization

## Verdict Review

PR #50 closes completion-monitoring convergence. The deterministic fake-Herdr
result is sufficient for the bounded receipt-first fix, but it is not evidence
that another Project OS component is a production bottleneck.

Keep these areas frozen until representative work identifies recurring cost:

- plan-to-dispatch coordination
- worker-contract and prompt compression
- Git preflight
- runtime-binding projection
- completion polling, diagnostic cadence, receipt grace, and the `0.5s` diagnostic cap
- schedulers, caches, context stores, telemetry services, and other persistent runtime state

Do not reopen a component because source code repeats an observation or because
one synthetic case looks expensive. Reopen only when ordinary Project OS work
shows a recurring material cost, the owner can name a baseline and expected
absolute improvement, correctness gates remain explicit, and the change does not
add an unnecessary owner or persistent state.

## Goal

Observe 10–20 ordinary Project OS attempts through the existing launcher, use
its current lifecycle and performance evidence to identify the dominant recurring
cost, and make one explicit retain/freeze/reopen decision. This plan does not
change launcher behavior, completion constants, worker contracts, or runtime
ownership.

## Implementation Outcomes

### Evidence hygiene

The completed convergence plan says `Next action: none; completed` and
`Blockers: none`. The committed completion-monitoring artifact records source
provenance that matches the measured clean revisions. Dirty working-tree
measurements remain explicitly labeled instead of being presented as `HEAD`.

### Representative observation set

Raw launcher results are preserved as JSON Lines at
`artifacts/runtime-observation/representative-work.jsonl`. Each record retains
the UTC capture time, Git revision, full launcher argv, launcher exit code, task
category, and parsed launcher evidence. The sample contains 10–20 ordinary
read-only or normal development tasks collected from actual Project OS use; it
does not add synthetic benchmark fixtures or a telemetry service.

### One-shot cost summary

`artifacts/runtime-observation/representative-work-summary.json` records phase
medians and p95 values, total duration, subprocess counts, attempt/retry data,
diagnostic errors and timeouts, cleanup state, reconciliation-required state,
task verification state, and receipt fields when present. Worker execution time
is kept separate from launcher phase time. `time_to_receipt_ms` is never labeled
as monitoring latency because it includes worker execution.

### Cost-gated decision

The observation record names one of these outcomes:

1. worker execution dominates: leave Project OS unchanged;
2. target discovery or launch preparation recurs as the largest non-worker cost:
   open a separate duplicate-pane-validation investigation;
3. observation recurs as the largest cost: inspect repeated diagnostic timeout,
   transport error, missing receipt, or reconciliation causes before changing
   `0.1s`, `2s`, or `0.5s` defaults;
4. retirement or recovery recurs as the largest cost: fix the repeated lifecycle
   cause rather than adding recovery infrastructure;
5. no recurring material cost: freeze current runtime and close this observation
   cycle.

An optimization is not admitted from this plan unless the decision record names
the affected owner, sample count, median and p95 cost, share of end-to-end time,
expected absolute improvement, correctness checks, and the separate follow-on
plan that will own the patch.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Workspace: current `main` checkout at merge commit `318ac66cf8637b4e63049b0673cc5971f207379b`
- Commit policy: no commit during observation; commit only the plan and accepted evidence after fresh verification
- Runtime changes: none in this plan
- Persistent services/state: none
- Preserved unrelated files: `.playwright-mcp/`, `db/`, and `temp_evidence.json`
- Required skills: `skill-writing-plans`, `skill-performance-optimization`, `skill-backend-verification`, `skill-verification-before-completion`
- Stop conditions: credentials or provider installation, unclear task ownership, missing authoritative receipt, cleanup outside task-owned paths, or a request to optimize before the evidence gate passes

## Coordination State

- Base commit: `318ac66cf8637b4e63049b0673cc5971f207379b`
- Expected branch: `main`
- Expected tracked state: clean before execution
- Working-tree preservation: do not modify or delete `.playwright-mcp/`, `db/`, or `temp_evidence.json`
- Shared write owner: lead controller owns both observation artifacts and both maintenance corrections
- Next action: none; completed
- Blockers: none

## Execution Record

- Task 1: completed. `artifacts/completion-monitoring/next-convergence-evidence.json` now records clean `main` revision `318ac66cf8637b4e63049b0673cc5971f207379b` and matching source SHA-256; completed convergence plan now says `Next action: none; completed`.
- Task 2: completed with 10 live read-only launcher attempts. Eight used a 20-second worker budget; two used the original 120-second budget. All preserved authoritative receipt, worker exit, descendant termination, and cleanup evidence.
- Task 2 limitation: standalone launcher runs omit managed assignment bindings, so `dcode-project` intentionally does not publish `task-result.json`. `task_result=unverified` and `reconciliation_required=true` are therefore expected for this probe mode; no runtime patch is justified without a managed-assignment reproduction.
- Task 3: completed. `artifacts/runtime-observation/representative-work-summary.json` reports observation median `20863.482ms`, p95 `120811.556ms`, pane-run median `80.043ms`, pane-run p95 `92.59ms`, and 10/10 cleanup removal.
- Task 4: completed. Decision is `freeze_project_os_runtime`; worker/provider execution dominates observed elapsed time. No component, timeout, cadence, watcher, cache, scheduler, or persistent state is reopened.
- Deviation: sample uses exploratory live read-only tasks with mixed worker budgets because provider-bound runs reached 20–120 seconds. Evidence is not a before/after benchmark and does not support a production latency claim.
- Task 5: verified. JSON/JSONL parsing passed; adapter sync check passed; runtime drift validation passed; planning lifecycle validation passed; focused launcher and planning tests passed (`220 passed in 6.30s`); `git diff --check` passed.

## Task Breakdown

### Task 1: Reconcile completed-plan and benchmark provenance state

**Purpose:**
- Restore Git-tracked planning truth and remove misleading benchmark provenance before collecting new evidence.

**Task Function:**
- Documentation and artifact maintenance.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded maintenance with no delegated implementation needed.

**Specification Coverage:**
- Completed convergence plan has no actionable next step.
- Benchmark artifact distinguishes clean `HEAD` measurement from dirty working-tree measurement.

**Required Skills:**
- `skill-writing-plans`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify `docs/superpowers/plans/2026-09-27-completion-monitoring-convergence-plan.md` coordination state.
- Regenerate `artifacts/completion-monitoring/next-convergence-evidence.json` from clean source revisions.
- Inspect `scripts/benchmark_completion_monitoring.py:revision` and `scripts/benchmark_completion_monitoring.py:main` without changing runtime behavior.

**Dependencies:**
- None.

**Authority:**
- Preauthorized: edit the named plan metadata, regenerate the named artifact, and run read-only validators.
- Stop for: any request to rewrite historical results, change benchmark cases, or alter launcher code.

**Steps:**
1. Set the completed plan coordination state to `Next action: none; completed` and `Blockers: none`.
2. Run `py scripts/benchmark_completion_monitoring.py --baseline-revision d797028 --repetitions 3 --output artifacts/completion-monitoring/next-convergence-evidence.json` from clean `main`.
3. Confirm artifact `candidate_revision` equals `318ac66cf8637b4e63049b0673cc5971f207379b` and its candidate source hash matches `git show HEAD:scripts/herdr_main_launcher.py`.
4. Validate with `python -m json.tool artifacts/completion-monitoring/next-convergence-evidence.json`.

**Verification:**
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python -m json.tool artifacts/completion-monitoring/next-convergence-evidence.json`
- `git diff --check`

**Exit Criteria:**
- Completed plan state is truthful, benchmark provenance is reproducible, and no launcher behavior changed.

### Task 2: Capture representative Project OS attempts

**Purpose:**
- Collect ordinary runtime evidence before selecting another optimization target.

**Task Function:**
- Live backend/runtime observation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live observation requires one owner for task admission, redaction, and cleanup proof.

**Specification Coverage:**
- Sample size is 10–20 ordinary attempts.
- Existing launcher evidence remains the single runtime source.
- No synthetic benchmark suite or telemetry service is added.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect `scripts/herdr_main_launcher.py:_new_performance_evidence`.
- Inspect `scripts/herdr_main_launcher.py:_record_performance_phase`.
- Inspect `scripts/herdr_main_launcher.py:_record_performance_attempt`.
- Inspect `scripts/herdr_main_launcher.py:_finalize_performance`.
- Write `artifacts/runtime-observation/representative-work.jsonl`.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized: run bounded ordinary tasks through the existing launcher and write redacted evidence under `artifacts/runtime-observation/`.
- Stop for: credentials, provider installation, ambiguous completion, missing cleanup proof, or any mutation outside the task-owned worktree.

**Steps:**
1. Use the documented launcher boundary: `py scripts/herdr_main_launcher.py --profile normal --session auto --pane auto --cwd "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter" --expected-base 318ac66cf8637b4e63049b0673cc5971f207379b --executor deepagents --grant-turns 4 --grant-wall-clock-seconds 120 --task "Return the requested result" --name "representative-observation"`; run one invocation per actual task and record its exact task text and unique name in the JSONL record.
2. Run 10–20 actual ordinary tasks, not repeated copies of one synthetic fixture; prefer read-only or normal development requests already occurring in this repository.
3. Capture stdout JSON, launcher exit code, UTC timestamp, Git revision, task category, and full argv for every attempt.
4. Redact credentials, prompts containing private data, and unrelated pane output; retain lifecycle, performance, cleanup, reconciliation, task-result, and completion-receipt fields.
5. Append one JSON object per attempt to `artifacts/runtime-observation/representative-work.jsonl`.

**Verification:**
- Every record parses with `python -c "import json, pathlib; [json.loads(line) for line in pathlib.Path('artifacts/runtime-observation/representative-work.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]"`.
- Record count is between 10 and 20.
- Each record has `captured_at_utc`, `git_revision`, `argv`, `launcher_exit_code`, and parsed launcher evidence.
- Each completed record has lifecycle, cleanup, reconciliation, and task-verification evidence or an explicit classified failure.

**Exit Criteria:**
- Representative raw evidence exists, is parseable, is redacted, and preserves direct success/failure/cleanup facts.

### Task 3: Produce one-shot representative cost summary

**Purpose:**
- Convert raw attempts into a decision record without introducing telemetry infrastructure.

**Task Function:**
- Offline evidence analysis.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: offline aggregation and attribution must use one evidence owner.

**Specification Coverage:**
- Phase cost, worker cost, subprocess overhead, retries, diagnostics, cleanup, reconciliation, and verification are visible.
- Receipt timing is not misclassified as orchestration latency.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Read `artifacts/runtime-observation/representative-work.jsonl`.
- Write `artifacts/runtime-observation/representative-work-summary.json`.
- Reuse phase names from `scripts/herdr_main_launcher.py:_PERFORMANCE_PHASES`.

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized: perform offline aggregation with Python standard library and write the named summary artifact.
- Stop for: missing fields that prevent honest attribution; record the limitation instead of inventing a metric.

**Steps:**
1. Group attempts by ordinary task category and outcome.
2. Report count, median, and p95 for each phase in `_PERFORMANCE_PHASES`, total duration, unattributed duration, subprocess total, and `pane_run_duration_ms` when present.
3. Report counts for retries/attempts, diagnostic errors, diagnostic timeouts, missing receipts, reconciliation-required outcomes, cleanup states, and task verification states using only fields present in the raw evidence.
4. Keep worker execution separate from launcher phases; label `time_to_receipt_ms` as end-to-end time-to-receipt when present.
5. Write the summary plus an explicit `decision` object containing `outcome`, `owner`, `sample_count`, `dominant_signal`, `expected_improvement`, `correctness_gates`, and `follow_on_plan`.
6. Do not add `scripts/summarize_runtime_traces.py` during the first observation cycle. Add it only in a separate plan after repeated manual aggregation is itself demonstrated as recurring work.

**Verification:**
- `python -m json.tool artifacts/runtime-observation/representative-work-summary.json`
- Every reported aggregate can be traced to raw JSONL records.
- No field calls `time_to_receipt_ms` monitoring latency.
- No controller-intervention metric appears unless explicit trace evidence exists.

**Exit Criteria:**
- Summary supports a reproducible freeze or reopen decision without unsupported performance claims.

### Task 4: Apply the cost gate and close or hand off the next optimization

**Purpose:**
- Prevent speculative runtime changes and create a separate owner only when evidence earns one.

**Task Function:**
- Optimization triage and plan handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: decision gate and follow-on plan handoff are controller-owned.

**Specification Coverage:**
- Worker-dominant work leaves Project OS unchanged.
- Target discovery, observation, retirement, and recovery reopen only with recurring material evidence.
- Frozen constants and ownership boundaries remain intact.

**Required Skills:**
- `skill-performance-optimization`
- `skill-writing-plans`

**Files And Symbols:**
- Read `artifacts/runtime-observation/representative-work-summary.json`.
- Update this plan's decision and coordination ledger.
- Create a separate plan under `docs/superpowers/plans/` only when the admission gate passes.

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized: record freeze/close decision and, when admitted, draft a separate implementation plan naming one component and one baseline.
- Stop for: direct runtime edits, timeout tuning, new service/state, or bundled optimization proposals.

**Steps:**
1. Mark the cycle `frozen` when no component is a recurring material cost.
2. Mark the worker path dominant and take no Project OS action when worker execution explains most elapsed time.
3. For target discovery or launch preparation, name duplicate pane validation as the only follow-on hypothesis; do not remove the earlier validation in this plan.
4. For observation, classify repeated timeout, transport error, missing receipt, or reconciliation causes before considering any constant change; keep `0.1s`, `2s`, and `0.5s` unchanged when failures are not recurring.
5. For retirement or recovery, trace the repeated lifecycle cause before proposing infrastructure.
6. Admit one follow-on optimization only when the summary names recurring count, median/p95 cost, end-to-end share, expected absolute improvement, correctness gates, and a single owning file/symbol set.

**Verification:**
- Decision cites exact raw and summary artifact paths.
- Frozen areas remain unchanged.
- Any follow-on plan has one component, one hypothesis, one before/after workload, and one correctness gate.

**Exit Criteria:**
- Current plan ends with a documented freeze or a bounded follow-on plan; no speculative runtime patch is included.

### Task 5: Final verification and reconciliation

**Purpose:**
- Prove observation artifacts, planning state, generated agent surfaces, and preserved workspace state are consistent.

**Task Function:**
- Final verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification is one sequential acceptance step.

**Specification Coverage:**
- Fresh checks pass and unrelated untracked files remain untouched.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify all files named in this plan.
- Verify `scripts/herdr_main_launcher.py` and its existing performance evidence contract remain unchanged.

**Dependencies:**
- Tasks 1–4 complete.

**Authority:**
- Preauthorized: run validators, inspect diffs, update this plan's evidence and final state.
- Stop for: failed validator, changed base, unrecorded scope deviation, or altered unrelated untracked files.

**Steps:**
1. Run `python scripts/sync_agent_adapters.py --all-platforms --check`.
2. Run `python scripts/validate_agent_runtime_drift.py --all-platforms`.
3. Run `python scripts/validate_planning_lifecycle.py --repo-root . --strict`.
4. Run `py -m pytest tests/test_herdr_main_launcher.py tests/test_validate_planning_lifecycle.py -q`.
5. Run `git diff --check` and `git status --short --branch`.
6. Record exact results, sample count, decision, and preserved untracked paths in this plan.

**Verification:**
- All declared commands pass, or the failing command and blocker are recorded.
- `.playwright-mcp/`, `db/`, and `temp_evidence.json` remain untouched.
- Plan status changes to `completed` only after fresh verification returns `verified`.

**Exit Criteria:**
- Evidence, decision, plan state, and workspace state reconcile with no unsupported optimization claim.

## Verification

- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `py -m pytest tests/test_herdr_main_launcher.py tests/test_validate_planning_lifecycle.py -q`
- `python -m json.tool artifacts/completion-monitoring/next-convergence-evidence.json`
- `python -m json.tool artifacts/runtime-observation/representative-work-summary.json`
- `git diff --check`

The plan is ready for completion verification only when:

1. Completion-monitoring provenance is truthful and the prior plan is operationally closed.
2. 10–20 ordinary attempts are captured without synthetic fixtures or a telemetry service.
3. Raw evidence preserves phase, subprocess, retry, diagnostic, cleanup, reconciliation, task-result, and receipt facts.
4. Worker execution is not conflated with launcher monitoring cost.
5. A freeze or reopen decision cites exact evidence and names its owner, expected improvement, and correctness gates.
6. No runtime component, constant, watcher, scheduler, cache, or persistent state changed without a separate admitted plan.
7. Fresh validators pass and unrelated untracked files remain untouched.
8. Plan status changes to `completed` only after `skill-verification-before-completion` returns `verified`.

## Completion Criteria

- Representative observation artifacts are committed only after redaction and validation.
- Current runtime remains unchanged unless a separate evidence-backed plan is approved.
- Cost-gated decision is durable in Git-tracked planning truth.
- No unsupported production-wide latency claim is made from deterministic or small-sample evidence.
