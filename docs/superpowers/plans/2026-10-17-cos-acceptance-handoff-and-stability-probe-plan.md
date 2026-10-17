---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: cos-acceptance-handoff-and-stability-probe
targets:
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/acceptance_handoff.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/secretary_live_runtime.py
  - scripts/run_live_stability_probe.py
  - scripts/secretary_live_pilot.py
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_secretary_live_runtime.py
  - tests/test_live_stability_probe.py
  - tests/test_secretary_live_pilot.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - artifacts/runtime-observation/2026-10-17-cos-acceptance-handoff-canary.json
  - artifacts/runtime-observation/2026-10-17-cos-acceptance-handoff-report.md
  - docs/superpowers/plans/2026-10-17-cos-acceptance-handoff-and-stability-probe-plan.md
---

# CoS Acceptance Handoff and Stability Probe

## Review Basis

This plan adopts the consolidated recommendation supplied after PR #97 and
reconciles it with the merged repository state at
`a60fa47183ceb40171522e6babf870bc636e5887` (`origin/main`). The review is
accepted only where current source and tests support it.

The source confirms that:

- `scripts/project_os_runtime/acceptance.py:evaluate_acceptance()` already
  produces `PASS | FAIL | BLOCKED` decisions and
  `validate_acceptance_decision()` validates their identity and evidence.
- `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions()`
  already owns the accepted Plan consequence and replay behavior.
- `scripts/herdr_parallel_dispatch.py` correctly stops at settled runtime
  evidence and reports acceptance as pending; it must not become the semantic
  acceptance owner.
- `scripts/run_live_stability_probe.py` requires an accepted lifecycle for
  observed rows, but the existing live evidence has no real CoS producer and
  therefore cannot produce comparable accepted trials.
- `scripts/secretary_live_runtime.py` exposes owned-resource evidence at both
  runtime and session-facing projections; the next probe must derive final
  disposition from one observed resource inventory, not from contradictory
  per-lane and session-level claims.

The recommendation is therefore narrowed to one operational correction and
its proof. It does not authorize another semantic model, registry, scheduler,
Worker acceptance field, runtime acceptance field, Secretary coordinator, or
performance optimization before accepted-outcome evidence exists.

## Goal

Make one real CoS/controller acceptance handoff operational from settled
Worker evidence through the existing `AcceptanceDecision` boundary and into
the existing Plan-transition API. Prove that controller boundary with a
bounded fixture-backed read-only canary and fail-closed probes, make probe
resource observations authoritative and reconcilable, and leave provider/
Herdr execution, physical cleanup, write-lifecycle qualification, and topology
measurement to separately approved plans.

## Non-Goals

- Do not redesign `PASS | FAIL | BLOCKED` or add another acceptance state
  machine.
- Do not let the Worker, runtime dispatcher, Secretary, or receipt validator
  decide semantic acceptance.
- Do not add retries, refill, unbounded continuation, a workflow database, a
  proof registry, or a second identity/digest representation.
- Do not optimize polling, scheduler behavior, controller reconstruction,
  review/integration, or managed Secretary behavior in this plan.
- Do not qualify the write lifecycle or run the topology-economics experiment
  here; those are separate follow-up plans after this correctness boundary is
  proven.
- Do not treat operational completion, settlement, cleanup, or process exit as
  semantic acceptance.
- Do not claim provider execution, physical cleanup, or process-level restart
  from fixture-backed controller-boundary evidence.

## Implementation Outcomes

### One thin authoritative CoS handoff

Add one controller-owned adapter at
`scripts/project_os_runtime/acceptance_handoff.py` only if the caller
inventory confirms that no existing production controller boundary can own the
call. The adapter loads the exact Plan/task/attempt/candidate binding, accepts
canonical evidence from the controller, calls `evaluate_acceptance()`, calls
`validate_acceptance_decision()`, and forwards only a validated `PASS` to
`apply_accepted_plan_transitions()`.

The adapter is not a new authority. It must not mutate Worker results, infer
acceptance from `acceptance_pending`, infer acceptance from cleanup, or
construct evidence from a receipt that is not bound to the same plan, task,
assignment, attempt, candidate, repository, checkpoint, and freshness facts.
`FAIL` and `BLOCKED` remain explicit outcomes with no Plan transition.

### One canonical probe resource inventory

The live probe and report derive final resource disposition from the runtime
owner's observed, attempt-bound inventory. Per-lane observations may contribute
entries, but a session-level summary is calculated from the deduplicated,
validated inventory and cannot override an unresolved or quarantined entry.
Successful cleanup requires every probe-owned resource to be observed as
removed or already absent; unresolved, preserved, or unverified resources keep
reuse blocked and fail the positive probe.

### One accepted controller-boundary proof

The probe records one exact-bound path:

```text
settled Worker evidence
  -> CoS acceptance evidence assembly
  -> evaluate_acceptance()
  -> validated AcceptanceDecision(PASS)
  -> apply_accepted_plan_transitions()
  -> dependent-task preparation
  -> persisted acceptance replay
```

It also records negative cases for stale identity, missing evidence,
condition failure, receipt mismatch, settlement uncertainty, and unavailable
acceptance producer. No synthetic accepted row is permitted.

### Follow-up handoff instead of speculative optimization

This plan records the prerequisites for later measurement but does not run the
18-trial topology experiment or provider-backed execution. A later plan may
bind a new protocol to the merged correctness revision only after it supplies
the missing provider and physical-resource evidence. A separate write-lifecycle
plan may qualify disposable candidate creation, release, cleanup, and recovery.
Neither follow-up may count capability-blocked or acceptance-pending trials as
successful evidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `optional native worktree from origin/main`; preserve the existing untracked prior-plan artifact in the current checkout
- Commit policy: `verified per-task checkpoint commits preauthorized`
- Preauthorized local actions: edit named source, test, documentation, and evidence surfaces; run declared local checks; create task checkpoint commits; use read-only probe fixtures under the task workspace
- User-approval actions: push, merge, publication, external provider writes, destructive recovery, branch/worktree deletion, and any write-lifecycle experiment
- Parallel ownership: `none`; acceptance wiring, resource accounting, and probe evidence share contracts and execute sequentially
- Sequential fallback: complete and verify the producer contract before changing probe aggregation; complete accepted-lifecycle and recovery proof before final documentation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cos-acceptance-handoff`
- Base commit: `a60fa47183ceb40171522e6babf870bc636e5887`
- Expected workspace: clean implementation worktree; preserve any pre-existing unrelated files without staging them
- Next action: run final repository, planning, and starter-kit verification
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | caller/owner inventory and source map | recorded; no prior production evaluator caller; acceptance_handoff.py selected |
| Task 2 | `completed` | current | `codex` | Task 1 | focused acceptance handoff tests | tests/test_acceptance_handoff.py; 3 passed |
| Task 3 | `completed` | current | `codex` | Task 2 | dispatcher-to-controller boundary tests | tests/test_herdr_parallel_dispatch.py and tests/test_herdr_main_launcher.py; 299 passed |
| Task 4 | `completed` | current | `codex` | Task 1 | resource inventory reconciliation tests | canonical_resource_inventory regressions; focused runtime matrix passed |
| Task 5 | `completed` | current | `codex` | Tasks 2-4 | accepted lifecycle, recovery, and fail-closed evidence | artifacts/runtime-observation/2026-10-17-cos-acceptance-handoff-canary.json; report.md; canary PASS |
| Task 6 | `completed` | current | `codex` | Task 5 | final repository and plan verification | 1379 passed, 2 skipped; repository/planning/starter-kit validators passed; diff clean |

## Task Breakdown

### Task 1: Establish the canonical CoS handoff owner

**Purpose:**
- Identify the actual evidence-producing controller invocation that can inspect
  a real Worker-produced artifact and own acceptance evidence assembly. Decide
  whether any handoff adapter is actually missing.

**Task Function:**
- Source-first ownership and caller inventory.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded repository mapping with no implementation ambiguity
  after source inspection.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: inventory is directly reviewable from source and tests.

**Specification Coverage:**
- CoS owns semantic acceptance; runtime settlement and Worker execution remain
  separate; no dispatcher-owned acceptance decision. The producer must inspect
  the artifact independently rather than merely forward a Worker claim.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`,
  `validate_acceptance_decision`, `authorize_dependent_transition`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel`, final lane
  classification, and `acceptance_pending`
- Inspect: `scripts/secretary_live_runtime.py:run_normal`, `run_probe`, and
  `_owned_resources`
- Inspect: `scripts/secretary_live_pilot.py:validate_receipt`
- Verify: all repository callers of the listed functions and all current
  acceptance/resource evidence schemas

**Dependencies:**
- Current merged source at the recorded base commit is authoritative.

**Authority:**
- Preauthorized local actions: inspect source, tests, plans, and artifacts; record the owner map in the plan or task evidence.
- Stop for: a required external provider contract, changed acceptance authority, new registry/state machine, or any ambiguity that cannot be resolved from repository evidence.

**Steps:**
- [x] Step 1: Trace every acceptance evaluator, transition, receipt, settlement,
  and probe-result caller.
- [x] Step 2: Identify the authoritative controller, its production invocation,
  the exact settled result it consumes, and how it independently inspects the
  actual artifact and computes or obtains the expected result.
- [x] Step 3: Map the source of every required-condition, artifact-condition,
  Plan/task/assignment/attempt/candidate, repository, checkpoint, and freshness
  fact through the existing evaluator and Plan-transition APIs.
- [x] Step 4: Select the existing controller boundary when it can invoke the
  supported APIs directly; only if glue is missing, specify one adapter module
  and its exact input/output binding without adding authority.

**Verification:**
- [x] `rg -n "evaluate_acceptance|apply_accepted_plan_transitions|acceptance_pending|owned_resources|released_resources" scripts tests docs`
- Expected: one documented CoS producer boundary with an actual artifact
  inspection path, no accidental dispatcher or Worker acceptance producer, and
  a complete list of affected consumers.

**Exit Criteria:**
- The real producer, invocation point, independent artifact inspection,
  evidence sources, and input contract are explicit. If the producer cannot be
  identified or exercised, the plan is recorded as `blocked` rather than
  deferred as if implementation were complete.

### Task 2: Implement the thin CoS acceptance handoff

**Purpose:**
- Assemble canonical acceptance inputs once and connect them to the existing
  evaluator and Plan consequence without duplicating semantic state. Preserve
  the controller's independent artifact inspection as the evidence producer.

**Task Function:**
- Controller-boundary implementation with fail-closed validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: choose the lowest discovered profile that can safely handle
  cross-module identity, stale-plan, and idempotency behavior after Task 1.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independently verify the acceptance boundary and negative
  cases after implementation.

**Specification Coverage:**
- Existing `AcceptanceDecision` remains the only semantic outcome; only
  validated `PASS` may authorize Plan transition.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: the Task 1-selected controller boundary, or add
  `scripts/project_os_runtime/acceptance_handoff.py` as the single thin adapter
- Reuse: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`,
  `validate_acceptance_decision`, `authorize_dependent_transition`
- Reuse: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Modify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`,
  and a focused handoff test module if needed
- Verify: `scripts/herdr_parallel_dispatch.py` remains acceptance-neutral

**Dependencies:**
- Task 1 owner map and exact input contract.

**Authority:**
- Preauthorized local actions: implement the selected adapter and focused tests; run backend boundary checks; create one checkpoint commit after proof.
- Stop for: any need to add Worker/runtime acceptance fields, bypass identity validation, infer PASS from process/cleanup state, or mutate Plan state outside the existing transition API.

**Steps:**
- [x] Step 1: Normalize the controller's independently observed artifact result
  and inputs for exact plan/task/assignment/attempt/candidate/repository/
  checkpoint/freshness binding.
- [x] Step 2: Invoke `evaluate_acceptance()` and validate the returned decision
  before any Plan mutation.
- [x] Step 3: Forward only validated `PASS` to
  `apply_accepted_plan_transitions()` and preserve replay/idempotency behavior.
- [x] Step 4: Return explicit `FAIL`, `BLOCKED`, stale, mismatch, and missing
  evidence outcomes without advancing the Plan.

**Verification:**
- [x] `py -B -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py`
- Expected: positive PASS authorizes exactly one accepted consequence; FAIL and
  BLOCKED remain non-mutating; stale identities, candidate drift, missing
  conditions, receipt mismatch, and replay fail closed or replay safely.

**Exit Criteria:**
- One controller-owned acceptance handoff exists and no other layer can
  authorize semantic acceptance.

### Task 3: Preserve the runtime-to-CoS boundary

**Purpose:**
- Wire settled runtime evidence to the controller handoff without making the
  dispatcher or Worker an acceptance producer.

**Task Function:**
- Boundary integration and contract regression.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: integration risk across dispatcher, launcher, and receipts.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: verify no runtime classification can become semantic PASS.

**Specification Coverage:**
- Settlement, retirement, cleanup, receipt correlation, and acceptance remain
  distinct facts; `acceptance_pending` is a handoff status only.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect and modify only as required: `scripts/herdr_parallel_dispatch.py`;
  final classification and result projection
- Inspect: `scripts/herdr_main_launcher.py` and
  `scripts/project_os_runtime/results.py`
- Verify: `tests/test_herdr_parallel_dispatch.py` and relevant launcher tests

**Dependencies:**
- Task 2 handoff API and output contract.

**Authority:**
- Preauthorized local actions: update only the controller-boundary transport or evidence projection needed to invoke Task 2; run focused lifecycle tests.
- Stop for: dispatcher-owned decision logic, Worker result schema changes, runtime acceptance flags, or any change to no-refill/capacity semantics.

**Steps:**
- [x] Step 1: Pass canonical settled evidence to the controller boundary without
  changing the meaning of runtime classification.
- [x] Step 2: Keep `acceptance_pending` true until a validated CoS decision is
  returned; do not derive it from a Worker field.
- [x] Step 3: Verify settlement, retirement, cleanup, grant, receipt, and stale
  identity failures remain fail-closed.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: settled completion remains acceptance-pending until CoS PASS;
  mismatched or unresolved evidence never reaches the handoff as accepted.

**Exit Criteria:**
- Runtime evidence reaches the CoS owner through one explicit boundary and the
  runtime remains semantically neutral.

### Task 4: Canonicalize probe resource inventory and cleanup reporting

**Purpose:**
- Make final resource disposition derive from one observed, attempt-bound
  inventory and remove contradictory summary claims.

**Task Function:**
- Evidence-schema correction and lifecycle accounting.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: resource ownership and cleanup are high-risk backend facts.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independently test unresolved, quarantined, removed, and
  already-absent inventory states.

**Specification Coverage:**
- Runtime owns settlement, retirement, and cleanup; probe/reporting consumes
  observed runtime evidence and never overrides it.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py:_owned_resources` and the smallest
  shared result projection required to expose one canonical inventory
- Modify: `scripts/run_live_stability_probe.py:validate_owner_result`,
  `_base_row`, and report aggregation helpers
- Verify: `tests/test_secretary_live_runtime.py`,
  `tests/test_live_stability_probe.py`, and relevant receipt/attempt tests

**Dependencies:**
- Task 1 ownership map; preserve current receipt and attempt contracts.

**Authority:**
- Preauthorized local actions: edit the named resource projections and validators; add lifecycle regressions; run focused cleanup/reconciliation checks.
- Stop for: a second resource ledger, a session-level override, inferred cleanup, or weakening reuse blocking when inventory is unresolved.

**Steps:**
- [x] Step 1: Define the canonical inventory shape and identity key from the
  existing runtime-owned resource entries.
- [x] Step 2: Derive session disposition from the validated deduplicated
  inventory; reject contradictory top-level cleanup claims.
- [x] Step 3: Preserve `removed`/`already_absent` success, quarantine or retain
  unresolved resources, and keep reuse blocked until proof exists.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_live_stability_probe.py tests/test_secretary_live_pilot.py`
- Expected: resource totals reconcile exactly; cleanup false positives,
  cross-attempt entries, missing inventory, and unresolved resources fail closed.

**Exit Criteria:**
- Every probe report has one authoritative resource disposition derived from
  observed inventory and no session summary can hide a lane/resource failure.

### Task 5: Prove one accepted read-only lifecycle and fail-closed negatives

**Purpose:**
- Produce a deterministic controller-boundary canary that reaches real CoS
  PASS and Plan consequence over settled artifacts, then prove invalid states
  do not advance the Plan.

**Task Function:**
- Representative-operation trace and backend lifecycle verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: live/probe orchestration requires exact evidence binding and
  controlled failure handling.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: inspect emitted evidence and replay behavior independently.

**Specification Coverage:**
- Accepted boundary proof requires an actual CoS decision, exact
  identity/freshness, required/artifact conditions, Plan transition, dependent
  preparation, persisted replay, and observed-resource reconciliation. It does
  not prove provider execution or physical cleanup; acceptance-pending is not
  a successful controller-boundary result.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `scripts/run_live_stability_probe.py` and its protocol/report fixtures
- Modify: `tests/test_live_stability_probe.py`,
  `tests/test_project_os_runtime.py`, and `tests/test_plan_preparation.py`
- Create: `artifacts/runtime-observation/2026-10-17-cos-acceptance-handoff-canary.json`
  and its report
- Verify: `scripts/project_os_runtime/acceptance_handoff.py`,
  `herdr_parallel_dispatch.py`, `secretary_live_runtime.py`

**Dependencies:**
- Tasks 2-4 complete and focused tests pass.

**Authority:**
- Preauthorized local actions: run the bounded read-only canary and deterministic negative probes; write sanitized task-owned evidence; do not retain raw provider output or credentials.
- Stop for: missing real CoS/controller producer, synthetic acceptance pressure, unresolved cleanup, stale binding, or any unauthorized Plan transition.

**Steps:**
- [x] Step 1: Build one exact-bound read-only workload with a temporary Plan,
  candidate/checkpoint, required conditions, and two independent lanes.
- [x] Step 2: Execute, settle, assemble controller evidence, obtain real CoS
  PASS, apply the accepted Plan transition, and prepare one dependent task.
- [x] Step 3: Reconstruct the controller from persisted acceptance and Plan
  evidence, recover the accepted consequence, and prove no duplicate Plan
  transition occurs.
- [x] Step 4: Reconcile the supplied attempt-bound resource observations;
  prove settled observations unblock reuse and unresolved or conflicting
  observations keep reuse blocked.
- [x] Step 5: Inject stale Plan/task/attempt/candidate identities, missing or
  false conditions, receipt mismatch, verification failure, artifact freshness
  mismatch, and absent CoS producer; record each as fail-closed. Provider and
  physical-cleanup execution remain explicit follow-up capability gates.

**Verification:**
- [x] `py -B -m pytest -q tests/test_live_stability_probe.py tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_secretary_live_runtime.py`
- Expected: one genuine controller acceptance boundary is recorded through the
  real producer; persisted replay produces no duplicate Plan transition; all
  injected invalid states produce zero unauthorized transitions; conflicting
  resource observations block reuse. Provider execution and physical cleanup
  are not claimed by this fixture-backed canary.

**Exit Criteria:**
- The report proves accepted controller-boundary, fail-closed, replay, and
  resource-observation outcomes with exact source and binding provenance. It
  cannot claim provider execution or physical cleanup from fixture evidence.

**Recorded Evidence:**
- `artifacts/runtime-observation/2026-10-17-cos-acceptance-handoff-canary.json`
  records `PASS`, two settled lane artifacts, dependent-task preparation,
  persisted replay, one attempt identity, settled resource observations,
  quarantined conflict, and seven fail-closed handoff cases plus absent CoS
  producer rejection.
- `artifacts/runtime-observation/2026-10-17-cos-acceptance-handoff-report.md`
  summarizes the bounded local read-only proof without provider credentials or
  raw output.
- Source checkpoint: `07fe73c4c8ecd206b1cdd96471125828a5125fd9`.

### Task 6: Reconcile documentation and complete verification

**Purpose:**
- Align runtime documentation, plan ledger, evidence, and final checks with
  the implemented owner boundaries.

**Task Function:**
- Final reconciliation and completion verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final source/plan/evidence reconciliation is controller-owned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independent completion verification is required by the plan
  lifecycle contract.

**Specification Coverage:**
- Plan plus Git are the durable workflow truth; no stale acceptance-pending or
  deferred-measurement claim remains after final evidence.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: this plan's task ledger, evidence, blockers, and deferred handoff
- Verify: all changed source, tests, generated/manifest surfaces, and artifacts

**Dependencies:**
- Tasks 1-5 complete or have explicit recorded capability gates and deferrals.

**Authority:**
- Preauthorized local actions: update documentation and plan evidence; run final checks; create the final verified checkpoint commit.
- Stop for: unresolved required task, stale plan state, failed required check, unrecorded scope change, or evidence that conflicts with source/tests.

**Steps:**
- [x] Step 1: Update runtime surfaces documentation to describe the one CoS
  handoff and canonical resource inventory.
- [x] Step 2: Record exact artifact paths, protocol digests, commit SHAs,
  capability gates, and deferred optimization questions.
- [x] Step 3: Run fresh final validation and obtain `verified` completion evidence
  before changing plan status to `completed`.

**Verification:**
- [x] `py -B -m pytest -q`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-17-cos-acceptance-handoff-and-stability-probe-plan.md`
- [x] `git diff --check`
- Expected: full suite and repository/planning validators pass; plan status and
  ledger agree with Git and recorded evidence.

**Verified Evidence:**
- Workspace: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter`.
- Branch: `codex/cos-acceptance-handoff`; base: `origin/main` at
  `a60fa47183ceb40171522e6babf870bc636e5887`.
- Implementation checkpoints: `4b6a472` and `1b99e2e`.
- Full suite: `1379 passed, 2 skipped`.
- Repository contracts, planning lifecycle, starter-kit help/validation, and
  `git diff --check`: passed.
- Approved deferrals: disposable write-lifecycle qualification and accepted
  outcome topology benchmarking remain separate follow-up plans.

**Exit Criteria:**
- The implementation, tests, docs, evidence, and plan provide a recoverable
  source-first record of the acceptance handoff and its proof boundary.

## Verification

- `py -B -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_live_stability_probe.py tests/test_secretary_live_pilot.py tests/test_evidence_release.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-17-cos-acceptance-handoff-and-stability-probe-plan.md`
- `py -B scripts/build_starter_kit.py --help`
- `py -B scripts/validate_starter_kit.py --help`
- `py -B -m pytest -q`
- `git diff --check`

Any live evidence command must additionally validate the accepted read-only
canary, recovery/replay, and resource-inventory artifacts against their
recorded protocol/base/source digests. A capability-blocked or
acceptance-pending run is valid evidence of a gate, not accepted lifecycle
proof.

## Completion Criteria

The plan is ready for completion verification when:

1. one explicit CoS/controller producer invokes the existing evaluator and
   validated Plan-transition API without moving semantic authority elsewhere;
2. Worker results and runtime dispatch remain acceptance-neutral, while exact
   identity, freshness, required-condition, artifact-condition, candidate,
   and controller checks remain enforced;
3. resource disposition is derived from one observed attempt-bound inventory,
   with no cleanup false-positive or unresolved-resource reuse;
4. one genuine accepted controller-boundary canary is proved over settled
   artifacts, with provider execution and physical cleanup explicitly not
   inferred from fixture evidence;
5. negative binding, freshness, condition, receipt, verification, artifact
   mismatch, and replay cases fail closed with no unauthorized Plan transition;
6. recovery and replay evidence is persisted, idempotent, and reconciled to the
   same attempt-bound identity and resource inventory;
7. documentation, tests, artifacts, task ledger, and final verification are
   reconciled to the exact implementation commit and base.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns verified evidence. Branch
publication, pull requests, merge, and worktree cleanup remain separately
authorized actions.

## Deferred Measurement Handoff

### Disposable write-lifecycle qualification

Create a separate approved plan to qualify disposable candidate creation,
evidence release, cleanup, and recovery. It must use the canonical resource
inventory and must not claim write-lifecycle stability from this read-only plan.

### Accepted-outcome topology experiment

After this correctness revision is merged, create a separate approved plan for
the 18-trial topology experiment. Run it only on comparable, genuinely
accepted outcomes; record protocol, base, source, and artifact digests; and
keep any optimization decision outside this plan.
