---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: live-stability-probe-and-measured-optimization
targets:
  - artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json
  - artifacts/runtime-observation/2026-10-17-live-stability-topology-raw.jsonl
  - artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl
  - artifacts/runtime-observation/2026-10-17-live-stability-probe-summary.json
  - artifacts/runtime-observation/2026-10-17-live-stability-probe-report.md
  - artifacts/runtime-observation/2026-10-17-live-stability-cos-canary.json
  - scripts/run_live_stability_probe.py
  - tests/test_live_stability_probe.py
  - docs/operating_system/procedures/live-stability-probe-procedure.md
  - docs/superpowers/plans/2026-10-17-live-stability-probe-and-measured-optimization-plan.md
---

# Live Stability Probe And Measured Optimization

## Review Basis

The supplied verdict is directionally correct and should be accepted with the
following implementation corrections:

1. The Secretary–CoS–Worker role model is frozen; this plan does not redesign
   roles, add a coordinator, restore refill, enable managed Secretary, or
   change acceptance, settlement, ownership, or Plan/Git authority.
2. The previous topology protocol is pinned to the older base
   `dba06a16f50d3fa120c18ec83b8efaa7b2fbd324`. Its blocked result remains
   historical evidence. New live evidence must use a new protocol pinned to
   current `main` at
   `2254a69990a1b013c17df88183d9972cf866f3c5`.
3. `BLOCKED_CAPABILITY` is a valid probe result, not a failed measurement to
   be replaced with fixtures or synthetic success. The stability gate must
   distinguish complete positive evidence from capability-blocked evidence.
4. The passive aggregator remains passive. The thin recorder is evidence-only:
   existing execution owners perform work, then the recorder validates
   attributable results, sanitizes them, and writes rows. It must not choose
   arms, decompose work, retry, continue, accept, settle, release ownership,
   mutate Plan state, or become a second task database.
5. The optional disposable write probe is not required for this plan. It needs
   separate explicit authorization because it creates a temporary branch and
   mutates a task-owned worktree.

## Goal

Run a pinned, attributable live stability probe against current `main` using
the existing direct, bounded Worker, and two-lane CoS execution paths. Existing
owners execute the work; an evidence-only recorder captures their results.
Exercise both positive and fail-closed behavior, keep the evidence streams
separate, and produce one evidence-bound decision about whether a single
measured optimization is justified.

No production optimization is implemented by this plan. If evidence supports
an optimization, the report names exactly one bottleneck and one bounded
follow-up hypothesis for a separate plan.

## Implementation Outcomes

### Pinned live-probe protocol

The repository contains a new versioned protocol derived from the existing
topology schema and pinned to exact base revision
`2254a69990a1b013c17df88183d9972cf866f3c5`. It fixes one harmless,
read-only, decomposable workload; the accepted artifact, acceptance criteria,
verification commands, provider/profile policy, trial order, and warm/cold
definitions are immutable across all three arms.

The arms remain exactly:

```text
direct_controller  = current controller completes the whole workload
single_worker      = one bounded Worker completes the whole workload
cos_two_lane       = exactly two predeclared independent CoS lanes complete it
```

### Thin live evidence producer

`scripts/run_live_stability_probe.py` provides evidence-only record entry
points, attributable observation validation, sanitization, and JSONL record
writing. Existing controller, Worker, and CoS owners execute the work and pass
their attributable results to the recorder. Explicit modes may include
`record-direct`, `record-worker-result`, `record-cos-result`, and
`record-blocked`; there is no generic `run_arm()` or arm adapter. The recorder
never chooses work, decomposes tasks, retries, continues, accepts, settles,
releases ownership, mutates Plan state, or aggregates results.

### Positive and negative evidence

When required capabilities are available, the probe records 18 interleaved
trials: three repetitions for each arm under `cold` and `warm` conditions.
When a required capability is unavailable, each planned admission is recorded
as `BLOCKED_CAPABILITY` with explicit provenance and unavailable metrics; no
synthetic accepted row is emitted.

Six isolated negative probes cover stale Plan revision, wrong base/HEAD drift,
attempt/receipt mismatch, timeout or silence, execution failure with successful
retirement, and cleanup failure. They are written to a separate fail-closed
evidence stream and validated by bounded tests/report logic, not by the
18-trial topology aggregator. Each probe records the expected fail-closed owner
and verifies that no unauthorized completion, reuse, retry, or Plan transition
occurs.

### Evidence-bound decision report

The existing `scripts/benchmark_operational_comparison.py` validates and
summarizes only the 18 sanitized topology rows without launching work. The
report records three separate verdicts:

```text
plan_execution_status = verified | blocked | failed
live_stability_status = proven_read_only | inconclusive | failed
optimization_disposition = freeze | inconclusive | follow_up_required
```

`BLOCKED_CAPABILITY` may still allow `plan_execution_status=verified`, but it
can never prove live stability. Without the separately authorized write probe,
the strongest claim is **live read-only execution/coordination stability**, not
full governed write-lifecycle stability.

The report includes medians/ranges by topology and condition, stage timings,
launch/subprocess counts, retries, continuations, interventions, and
attributable usage/cost where available. It does not establish an arbitrary
latency threshold.

### Frozen architecture and runtime boundaries

Direct execution, one bounded Worker, bounded CoS coordination, sequential lane
acquisition, no-refill waves, acceptance identity checks, settlement separation,
stale-result protection, retirement/cleanup proof, review/integration gates,
and Plan/Git ownership remain unchanged. Managed Secretary remains capability
gated until attributable structured results, a real consumer, matched
correctness, and measurable benefit all exist.

## Scope Classification

- **Implement now:** new current-base protocol, thin live-probe recorder,
  protocol/record tests, probe procedure, positive/negative evidence capture,
  passive validation, and decision report.
- **Reuse unchanged:** `benchmark_operational_comparison.py`, existing Herdr
  launcher, parallel dispatcher, plan preparation, runtime receipts, and
  acceptance/settlement owners unless a focused test proves a contract gap.
- **Measure before changing:** cold-start reconstruction, Work Binding and
  Attention Audit evidence reuse, lane acquisition, wave imbalance,
  review/integration activation, whole-plan invalidation, continuation/regrant
  churn, and observation subprocess cost.
- **Deferred:** derived-fact caching, dispatch-freshness split, refill or
  dynamic scheduling, polling changes, deterministic integration changes,
  managed Secretary enablement, and the optional write probe.
- **Non-goals:** installing providers, adding credentials, changing sandbox
  permissions, creating an attention database or heartbeat, changing the
  passive aggregator into an orchestrator, or publishing external results.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-using-git-worktrees`, `skill-backend-verification`, `skill-performance-optimization`, `skill-disposable-artifact-cleanup`, `skill-verification-before-completion`
- Isolation: `clean task-owned worktree from current main`
- Commit policy: `seal protocol and recorder before live execution; no source edits after the seal`
- Preauthorized local actions: create the declared worktree, edit declared protocol/recorder/tests/procedure files, run already-configured local probes, write sanitized task-owned evidence, and remove task-owned disposable resources after retirement proof
- User-approval actions: provider installation, credential or sandbox changes, external runtime setup, optional write probe, push, merge, publication, destructive cleanup outside task-owned resources, or any production behavior change
- Parallel ownership: `none; one lead controller owns the protocol, recorder, evidence, and plan ledger`
- Sequential fallback: `complete protocol and recorder tests, Review A, seal the checkpoint, run canaries before the remaining topology trials, run negative probes, aggregate/report, Review B, then perform final verification`

The seal gate occurs after protocol/recorder tests and Review A, before any live
trial. Record the immutable checkpoint commit SHA, protocol digest, recorder
and focused-test digest, environment identity, and base revision. Tasks 3–5
run only from that checkpoint; no source, protocol, or test edits are allowed
after sealing. Evidence-only output changes are allowed. If the seal cannot be
reproduced, stop before live execution.

Review boundaries are intentionally consolidated:

- Review A covers the protocol, evidence-only recorder, focused tests, and the
  seal checkpoint.
- Review B covers topology/fail-closed evidence, summary, report, and the three
  verdicts before final verification.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/live-stability-probe`
- Base commit: `2254a69990a1b013c17df88183d9972cf866f3c5`
- Expected workspace: `clean dedicated worktree; original main checkout remains untouched`
- Next action: `handoff to explicitly authorized branch finishing; no push, merge, or worktree cleanup performed`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | task worktree | `codex` | none | current-base protocol and preflight baseline pass | `2254a699` base pin; protocol validation; 12 benchmark tests; repo config/contracts pass |
| Task 2 | `completed` | task worktree | `codex` | Task 1 | recorder and adapter contract tests pass | owner-bound identities and canonical pre-write validation; focused recorder tests pass; evidence-only modes; no external provider launch |
| Task 3 | `completed` | sealed task worktree | `codex` | Task 2 | 18 attributable topology rows or explicit inconclusive/blocked rows | `18 BLOCKED_CAPABILITY`; no producer launch; topology validation passed |
| Task 4 | `completed` | sealed task worktree | `codex` | Task 2 | six negative probes fail closed at expected owners | `6` separate records bound to exact regression tests; `233` affected lifecycle/receipt/plan/recorder tests pass |
| Task 5 | `completed` | sealed task worktree | `codex` | Tasks 3–4 | passive validation, summary, report, and one disposition | `18-row topology validation passed`; three verdicts recorded; six fail-closed records separate |
| Task 6 | `completed` | sealed task worktree | `codex` | Task 5 | final repository, plan, adapter, and kit verification | `1371 passed, 2 skipped`; contracts/planning/adapter/starter-kit/artifact checks passed |

## Task Breakdown

### Task 1: Pin the current-base protocol and workload

**Purpose:**
- Create a new live-probe protocol without mutating or appending to the
  historical `2026-10-16` protocol.
- Fix the harmless decomposable read-only workload, identical acceptance
  artifact, warm/cold definitions, interleaved 18-trial order, provenance
  fields, lifecycle states, and stage/metric names.

**Task Function:**
- Convert the approved live-probing scope into one immutable evidence contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low ambiguity and direct ownership of the protocol contract.

**Specification Coverage:**
- Review Basis items 1–3; Pinned live-probe protocol; no synthetic success.

**Required Skills:**
- `skill-writing-plans`, `skill-using-git-worktrees`

**Files And Symbols:**
- Inspect: `artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json`
- Inspect: `scripts/benchmark_operational_comparison.py:validate_protocol`
- Modify: `artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json`
- Modify: `tests/test_benchmark_operational_comparison.py`
- Verify: `repo_config/starter-kit-manifest.json`, `scripts/validate_repo_config.py`, `scripts/validate_repo_contracts.py`

**Dependencies:**
- Current `main` is exactly `2254a69990a1b013c17df88183d9972cf866f3c5`.

**Authority:**
- Preauthorized local actions: create the task worktree, derive the new protocol from the existing schema, and run read-only repository/configuration validation.
- Stop for: base drift, unresolved workload/acceptance identity, required capability changes, or a request to alter existing runtime safeguards.

**Steps:**
- [x] Step 1: Create a clean task-owned worktree from current `main` and record `HEAD`, branch, status, and expected base.
- [x] Step 2: Copy the existing protocol shape into a new dated protocol, replace the base revision and protocol identity, and preserve the interleaved arm/condition order.
- [x] Step 3: Define the exact read-only workload, final artifact digest, acceptance digest, verification command digest, provider/profile policy, and warm/cold reset rules.
- [x] Step 4: Add a focused regression assertion that a current-base row under the historical protocol is rejected with a base-mismatch reason, then validate the new protocol directly.

**Verification:**
- [x] `python scripts/validate_repo_config.py`
- [x] `python scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `python -m pytest -q tests/test_benchmark_operational_comparison.py`
- [x] `python -c "from scripts.benchmark_operational_comparison import load_json, validate_protocol; assert validate_protocol(load_json('artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json')) == []"`
- Expected: every command returns zero; repository checks pass; the new protocol is self-consistent; the focused regression assertion proves historical/current-base evidence cannot be mixed.

**Exit Criteria:**
- The new protocol pins current `main`, fixes one identical workload and 18-trial order, and contains no production optimization or synthetic fallback.

### Task 2: Implement the thin live evidence recorder

**Purpose:**
- Add a bounded producer that invokes existing execution owners and emits
  sanitized protocol rows without taking over dispatch, acceptance, settlement,
  retry, or Plan mutation.

**Task Function:**
- Adapt attributable runtime outputs into the existing passive evidence schema.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the recorder is a bounded evidence adapter and the lead controller retains acceptance and Git authority.

**Specification Coverage:**
- Thin live evidence producer; passive aggregator boundary; frozen runtime ownership.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:launch_preflight`, `run_lane`, `run_parallel_from_plan`
- Inspect: `scripts/herdr_main_launcher.py:main`, observation and receipt handling near `_DEEPAGENTS_*_POLL_SECONDS`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:prepare_plan_lanes`, `prepare_task`
- Inspect: `scripts/secretary_live_runtime.py:run_probe`, `_normal_managed_result_capability_available`
- Modify: `scripts/run_live_stability_probe.py:main`, `record_direct`, `record_worker_result`, `record_cos_result`, `record_blocked`, `validate_owner_result`, `sanitize_record`, `write_row`
- Modify: `scripts/benchmark_operational_comparison.py:validate_protocol`, `validate_row`, `_validate_stage_timestamps`
- Modify: `tests/test_live_stability_probe.py`
- Verify: `scripts/benchmark_operational_comparison.py` remains unchanged unless a focused contract test proves an existing schema gap.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: add the declared recorder and unit tests, invoke only already-configured local commands, and preserve raw evidence only in sanitized task-owned output.
- Stop for: missing attribution, a need to install/authenticate/change permissions, a request to add a second lifecycle database, or any ambiguity about acceptance/settlement ownership.

**Steps:**
- [x] Step 1: Define explicit evidence-only record modes for `direct_controller`, `single_worker`, `cos_two_lane`, and `BLOCKED_CAPABILITY`; each mode accepts an attributable owner result and writes one row without selecting or running work.
- [x] Step 2: Validate immutable base/workload/acceptance/configuration digests, arm, trial identity, condition, stage timestamps, intervals, retries, continuations, interventions, subprocesses, result/cleanup/reconciliation evidence, and metric provenance before writing.
- [x] Step 3: Keep capability preflight observational only; emit `BLOCKED_CAPABILITY` with unavailable metrics when the owning runtime cannot prove a required capability, and never synthesize an accepted result.
- [x] Step 4: Add tests for owner-result identity binding, sanitization, blocked capability, successful retirement evidence, rejection of runtime completion as semantic acceptance, and the absence of generic dispatch/retry behavior.

**Verification:**
- [x] `python -m pytest -q tests/test_live_stability_probe.py tests/test_benchmark_operational_comparison.py tests/test_benchmark_dispatch.py`
- [x] `python -m pytest -q tests/test_live_stability_probe.py::test_failclosed_evidence_is_bound_to_expected_tests`
- Expected: recorder tests pass; no test launches an external provider; blocked and accepted states remain distinct; the recorder has no generic `run_arm()` or arm adapter; the passive aggregator remains the only summarizer.

**Exit Criteria:**
- The recorder can produce attributable rows from existing owners or a precise blocked-capability row, with no new authority or orchestration layer.

### Review A and seal gate

Before live execution, perform one independent Review A of the protocol,
evidence-only recorder, focused tests, and frozen architecture boundary. After
Review A passes, create the immutable local checkpoint and record its commit
SHA, protocol digest, recorder/test digest, environment identity, and base
revision in the coordination evidence. Tasks 3–5 must run from that checkpoint;
source, protocol, and test edits after the seal are a stop condition.

### Task 3: Run the matched positive topology trials

**Purpose:**
- Exercise the three existing topology arms with one identical workload and
  produce either complete matched evidence or explicit capability-blocked/
  inconclusive evidence in the topology-only stream.

**Task Function:**
- Execute and observe a bounded live stability experiment.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live runtime authority, evidence attribution, and cleanup decisions must remain with one lead controller.

**Specification Coverage:**
- Positive trial procedure; 3 arms × 3 repetitions × 2 conditions; canary
  safety gate; capability-blocked/inconclusive semantics.

**Required Skills:**
- `skill-backend-verification`, `skill-performance-optimization`, `skill-disposable-artifact-cleanup`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Inspect: `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`, `scripts/secretary_live_runtime.py`
- Modify: `artifacts/runtime-observation/2026-10-17-live-stability-topology-raw.jsonl`
- Add: `artifacts/runtime-observation/2026-10-17-live-stability-cos-canary.json`
- Verify: task-owned worktree, runtime resources, receipts, TaskResults, cleanup, and reconciliation evidence.

**Dependencies:**
- Task 2 complete; Review A passed; the protocol and recorder are sealed at an
  immutable checkpoint; all capabilities must already be configured and authorized.

**Authority:**
- Preauthorized local actions: run the fixed read-only workload through the three declared arms, observe task-owned resources, write sanitized rows, and retire task-owned resources after positive proof.
- Stop for: credential/provider/sandbox changes, base or workload drift, unowned resource access, unresolved cleanup, or any request to treat blocked evidence as success.

**Steps:**
- [x] Step 1: Record the warm/cold definition and execute the exact interleaved order from the protocol; the first applicable `direct_controller`, `single_worker`, and `cos_two_lane` entries are the three canaries and count toward the 18 rows.
- [x] Step 2: Run the direct canary through the current controller owner without artificial Herdr activity; verify attribution, expected accepted artifact, no identity drift, settled ownership, cleanup, and no unexpected Plan mutation.
- [x] Step 3: Run the Worker canary through existing runtime binding and launcher owners; verify the same gate before continuing.
- [x] Step 4: Run the two-lane CoS canary through `herdr_parallel_dispatch.py` with exactly two disjoint tasks and no refill; verify the same gate before continuing. The live canary completed both read-only lanes with verified grants, authoritative receipts, confirmed lifecycle settlement, and removed generated role views; semantic acceptance remained `null`.
- [x] Step 5: If any canary has cleanup or ownership uncertainty, or semantic acceptance is not proven, stop the matrix and preserve separate canary evidence plus the existing capability-blocked topology rows; never manufacture additional executions or successes.
- [x] Step 6: If all canaries pass, run the remaining 15 scheduled trials through the existing owners and record explicit provenance, stage timestamps, intervals, cleanup, and metric status for all 18 rows.

**Verification:**
- [x] `python scripts/benchmark_operational_comparison.py validate --protocol artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json --input artifacts/runtime-observation/2026-10-17-live-stability-topology-raw.jsonl`
- Expected: the topology stream contains exactly 18 unique protocol rows; rows are valid accepted, `BLOCKED_CAPABILITY`, `unavailable`, or safety-stop `INCONCLUSIVE` evidence; no duplicate execution or false accepted outcome exists.

**Exit Criteria:**
- The topology evidence contains complete matched positive trials, complete capability-blocked evidence, or an explicitly safety-stopped/inconclusive 18-row dataset with no synthetic success and no leaked task-owned resources.

### Task 4: Run isolated fail-closed probes

**Purpose:**
- Prove that stale identity, unresolved ownership, failed execution, and
  cleanup uncertainty fail closed at the existing owner boundary.

**Task Function:**
- Exercise negative lifecycle and identity paths without weakening safeguards.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: each probe changes only a disposable task-owned fixture and requires direct lifecycle evidence.

**Specification Coverage:**
- Six negative probes: stale Plan revision, wrong base/HEAD, attempt/receipt mismatch, timeout/silence, failed execution with successful retirement, and cleanup failure.

**Required Skills:**
- `skill-backend-verification`, `skill-disposable-artifact-cleanup`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:launch_preflight`, `run_lane`, `runtime_completion_is_not_acceptance`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`, `apply_plan_transitions`
- Inspect: `scripts/secretary_live_runtime.py:run_probe`, receipt validation and resource-evidence helpers
- Modify: `artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl`
- Verify: task-owned disposable fixtures and final retirement/cleanup state.

**Dependencies:**
- Task 2 complete; Review A and the seal gate complete; Task 3 may run before
  or after these probes, but they must use isolated fixtures and a separate
  evidence stream.

**Authority:**
- Preauthorized local actions: create disposable task-owned fixtures, induce the six declared failure conditions, capture fail-closed evidence, and clean up after retirement proof.
- Stop for: any failure requiring production code changes, unresolved ownership, destructive cleanup outside task-owned fixtures, or a semantic choice about expected lifecycle behavior.

**Steps:**
- [x] Step 1: Change non-executed Plan text after admission and verify `plan_revision_changed`, no Worker start, no Plan advancement, and no leaked resource; record the result as a deterministic fail-closed probe.
- [x] Step 2: Change task worktree HEAD after preparation and verify base drift blocks before execution without out-of-scope writes; record the base-drift evidence class.
- [x] Step 3: Present stale or mismatched attempt/receipt evidence and verify rejection, reconciliation where required, and no dependent advancement.
- [x] Step 4: Run a bounded timeout/silence case and verify timeout is not retirement proof, reuse remains blocked, and no duplicate retry occurs.
- [x] Step 5: Run a Worker failure with successful retirement and verify execution failure is distinct from unresolved ownership.
- [x] Step 6: Induce task-owned cleanup failure and verify `recovery_required`, reuse blocking, and no successful settlement.
- [x] Step 7: Write exactly six records to the fail-closed stream with explicit `evidence_class` (`live` or `deterministic`), expected owner, observed fail-closed state, cleanup state, and no synthetic topology trial IDs.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_plan_preparation.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py tests/test_live_stability_probe.py`
- Expected: each negative probe fails closed at the expected owner; the dedicated bounded tests validate the six fail-closed records without passing them to `benchmark_operational_comparison.py`; no false completion, reuse, retry, or dependent transition is observed.

**Exit Criteria:**
- All six negative probes have attributable evidence in the separate fail-closed stream and preserve the current identity, authority, acceptance, settlement, retirement, and cleanup boundaries.

### Task 5: Validate evidence and publish one decision report

**Purpose:**
- Validate raw rows with the existing passive aggregator, summarize only valid
  evidence, and record one disposition plus one measured follow-up hypothesis at
  most.

**Task Function:**
- Convert probe evidence into an auditable stability and optimization decision.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: report ownership is part of the plan ledger and must not be delegated to the runtime producer.

**Specification Coverage:**
- Evidence-bound decision report; no arbitrary latency threshold; one bottleneck maximum.

**Required Skills:**
- `skill-performance-optimization`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/benchmark_operational_comparison.py:validate_rows`, `summarize`, `_metric_aggregate`
- Inspect: `artifacts/runtime-observation/2026-10-17-live-stability-topology-raw.jsonl`
- Inspect: `artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl`
- Modify: `artifacts/runtime-observation/2026-10-17-live-stability-probe-summary.json`
- Modify: `artifacts/runtime-observation/2026-10-17-live-stability-probe-report.md`
- Modify: `docs/operating_system/procedures/live-stability-probe-procedure.md`
- Verify: `artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json`, raw rows, summary, and report.

**Dependencies:**
- Tasks 3 and 4 complete.

**Authority:**
- Preauthorized local actions: run passive validation/summarization, write sanitized summary/report/procedure documentation, and record blocked or deferred outcomes.
- Stop for: any request to infer success from blocked rows, change the aggregator into a producer, create multiple optimization plans, or edit production behavior from one experiment.

**Steps:**
- [x] Step 1: Validate only the topology stream against the new protocol and reject mixed-base, duplicate, malformed, or lifecycle-invalid rows; validate the six fail-closed records with dedicated bounded test/report logic.
- [x] Step 2: Summarize topology medians/ranges by topology and condition, stage timings, useful interval sum/union, launches, subprocesses, retries, continuations, interventions, and attributable usage/cost.
- [x] Step 3: Record separate `plan_execution_status` (`verified`, `blocked`, or `failed`), `live_stability_status` (`proven_read_only`, `inconclusive`, or `failed`), and `optimization_disposition` (`freeze`, `inconclusive`, or `follow_up_required`). `BLOCKED_CAPABILITY` or incomplete matched evidence makes live stability `inconclusive`, never proven.
- [x] Step 4: If `optimization_disposition=follow_up_required`, name exactly one measured bottleneck and one bounded hypothesis; create no implementation changes in this plan.
- [x] Step 5: Document that the strongest claim is live read-only execution/coordination stability unless a separately authorized write probe succeeds; document the frozen safeguards and write-probe deferral without adding a registry, heartbeat, or second task database.

**Verification:**
- [x] `python scripts/benchmark_operational_comparison.py validate --protocol artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json --input artifacts/runtime-observation/2026-10-17-live-stability-topology-raw.jsonl`
- [x] `python scripts/benchmark_operational_comparison.py summarize --protocol artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json --input artifacts/runtime-observation/2026-10-17-live-stability-topology-raw.jsonl --output artifacts/runtime-observation/2026-10-17-live-stability-probe-summary.json`
- [x] `python -c "import json; from pathlib import Path; rows=[json.loads(line) for line in Path('artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]; assert len(rows) == 6 and all(row.get('evidence_class') in {'live', 'deterministic'} for row in rows)"`
- Expected: topology summary traces only to valid topology rows; fail-closed evidence is validated separately; blocked metrics remain unavailable; the report contains all three verdicts, exactly one optimization disposition, and at most one follow-up bottleneck.

**Exit Criteria:**
- The report is sanitized, parseable, reproducible, and explicit about the three verdicts and the narrower read-only stability claim; no speculative production optimization is bundled.

### Review B gate

After Tasks 3–5 produce the separate evidence streams, summary, procedure, and
report, perform one independent Review B of evidence traceability, canary and
fail-closed conclusions, verdict separation, and the absence of write-lifecycle
overclaiming. Task 6 may begin only after Review B is recorded as passed or the
reviewed final issues are resolved.

Review B result: passed. The topology validator accepted exactly 18 rows, the
fail-closed stream contains exactly six non-topology records, and the report
keeps plan execution, live stability, and optimization disposition separate.

### Task 6: Run final repository and generated-surface verification

**Purpose:**
- Prove that the probe plan and evidence are internally consistent and that no
  generated, starter-kit, repository-contract, or whitespace drift remains.

**Task Function:**
- Perform fresh final acceptance verification and prepare the plan for handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and plan-ledger state remain with the lead controller.

**Specification Coverage:**
- Completion criteria; frozen architecture; source/generated boundaries; clean task-owned resources.

**Required Skills:**
- `skill-verification-before-completion`, `skill-disposable-artifact-cleanup`

**Files And Symbols:**
- Inspect: all declared task targets and current plan ledger
- Verify: `tests/`, `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`, `scripts/sync_agent_adapters.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`

**Dependencies:**
- Task 5 complete and Review B recorded.

**Authority:**
- Preauthorized local actions: run declared repository, plan, adapter, starter-kit, JSON, test, whitespace, and task-owned cleanup verification.
- Stop for: stale plan state, failed required check, unresolved resource, undeclared file, base drift, or any need to rewrite evidence after verification.

**Steps:**
- [x] Step 1: Run focused probe/runtime tests and repository contract validation; reserve the full repository suite for the final verification boundary below.
- [x] Step 2: Run planning lifecycle validation against this exact plan path.
- [x] Step 3: Run all-platform adapter drift, starter-kit build, and starter-kit validation checks.
- [x] Step 4: Parse the protocol, topology JSONL, fail-closed JSONL, summary, and report; inspect `git diff --check`, status, and task-owned resource retirement.
- [x] Step 5: Apply `skill-verification-before-completion`; change plan status only after fresh evidence returns `verified`.

**Verification:**
- [x] `python -m pytest -q tests/test_live_stability_probe.py tests/test_benchmark_operational_comparison.py tests/test_benchmark_dispatch.py tests/test_herdr_attempt_contract.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py`
- [x] `python scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `python scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-17-live-stability-probe-and-measured-optimization-plan.md`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `python scripts/build_starter_kit.py --repo-root . --output-root .tmp-tests/live-stability-starter-kit`
- [x] `python scripts/validate_starter_kit.py --repo-root . --output-root .tmp-tests/live-stability-starter-kit`
- [x] `python -m json.tool artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json`
- [x] `python -m json.tool artifacts/runtime-observation/2026-10-17-live-stability-probe-summary.json`
- [x] `git diff --check`
- Expected: all required checks pass; generated surfaces are synchronized; evidence files parse; only declared task-owned changes remain before final disposition.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`, all required task evidence is present, and no unresolved blocker or scope deviation remains.

## Verification

Final artifact-level verification must run from the same clean task worktree:

- `python -m pytest -q`
- `python scripts/validate_repo_contracts.py --repo-root . --fast`
- `python scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-17-live-stability-probe-and-measured-optimization-plan.md`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/build_starter_kit.py --repo-root . --output-root .tmp-tests/live-stability-starter-kit`
- `python scripts/validate_starter_kit.py --repo-root . --output-root .tmp-tests/live-stability-starter-kit`
- `python -m json.tool artifacts/runtime-observation/2026-10-17-live-stability-probe-protocol.json`
- `python -m json.tool artifacts/runtime-observation/2026-10-17-live-stability-probe-summary.json`
- `python -c "import json; from pathlib import Path; rows=[json.loads(line) for line in Path('artifacts/runtime-observation/2026-10-17-live-stability-failclosed.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]; assert len(rows) == 6 and all(row.get('evidence_class') in {'live', 'deterministic'} for row in rows)"`
- `git diff --check`
- `git status --short --branch`, confirming only declared plan/probe/evidence changes exist before authorized Git disposition.

## Completion Criteria

The plan is ready for completion verification when:

1. the new protocol is pinned to current `main` and fixes one identical
   workload, acceptance contract, verification command set, configuration
   policy, trial order, and warm/cold definition;
2. the thin recorder delegates to existing runtime owners and cannot accept,
   settle, retry, release, mutate Plan state, or aggregate evidence;
3. positive trials are either complete and matched or explicitly recorded as
   `BLOCKED_CAPABILITY`/unavailable/inconclusive without synthetic success, with
   three canaries gating the remaining matrix;
4. all six negative probes fail closed at the expected owner with no false
   completion, reuse, retry, dependent advancement, or leaked resource;
5. passive topology validation and separate fail-closed validation preserve
   provenance, identity, lifecycle, cleanup, blocked, unavailable, and
   overlapping-interval semantics;
6. the report separates `plan_execution_status`, `live_stability_status`, and
   `optimization_disposition`, claims only read-only execution/coordination
   stability without a write probe, and names at most one measured follow-up
   bottleneck;
7. direct execution, Worker, CoS, Secretary capability gating, acceptance,
   settlement, ownership, stale-result, review, cleanup, and Plan/Git
   safeguards remain unchanged;
8. the optional disposable write probe is clearly deferred and not required for
   a `verified` result;
9. focused tests, exactly one final full `python -m pytest -q`, repository
   contracts, planning validation, adapter drift, starter-kit validation, JSON
   and fail-closed evidence parsing, and diff checks pass; and
10. `skill-verification-before-completion` returns `verified` before this plan
    changes from `proposed`/`active` to `completed`.

Branch publication, pull-request review, merge, branch deletion, worktree
cleanup, and any optional write probe remain separate explicitly authorized Git
or runtime actions.
