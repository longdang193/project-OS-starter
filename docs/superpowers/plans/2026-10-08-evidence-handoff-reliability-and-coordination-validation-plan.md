---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: evidence-handoff-reliability-and-coordination-validation
targets:
  - scripts/herdr_parallel_dispatch.py
  - scripts/dcode_project.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_dcode_project.py
  - tests/test_herdr_main_launcher.py
  - tests/test_project_os_runtime.py
  - tests/test_secretary_adapter.py
  - tests/test_secretary_events.py
  - tests/test_secretary_benchmark.py
  - docs/superpowers/plans/2026-10-08-evidence-handoff-reliability-and-coordination-validation-plan.md
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Evidence Handoff Reliability and Coordination Validation

## Verdict Review

Verdict direction is sound. Immediate work must stay narrow:

- restore universal rejection of actual dispatcher preflight blockers;
- preserve sanitized publication failure causes instead of collapsing them to
  generic unknown evidence;
- reconcile every Worker attempt before changing publication mechanics;
- keep publication validity, completion-proof sufficiency, and CoS acceptance
  as separate decisions;
- prove native CoS acceptance with negative and positive cases;
- measure evidence-reconstruction and Secretary value before adding projections
  or automation;
- preserve Secretary–CoS–Worker ownership and existing attempt-bound mechanics.

The plan does not introduce a new TaskResult schema, evidence database,
publication daemon, event bus, heartbeat service, dashboard, scheduler, or
automatic target-provisioning path. Live controller probes remain evidence
tasks, not substitutes for deterministic regression tests.

## Goal

Make Worker evidence handoffs diagnostically reliable and make coordination
decisions independently verifiable without weakening launch safety, attempt
ownership, settlement, cleanup, authorization, or semantic acceptance.

## Implementation Outcomes

### Universal preflight safety

Legacy/manual and coordinated launches reject every actual `BLOCKED`
`LaunchCheck` before starting a launcher subprocess. Missing required binding
evidence remains `UNVERIFIED` only for coordinated lanes. Existing launcher-
owned budget and target checks remain unchanged.

### Precise Worker publication evidence

Malformed, unavailable, mismatched, or unauthorized Worker TaskResult evidence
surfaces a compact sanitized diagnostic projection. Wrapper fallback evidence
preserves failure classification without retaining malformed payload contents or
secrets.

### Separate evidence stages

The runtime distinguishes valid publication, sufficient completion proof, and
CoS acceptance. A runtime result never becomes accepted merely because it is
published or settled. Missing task-specific completion proof cannot produce a
strong completion signal.

### Native acceptance proof

Two live controller-path cases prove that false completion is rejected without
dependent advancement and correct implementation is accepted only after
independent CoS verification. Evidence includes both the decision and resulting
coordination state.

### Measured coordination value

A reconciled Worker publication cohort, a conditional read-only evidence-slice
decision, and matched live-supervised CoS-only versus Secretary-assisted
correctness evidence exist in the existing plan evidence table. Efficiency
value is `INCONCLUSIVE` because provider/runtime counters and attributed
latency are unavailable; deterministic Secretary tests remain labeled
`deterministic-fake` and no efficiency claim is made.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-plan-document-reviewer`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `task-specific isolated worktree`; preserve current checkout artifacts
- Commit policy: `no commits during execution`; lead controller commits only after final verification
- Preauthorized local actions: edit named repository files, run declared deterministic tests and validators, inspect configured local runtime evidence, and record sanitized probe results in this plan
- User-approval actions: native controller execution requiring external credentials or authority, external publication, push, pull request, merge, destructive cleanup, and discard of preserved artifacts
- Parallel ownership: none; preflight, publication, and acceptance contracts share evidence consumers and execute sequentially
- Sequential fallback: Task 1 → Task 2 → Task 3 → Task 4 → Task 7 → Task 5 → Task 6 → Task 8

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/evidence-handoff-reliability`
- Base commit: `41bed545894cd4e40cfbcf100e73c4f62eb5e0a9`
- Expected workspace: current checkout preserves `.playwright-mcp/`, `db/`, `temp_evidence.json`, and the prior untracked plan; execution uses a clean isolated worktree
- Next action: branch finishing after final verification; revisit Secretary efficiency only when provider counters and attributed timestamps exist
- Blockers: none
- Approved limitation: Secretary efficiency remains an explicit `INCONCLUSIVE` disposition, not a success claim

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated worktree | `codex` | none | source map and baseline | 465 passed; base and source audit recorded |
| Task 2 | `completed` | isolated worktree | `codex` | Task 1 | universal blocker regression suite | `82 passed`; both dispatcher callers covered |
| Task 3 | `completed` | isolated worktree | `codex` | Task 1 | reconciled cohort and root-cause classification | summary says `3/5`; raw attempt IDs unavailable; no helper justified |
| Task 4 | `completed` | isolated worktree | `codex` | Task 1, Task 3 | diagnostic projection and evidence-stage tests | `347 passed` across parser, wrapper, launcher, and runtime compatibility tests; exact `deepagents-worker` provenance enforced; sanitized fallback reason preserved |
| Task 5 | `completed` | isolated worktree | `codex` | Task 4 | native CoS negative/positive acceptance evidence | native Codex/`9router` probe on October 8, 2026 exercised `evaluate_acceptance()` and `authorize_dependent_transition()` without file changes: false artifact → `FAIL`, dependent `pending`; valid evidence → `PASS`, dependent `active`; focused acceptance tests `15 passed`, including Git-plan and accepted-task identity regressions |
| Task 6 | `completed` | isolated worktree | `codex` | Task 4 | reconstruction-cost decision and matched Secretary measurements | prior approved live-supervised probe: matched baseline/candidate order, fresh worktrees/contexts, `matched_inputs=true`, semantic reconciliation `PASS`; value `INCONCLUSIVE`; timing/token counters unavailable, no projection added |
| Task 7 | `completed` | isolated worktree | `codex` | Task 2, Task 4 | Phase A deterministic release gate | `961 passed, 1 skipped`; preflight, audit, lifecycle, adapter, runtime-drift, and diff checks pass; Phase A independently releasable |
| Task 8 | `completed` | isolated worktree | `codex` | Task 5, Task 6, Task 7 | final verification and plan reconciliation | deterministic tests, validators, generated sync, runtime drift, and diff checks pass; approved measurement limitation reconciled |

Only lead controller writes this ledger. Checkboxes record progress, not proof.

## Root-Cause Follow-Up

- Provider route was not causal: configured `9router` plus `auth.json` completed
  native Codex execution.
- Shared-caller trace found settlement and continuation gates in
  `scripts/project_os_runtime/attempt.py`, publication and `accepted` parsing in
  `scripts/project_os_runtime/results.py`, `acceptance_pending` classification
  in `scripts/herdr_parallel_dispatch.py`, and plan-state validation in
  `scripts/validate_planning_lifecycle.py`.
- No existing caller evaluated artifact conditions or authorized a dependent
  task transition. Worker and launcher paths intentionally kept `accepted` as
  `None`; no alternate acceptance setter existed elsewhere.
- Root cause: native Project OS runtime had no callable CoS acceptance boundary
  joining controller identity/authority, plan/task binding, artifact conditions,
  Git checkpoint, verification, settlement, and dependent-task gating.
- Patch: `scripts/project_os_runtime/acceptance.py` adds pure
  `PASS | FAIL | BLOCKED` evaluation and a derived dependent-transition gate;
  it writes no plan state, adds no result schema, and creates no second
  authority. Focused regression proof covers false artifact, valid acceptance,
  missing controller binding, and unsettled resources.

## Task Breakdown

### Task 1: Freeze merged contracts and reconcile baseline

**Purpose:**
- Establish source ownership, current consumers, preserved artifacts, and
  baseline behavior before changing code or interpreting live evidence.

**Task Function:**
- Source gate and evidence inventory.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: exact contract and consumer mapping require controller judgment.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic source and test baseline.

**Specification Coverage:**
- Preserve SSOT, attempt identity, settlement, cleanup, acceptance ownership,
  generated-surface boundaries, and sparse communication boundaries.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect `scripts/herdr_parallel_dispatch.py`: `LaunchCheck`,
  `LaunchPreflight`, `_is_coordinated_lane`, `launch_preflight`,
  `verify_launch_bindings`, `run_lane`
- Inspect `scripts/project_os_runtime/results.py`: `validate_task_result`,
  `parse_task_result`, `publish_task_result`
- Inspect `scripts/dcode_project.py`: `_worker_task_result` and wrapper fallback
  construction
- Inspect `scripts/herdr_main_launcher.py`: `_classify_deepagents_outcome` and
  assignment-result projection
- Inspect `scripts/project_os_runtime/attempt.py` settlement functions
- Inspect `scripts/project_os_runtime/secretary_adapter.py`,
  `scripts/project_os_runtime/secretary_events.py`, and
  `scripts/benchmark_secretary_architecture.py`
- Inspect focused tests for each named owner.

**Dependencies:**
- PR #58 is present on `main`.
- Current checkout artifacts remain preserved and are not staged or deleted.

**Authority:**
- Preauthorized local actions: inspect named files, run baseline checks, and record sanitized source facts and cohort fields in this plan
- Stop for: missing merged base, unavailable owner, missing settlement contract, or evidence that scope requires a new authority or durable store

**Steps:**
- [x] Create isolated worktree from `main` and record branch/base identity.
- [x] Inventory preserved current-checkout artifacts without modifying them.
- [x] Map every `LaunchPreflight`, `ready`, `task_result`, `reported_completed`,
  and `accepted` consumer.
- [x] Map parser failure details to wrapper fallback and launcher classification.
- [x] Record native CoS controller entry path and distinguish it from Herdr-bound
  or in-memory surrogates.
- [x] Run deterministic baseline tests before edits: `465 passed in 8.78s`.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py tests/test_project_os_runtime.py tests/test_herdr_main_launcher.py tests/test_secretary_adapter.py tests/test_secretary_events.py tests/test_secretary_benchmark.py -q` — `465 passed in 8.78s`
- [x] `git diff --check`
- Expected: baseline passes; source map names concrete consumers and native
  acceptance boundary; no tracked source changes.

**Exit Criteria:**
- Contracts, consumers, baseline results, capability limits, and preserved
  artifacts are recorded.

### Task 2: Restore universal rejection of actual preflight blockers

**Purpose:**
- Restore the pre-PR #58 safety invariant without reopening preflight design.

**Task Function:**
- Minimal dispatcher correctness fix.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small high-confidence change with direct regression proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused deterministic tests cover every changed branch.

**Specification Coverage:**
- Actual `BLOCKED` checks reject in every launch mode.
- Coordinated missing binding evidence remains `UNVERIFIED` and does not start.
- Legitimate legacy/manual lanes remain compatible when no actual blocker exists.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Modify `scripts/herdr_parallel_dispatch.py`: `run_lane`,
  `verify_launch_bindings`
- Extend `tests/test_herdr_parallel_dispatch.py`.

**Dependencies:**
- Task 1 source map and baseline.

**Authority:**
- Preauthorized local actions: modify named dispatcher symbols and focused tests, then run declared checks
- Stop for: any need to alter `PreparedLane`, launcher-owned budget/target checks, or downstream runtime authority

**Steps:**
- [x] Make `preflight.blockers` an unconditional early rejection before
  subprocess start.
- [x] Keep coordinated `binding_status == "UNVERIFIED"` rejection separate from
  actual blockers.
- [x] Keep legacy/manual missing optional binding compatibility when no blocker
  exists.
- [x] Add tests for legacy/manual missing worktree, invalid Git base, and missing
  accepted prerequisite; assert subprocess factory is never called.
- [x] Verify an actual legacy blocker is rejected through both `run_lane()` and
  `verify_launch_bindings()`.
- [x] Retain tests for coordinated missing binding, binding mismatch, and valid
  legacy launch.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_herdr_parallel_dispatch.py -q` — `82 passed in 4.18s`
- [x] Expected: all dispatcher tests pass; blocked lanes never invoke launcher.

**Exit Criteria:**
- Every actual `BLOCKED` preflight check rejects before launcher start in both
  legacy/manual and coordinated modes.

### Task 3: Reconcile Worker publication cohort before mechanics

**Purpose:**
- Establish why each observed publication attempt succeeded or failed before
  changing parser, wrapper, or launcher mechanics.

**Task Function:**
- Evidence cohort reconciliation and root-cause classification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: evidence classification must precede mechanical changes.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: source artifacts and deterministic fixtures establish the cohort.

**Specification Coverage:**
- Every observed attempt is retained and classified.
- Worker non-publication, invalid publication, wrapper misclassification, and
  unresolved evidence remain distinguishable.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect `scripts/project_os_runtime/results.py`: `parse_task_result`.
- Inspect `scripts/dcode_project.py`: `_worker_task_result` and wrapper fallback.
- Inspect `scripts/herdr_main_launcher.py`: `_classify_deepagents_outcome`.
- Record the evidence table in this plan; do not create another ledger or
  diagnostic store.

**Dependencies:**
- Task 1 source map and baseline.

**Authority:**
- Preauthorized local actions: classify available attempts and record sanitized evidence in this plan without changing source mechanics
- Stop for: unavailable attempt artifacts that would require invented results, or any proposal to remove failed runs silently

**Steps:**
- [x] List every available attempt reference, workload class, configuration,
  Worker exit, publication owner, parser diagnosis, settlement state, and
  eligibility. Raw attempt IDs are unavailable in preserved artifacts.
- [x] Explain the `3/5` versus six-attempt discrepancy explicitly; no failed or
  infrastructure attempt was silently removed; raw rows remain unavailable.
- [x] Classify each failure as Worker never invoked publication, Worker emitted
  invalid content, wrapper/launcher misclassified usable evidence, or evidence
  unavailable. Available summary supports `3/5` valid and two wrapper fallbacks;
  root cause remains unresolved.
- [x] Record missing local artifacts as unresolved evidence with a concrete
  reason; do not invent a result or denominator.
- [x] Decide whether a publication helper is justified only when evidence shows
  mechanical field reconstruction or invocation complexity is causal.

**Verification:**
- [x] Record one compact evidence table with the available summary and explicit
  unavailable-artifact limitation.
- [x] Confirm every available attempt reference has an inclusion decision and
  root-cause classification, or an explicit unavailable-artifact limitation.

**Exit Criteria:**
- Publication summary and causal limitation are explicit; no publication helper
  or mechanics change is authorized from incomplete raw cohort evidence.

### Task 4: Preserve diagnostics and evidence-stage boundaries

**Purpose:**
- Preserve actionable publication provenance and keep runtime evidence checks
  separate from task-semantic acceptance.

**Task Function:**
- Narrow parser, producer-boundary, wrapper, and launcher classification fix.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: existing owners already implement each boundary.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: parser, wrapper, launcher, and compatibility fixtures.

**Specification Coverage:**
- Parser owns missing, malformed, and identity-mismatch detection.
- `dcode_project.py` owns authorized Worker provenance and safe fallback.
- Launcher owns execution/evidence projection; task-specific checks and CoS own
  proof sufficiency and semantic acceptance.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect or minimally modify `scripts/project_os_runtime/results.py`:
  `validate_task_result`
- Inspect or minimally modify `scripts/herdr_main_launcher.py`:
  `_classify_deepagents_outcome`
- Inspect `scripts/project_os_runtime/attempt.py` settlement decisions.
- Extend tests in `tests/test_project_os_runtime.py` and
  `tests/test_herdr_main_launcher.py`.
- Record evidence in this plan's evidence table; do not create another ledger.

**Dependencies:**
- Tasks 1 and 3.

**Authority:**
- Preauthorized local actions: modify named parser, wrapper, launcher, and focused tests without changing TaskResult schema or acceptance ownership
- Stop for: ambiguous task requirements, missing compatibility inventory, or any request to make runtime semantic acceptance decisions

**Steps:**
- [x] Preserve existing parser `detail` values as sanitized diagnostic reasons;
  add no duplicate generic taxonomy.
- [x] At `scripts/dcode_project.py:_worker_task_result`, accept only the exact
  authorized Worker producer `deepagents-worker`; preserve other producer
  identities for consumers that own those contracts.
- [x] Preserve parser reason when wrapper fallback is published; never copy raw
  malformed content or secrets.
- [x] Enumerate existing null-checkpoint and alternate-proof consumers/tests
  before tightening completion classification.
- [x] Keep Stage A publication validity, Stage B task-type completion evidence,
  and Stage C CoS semantic acceptance separate.
- [x] Mark missing required completion evidence `unverified` only at the correct
  caller boundary; retain legitimate read-only, failed, and continuation forms.
- [x] Add fixtures for missing file, malformed JSON, identity mismatch,
  unauthorized producer, valid Worker result, and insufficient completion proof.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_project_os_runtime.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py -q`
- [x] Assert diagnostics are stable, sanitized, preserve existing `state`
  consumers, and do not make runtime acceptance decisions.

**Exit Criteria:**
- CoS-facing evidence identifies publication failure provenance, exact Worker
  ownership is enforced at its boundary, and evidence stages remain distinct.

### Task 5: Prove native CoS acceptance behavior

**Purpose:**
- Replace surrogate delivery evidence with direct proof of acceptance and
  dependent-coordination behavior.

**Task Function:**
- Authorized live controller validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: native controller capability and provider authority must be
  resolved at execution time.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent acceptance evidence requires a separate validator.

**Specification Coverage:**
- False completion is rejected and dependent work does not advance.
- Correct implementation is independently accepted and only authorized
  dependent advancement occurs.
- Herdr-bound or in-memory probes are labeled surrogate when native path is not
  available.

**Required Skills:**
- `skill-backend-verification`
- `skill-executing-plans`
- `skill-chief-of-staff`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect native CoS controller entry path discovered in Task 1.
- Inspect `scripts/project_os_runtime/attempt.py` settlement and continuation
  gates.
- Use an explicitly authorized, isolated plan-bound CoS test scenario. Reuse an
  existing approved test plan when available; otherwise use the smallest
  bounded fixture plan that binds repository, branch, base, current revision,
  native CoS identity, authority, task criteria, Worker evidence, settlement,
  and dependent advancement. Do not enable CoS for this whole implementation.
- Use existing Plan, Git, TaskResult, receipt, and task-specific verification
  records; do not add a new acceptance store.

**Dependencies:**
- Task 4 evidence-stage contract.

**Authority:**
- Preauthorized local actions: prepare bounded fixtures and inspect resulting evidence; native CoS opt-in is explicit for this task only
- Stop for: missing native controller authority, missing provider credentials, inability to prove coordination-state consequence, or any attempt to substitute a Herdr pane or in-memory controller

**Steps:**
- [x] Run negative case: valid bound Worker TaskResult and settled receipt, but
  required artifact condition false.
- [x] Confirm native CoS records `FAIL` or `BLOCKED` and dependent task remains
  non-advancing.
- [x] Run positive case: Worker evidence, artifact, Git checkpoint, verification,
  and settlement agree.
- [x] Confirm native CoS records `PASS` and permits only authorized dependent
  advancement.
- [x] Capture controller decision, input evidence references, resulting state,
  and limitation for each case.
- [x] Record native controller identity, plan binding, authority grant, and exact
  dependent-task state for each case.

**Verification:**
- [x] Direct boundary evidence contains both decision and state transition.
- [x] No surrogate probe is labeled native acceptance.

**Exit Criteria:**
- Native acceptance is proven for both negative and positive cases, or the plan
  records a concrete external capability blocker without claiming acceptance.

### Task 6: Measure reconstruction cost and Secretary value

**Purpose:**
- Decide whether a transient evidence slice or Secretary routing reduces real
  coordination cost before adding runtime complexity.

**Task Function:**
- Controlled measurement and attribution.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: measurement method depends on available native timing and
  token counters.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: correctness and measurement integrity require independent review.

**Specification Coverage:**
- Evidence slice is read-only and conditional on measured repeated reconstruction
  cost.
- Secretary remains optional and only routes changed project-level attention.
- Deterministic fake benchmark remains contract evidence, not live efficiency
  evidence.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect `scripts/project_os_runtime/secretary_adapter.py`: `AttentionDelta`,
  `CoordinationDelta`, `CommunicationEnvelope`.
- Inspect `scripts/project_os_runtime/secretary_events.py`:
  `coalesce_event_hints`, `reconcile_event_hint`.
- Inspect `scripts/benchmark_secretary_architecture.py` and its tests.
- Treat Secretary files as inspect/measure-only. If threshold is met, add the
  smallest read-only projection beside the existing canonical evidence owner
  discovered in Task 1 and test that owner; otherwise make no projection change.

**Dependencies:**
- Task 4 evidence-stage contract.

**Authority:**
- Preauthorized local actions: run matched deterministic and authorized live measurements, inspect existing metrics, and add only a bounded read-only projection when the declared threshold is met
- Stop for: unequal workload/model/grant/acceptance conditions, missing timestamps, or pressure to infer automated savings from manual relay time

**Steps:**
- [x] Inspect current CoS evidence reconstruction through the approved
  live-supervised probe; observable turns and elapsed/token counters remain
  unavailable, so no efficiency value is inferred.
- [x] Attempt targeted canonical reads first: task row, direct prerequisite
  anchors, current Git state, TaskResult, settlement, and required artifact.
- [x] Make no projection: the threshold is not met because repeated measured
  reconstruction cost and attributable savings are unavailable.
- [x] Keep CoS artifact inspection mandatory when criteria require it.
- [x] Use matched CoS-only and Secretary-assisted workstreams from the approved
  live-supervised probe with identical frozen inputs, fresh worktrees/contexts,
  and correctness gates.
- [x] Record available evidence handoff reliability, management amplification,
  unnecessary wake rate, human intervention, completion latency, coordination
  cost, and correctness fields; retain unavailable values as unknown.
- [x] Attribute dispatch, Worker, publication, settlement, acceptance, and
  project-consequence intervals only where timestamps exist; keep unknown
  intervals unknown.
- [x] Preserve deterministic benchmark label `deterministic-fake`.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_secretary_adapter.py tests/test_secretary_events.py tests/test_secretary_benchmark.py -q` — `38 passed`
- [x] Produce matched baseline/candidate evidence with correctness as a hard
  gate; record value `INCONCLUSIVE` and make no efficiency claim when counters
  are unavailable.

**Exit Criteria:**
- Projection decision and Secretary value decision are evidence-backed, with no
  new communication protocol or telemetry service.

### Task 7: Close Phase A deterministic release gate

**Purpose:**
- Prove deterministic correctness and make the P0 code fix independently
  releasable from live controller and efficiency experiments.

**Task Function:**
- Phase A verification gate.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final proof and plan reconciliation require controller authority.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent review is selected from current registry at execution.

**Specification Coverage:**
- Tasks 2 and 4 are proven independently of Tasks 5 and 6.

**Required Skills:**
- `skill-executing-plans`
- `skill-verification-before-completion`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Changed files from Tasks 2 and 4.
- This plan's Task 7 gate and deterministic evidence rows.

**Dependencies:**
- Tasks 2 and 4 complete with recorded deterministic evidence.

**Authority:**
- Preauthorized local actions: run focused/full deterministic proof, review Phase A diff, and record independent release readiness
- Stop for: failed deterministic proof, unreviewed scope, stale generated output, or unresolved P0 blocker

**Steps:**
- [x] Run focused dispatcher, parser, wrapper, launcher, and compatibility tests.
- [x] Run the full deterministic suite and repository validators.
- [x] Review Phase A diff for credentials, `.deepagents/`, temp artifacts, raw
  malformed payloads, unrelated files, and generated-source violations.
- [x] Record Phase A as independently releasable; keep Task 6 blocked without
  weakening the deterministic gate.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider -q` — `961 passed, 1 skipped in 53.17s`.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-08-evidence-handoff-reliability-and-coordination-validation-plan.md` — passed.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit` — passed.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-08-evidence-handoff-reliability-and-coordination-validation-plan.md` — passed.
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — passed.
- [x] `git diff --check` — passed; only line-ending warnings.
- Expected: all required commands pass; skipped or unavailable evidence is
  explicitly recorded; no unrelated file is staged.

**Exit Criteria:**
- P0 deterministic correctness passes and can be reviewed or released without
  native CoS or Secretary experiment completion.

### Task 8: Final verification and reconcile plan

**Purpose:**
- Reconcile deterministic code, evidence, live validation, measurements, and
  explicit limitations before completion status changes.

**Task Function:**
- Final verification and acceptance handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final proof and plan reconciliation require controller authority.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent review is selected from current registry at execution.

**Specification Coverage:**
- All implementation outcomes, accepted deviations, residual risks, and
  capability blockers reconcile with source and evidence.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- All changed files from Tasks 2 and 4.
- This plan's Coordination State, ledger, evidence table, and Completion Criteria.

**Dependencies:**
- Task 7 complete; Tasks 5 and 6 complete, blocked, or explicitly unverified.

**Authority:**
- Preauthorized local actions: run final validators, review diff, reconcile this plan, and prepare verified handoff
- Stop for: failed required proof, unreviewed scope, stale generated output, unresolved required blocker, or unproven native acceptance claim

**Steps:**
- [x] Run focused and full test suites.
- [x] Run repository contract, planning lifecycle, generated adapter, runtime
  drift, and whitespace validators.
- [x] Review diff for credentials, `.deepagents/`, temp artifacts, raw malformed
  payloads, unrelated files, and generated-source violations.
- [x] Update each task state only from command or evidence output.
- [x] Record explicit deferrals: live Worker reliability outside reconciled
  cohort, Secretary metrics when counters are unavailable, and latency
  intervals with unknown timestamps.
- [x] Return `verified`, `incomplete`, or `blocked` through
  `skill-verification-before-completion`; do not mark this plan completed from
  checkboxes alone.

**Verification Result:** `verified` — deterministic implementation proof,
native CoS acceptance proof, and matched live-supervised correctness evidence
pass. Efficiency value remains `INCONCLUSIVE`; unavailable counters and
timestamps are explicitly preserved as unknown, with no efficiency claim.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider -q` — `961 passed, 1 skipped in 53.17s`.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-08-evidence-handoff-reliability-and-coordination-validation-plan.md` — passed.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit` — passed.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-08-evidence-handoff-reliability-and-coordination-validation-plan.md` — passed.
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — passed.
- [x] `git diff --check` — passed; only line-ending warnings.
- Expected: all required commands pass; skipped or unavailable evidence is
  explicitly recorded; no unrelated file is staged.

**Exit Criteria:**
- Plan, source, tests, evidence, and generated surfaces reconcile; final status
  is set only by verification skill.

## Verification

### Focused proof

- Dispatcher blocker and binding tests pass.
- Parser, wrapper fallback, exact producer identity, and completion-proof tests pass.
- Secretary event, adapter, and deterministic benchmark tests pass.
- Native CoS negative and positive cases include decision plus coordination-state
  evidence when capability is available.

### Broad proof

- Full suite passes with exact skipped-test accounting.
- Repository preflight and audit validators pass.
- Planning lifecycle validation passes for this plan.
- Generated adapter sync check passes.
- Runtime drift check passes when canonical runtime surfaces changed.
- `git diff --check` passes.

### Evidence table

| Claim | Result | Evidence reference | Limitation | Next action |
| --- | --- | --- | --- | --- |
| Actual preflight blockers reject in every mode | proven | Task 2 focused tests: `82 passed` | none accepted | retain regression coverage |
| Worker publication cohort is reconciled | proven with limitation | Task 3 cohort summary: `3/5` valid; raw attempt IDs unavailable | six-attempt discrepancy remains explicit; no helper justified | obtain raw attempt IDs if source becomes available |
| Worker publication failures retain sanitized causes | proven | Task 4 focused proof included in `347 passed` | raw payloads excluded | retain regression coverage |
| Completion proof is separate from publication | proven | Task 4 launcher and runtime tests included in `347 passed` | task-specific proof varies | retain stage boundaries |
| Native CoS rejects false completion | proven | native Codex/`9router` probe on October 8, 2026: `FAIL`, dependent `pending`; focused regression proof `15 passed` | controller identity is explicit probe input; plan/Git remain caller-owned | retain gate and review output |
| Native CoS accepts correct implementation | proven | native Codex/`9router` probe on October 8, 2026: `PASS`, dependent `active`; focused regression proof `15 passed` | controller identity is explicit probe input; plan/Git remain caller-owned | retain gate and review output |
| Evidence slice reduces reconstruction cost | inconclusive | approved live-supervised probe and targeted canonical reads; no projection added | repeated attributable reconstruction cost unavailable | revisit only when native counters exist |
| Secretary improves coordination efficiency | inconclusive | `C:\tmp\project-os-secretary-probe\20261008-task4-r2\evidence.json`; matched inputs and semantic reconciliation `PASS`; Secretary benchmark `38 passed` | `live=false` deterministic benchmark; no provider token/turn counters | make no efficiency claim |
| Latency interval is attributed | inconclusive | live-supervised probe records trial order and correctness evidence | phase timestamps unavailable; intervals remain unknown | revisit only with attributed timestamps |

## Completion Criteria

- [x] Every actual `BLOCKED` dispatcher preflight check rejects before launcher
  start in legacy/manual and coordinated modes.
- [x] Coordinated missing binding evidence remains fail-closed and legacy/manual
  compatibility remains intact when no actual blocker exists.
- [x] Worker publication failure reasons remain sanitized, precise, and tied to
  existing parser outcomes.
- [x] No wrapper fallback is treated as Worker-owned proof.
- [x] Publication validity, completion-proof sufficiency, settlement, and CoS
  acceptance remain separate states.
- [x] Every observed publication attempt has explicit inclusion and failure
  classification; no failed run is silently removed.
- [x] Native CoS negative and positive acceptance behavior is proven, or the
  exact external blocker is recorded without claiming proof.
- [x] Evidence-slice and Secretary decisions use matched, correctness-gated
  live-supervised evidence; efficiency remains `INCONCLUSIVE` when counters
  are unavailable, and deterministic fake results are labeled correctly.
- [x] No new result schema, authority owner, communication channel, telemetry
  service, heartbeat, dashboard, or scheduler is introduced.
- [x] Focused tests, full tests, validators, generated-surface checks, and final
  diff review pass.
- [x] Verification skill returns `verified` before plan status changes to
  `completed`.
