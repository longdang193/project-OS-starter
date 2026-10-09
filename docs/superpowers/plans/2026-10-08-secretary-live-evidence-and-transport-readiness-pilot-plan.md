---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: secretary-live-evidence-and-transport-readiness-pilot
targets:
  - docs/superpowers/plans/2026-10-08-secretary-live-evidence-and-transport-readiness-pilot-plan.md
  - docs/architecture.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - .github/workflows/runtime-contracts.yml
  - .github/workflows/repo-contracts.yml
  - scripts/project_os_runtime/secretary_adapter.py
  - scripts/project_os_runtime/secretary_events.py
  - scripts/project_os_runtime/secretary_evidence.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/secretary_live_pilot.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_events.py
  - tests/test_secretary_benchmark.py
  - tests/test_secretary_evidence.py
  - tests/test_secretary_live_pilot.py
  - tests/test_plan_preparation.py
  - pilot_artifacts/secretary-live-evidence/capability-inventory.json
  - pilot_artifacts/secretary-live-evidence/workload-manifest.json
  - pilot_artifacts/secretary-live-evidence/comparison-report.md
---

# Secretary Live Evidence and Transport Readiness Pilot Plan

## Goal

Run a bounded Secretary pilot that answers three questions without creating a
second workflow system:

1. Can Secretary reconstruct current project attention from Plan, Git,
   Worker evidence, acceptance, and runtime receipts without copying canonical
   state?
2. Does supervised Secretary routing reduce human coordination or unnecessary
   handoffs versus CoS-only execution while preserving correctness?
3. Does an existing native runtime provide safe controller-session resolution,
   delivery, receipt, recovery, and permission boundaries for a future adapter?

This plan proves live evidence and transport readiness only. It does not build
a permanent Secretary runtime, background scheduler, event bus, dashboard,
message archive, workflow database, Paseo integration, or autonomous
Secretary-to-CoS authority.

## Verdict Review

The supplied verdict is directionally correct and has the right sequence:
live evidence visibility, supervised comparison, then conditional transport
integration. Three corrections make it executable and prevent false progress:

### [P1] Make evidence attribution a hard admission gate

The existing `InMemoryControllerSessionAdapter` and
`benchmark_secretary_architecture.py` prove contracts only. Their
`deterministic-fake` results cannot support live latency, token, cost, or
efficiency claims. Every pilot receipt must bind `pair_id`, `run_id`,
`arm`, repository identity, Plan identity, Plan revision, worktree, provider,
model, controller/session identity, and event timestamps. Missing attribution
must produce `BLOCKED_CAPABILITY` or `INCONCLUSIVE`, not an inferred success.

### [P1] Separate ordinary CoS proof from callable API proof

PR #60 strengthens `apply_accepted_plan_transitions()`, but a tested callable
boundary does not prove that ordinary native CoS execution invokes it with
independently checked evidence. The pilot must run one real supervised CoS
operation through the existing launcher path or record
`BLOCKED_CAPABILITY` with the missing invocation surface. It must not perform
another broad acceptance refactor.

### [P1] Treat transport readiness as inspection, not implementation

The repository owns transport-neutral contracts and an in-memory journal, not a
named live Secretary-to-CoS transport. Stage C therefore records the actual
transport, session owner, receipt mechanism, restart behavior, idempotency,
and permission boundary. If any required fact is unavailable, the stage ends
`BLOCKED_CAPABILITY`; no guessed adapter or provider fallback is added.

## Scope Boundaries

### In scope

- Read-only, on-demand evidence projection from canonical sources.
- One genuine cross-workstream dependency with frozen paired inputs.
- CoS-only baseline and supervised Secretary-assisted candidate arms.
- Attributable timestamps, interventions, management turns, publication,
  settlement, acceptance, duplicate effects, and optional provider usage.
- Existing Codex/Herdr capability discovery and configured provider routing.
- A `READY` or `BLOCKED_CAPABILITY` transport-readiness disposition.

### Deferred

- Production Secretary-to-CoS adapter implementation.
- Unattended Secretary activation or polling.
- New durable journal, message archive, scheduler, event bus, or database.
- Dashboard or broad history-indexing surface.
- Paseo integration and cross-workstream mesh routing.
- Any Secretary efficiency or savings claim without live attributed evidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Baseline commit: `main` containing PR #60 merge `34d6e8d`.
- Execution mode: sequential; Tasks 1–7 have shared evidence and runtime
  prerequisites, so do not parallelize them.
- Primary executor: `codex`.
- Validator: independent review of evidence schema, correctness gate, and
  transport disposition; validator identity must differ from executor identity.
- Provider: use existing Codex `config.toml` and `auth.json` through the
  configured `9router` route. Do not expose credentials or invent fallback
  providers. If Secretary cannot be launched through an owned existing path,
  record the capability gap.
- Workspaces: use separate fresh worktrees for paired arms. Preserve existing
  untracked files and do not reuse stale pilot receipts.
- Writes: Plan, Git, Worker TaskResult, and runtime remain canonical owners.
  Pilot artifacts are receipts and analysis only; they are not workflow state.
- External actions: no install, authentication, deployment, provider change,
  remote publication, push, merge, or destructive cleanup without explicit
  approval.

## Coordination State

- Coordination owner: single lead controller.
- Coordination schema: `1`
- Branch: controller-selected `codex/secretary-live-evidence-transport-readiness`.
- Base commit: `34d6e8d`.
- Expected workspace: tracked clean before execution; preserve unrelated
  `.playwright-mcp/`, `db/`, and `temp_evidence.json` if present.
- Next action: retain direct CoS coordination; revisit Secretary only with an
  owned runtime, attributable receipts, and separately approved transport work.
- Blockers: none
  Tasks 3, 5, and 6 closed with explicit
  `BLOCKED_CAPABILITY` evidence because no owned live Secretary-to-CoS transport
  or ordinary CoS acceptance caller was found; no fake live telemetry is
  permitted.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | codex | none | baseline and capability inventory | `pilot_artifacts/secretary-live-evidence/capability-inventory.json` |
| Task 2 | `completed` | current | codex | Task 1 | read-only evidence snapshot tests | `4 passed` |
| Task 3 | `completed` | current | codex | Task 1, Task 2 | ordinary CoS acceptance-path result | `BLOCKED_CAPABILITY` in capability inventory |
| Task 4 | `completed` | current | codex | Task 2, Task 3 | frozen paired workload and receipt schema | `18 passed`; workload manifest |
| Task 5 | `completed` | current | codex | Task 4 | correctness-gated paired comparison | `BLOCKED_CAPABILITY` comparison report |
| Task 6 | `completed` | current | codex | Task 1, Task 4 | named transport readiness disposition | `BLOCKED_CAPABILITY` in capability inventory |
| Task 7 | `completed` | current | codex | Task 2–6 | final reconciliation and plan disposition | validators and fresh test output |

## Task Breakdown

### Task 1: Establish baseline and inspect existing capability boundaries

**Purpose:** Confirm execution starts from PR #60's merged correctness baseline
and identify whether an owned live Secretary or native CoS session surface
exists before adding pilot code.

**Task Function:** Source-first architecture and runtime capability inventory.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: resolve from scope, runtime access, and evidence risk; do not
  select by task name.

**Specification Coverage:** Verdict review, configured provider route, ordinary
CoS integration check, and transport readiness prerequisites.

**Required Skills:** `skill-backend-verification`, `skill-project-secretary`,
`skill-chief-of-staff`, `skill-code-standards`.

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_adapter.py` symbols
  `ControllerSessionAdapter`, `InMemoryControllerSessionAdapter`,
  `InMemoryControllerSessionJournal`, and receipt dataclasses.
- Inspect: `scripts/project_os_runtime/secretary_events.py` symbols
  `EventHint`, `coalesce_event_hints()`, and `reconcile_event_hint()`.
- Inspect: `scripts/herdr_main_launcher.py` existing-target resolution and
  launcher entry point; `scripts/herdr_parallel_dispatch.py` function
  `run_parallel_from_plan()` and CLI parser.
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md`,
  `docs/operating_system/tooling/runtime-tool-resolution.md`,
  `repo_config/switchyard-routing.toml`, and configured Codex paths.
- Create: `pilot_artifacts/secretary-live-evidence/capability-inventory.json`.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: read repository sources, inspect local configured capability
  metadata, run non-mutating help/dry-run probes, and write the named local
  inventory artifact.
- Stop for: missing credentials, requested authentication, provider change, install,
  deployment, remote write, or any claimed live Secretary runtime without an
  attributable owner and receipt.

**Steps:**
- [x] Verify `main` contains merge `34d6e8d`; stop and rebase before execution
  if the active checkout is older.
- [x] Record existing adapter contracts and deterministic-fake limitations.
- [x] Trace the actual native CoS launch path and distinguish CoS sessions from
  Herdr Worker panes; do not treat Worker prompt delivery as CoS transport.
- [x] Record configured provider/model route without secrets and record whether
  Secretary has an owned launch path.
- [x] Record transport answers for session resolution, delivery, receipt,
  restart, idempotency, binding validation, and permission separation.
- [x] For every supported native probe, record exact command or interface,
  target binding, maximum turns/duration, disposable state boundary, expected
  result, receipt source, authorized effects, and cleanup action. A capability
  description without an executable probe definition is not readiness evidence.

**Verification:**
- [x] `py -B scripts/herdr_main_launcher.py --help`
- [x] `py -B scripts/herdr_parallel_dispatch.py --help`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan .\docs\superpowers\plans\2026-10-08-secretary-live-evidence-and-transport-readiness-pilot-plan.md`
- [x] Inventory contains explicit `AVAILABLE`, `NOT_AVAILABLE`, or
  `BLOCKED_CAPABILITY` for each required capability; no blank or inferred value.

**Exit Criteria:** Baseline and capability inventory identify exact existing
owners, commands, receipt surfaces, and gaps. No transport code is added.

### Task 2: Build a compact read-only evidence projection

**Purpose:** Prove Secretary can reconstruct current attention from canonical
facts without owning task status, acceptance, lifecycle, or a duplicate ledger.

**Task Function:** Backend evidence projection and direct boundary verification.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: small typed projection with missing/stale evidence risk.

**Specification Coverage:** Stage A, reconstructible evidence, stale/missing
  detection, sparse communication, and no Worker wake for status.

**Required Skills:** `skill-backend-verification`, `skill-project-secretary`,
`skill-code-standards`, `skill-test-driven-development`.

**Files And Symbols:**
- Create: `scripts/project_os_runtime/secretary_evidence.py` with
  `EvidenceSnapshot`, `EvidenceStatus`, and `build_evidence_snapshot()`.
- Create: `tests/test_secretary_evidence.py`.
- Reuse: `scripts/project_os_runtime/plan_preparation.py` `load_plan()` and
  `parse_plan()`; do not create another Plan parser.
- Reuse: `scripts/project_os_runtime/secretary_adapter.py` receipt types; do
  not create another controller-session journal.

**Dependencies:** Task 1.

**Authority:**
- Preauthorized local actions: add the named pure projection module and focused tests.
- Stop for: any request to persist task state, acceptance state, runtime lifecycle,
  full history, or Secretary-owned workflow transitions.

**Steps:**
- [x] Define immutable snapshot fields: repository identity, workstream,
  Plan identity, Plan revision, Git revision, selected task and state, accepted
  prerequisite references, Worker result reference, settlement state,
  acceptance decision, project consequence, next authorized attention action,
  and source provenance.
- [x] Make `build_evidence_snapshot()` return `CURRENT`, `MISSING`, or `STALE`
  with explicit reasons; never convert absent evidence into success.
- [x] Require Plan/Git identity agreement and reject mismatched task/result,
  stale revision, missing settlement, and missing acceptance references.
- [x] Keep output compact and reference-based. Do not read full histories or
  wake Workers solely to create a snapshot.
- [x] Serialize only sanitized evidence; exclude credentials, private prompts,
  agent memory, and internal provider tokens.

**Verification:**
- [x] Add focused tests for current evidence, missing evidence, stale
  Plan/Git revision, mismatched workstream, and unsupported acceptance.
- [x] `py -B -m pytest -p no:cacheprovider tests/test_secretary_evidence.py -q` (`4 passed`)

**Exit Criteria:** Snapshot tests prove current facts are reconstructible and
missing/stale facts remain unresolved without creating a second state owner.

### Task 3: Prove ordinary CoS acceptance-path usage or record capability gap

**Purpose:** Distinguish PR #60's callable acceptance writer from a real
supervised CoS operation that invokes it with fresh evidence.

**Task Function:** Native runtime integration check and acceptance boundary proof.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: live boundary evidence may require a different profile than
  source-only validation.

**Specification Coverage:** PR #60 follow-up check, acceptance authority,
  actual Git freshness, and no broad acceptance refactor.

**Required Skills:** `skill-backend-verification`, `skill-chief-of-staff`,
`skill-systematic-debugging`, `skill-test-driven-development`.

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py` functions
  `evaluate_acceptance()` and `authorize_dependent_transition()`.
- Inspect: `scripts/project_os_runtime/plan_preparation.py` functions
  `apply_accepted_plan_transitions()` and `apply_plan_transitions()`.
- Inspect: `scripts/herdr_main_launcher.py` and
  `scripts/herdr_parallel_dispatch.py` for the actual CoS invocation path.
- Extend only if a real caller exists: the caller's focused integration test;
  do not add a new acceptance service or mutation owner.
- Record: `pilot_artifacts/secretary-live-evidence/capability-inventory.json`.

**Dependencies:** Task 1 and Task 2.

**Authority:**
- Preauthorized local actions: run one supervised local operation through an existing
  configured path and record sanitized receipt facts.
- Stop for: no native CoS session, no attributable runtime receipt, stale Git
  evidence, or request for a guessed caller. Record `BLOCKED_CAPABILITY`.

**Steps:**
- [ ] Prepare one active task with one accepted Worker result and one dependent
  pending task in a disposable fresh worktree.
- [ ] Re-read actual Plan revision, Git HEAD, write scope, and relevant
  artifact evidence immediately before acceptance-bound mutation.
- [ ] Run the existing native CoS path and capture controller identity, task and
  Plan bindings, acceptance decision, transition result, and final Plan state.
- [ ] Verify one accepted task completes and only explicitly authorized
  dependent activation occurs; verify stale or mismatched evidence does not
  mutate Plan.
- [x] If no ordinary caller exists, record the exact missing boundary and close
  this task `BLOCKED_CAPABILITY`; do not label callable tests as live proof.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_plan_preparation.py tests/test_project_os_runtime.py -q`
- [x] Capability inventory records missing ordinary CoS acceptance caller and
  no live receipt; callable tests remain contract evidence only.
- [x] No acceptance mutation occurs when the live boundary or freshness proof is
  missing.

**Exit Criteria:** Ordinary CoS usage is proven once, or capability absence is
  explicitly recorded. Neither outcome changes the acceptance architecture.

### Task 4: Freeze matched workload and attributable receipt contract

**Purpose:** Make baseline and candidate comparison reproducible, paired, and
  resistant to fake or unbound telemetry.

**Task Function:** Pilot harness and evidence-contract implementation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded data-contract work with correctness-sensitive input.

**Specification Coverage:** Stage B workload freeze, live attribution, metrics,
  separate manual relay time, and provenance.

**Required Skills:** `skill-backend-verification`, `skill-project-secretary`,
`skill-test-driven-development`.

**Files And Symbols:**
- Create: `scripts/secretary_live_pilot.py` with CLI subcommands
  `prepare`, `record`, and `compare`.
- Create: `tests/test_secretary_live_pilot.py`.
- Create/update: `pilot_artifacts/secretary-live-evidence/workload-manifest.json`.
- Reuse: configured launcher and dispatcher paths; no second launcher.

**Dependencies:** Task 2 and Task 3.

**Authority:**
- Preauthorized local actions: create the named local harness, schema tests, sanitized
  manifests, and local receipts.
- Stop for: no live run may proceed with missing identity binding, mutable workload
  inputs, unknown correctness status, or undisclosed manual relay time.

**Steps:**
- [x] Define one genuine cross-workstream dependency, fixed Plan revision,
  task order, Worker profile/grant, correctness gate, acceptance requirements,
  runtime base, and separate fresh worktrees.
- [x] Define receipt fields: `pair_id`, `run_id`, `arm`, `task_id`,
  `plan_revision`, `repository_identity`, `worktree`, provider/model, controller
  and session identity, entry/exit timestamps, first useful Worker action,
  publication, settlement, acceptance, Secretary relay, human interventions,
  CoS/Secretary turns, duplicate/irrelevant wakes, correctness result,
  token usage, cost, and provenance.
- [x] Require source references to the producer-owned launch/attempt receipt,
  assignment binding, Worker `TaskResult`, verification output, settlement
  receipt, and separate CoS acceptance proof. Validate producer identity,
  `assignment_id`, `attempt_id`, task binding, Plan revision, worktree, and
  checkpoint against those sources; never trust relabeled top-level fields.
- [x] Encode missing token or cost counters as `unknown`; never substitute
  deterministic benchmark numbers.
- [x] Make `record` reject mismatched pair bindings, duplicate run IDs,
  impossible timestamp order, missing publication/settlement/acceptance facts,
  unclassified manual relay time, relabeled historical evidence, and
  cross-attempt replay.
- [x] Freeze `max_attempted_pairs: 5`, `minimum_valid_pairs: 3`,
  `max_arm_runs: 10`, and `max_total_wall_clock_minutes: 180` in the workload
  manifest. Stop after 3 valid pairs, stop immediately on capability failure
  or correctness failure, and classify exhaustion before 3 valid pairs as
  `INCONCLUSIVE`.
- [x] Freeze primary metric `human_interventions_per_accepted_workstream`.
  `VERIFIED_BENEFIT` requires at least one fewer median intervention in the
  candidate across 3 valid pairs, no correctness defect, and candidate accepted
  completion time no more than 10% slower than baseline. All other metrics are
  secondary and cannot override the correctness gate.
- [x] Make `compare` emit paired deltas only after the correctness gate passes;
  keep token/cost deltas separate from intervention/turn deltas.

**Verification:**
- [x] Add failing tests for missing attribution, duplicate delivery, stale Plan
  revision, incorrect result, publication failure, and valid paired receipt.
- [x] `py -B scripts/secretary_live_pilot.py --help`
- [x] `py -B -m pytest -p no:cacheprovider tests/test_secretary_live_pilot.py -q`

**Exit Criteria:** Frozen manifest and receipt schema reject unsupported claims
and accept only attributable, correctness-classified pilot evidence.

### Task 5: Run supervised CoS-only and Secretary-assisted matched trials

**Purpose:** Measure coordination outcomes without confusing relay or provider
  overhead with Secretary benefit.

**Task Function:** Live supervised experiment and paired evidence analysis.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: live runtime task with higher evidence and operational risk.

**Specification Coverage:** Stage B comparison, decision rule, correctness hard
  gate, and `INCONCLUSIVE` disposition.

**Required Skills:** `skill-backend-verification`, `skill-project-secretary`,
`skill-chief-of-staff`, `skill-verification-before-completion`.

**Files And Symbols:**
- Execute: `scripts/herdr_main_launcher.py` for configured live launches and
  `scripts/herdr_parallel_dispatch.py` only for approved bounded Worker lanes.
- Record: `pilot_artifacts/secretary-live-evidence/trials/run-001.json` and
  increment the numeric filename for each additional receipt.
- Update: `pilot_artifacts/secretary-live-evidence/comparison-report.md`.
- Do not modify: `scripts/project_os_runtime/secretary_adapter.py` or provider
  configuration during trial execution.

**Dependencies:** Task 4.

**Authority:**
- Preauthorized local actions: supervised local trial runs using existing configured runtime,
  sanitized receipt capture, and local report generation.
- Stop for: provider/authentication failure, unowned Secretary runtime, missing
  receipt, incorrect result, stale evidence acceptance, unauthorized write,
  duplicate execution, or publication failure. Mark affected pair invalid and
  do not infer efficiency.

**Steps:**
- [ ] Run baseline arm: CoS-only routing for the frozen dependency.
- [ ] Run candidate arm: CoS plus supervised Secretary routing; manual relay is
  allowed and measured separately from agent processing.
- [ ] Use fresh worktrees and equivalent plan/task/runtime inputs; alternate
  arm order when collecting more than one pair.
- [ ] Capture one complete receipt per arm and preserve producer-owned source
  evidence locally; publish only sanitized references and derived metrics.
- [ ] Run no more than 5 attempted pairs and stop after 3 valid pairs. Do not
  continue after capability failure, correctness failure, or budget exhaustion.
- [ ] Apply the hard correctness gate before calculating any coordination delta.
- [x] Record `BLOCKED_CAPABILITY` with zero valid pairs when no owned live
  Secretary runtime and attributable receipt surface exist; generate no fake
  live telemetry.

**Verification:**
- [ ] Every accepted receipt has live provenance, binding identity, timestamps,
  and final state evidence.
- [ ] Report human interventions, management turns, first useful Worker action,
  accepted completion time, duplicate/irrelevant wakes, valid publication rate,
  incorrect acceptance/duplicate execution, and optional token/cost data.
- [ ] Classify outcome as `VERIFIED_BENEFIT`, `NO_MEASURED_BENEFIT`,
  `INCONCLUSIVE`, or `BLOCKED_CAPABILITY`.
- [x] Classification is `BLOCKED_CAPABILITY`; no comparative claim is emitted.

**Exit Criteria:** Secretary is recommended as optional only when paired,
correctness-gated evidence shows reduced coordination cost without regression.
Otherwise report no benefit, inconclusive evidence, or capability blockage and
keep direct CoS coordination as default.

### Task 6: Assess native transport readiness without implementing an adapter

**Purpose:** Determine whether an existing runtime can safely support a future
Secretary-to-CoS adapter.

**Task Function:** Runtime boundary inspection and capability disposition.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: transport and permission analysis, not generic feature work.

**Specification Coverage:** Stage C, transport prerequisites, permission
  separation, recovery, idempotency, and conditional Stage D gate.

**Required Skills:** `skill-backend-verification`, `skill-project-secretary`,
`skill-code-standards`.

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_adapter.py` protocol methods
  `resolve()`, `activate()`, `resume()`, `observe()`, `deliver()`, and
  `release_session()` plus receipt dataclasses.
- Inspect: `scripts/herdr_main_launcher.py`, `scripts/dcode_project.py`, and
  `docs/operating_system/runtime/runtime-surfaces.md` for actual transport
  ownership and restart behavior.
- Update: `pilot_artifacts/secretary-live-evidence/capability-inventory.json`.

**Dependencies:** Task 1 and Task 4.

**Authority:**
- Preauthorized local actions: source inspection, local capability queries, and
  bounded probes against disposable local state only when Task 1 records the
  exact command/interface, target binding, limits, effects, expected result,
  receipt source, and cleanup action; write sanitized readiness evidence.
- Stop for: no transport installation, authentication, provider substitution,
  remote or production state mutation, unbounded activation/delivery, durable
  state creation, scheduler, or autonomous authority expansion. Classify any
  required probe outside the recorded disposable boundary as
  `BLOCKED_CAPABILITY` until separately approved.

**Steps:**
- [x] Name the available contract-only transport surface and record that no
  owned live Secretary transport owner or endpoint exists; controller-session
  identity source is unavailable.
- [ ] Execute bounded native probes named in Task 1 for activation, delivery,
  resume, duplicate activation/delivery, binding drift, and authority boundary.
  Store one sanitized receipt per probe under
  `pilot_artifacts/secretary-live-evidence/transport-probes/`.
- [ ] Prove or classify receipt behavior for delivery, observation, restart,
  and session resume.
- [ ] Prove or classify idempotency for repeated activation and repeated
  delivery, including payload/binding conflict behavior.
- [ ] Verify current Plan/Git identity is checked on resume and that Secretary
  cannot execute Worker work or accept Plan transitions.
- [ ] Emit exactly `READY` only when all prerequisites are evidenced; otherwise
  emit `BLOCKED_CAPABILITY` with missing facts and a stop condition.
- [x] Emit `BLOCKED_CAPABILITY` because native activation, delivery, resume,
  receipt, idempotency, and permission probes have no executable live target.
- [ ] If `READY` and Task 5 reports `VERIFIED_BENEFIT`, draft a separate
  adapter implementation plan. Do not implement that adapter in this plan.

**Verification:**
- [x] Existing deterministic contract tests remain green:
  `py -B -m pytest -p no:cacheprovider tests/test_secretary_adapter.py tests/test_secretary_events.py tests/test_secretary_benchmark.py -q`
- [x] Native probe receipts are not claimed; missing executable targets remain
  `BLOCKED_CAPABILITY`. Deterministic contract tests cannot produce `READY`.
- [x] Inventory records transport name, owner, evidence source, readiness,
  unresolved capabilities, and permission boundary.

**Exit Criteria:** Transport is explicitly `READY` or `BLOCKED_CAPABILITY`;
there is no guessed live integration and no new authority layer.

### Task 7: Reconcile pilot evidence and close with an honest disposition

**Purpose:** Validate all artifacts and close the plan without upgrading a
missing capability or fake telemetry into a performance claim.

**Task Function:** Independent verification, evidence reconciliation, and plan
  lifecycle closure.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: independent validator must inspect exact receipts and gates.

**Specification Coverage:** Final verification, plan status, generated surfaces,
  no-secret publication, and deferred Stage D handoff.

**Required Skills:** `skill-verification-before-completion`,
`skill-plan-document-reviewer`, `skill-code-standards`.

**Files And Symbols:**
- Review all changed files and `pilot_artifacts/secretary-live-evidence/*`.
- Independent validator reads receipts and returns a read-only evidence report
  and verdict; it does not update Coordination State, task rows, or plan status.
- The single lead controller updates this plan's Coordination State, task table,
  deviations, and final disposition after reviewing validator output.
- If a separate adapter plan is justified, create it as a new proposed plan;
  do not fold adapter implementation into this plan.

**Dependencies:** Tasks 2–6.

**Authority:**
- Preauthorized local actions: independent validator runs local tests/validators
  and writes read-only reports; lead controller sanitizes reports and updates
  coordination state after validator handoff.
- Stop for: unresolved receipt identity, unverified correctness, secret leakage,
  unexpected generated drift, or any claim not supported by a source artifact.

**Steps:**
- [x] Reconcile every task row with a receipt or explicit
  `BLOCKED_CAPABILITY`/`INCONCLUSIVE` evidence reference.
- [x] Have independent validator return `verified`, `incomplete`, or `blocked`
  with source references and no coordination writes.
- [x] Have lead controller apply validator result to task rows and plan status;
  no second writer edits the active plan.
- [x] Confirm no deterministic-fake benchmark result appears as live evidence.
- [x] Confirm no Secretary message is emitted when project consequence is
  unchanged and no canonical state is duplicated.
- [x] Confirm Task 5 decision and Task 6 readiness are reported independently.
- [x] Set plan `status: completed` only after verification returns `verified`;
  completion may contain explicit `INCONCLUSIVE` or `BLOCKED_CAPABILITY`
  outcomes when the pilot boundary is honestly closed.

**Verification:**
- [x] Focused runtime suites: `109 passed`.
- [x] Full suite: `998 passed, 1 skipped`.
- [x] Preflight and audit repository contract validation passed.
- [x] Planning lifecycle and required-section validation passed.
- [x] Adapter sync check and runtime drift validation passed.
- [x] `git diff --check` passed.

**Exit Criteria:** Fresh tests and validators pass; report distinguishes live
evidence, deterministic contract evidence, `INCONCLUSIVE`, and
`BLOCKED_CAPABILITY`; no unsupported Secretary benefit or transport claim
remains.

## Decision Rules

Apply classifications in this order; each run receives exactly one outcome:

1. `BLOCKED_CAPABILITY`: required owned runtime, session, receipt, permission,
   or recorded disposable probe is absent. Do not spend remaining trial budget.
2. `INCONCLUSIVE`: fewer than `minimum_valid_pairs: 3` remain after the cap of
   `max_attempted_pairs: 5`, or attribution/counters remain insufficient for a
   comparative claim.
3. `VERIFIED_BENEFIT`: all 3 valid pairs pass correctness; candidate median
   `human_interventions_per_accepted_workstream` is at least one lower than
   baseline; and candidate median accepted completion time, computed across
   the same 3 pairs, is no more than 10% slower than baseline.
4. `NO_MEASURED_BENEFIT`: all 3 valid pairs pass correctness but the frozen
   `VERIFIED_BENEFIT` thresholds are not both met. This includes added latency,
   added turns, no intervention reduction, or a completion-time regression
   above 10%.

Any incorrect result, stale-evidence acceptance, unauthorized write, duplicate
execution, or publication failure invalidates the affected pair and prevents
that pair from satisfying the valid-pair minimum.

## Deferred Stage D Handoff

Only both conditions authorize a separate adapter plan:

1. Task 5 returns `VERIFIED_BENEFIT` with attributable live receipts.
2. Task 6 returns `READY` with named transport and proven receipt/recovery/
   permission behavior.

If either condition fails, keep Secretary optional, retain direct CoS routing,
and stop without adding transport infrastructure.

## Final Reconciliation Checklist

- [x] Read-only evidence reconstructs current Plan/Git/runtime facts.
- [x] Missing and stale evidence remains unresolved.
- [x] Ordinary CoS acceptance usage is explicitly blocked by capability inventory.
- [x] Matched workload uses frozen inputs and bounded pair budgets; live arms are
  blocked before execution because Secretary runtime is unavailable.
- [x] Correctness gate remains required before any coordination delta.
- [x] Token/cost claims remain separate and `unknown` when unavailable.
- [x] Transport readiness is `BLOCKED_CAPABILITY` with evidence.
- [x] Secretary owns no task ledger, acceptance decision, or runtime lifecycle.
- [x] No permanent adapter or new infrastructure is hidden in pilot work.
- [x] Plan closes after fresh verification and honest disposition.

## Implementation Outcomes

- A compact read-only evidence projection reconstructs current workstream
  attention from Plan, Git, Worker, acceptance, and runtime sources.
- A supervised matched-trial harness records attributable baseline and
  candidate receipts, applies the correctness gate, and reports paired deltas
  without treating deterministic-fake metrics as live evidence.
- Ordinary CoS acceptance usage is either proven through an existing native
  path or recorded as `BLOCKED_CAPABILITY`.
- Native transport readiness is independently classified as `READY` or
  `BLOCKED_CAPABILITY` with named missing facts.
- No new Secretary authority, duplicate workflow ledger, background runtime,
  or permanent transport adapter is introduced by this pilot.

## Verification

Task-local verification covers evidence projection, receipt validation,
acceptance-path behavior, matched-pair correctness, and transport disposition.
Final verification runs the focused suites, full suite, repository contract
validators, planning lifecycle validator, required-section validator, adapter
sync check, runtime drift check, and `git diff --check` listed in Task 7.

## Completion Criteria

The plan may move from `proposed` to `completed` only after fresh verification
returns `verified`, all task rows have evidence or explicit capability
dispositions, and the final report separates `VERIFIED_BENEFIT`,
`NO_MEASURED_BENEFIT`, `INCONCLUSIVE`, and `BLOCKED_CAPABILITY`. A missing
Secretary runtime does not remain an implicit blocker: it closes as an explicit
capability disposition and leaves direct CoS coordination as default.
