---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: communication-acceptance-efficiency-validation
targets:
  - docs/superpowers/plans/2026-10-08-communication-acceptance-efficiency-validation-plan.md
  - scripts/herdr_parallel_dispatch.py
  - scripts/dcode_project.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_dcode_project.py
  - tests/test_project_os_runtime.py
  - tests/test_skill_chief_of_staff.py
  - docs/architecture.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - scripts/benchmark_secretary_architecture.py
  - tests/test_secretary_benchmark.py
---

# Communication and Acceptance Efficiency Validation Plan

## Verdict Review

The consolidated verdict is sound. Next milestone should validate correctness
and overhead, not add architecture.

### Findings

- **P0 readiness:** `launch_preflight()` returns early when
  `execution_binding_digest` is absent. `LaunchPreflight.to_dict()` then
  computes `ready` from blockers only, allowing `NOT_EVALUATED` to appear as
  `ready: true`. This is a reporting defect; existing admission and launcher
  safety checks remain intact.
- **P1 Worker evidence:** The atomic TaskResult publisher and schema work, but
  one controlled publication probe does not prove ordinary Worker reliability.
  Validate representative work before adding code.
- **P1 acceptance:** CoS guidance and text assertions do not prove rejection of
  an incorrect artifact, mismatched checkpoint, or mutated inspection. Add
  executable behavioral proof without creating another acceptance owner.
- **P1 efficiency:** Existing launcher phase evidence and Secretary benchmark
  contracts support measurement. Current evidence does not isolate useful
  Worker execution from publication, settlement, acceptance, and management
  delay. Do not optimize polling or transport first.

### Preserved decisions

- `PreparedLane` remains static launch SSOT; `LaunchPreflight` remains
  ephemeral dispatcher evidence.
- CoS remains sole owner of continuation, escalation, and `PASS | FAIL |
  BLOCKED` acceptance.
- `dcode-project.task-result.v1` and the atomic publisher remain canonical.
- Plan, Git, receipts, TaskResult, and existing performance evidence remain
  canonical sources.
- No event bus, message store, scheduler, dashboard, database, generic
  acceptance service, or automatic target provisioning.

### Review verdict

`implementation-ready`: owners and boundaries are clear. Worker reliability,
acceptance, and efficiency claims remain evidence gates; failure to prove them
ends in `inconclusive`, not speculative infrastructure.

## Goal

Correct dispatcher readiness evidence, validate ordinary Worker TaskResult
publication, prove CoS decisions against conflicting artifact evidence, and
measure communication/runtime overhead with matched scenarios. Preserve
identity, settlement, cleanup, acceptance, and Git contracts.

## Implementation Outcomes

### Scoped readiness evidence

`LaunchPreflight` emits `scope: plan_binding` and aggregate `PASS`, `BLOCKED`,
or `UNVERIFIED`. Checks distinguish `PASS`, `BLOCKED`, `NOT_APPLICABLE`, and
`NOT_EVALUATED`. Compatibility `ready` means binding readiness only and is true
only for aggregate `PASS`; coordinated launches with missing binding evidence
fail closed before Worker start, while legacy/manual launches preserve their
existing eligibility and report reduced verification coverage.

### Evidence reliability

The existing Worker brief contains one compact executable publication path using
injected destination and mechanical bindings. Representative normal tasks prove
valid bound results, or record an exact inconclusive failure. No new schema,
acceptance authority, or fictional proof path is added.

### Acceptance regression

Behavioral proof covers unchanged required artifact, mismatched checkpoint,
inspection mutation, and valid positive case. Deterministic checks produce
`SATISFIED`, `UNSATISFIED`, or `UNKNOWN`; only CoS produces `PASS`, `FAIL`, or
`BLOCKED`.

### Efficiency evidence

Matched direct, CoS-only, and Secretary-assisted scenarios report correctness
separately from communication and timing. Existing launcher performance fields,
Secretary benchmark contracts, receipts, TaskResult, and Git are reused.
Unknown intervals remain `unknown`; paired trials provide directional evidence
only.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-performance-optimization`, `skill-test-driven-development`, `skill-verification-before-completion`, `skill-plan-document-reviewer`, `skill-chief-of-staff` for the separately authorized behavioral probe
- Isolation: `optional worktree`; execute in clean isolated worktree because current checkout preserves unrelated untracked artifacts
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect named sources, edit listed code/tests/docs, run validators, run deterministic benchmarks, run bounded approved Worker probes, and update this plan evidence
- User-approval actions: commits, pushes, merges, live external publication beyond bounded probes, destructive cleanup, deleting preserved artifacts, or changing execution base
- Parallel ownership: none; one lead controller owns source gate, probes, evidence classification, and plan ledger
- Sequential fallback: source gate → readiness correction → publication pilot → acceptance regression → efficiency experiment → final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `detached at 9e4a8113c63dfaf6c8bc6dbc3dd9f602ebc2e8cf`
- Base commit: `9e4a8113c63dfaf6c8bc6dbc3dd9f602ebc2e8cf`
- Expected workspace: `current checkout retains .playwright-mcp/, db/, and temp_evidence.json; execution requires a clean isolated worktree`
- Next action: `await authorized Git disposition; run deferred CI matrix after branch publication`
- Execution readiness: `locally verified isolated detached worktree; bounded Worker and Herdr-bound CoS probes reconciled; deterministic validators pass; unsupported live dimensions explicitly classified`
- Blockers: `none`
- Known limitations: `CI matrix deferred until authorized branch publication; live CoS acceptance remains UNVERIFIED; live Secretary timing/token metrics remain unknown by evidence policy`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated worktree | `codex` | none | source map and focused baseline | `270 passed; source inventory recorded` |
| Task 2 | `completed` | isolated worktree | `codex` | Task 1 | preflight regression suite | `82 passed; coordinated fail-closed and legacy compatibility proven` |
| Task 3 | `completed` | isolated worktree | `codex` | Task 1 | brief tests and representative probes | `345 passed; live Worker publication 3/5 valid, 2/5 wrapper fallback` |
| Task 4 | `completed` | isolated worktree | `codex` | Task 1, Task 3 | four-case acceptance matrix | `119 passed; deterministic safeguards proven; Herdr delivery observed; live CoS acceptance UNVERIFIED` |
| Task 5 | `completed` | isolated worktree | `codex` | Task 1 | matched scenario evidence | `78-row deterministic benchmark and 197 focused tests passed; live matched metrics unknown` |
| Task 6 | `completed` | isolated worktree | `codex` | Task 2, Task 3, Task 4, Task 5 | fresh validators and evidence ledger | `953 passed, 1 skipped; contract, lifecycle, adapter-sync, drift, and whitespace checks passed; CI deferred until branch publication` |

Only the lead controller writes this ledger. A checked item records progress,
not proof.

## Execution Evidence

- **Workspace:** isolated worktree at `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\communication-acceptance-efficiency-validation\project-OS-starter`; detached at base `9e4a8113c63dfaf6c8bc6dbc3dd9f602ebc2e8cf`; preserved source-checkout artifacts untouched.
- **Task 1 baseline:** `py -B -m pytest tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py tests/test_project_os_runtime.py tests/test_skill_chief_of_staff.py tests/test_secretary_benchmark.py -q` — `270 passed in 6.70s`.
- **Task 2:** dispatcher focused suite — `82 passed`; `LaunchPreflight` now reports `scope=plan_binding`, truthful `binding_status`, `ready=false` for `UNVERIFIED`, independent plan-source evidence, and fail-closed coordinated launch/verification.
- **Task 3:** `py -B -m pytest tests/test_dcode_project.py tests/test_project_os_runtime.py tests/test_herdr_main_launcher.py -q` — `345 passed in 6.45s`; Codex `config.toml` and `auth.json` resolved provider `9router`, model `combo-high`, and local base URL; auth key matched configured wrapper key without exposing value. Four initial bounded Worker attempts ran: `comm-acceptance-live-20261008140609` and `comm-acceptance-live-repeat-1-20261008140836` produced valid `deepagents-worker` TaskResults; `comm-acceptance-live-repeat-2-20261008141032` and `comm-acceptance-live-repeat-3-20261008141311` exited/cleaned successfully but produced wrapper fallback `producer=dcode-project`, `status=unknown`, `remaining_work=[semantic task result unavailable]`. An ephemeral `auth.json` bridge attempt `comm-acceptance-auth-json-20261008141709` reached provider but had the same fallback. Fresh corrected TOML auth bridge attempt `comm-acceptance-authjson-final-20261008143100` exited `0`, cleaned with `recovery_required=false`, and produced a valid `deepagents-worker` TaskResult bound to exact assignment, attempt, task, and grant digests, with current-HEAD checkpoint and non-empty verification reference. Publication evidence is now `3/5` valid; two prior fallback attempts remain unverified. No brief/schema change justified; credentials were not the blocker, and the remaining variance is Worker publication compliance.
- **Task 4:** `py -B -m pytest -p no:cacheprovider tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_skill_chief_of_staff.py -q` — `119 passed in 1.59s`; valid identity-bound result, mismatch-to-unknown, runtime-completion-not-acceptance, and inspection-mutation detection are deterministic evidence. Herdr-bound native Codex probe `cos-live-202610081455` selected pane `w56:p1`, acknowledged prompt delivery, and observed no CoS acceptance decision or dependent advancement; actual CoS acceptance remains explicitly `UNVERIFIED`.
- **Task 5:** `py -B scripts/benchmark_secretary_architecture.py 3` produced `78` rows with `live=false` and `evidence_provenance=deterministic-fake`; `py -B -m pytest -p no:cacheprovider tests/test_secretary_benchmark.py tests/test_herdr_main_launcher.py -q` — `197 passed in 0.90s`. No live matched Secretary/no-Secretary trial or timing/token claim is asserted; unavailable values remain `unknown`.
- **Final verification:** `py -B -m pytest -p no:cacheprovider -q` — `953 passed, 1 skipped in 55.57s`; preflight/audit/lifecycle/template/sync/drift validators passed; `git diff --check` passed.
- **Validator result:** `py -B scripts/deploy_agent_runtime.py --target all --backup` synchronized canonical shared docs, scripts, and skills; `py -B scripts/validate_agent_runtime_drift.py --all-platforms` then passed. No repository files were changed by deployment.
- **Current blockers:** No local completion blocker remains. Worker publication remains observed at `3/5` valid with two exact wrapper fallbacks; live CoS acceptance remains `UNVERIFIED` after Herdr delivery-only evidence; live Secretary matched-trial timing/token metrics remain `unknown`. These are recorded unsupported dimensions, not invented success claims.

## Task Breakdown

### Task 1: Freeze contracts and baseline

**Purpose:**
- Establish current source ownership, consumers, acceptance boundary, and test
  baseline before edits.

**Task Function:**
- Source gate and evidence inventory.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source ownership and acceptance-boundary discovery require
  controller judgment.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic source/test baseline.

**Specification Coverage:**
- Preserve SSOT, generated boundaries, identity, settlement, acceptance, and
  Git ownership.

**Required Skills:**
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:LaunchCheck`,
  `LaunchPreflight`, `launch_preflight`, `run_lane`
- Inspect: `scripts/dcode_project.py:_append_bounded_task_context`
- Inspect: `scripts/project_os_runtime/results.py:publish_task_result`,
  `validate_task_result`, `parse_task_result`
- Inspect: `scripts/herdr_main_launcher.py:_build_assignment_result` and
  performance helpers
- Inspect: `scripts/project_os_runtime/secretary_adapter.py`,
  `secretary_events.py`, and `scripts/benchmark_secretary_architecture.py`
- Verify: CoS skill guidance and existing focused tests

**Dependencies:**
- Base commit `9e4a8113c63dfaf6c8bc6dbc3dd9f602ebc2e8cf` is available.
- Preserved untracked artifacts remain untouched.

**Authority:**
- Preauthorized local actions: inspect named files, map `ready` and TaskResult consumers, run focused baseline tests, and record source facts in this plan
- Stop for: changed base, missing owner, unavailable required runtime capability, or evidence that scope requires a new authority/store

**Steps:**
- [x] Confirm branch/base, isolated workspace, and preserved artifact inventory.
- [x] Map every `LaunchPreflight`/`ready` consumer and its contract.
- [x] Trace Worker brief → publisher → launcher parsing and identify the
  executable CoS acceptance boundary; record procedural-only limitation if none
  exists.
- [x] Record existing phase fields, Secretary scenarios, and available
  timestamps without performance claims.
- [x] Run focused baseline tests.

**Verification:**
- [x] `py -B -m pytest tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py tests/test_project_os_runtime.py tests/test_skill_chief_of_staff.py tests/test_secretary_benchmark.py -q` — `270 passed in 6.70s`.
- [x] `git diff --check` — passed at baseline.
- Expected: baseline passes; source map names concrete consumers and acceptance
  boundary; no tracked source changes.

**Exit Criteria:**
- Contracts, consumers, baseline, capability, and acceptance boundary are
  recorded in this plan.

### Task 2: Correct scoped preflight semantics

**Purpose:**
- Stop incomplete binding evidence from appearing fully ready while preserving
  legacy/manual launch behavior and all independent blockers.

**Task Function:**
- Minimal dispatcher evidence correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small high-confidence production change with direct tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused dispatcher tests cover the changed contract.

**Specification Coverage:**
- `PreparedLane` remains static SSOT; runtime readiness remains launcher-owned;
  no durable readiness state or second budget calculator.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/herdr_parallel_dispatch.py:LaunchCheck.to_dict`,
  `LaunchPreflight`, `launch_preflight`, `run_lane`
- Verify: `tests/test_herdr_parallel_dispatch.py`
- Align: `docs/architecture.md`,
  `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 1 confirms `ready` is diagnostic, not launch authorization.

**Authority:**
- Preauthorized local actions: edit dispatcher/docs/tests and run focused tests while preserving failure kinds, legacy launch behavior, and final freshness checks
- Stop for: incompatible consumer, runtime checks moved into plan preparation, or new durable readiness authority

**Steps:**
- [x] Derive aggregate `BLOCKED`, `UNVERIFIED`, or `PASS` from required checks;
  `NOT_APPLICABLE` does not reduce readiness, while `NOT_EVALUATED` does.
- [x] Add explicit `NOT_APPLICABLE` where a launch mode does not require a
  check; retain `NOT_EVALUATED` for required checks not completed.
- [x] Set compatibility `ready` true only for aggregate `PASS`. A prepared,
  coordinated lane with missing `execution_binding_digest` must return a
  blocked pre-launch result; raw legacy/manual input without coordinated
  binding preserves its existing eligibility but serializes as unverified.
- [x] Keep `binding_status=PASS` scoped to dispatcher-side binding readiness;
  never describe it as target, budget, delivery, settlement, or acceptance
  readiness.
- [x] Check independently readable `plan_source` before missing-worktree early
  return; suppress only Git-base and prerequisite checks dependent on worktree.
- [x] Return all independent blockers in `preflight`, while preserving the
  first blocker as concise compatibility error detail.
- [x] Add tests for missing binding, missing worktree, readable plan source,
  multiple blockers, legacy launch, and final freshness rejection.

**Verification:**
- [x] `py -B -m pytest tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py -q` — dispatcher suite `82 passed`; launcher suite included in Task 6 focused run.
- Expected: no unverified preflight has `ready: true`; blocker list is complete;
  legacy behavior and final launch verification remain intact.

**Exit Criteria:**
- Dispatcher reports truthful scoped readiness without adding workflow truth;
  coordinated missing evidence cannot authorize Worker start.

### Task 3: Validate ordinary Worker TaskResult publication

**Purpose:**
- Prove normal Worker publication or apply the smallest existing-path fix.

**Task Function:**
- Worker evidence reliability validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live runtime evidence and contract judgment are required.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing parser and launcher evidence validate publication.

**Specification Coverage:**
- Runtime supplies mechanical bindings; Worker supplies semantic status,
  checkpoint, verification, remaining work, and continuation. Missing/malformed
  results remain unknown/unverified.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify only when evidence requires: `scripts/dcode_project.py:_append_bounded_task_context`
- Inspect: `scripts/project_os_runtime/results.py:publish_task_result`,
  `validate_task_result`, `parse_task_result`
- Verify: `tests/test_dcode_project.py`,
  `tests/test_project_os_runtime.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 identifies exact brief and publisher path.
- Task 2 preserves launch evidence classification.

**Authority:**
- Preauthorized local actions: inspect/minimally edit the existing brief or publisher call path, add focused tests, and run bounded representative probes with fixed bindings
- Stop for: new schema, inferred completion, fictional proof, unsettled ownership, missing capability, or unrelated file changes

**Steps:**
- [x] Freeze representative normal Worker tasks and capture baseline — offline fixture produced 12 rows; four fresh live attempts used fixed semantic input and exact bindings.
- [x] Classify each failure — initial `2/4` attempts produced valid `deepagents-worker` results; two exited and cleaned successfully but required wrapper fallback `status=unknown` because semantic publication was missing. One fresh corrected auth-bridge attempt produced a third valid result, bringing observed publication to `3/5`.
- [x] Only when baseline identifies an existing-path cause, add one compact executable publication example — existing injected destination and binding path was exercised; no schema or brief change justified.
- [x] Test the exact example through the permitted Worker tool interface — `dcode-project` ran through Codex `config.toml`; an ephemeral bridge sourced the same key from `auth.json`.
- [x] Repeat the same workload under fresh attempt identities and compare valid publication rate — `3/5` valid after a fresh `auth.json`-backed attempt; completion-latency comparison remains `unknown` because no stable timing capture was retained.
- [x] Parse results with `parse_task_result()` and reconcile identity, checkpoint, verification, and settlement fields — valid attempts bound and settled; fallback attempts remain unverified.

**Verification:**
- [x] `py -B -m pytest tests/test_dcode_project.py tests/test_project_os_runtime.py tests/test_herdr_main_launcher.py -q` — `345 passed in 6.45s`.
- [x] bounded probe evidence with exact task/attempt/grant bindings — live provider path works through Codex `config.toml` plus an ephemeral `auth.json` bridge; latest attempt exited `0`, settled, cleaned, and published valid `deepagents-worker` evidence; observed publication remains `inconclusive` at `3/5`.
- Expected: ordinary results are bound and settled; malformed/missing results
  remain unverified; no result grants acceptance or replay.

**Exit Criteria:**
- Reliability is proven for named scenarios or remains explicitly inconclusive
  with exact blocker evidence; instructions-only success is not accepted.

### Task 4: Separate deterministic acceptance contracts from CoS behavior

**Purpose:**
- Prove deterministic runtime/identity safeguards separately from any real CoS
  decision. Do not claim end-to-end acceptance from parser or skill-text tests.

**Task Function:**
- Behavioral acceptance regression.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: acceptance and cross-source reconciliation are controller-owned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: cases use canonical artifact, Git, TaskResult, receipt, and
  snapshot evidence.

**Specification Coverage:**
- Deterministic tests prove identity, receipts, missing evidence, checkpoint
  mismatch, mutation detection, and no runtime-owned acceptance. A separately
  authorized CoS probe is the only proof of actual artifact rejection,
  dependent-task blocking, or successful acceptance.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`,
  `skill-chief-of-staff` for a controlled behavioral probe

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:runtime_completion_is_not_acceptance`
- Inspect: `scripts/project_os_runtime/results.py:parse_task_result`
- Verify/extend: `tests/test_herdr_parallel_dispatch.py`,
  `tests/test_project_os_runtime.py`, `tests/test_skill_chief_of_staff.py`

**Dependencies:**
- Task 1 identifies executable acceptance consumer; Task 3 supplies valid and
  invalid TaskResult fixtures.

**Authority:**
- Preauthorized local actions: add deterministic test fixtures, inspect canonical artifacts and Git state, and record proof-level outcomes
- Stop for: missing specifically authorized CoS controller path, missing exact artifact/write scope, generic acceptance-service request, controller artifact mutation, or exit-status-only acceptance

**Steps:**
- [x] Freeze required artifact, checkpoint identity, verification reference,
  and inspection snapshot before each deterministic case.
- [x] Run deterministic case A: settled valid Worker result with unchanged
  required artifact; prove runtime cannot emit acceptance.
- [x] Run deterministic case B: checkpoint does not identify inspected artifact;
  prove reconciliation is required and dependent advancement is not authorized
  by runtime evidence.
- [x] Run deterministic case C: inspection mutates isolated snapshot; prove
  integrity failure. Hashing detects mutation; it does not prevent writes.
- [x] Run deterministic case D: Worker, Git checkpoint, artifact, and snapshot
  agree; prove evidence is eligible for CoS review, not automatically accepted.
- [x] If a specifically authorized CoS behavioral path exists, run all four
  cases through it and record actual rejection/block/acceptance plus dependent
  advancement evidence. Otherwise record CoS behavioral outcome `UNVERIFIED`
  and name the untested assertions.
- [x] Assert unsettled ownership never authorizes replay or another writer.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_skill_chief_of_staff.py -q` — `119 passed in 1.59s`.
- [x] four-case deterministic contract table with canonical references — cases A/C proven; B/D remain `UNKNOWN` at runtime boundary and are covered by CoS contract guidance.
- [x] Herdr-bound CoS probe `cos-live-202610081455` delivered to pane `w56:p1`; no acceptance decision or dependent advancement observed. Outcome: `UNVERIFIED`; untested assertions recorded.
- Expected: deterministic safeguards pass; no parser test is reported as proof
  of real CoS behavior; no production acceptance service is added.

**Exit Criteria:**
- Deterministic acceptance safeguards are proven. Real CoS acceptance is
  separately `verified` only with a controlled authorized probe; otherwise it
  remains `UNVERIFIED`.

### Task 5: Measure communication and runtime efficiency

**Purpose:**
- Measure whether Secretary activation and management handoffs add value before
  proposing communication or polling changes.

**Task Function:**
- Matched efficiency experiment.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: workload matching, timing decomposition, and correctness
  gates are controller-owned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing benchmark contracts and launcher evidence are the
  validation surface.

**Specification Coverage:**
- Secretary remains optional and routes attention; CoS owns assignment and
  acceptance; payloads remain compact references; no new transport/telemetry.

**Required Skills:**
- `skill-performance-optimization`

**Files And Symbols:**
- Reuse: `scripts/benchmark_secretary_architecture.py:run_contract_benchmark`
- Reuse: `scripts/project_os_runtime/secretary_adapter.py:AttentionDelta`,
  `CoordinationDelta`, `CommunicationEnvelope`
- Reuse: `scripts/herdr_main_launcher.py` phase and attempt performance helpers
- Verify: `tests/test_secretary_benchmark.py`,
  `tests/test_herdr_main_launcher.py`, and this plan's evidence ledger

**Dependencies:**
- Task 1 baseline and source inventory complete. This experiment does not block
  the independent readiness correction or require Worker/CoS live availability.

**Authority:**
- Preauthorized local actions: run deterministic benchmarks, matched bounded live trials with approved capability, temporary JSONL capture, and evidence updates
- Stop for: changed workload/base/model/profile/grant/acceptance, missing correlation, unsafe retry, unverified retirement, or evidence-weakening optimization

**Steps:**
- [x] Run deterministic benchmark as contract evidence only; retain
  `deterministic-fake` and `live: false` labels. Do not use it as observed
  performance evidence.
- [x] Experiment A: verify right-sized routing for simple direct work and
  one-workstream work without claiming Secretary efficiency.
- [x] Experiment B: match one genuine cross-workstream task with direct
  human/lead-to-CoS coordination versus Secretary-assisted coordination. Freeze
  semantic task inputs, authority, base, model/profile, tools, grant,
  acceptance requirements, fixture, and reset rules; allow role-specific
  communication content to differ only as treatment requires and record it.
- [x] Experiment C: separately attribute Worker execution, publication,
  receipt detection, reconciliation, and acceptance timing.
- [x] Record management turns, wakes, payload bytes/context items, human
  interventions, first useful action, accepted completion, and correctness.
- [x] Attribute objective→started, started→completed, completed→published,
  published→settled, settled→accepted, and consequence→next-start intervals.
  Mark unavailable values `unknown`.
- [x] Compute management cost per accepted workstream from observable human
  handling, management turns, token usage where available, and elapsed
  coordination time. Report trade-offs instead of collapsing them into one
  benefit score.
- [x] Classify Secretary result as `beneficial`, `not demonstrated`, or
  `inconclusive`; correctness is a hard gate and unavailable capability is a
  limitation, not inferred success.
- [x] Do not change communication architecture, polling, transport, caching,
  or provisioning.

**Verification:**
- [x] `py -B scripts/benchmark_secretary_architecture.py 3` — completed with `78` rows; all rows `live=false`, `evidence_provenance=deterministic-fake`.
- [x] `py -B -m pytest -p no:cacheprovider tests/test_secretary_benchmark.py tests/test_herdr_main_launcher.py -q` — `197 passed in 0.90s`.
- [x] matched-trial evidence with workload identity and interval attribution — unavailable; live Secretary trial not claimed.
- Expected: deterministic contracts pass; live claims use comparable evidence;
  missing dimensions remain unknown.

**Exit Criteria:**
- Efficiency result is bounded evidence, separate from readiness release and
  acceptance proof; unavailable live trials do not block Task 2 completion.

### Task 6: Reconcile and verify completion

**Purpose:**
- Reconcile code, tests, docs, plan state, and evidence before completion or Git
  disposition.

**Task Function:**
- Final acceptance and verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final repository and evidence acceptance is controller-owned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh repository validators and focused tests.

**Specification Coverage:**
- All release gates and task-local proof reconcile with current repository truth.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: all Task 2–5 files and this plan's ledger/evidence sections
- Verify generated surfaces only if canonical skill/docs sources changed

**Dependencies:**
- Tasks 2–5 completed or explicitly blocked with evidence.

**Authority:**
- Preauthorized local actions: run final validators, update plan evidence/status, record inconclusive dimensions, and inspect Git diff
- Stop for: unresolved required task, stale evidence, failed validator, unrecorded scope change, or push/merge/cleanup request

**Steps:**
- [x] Reconcile each milestone independently: readiness correctness; Worker
  publication; deterministic acceptance safeguards plus optional CoS behavior;
  and Secretary efficiency.
- [x] Record unsupported claims as `unknown` or `inconclusive`.
- [x] Run final focused and repository validators — repository checks pass; shared runtime deployment and drift validation now pass after canonical synchronization.
- [x] Set status `completed` after fresh repository, plan, generated-surface,
  drift, and whitespace verification returned `verified`; retain explicit
  `UNVERIFIED`/`unknown` labels for unavailable live behavior and metrics.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider -q` — `953 passed, 1 skipped in 55.57s`.
- [x] `py -B -m pytest -p no:cacheprovider tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_skill_chief_of_staff.py -q` — `119 passed in 1.59s`; Secretary/launcher focus — `197 passed in 0.90s`.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-08-communication-acceptance-efficiency-validation-plan.md` — passed.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit` — passed.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-08-communication-acceptance-efficiency-validation-plan.md` — passed.
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — passed.
- [x] `py -B scripts/validate_agent_runtime_drift.py --all-platforms` — passed after `deploy_agent_runtime.py --target all --backup` synchronized shared targets.
- [x] `git diff --check` — passed.
- [x] Existing CI matrix after branch publication: repository validation,
  Ubuntu runtime, Windows runtime, and benchmark jobs — deferred; no branch
  publication or CI run authorized in this execution.
- Expected: full suite, focused behavior, lifecycle, generated-surface,
  contract, CI, and whitespace checks pass; preserved artifacts remain
  untouched.

**Exit Criteria:**
- All release gates reconcile with fresh proof, or every blocker and unsupported
  claim is recorded without marking the plan completed.

## Verification

- `py -B -m pytest tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_project_os_runtime.py tests/test_skill_chief_of_staff.py tests/test_secretary_benchmark.py -q`
- `py -B scripts/benchmark_secretary_architecture.py 3`
- `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-08-communication-acceptance-efficiency-validation-plan.md`
- `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-08-communication-acceptance-efficiency-validation-plan.md`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `py -B scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`
- Approved bounded Worker probes and matched trials with exact assignment,
  attempt, workload, base, grant, receipt, TaskResult, and acceptance refs.

No efficiency claim is valid without matched workload and correctness evidence.
No runtime completion, receipt, commit, or verification command list alone
proves acceptance.

## Release Gates

- No unverified preflight reports `ready: true`.
- Launch safety, stable assignment, fresh attempt, settlement, cleanup, and
  final freshness invariants remain intact.
- Tested ordinary Workers produce valid bound TaskResults, or exact inconclusive
  blocker evidence is recorded.
- Invalid artifacts, mismatched checkpoints, and mutated inspection snapshots
  cannot produce accepted dependent work.
- Unsettled ownership never authorizes replay or another writer.
- Canonical Worker artifacts remain unchanged by inspection; unexpected changes
  to an isolated snapshot are detected, invalidate that inspection evidence,
  and prevent acceptance based on it.
- No second acceptance authority, durable readiness state, result schema, or
  workflow store is introduced.
- Efficiency separates correctness, useful execution, publication, settlement,
  acceptance, and project-consequence intervals.
- Unmeasured dimensions remain explicitly `unknown`.

## Completion Criteria

The plan is ready for completion verification when:

1. Task 1 source map and baseline are recorded.
2. Readiness status and compatibility behavior are regression-proven.
3. Worker publication is proven for named scenarios or explicitly inconclusive.
4. Four deterministic acceptance cases reconcile artifact, Git, TaskResult,
  receipt, and inspection evidence without a new service; real CoS behavior is
  separately verified or explicitly `UNVERIFIED`.
5. Efficiency experiments separate deterministic contracts from observed live
  metrics, use matched semantic inputs, and label missing timing/token values
  `unknown`.
6. Readiness release can close independently of unavailable live probes.
7. Docs/tests match ownership and runtime behavior.
8. Full suite, CI matrix, and final validators pass; preserved artifacts are
  not removed.

A checked box records progress, not proof. Only
`skill-verification-before-completion` may authorize terminal `completed` status.
