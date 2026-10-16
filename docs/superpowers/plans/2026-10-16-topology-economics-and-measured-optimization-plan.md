---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: topology-economics-and-measured-optimization
targets:
  - artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json
  - artifacts/runtime-observation/2026-10-16-topology-economics-raw.jsonl
  - artifacts/runtime-observation/2026-10-16-topology-economics-summary.json
  - artifacts/runtime-observation/2026-10-16-topology-economics-report.md
  - scripts/benchmark_operational_comparison.py
  - tests/test_benchmark_operational_comparison.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/superpowers/plans/2026-10-16-topology-economics-and-measured-optimization-plan.md
---

# Topology Economics And Measured Optimization

## Review Basis

This plan adopts the consolidated post-PR #94 verdict at merged `main`
revision `dba06a16f50d3fa120c18ec83b8efaa7b2fbd324`.

The Secretary–CoS–Worker hierarchy is treated as architecturally converged.
This plan does not redesign the role model, add another coordinator, restore
refill, weaken acceptance or settlement boundaries, or enable the managed
Secretary runtime. It measures the cost of applying the existing supported
topologies to the same work and records exactly one measured next action.

The supplied verdict is evidence-backed direction, not a live run result.
Unsupported measurements remain `unavailable`; blocked capabilities remain
`BLOCKED_CAPABILITY`; no synthetic result is promoted to an optimization
decision.

## Goal

Measure the accepted-outcome cost imposed by three existing execution paths on
one identical decomposable workload, using interleaved warm/cold trials and a
passive evidence aggregator, then produce one evidence-bound decision about
whether a single follow-up optimization plan is justified.

## Implementation Outcomes

### Matched topology evidence

The repository contains a versioned protocol and sanitized raw JSONL evidence
for exactly these arms:

```text
direct_controller  = one controller completes the whole workload
single_worker      = one bounded Worker completes the whole workload
cos_two_lane       = exactly two predeclared independent lanes complete the workload
```

Every attempted run records the immutable base revision, workload and
acceptance digests, provider/model/profile configuration, arm, trial order,
warm/cold classification, stage timestamps, retries, interventions,
continuations, repeated evidence reads, subprocesses, completion delay,
unresolved resources, review/integration activations, attributable usage/cost,
and explicit provenance or `unavailable` status for each metric.

### Passive, auditable aggregation

`scripts/benchmark_operational_comparison.py` validates and aggregates
controller-produced records. It does not choose work, launch a topology,
dispatch Workers, own retries, perform acceptance, or become a coordination
authority. The summary traces every aggregate to raw rows and marks incomplete
or unmatched arms without calculating a false zero.

### One-gate optimization handoff

The report classifies the result as `freeze`, `inconclusive`, or `follow_up_required`.
`follow_up_required` names exactly one measured bottleneck and one bounded
follow-up hypothesis. No production optimization is implemented in this plan.
The follow-up plan must preserve all current identity, authority, lifecycle,
settlement, stale-result, ownership, review, and Plan/Git safeguards.

### Frozen boundaries remain explicit

Runtime documentation records that direct execution, one bounded Worker, and
CoS coordination remain the supported ladder; managed Secretary remains
capability-gated until attributable structured results, a real consumer,
matched correctness, and measurable benefit all exist. Existing acceptance,
settlement, sequential acquisition, bounded-wave, and no-refill behavior stays
unchanged.

## Scope Classification

- **Implement now:** matched-trial protocol, passive record validator/aggregator,
  evidence schema tests, sanitized report, and documentation of the measured
  decision boundary.
- **Already satisfied and frozen:** optional Secretary routing, direct/local
  execution, one bounded Worker path, no CoS mesh, sequential acquisition,
  refill removal, acceptance identity consistency, settlement separation,
  validation-reason propagation, and the managed-Secretary capability block.
- **Measure before changing:** CoS cold-start reconstruction, Attention Audit
  snapshot reuse, review/integration handoff cost, whole-plan invalidation,
  continuation/regrant churn, wave imbalance, and monitoring subprocess cost.
- **Deferred:** deterministic exact-head integration, derived-fact reuse,
  dispatch-freshness refinement, polling changes, dynamic scheduling, and the
  physical evidence-release split in `acceptance.py`.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-performance-optimization`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `one dedicated task-owned worktree created from merged main revision dba06a16f50d3fa120c18ec83b8efaa7b2fbd324; preserve the current dirty main checkout`
- Commit policy: `no commits during execution; one checkpoint only after fresh verification and explicit Git authorization`
- Preauthorized local actions: `inspect named sources and existing evidence, create the passive validator and focused tests, write the named protocol/evidence/report/docs files, run bounded authorized trials through existing owners, and run declared local validation`
- User-approval actions: `credentials, provider installation, external writes, live runs requiring unavailable capability, push, merge, publication, destructive cleanup, and any production behavior change not admitted by the measured decision gate`
- Parallel ownership: `none; the protocol, aggregator, evidence, report, and documentation share one sequential owner`
- Sequential fallback: `complete Tasks 1–2 with deterministic fixtures; record Task 3 as BLOCKED_CAPABILITY or INCONCLUSIVE when live topology execution cannot produce attributable accepted-outcome evidence; do not substitute synthetic data`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `dedicated topology-economics branch created from dba06a16f50d3fa120c18ec83b8efaa7b2fbd324 before activation`
- Base commit: `dba06a16f50d3fa120c18ec83b8efaa7b2fbd324`
- Expected workspace: `clean dedicated worktree; the existing dirty main checkout and its four local plan edits remain untouched`
- Next action: `none; retain the inconclusive evidence and require a separately approved live producer before remeasurement`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated worktree | `codex` | none | protocol JSON and fixture validation | `protocol JSON validated` |
| Task 2 | `completed` | dedicated worktree | `codex` | Task 1 | passive aggregator tests and schema checks | `5 focused tests and repo contracts passed` |
| Task 3 | `completed` | dedicated worktree | `codex` | Task 2 | matched topology JSONL and accepted-outcome summary | `18 BLOCKED_CAPABILITY admissions; 0 observed rows` |
| Task 4 | `completed` | dedicated worktree | `codex` | Task 3 | report, documentation, validators, and one decision gate | `inconclusive report and frozen-boundary docs` |

## Task Breakdown

### Task 1: Freeze the matched workload and protocol

**Purpose:**
- Define one decomposable workload and immutable trial contract before any
  topology run so order, provider, acceptance, and environment differences are
  visible rather than inferred after the fact.

**Task Function:**
- Measurement protocol definition and evidence-boundary review.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded design and repository evidence task with no
  implementation ambiguity after the supplied verdict.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing JSON and planning validators plus focused tests.

**Specification Coverage:**
- One identical workload across `direct_controller`, `single_worker`, and
  `cos_two_lane`; same base, objective, final artifacts, acceptance criteria,
  verification commands, and controllable runtime configuration.
- Interleaved arm order with a recorded fixed seed, three repetitions per arm
  in each declared warm/cold condition, for 18 attempted trials.
- No optimization claim from fewer than three valid matched trials per arm;
  incomplete or blocked conditions remain explicitly classified.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_new_performance_evidence`
- Inspect: `scripts/herdr_main_launcher.py:_finalize_performance`
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel`
- Inspect: `scripts/secretary_live_runtime.py:run_normal`
- Inspect: `scripts/secretary_live_pilot.py:DEFAULT_MANIFEST`
- Inspect: `artifacts/runtime-observation/representative-work-summary.json`
- Write: `artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json`

**Dependencies:**
- Merged `main` at `dba06a16f50d3fa120c18ec83b8efaa7b2fbd324`.
- Existing representative workload and launcher evidence are available.

**Authority:**
- Preauthorized local actions: inspect the named sources and evidence, define the protocol JSON, and run deterministic protocol validation
- Stop for: workload cannot be held identical, arm ownership is not disjoint, required live capability is unavailable, or a proposed change adds a coordinator or new durable state source

**Steps:**
- [x] Step 1: Create the dedicated worktree from the merged base and record
  `HEAD`, `origin/main`, merge-base, status, and the untouched-main boundary.
- [x] Step 2: Define the workload digest, final artifact digest, acceptance
  criteria digest, verification-command digest, provider/model/profile fields,
  fixed trial seed, arm order, warm/cold labels, and stage timeline.
- [x] Step 3: Define raw-row statuses for `observed`, `unavailable`,
  `BLOCKED_CAPABILITY`, `INCONCLUSIVE`, and `invalid`; require source producer,
  source digest, run identity, and base identity for every non-invalid row.

**Verification:**
- [x] `python -m json.tool artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json`
- Expected: the protocol names all three arms, 18 attempted trials, fixed
  matching inputs, provenance rules, stage fields, and no synthetic fallback.

**Exit Criteria:**
- The protocol is immutable for Task 3 and every later comparison can be
  rejected as unmatched without guessing.

### Task 2: Implement the passive evidence validator and aggregator

**Purpose:**
- Reuse existing evidence conventions to validate raw topology rows and produce
  reproducible aggregates without adding an execution or coordination layer.

**Task Function:**
- Passive measurement tooling and contract-focused regression coverage.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded Python utility and focused tests with no runtime
  authority.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the focused test module and repository contract validator
  directly exercise the new utility.

**Specification Coverage:**
- Validate arm matching, base/workload/acceptance/verification/configuration
  digests, warm/cold attribution, trial order, stage monotonicity, retries,
  continuations, messages, interventions, subprocesses, completion delay,
  unresolved resources, review/integration events, token/cost provenance, and
  explicit unavailable states.
- Aggregate accepted-outcome wall time, useful execution intervals, topology
  overhead, launches, messages, interventions, continuations, evidence reads,
  subprocesses, completion delay, unresolved resources, review/integration
  activations, tokens, and estimated cost without double-counting overlapping
  Worker intervals.
- Return nonzero for malformed, mixed, duplicated, or identity-mismatched rows.

**Required Skills:**
- `skill-performance-optimization`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/benchmark_dispatch.py:benchmark_dispatch`
- Inspect: `scripts/benchmark_completion_monitoring.py:main`
- Inspect: `scripts/project_os_runtime/secretary_economics.py:normalize_response_usage`
- Inspect: `scripts/project_os_runtime/secretary_receipts.py:validate_live_receipt`
- Create: `scripts/benchmark_operational_comparison.py:validate_rows, aggregate_rows, main`
- Create: `tests/test_benchmark_operational_comparison.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:measurement boundary`

**Dependencies:**
- Task 1 protocol JSON.

**Authority:**
- Preauthorized local actions: create the named passive utility and focused tests, update the named runtime documentation, and run deterministic fixture validation
- Stop for: the utility launches a process, dispatches a Worker, owns retries, performs acceptance, mutates a plan, or introduces a parallel registry or receipt schema

**Steps:**
- [x] Step 1: Implement schema validation and identity matching against the
  Task 1 protocol; preserve `unavailable` and blocked statuses as data.
- [x] Step 2: Implement stage-aware aggregation with elapsed wall time distinct
  from summed overlapping Worker intervals and with descriptive p50/p95 labels.
- [x] Step 3: Add fixtures for valid matched rows, mixed base revisions,
  duplicate trials, missing provenance, unavailable metrics, blocked capability,
  late receipt, unresolved cleanup, and overlapping two-lane intervals.
- [x] Step 4: Document that the utility consumes controller-owned records and
  cannot become an execution authority.

**Verification:**
- [x] `python -m pytest -q tests/test_benchmark_operational_comparison.py tests/test_benchmark_dispatch.py tests/test_benchmark_completion_monitoring.py`
- Expected: valid rows aggregate deterministically; invalid or mixed rows are
  rejected; unavailable and blocked values are not converted to zero; parallel
  useful intervals are not double-counted.
- [x] `python scripts/validate_repo_contracts.py --repo-root . --fast`
- Expected: the new utility imports only approved repository/runtime modules and
  does not cross the execution-owner boundary.

**Exit Criteria:**
- The passive utility can validate and aggregate the Task 1 protocol using only
  fixture records and cannot launch or mutate governed work.

### Task 3: Run the interleaved topology comparison

**Purpose:**
- Produce current, attributable evidence for the exact question: what accepted
  outcome cost does each supported topology impose on the same work?

**Task Function:**
- Bounded operational measurement through existing execution owners.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the live producer was unavailable, so the lead controller
  recorded the bounded capability outcome without dispatching a substitute.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller validates identity, provenance,
  lifecycle, and matched-trial completeness through the passive aggregator and
  declared repository checks.

**Specification Coverage:**
- Existing controllers and executors perform all runs; the passive utility only
  validates and aggregates their records.
- Every trial records accepted-outcome wall time including retries, controller
  preparation, lane acquisition/startup, useful execution, observation,
  acceptance, review, integration, retirement, and cleanup/reconciliation.
- A blocked or unattributable run is evidence of capability state, not a zero-cost
  success; a mixed configuration is excluded from matched aggregates.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Read: `artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json`
- Invoke: existing direct, bounded Worker, and two-lane CoS execution owners
- Write: `artifacts/runtime-observation/2026-10-16-topology-economics-raw.jsonl`
- Write: `artifacts/runtime-observation/2026-10-16-topology-economics-summary.json`

**Dependencies:**
- Task 2 complete.
- The exact merged base and protocol digest remain unchanged.

**Authority:**
- Preauthorized local actions: run only the bounded trials admitted by the protocol, capture sanitized producer evidence, and invoke the passive aggregator
- Stop for: credentials/provider installation, capability not attributable to a supported producer, base/workload/configuration drift, unsafe cleanup, or any request to substitute synthetic records

**Steps:**
- [x] Step 1: Record the fixed interleaved order for 18 planned admissions;
  live execution is blocked before start because no approved producer is available,
  so every row records `attempted: false` and `BLOCKED_CAPABILITY`.
- [x] Step 2: Validate each raw row immediately; quarantine invalid rows without
  editing them into apparent success.
- [x] Step 3: Aggregate only the valid matched subset and record the count,
  missing arms, blocked capabilities, unavailable metrics, and lifecycle errors.
- [x] Step 4: Remove only task-owned temporary runtime resources after positive
  retirement and preserve the sanitized raw evidence and summary paths.

**Verification:**
- [x] `python scripts/benchmark_operational_comparison.py validate --protocol artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json --input artifacts/runtime-observation/2026-10-16-topology-economics-raw.jsonl`
- Expected: every accepted row matches the immutable protocol and every rejected
  row has an explicit reason.
- [x] `python scripts/benchmark_operational_comparison.py summarize --protocol artifacts/runtime-observation/2026-10-16-topology-economics-protocol.json --input artifacts/runtime-observation/2026-10-16-topology-economics-raw.jsonl --output artifacts/runtime-observation/2026-10-16-topology-economics-summary.json`
- Expected: the summary traces to raw rows, separates elapsed and useful time,
  and preserves unavailable/blocked statuses.

**Exit Criteria:**
- The evidence is either complete enough for a decision or explicitly marked
  `BLOCKED_CAPABILITY`/`INCONCLUSIVE`; no unsupported optimization claim exists.

### Task 4: Record one decision and preserve frozen boundaries

**Purpose:**
- Convert the measured result into one bounded next action without reopening the
  architecture or making several speculative production changes.

**Task Function:**
- Evidence reconciliation, decision recording, and final contract verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final ledger and documentation reconciliation require one
  owner and no delegated implementation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing plan, repository, adapter, and starter-kit
  validators provide the final proof.

**Specification Coverage:**
- `freeze` records that no measured bottleneck justifies production change.
- `inconclusive` records the missing capability or evidence and leaves runtime
  behavior unchanged.
- `follow_up_required` names one bottleneck, one hypothesis, one target metric,
  one correctness gate, and one separate follow-up plan; it does not implement
  the optimization here.
- Managed Secretary remains blocked until its four exit conditions are proven;
  stale plan cleanup uses explicit plan paths and revisions rather than a plan
  registry or newest-file discovery.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-backend-verification`

**Files And Symbols:**
- Read: `scripts/secretary_live_runtime.py:_normal_managed_result_capability_available`
- Read: `scripts/secretary_live_runtime.py:run_normal`
- Read: `scripts/validate_planning_lifecycle.py:validate_planning_artifacts`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:measurement and freeze boundary`
- Modify: `docs/operating_system/tooling/runtime-tool-resolution.md:managed Secretary exit condition`
- Write: `artifacts/runtime-observation/2026-10-16-topology-economics-report.md`
- Modify: `docs/superpowers/plans/2026-10-16-topology-economics-and-measured-optimization-plan.md`

**Dependencies:**
- Task 3 summary and raw evidence exist, or Task 3 has an explicit blocked or
  inconclusive disposition.

**Authority:**
- Preauthorized local actions: reconcile the named evidence/report/docs/plan files and run final validation without changing production execution behavior
- Stop for: more than one optimization request, a request to weaken a safeguard, unowned active-plan mutation, managed Secretary enablement, external publication, or destructive cleanup

**Steps:**
- [x] Step 1: Reconcile the raw rows and summary into the named Markdown report,
  including exact base/protocol digests, valid counts, unavailable metrics,
  blocked capabilities, and lifecycle/cleanup outcomes.
- [x] Step 2: Select exactly one disposition: `freeze`, `inconclusive`, or
  `follow_up_required`; record the single next measurement or implementation
  hypothesis and its acceptance gate.
- [x] Step 3: Confirm no production source changed for a freeze or inconclusive
  result; for a follow-up result, create only the separate plan handoff.
- [x] Step 4: Read currently active plans using explicit paths and revisions;
  record stale or superseded candidates in the report, preserve the four
  pre-existing dirty main-checkout plans, and do not build a registry.
- [x] Step 5: Run final validators and record evidence, deviations, blockers,
  and deferrals in this plan.

**Verification:**
- [x] `python -m json.tool artifacts/runtime-observation/2026-10-16-topology-economics-summary.json`
- Expected: the summary is parseable and all aggregates trace to valid raw rows.
- [x] `python scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-16-topology-economics-and-measured-optimization-plan.md`
- Expected: the plan ledger, task authority, dependencies, and completion proof
  are internally consistent.
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: canonical and generated agent surfaces are synchronized.
- [x] `python scripts/build_starter_kit.py --repo-root . --output-root .tmp-tests/topology-economics-starter-kit`
- Expected: the starter kit builds without copying private measurement data.
- [x] `python scripts/validate_starter_kit.py --repo-root . --output-root .tmp-tests/topology-economics-starter-kit`
- Expected: the built starter kit passes its structural and public-surface checks.
- [x] `git diff --check`
- Expected: no whitespace errors exist in the task-owned changes.

**Exit Criteria:**
- One evidence-bound disposition is recorded, frozen safeguards remain intact,
  no speculative optimization was implemented, and final verification is fresh.

## Verification

Final artifact-level verification must run from the same dedicated worktree:

- `python -m pytest -q tests/test_benchmark_operational_comparison.py tests/test_benchmark_dispatch.py tests/test_benchmark_completion_monitoring.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py tests/test_validate_planning_lifecycle.py`
- `python scripts/validate_repo_contracts.py --repo-root . --fast`
- `python scripts/validate_planning_lifecycle.py --repo-root . --plan docs/superpowers/plans/2026-10-16-topology-economics-and-measured-optimization-plan.md`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/build_starter_kit.py --repo-root . --output-root .tmp-tests/topology-economics-starter-kit`
- `python scripts/validate_starter_kit.py --repo-root . --output-root .tmp-tests/topology-economics-starter-kit`
- `git diff --check`
- `git status --short --branch`, confirming only declared task-owned changes and preserved pre-existing local main edits are present.

## Completion Criteria

The plan is ready for completion verification when:

1. the protocol fixes one identical workload, base, acceptance contract,
   verification command set, configuration policy, order, and warm/cold design;
2. the passive aggregator validates provenance, identity, lifecycle, cleanup,
   unavailable, blocked, and overlapping-interval cases without owning runtime;
3. raw evidence and summaries are sanitized, parseable, reproducible, and trace
   every aggregate to valid rows;
4. the experiment records complete matched evidence or an explicit
   `BLOCKED_CAPABILITY`/`INCONCLUSIVE` outcome without synthetic success;
5. exactly one disposition is recorded and no speculative production
   optimization is bundled with the measurement;
6. managed Secretary, acceptance, settlement, ownership, stale-result,
   retirement, review, and Plan/Git safeguards remain unchanged;
7. active-plan hygiene uses explicit path/revision binding and adds no registry;
8. focused tests, repository contracts, planning validation, adapter drift,
   starter-kit validation, and diff checks pass at one verified checkpoint; and
9. `skill-verification-before-completion` returns `verified` before this plan
   changes from `proposed`/`active` to `completed`.

Branch publication, pull-request review, merge, branch deletion, and worktree
cleanup remain separate explicitly authorized Git actions.

## Verification Result

`verified` in the dedicated worktree
`C:\Users\HOANG PHI LONG DANG\.codex\worktrees\topology-economics-measurement\project-OS-starter`
on branch `codex/topology-economics-measurement`, based on
`dba06a16f50d3fa120c18ec83b8efaa7b2fbd324`. Fresh evidence includes 215 focused
tests passing, repository-contract validation, planning-lifecycle validation,
adapter synchronization, starter-kit build and validation, summary JSON parsing,
and `git diff --check`. The only approved residual is the explicit
`BLOCKED_CAPABILITY`/`inconclusive` live-measurement outcome; no production
optimization or managed Secretary enablement was performed.
