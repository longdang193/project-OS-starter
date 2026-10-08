---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: trustworthy-acceptance-and-low-overhead-coordination
targets:
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - scripts/project_os_runtime/__init__.py
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/rules/git-tracked-coordination-rule.md
  - docs/superpowers/plans/2026-10-08-trustworthy-acceptance-and-low-overhead-coordination-plan.md
---

# Trustworthy Acceptance and Low-Overhead Coordination

## Verdict Review

Consolidated verdict is directionally correct. PR #59 established useful
acceptance policy, identity binding, and evidence separation, but merged API is
not yet safe as autonomous downstream-advancement boundary.

Confirmed gaps:

- `authorize_dependent_transition()` accepts caller-supplied `PASS` mapping
  without proving transition fields complete and internally consistent.
- `evaluate_acceptance()` can return `PASS` when task state is absent or
  ineligible.
- Nonempty artifact-condition mapping does not prove every required condition
  was evaluated.
- No ordinary production caller currently performs full evidence → acceptance
  → guarded Plan update path.

Recommended order:

1. Close pure acceptance contract.
2. Connect one trusted native CoS path to Plan/Git truth.
3. Prove one complete negative-to-positive cycle.
4. Improve Worker publication only from fresh failure evidence.
5. Reduce duplicate handoffs without creating another authority.
6. Measure Secretary value only after correctness is proven.

Keep existing ownership model, result schema, runtime mechanics, and Plan/Git
source of truth. Do not add result schema, evidence database, authority
registry, retry daemon, message bus, scheduler, or second Plan authority.

## Goal

Make acceptance complete, fail-closed, and plan-bound. Make one native CoS path
revalidate and persist that decision through existing Plan/Git ownership. Then
reduce coordination overhead using measured Worker and Secretary evidence.

## Implementation Outcomes

### Complete acceptance contract

`evaluate_acceptance()` rejects missing or ineligible task state, incomplete or
contradictory evidence, stale Plan/Git anchors, and condition sets whose
required members were not explicitly evaluated. Approved Plan/task checks own
the required condition set; CoS resolves those explicit condition IDs and
independent verification supplies observed results. It returns `PASS`, `FAIL`,
or `BLOCKED` without mutating Plan state.

### Strict dependent-transition authorization

`authorize_dependent_transition()` consumes only a complete, internally
consistent acceptance decision for same task and plan. Partial, contradictory,
stale, cross-plan, repeated, or unsettled decisions preserve dependent state.

### Operational native CoS path

One existing native CoS procedure gathers canonical evidence once, evaluates
acceptance, revalidates Plan/Git freshness, and lets sole lead controller apply
one guarded Plan transition. If no existing mutation owner exists, task stops
with explicit blocker; it does not invent second writer or persistence service.

### End-to-end behavioral proof

A disposable Git-tracked plan proves incorrect artifact rejection, dependent
preservation, corrected-attempt acceptance, one source-task completion, and
legitimate dependent advancement. Evidence includes Plan before/after state and
dispatch eligibility, not only helper returns.

### Evidence-led coordination improvements

Worker publication changes occur only after fresh bounded cohort classifies
actual failure causes. Communication changes use compact references and
consequences, preserve Worker/CoS/Secretary ownership, and add no mandatory
handoff document.

### Conditional efficiency decision

Matched CoS-only and Secretary-assisted trials report correctness, human
interventions, coordination turns, elapsed intervals, publication success,
accepted completion, duplicate messages, false acceptance, duplicate
execution, and unauthorized writes. Correctness is a hard gate. Human
interventions, management turns, elapsed latency, and publication success are
reported independently; token usage and cost remain `unknown` when unavailable.
Secretary stays optional unless measured benefit survives correctness gates.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `task-specific isolated worktree` from `origin/main` after PR #59 merge
- Commit policy: `no commits during execution`; lead controller commits only after final verification
- Preauthorized local actions: inspect named sources, edit named repository files, create disposable Git-tracked fixtures, run declared tests and validators, and record sanitized evidence in this plan
- User-approval actions: external provider execution, push, pull request, merge, destructive cleanup, discard, and new external authority or persistence service
- Parallel ownership: none; acceptance, Plan mutation, and evidence consumers share contracts
- Sequential fallback: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/trustworthy-acceptance-low-overhead-coordination`
- Base commit: `f26681e0232f94bfc8efd2cc8c65e3cfdf646ed6` (PR #59 merge)
- Expected workspace: `clean task-specific worktree`; preserve current checkout artifacts and unrelated untracked files
- Next action: none — implementation and final verification complete
- Blockers: none
- Deferred external evidence: live Secretary attribution/counters/timestamps remain unavailable; efficiency is `INCONCLUSIVE` by design and outside this plan's current system boundary; no savings claim is authorized

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated worktree | `codex` | none | source map, contract decision, baseline proof | 35 baseline tests passed; no production caller or Plan writer found |
| Task 2 | `completed` | isolated worktree | `codex` | Task 1 | strict acceptance and transition regressions | 26 focused tests passed; exact condition coverage, active-state gate, malformed-input fail-closed behavior, complete decision proof |
| Task 3 | `completed` | isolated worktree | `codex` | Task 2 | acceptance-bound Plan mutation boundary or explicit caller gap | acceptance-bound writer requires complete bound controller/task/proof identity, target Plan identity, PASS/Git proof, and exact authorized batch; cooperating writers serialize; 53 focused acceptance/Plan tests passed |
| Task 4 | `completed` | isolated worktree | `codex` | Task 3 | negative-to-positive cycle | bad artifact preserved ledger; valid proof completed source and activated dependent once; stale replay blocked |
| Task 5 | `completed` | isolated worktree | `codex` | Task 2 | Worker cohort and scoped correction | 420 Worker/Herdr publication tests passed; no attributable defect; no code change |
| Task 6 | `completed` | isolated worktree | `codex` | Task 2 | sparse handoff and ownership proof | 38 Secretary adapter/event/benchmark tests passed; no ownership defect; no code change |
| Task 7 | `completed` | isolated worktree | `codex` | Task 4, Task 6 | matched efficiency evidence or `INCONCLUSIVE` | correctness gate passed; live attribution/counters/timestamps unavailable; `INCONCLUSIVE` by design, outside current system boundary; no savings claim or automation expansion |
| Task 8 | `completed` | isolated worktree | `codex` | Task 2, Task 3, Task 4, Task 5, Task 6, Task 7 | final verification and reconciliation | review remediation verified; focused suites 53 and 366 passed; full suite 980 passed, 1 skipped; validators, adapter sync, runtime drift, and diff check passed |

## Task Breakdown

### Task 1: Freeze acceptance inputs and owners

**Purpose:**
- Establish exact acceptance inputs from merged PR #59 and identify existing
  lead-controller procedure that owns Plan mutation.

**Task Function:**
- Contract mapping and root-cause confirmation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: merged source and ownership rules are authoritative.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent contract and source-map challenge.

**Specification Coverage:**
- Plan/Git remain workflow truth; CoS remains acceptance owner; runtime remains
  evidence and settlement owner.

**Required Skills:**
- `skill-systematic-debugging`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`
- Inspect: `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:PlanGraph`, `parse_plan`, `prepare_plan_lanes`
- Inspect: `scripts/project_os_runtime/results.py:validate_task_result`, `parse_task_result`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Inspect: `.agents/skills/skill-executing-plans/SKILL.md`
- Inspect: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`

**Dependencies:**
- PR #59 merge commit `f26681e0232f94bfc8efd2cc8c65e3cfdf646ed6`.

**Authority:**
- Preauthorized local actions: inspect named sources, run baseline focused tests, and update this plan with ownership facts
- Stop for: conflicting source-of-truth owners, missing merged content, or need for a new persistence or authority layer

**Steps:**
- [x] Record acceptance inputs, decision fields, Plan identity, task identity,
  Git anchor, freshness fields, settlement fields, and dependency state fields.
- [x] Define the required condition set as structured checks owned by the
  approved Plan/task contract. CoS resolves explicit condition IDs; independent
  verification records observed results. Do not parse free-form
  `PlanTask.required_proof` or global acceptance language.
- [x] Treat missing, ambiguous, or incomplete canonical condition resolution as
  `BLOCKED`; never let CoS omit requirements by sending a smaller mapping.
- [x] Confirm eligibility policy: first acceptance requires `active`; `pending`,
  `blocked`, missing, or invalid state is not eligible; `completed` receives no
  second completion transition.
- [x] Locate existing sole lead-controller Plan writer. If none exists, record
  Task 3 as externally blocked and do not create one in this plan.
- [x] Run baseline acceptance, plan-preparation, and result-contract tests.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_project_os_runtime.py tests/test_plan_preparation.py -q`
- Expected: baseline passes; source map names one canonical mutation owner or
  records Task 3 blocker.

**Exit Criteria:**
- Acceptance inputs, eligibility rules, condition authority, and Plan mutation
  owner are explicit and consistent with repository rules.

### Task 2: Close acceptance and transition contracts

**Purpose:**
- Prevent partial, stale, contradictory, ineligible, incomplete, and cross-plan
  decisions from authorizing continuation.

**Task Function:**
- Minimal policy hardening with regression proof.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: narrow backend contract change with high correctness risk.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: adversarial decision-shape and state-transition review.

**Specification Coverage:**
- Acceptance is pure policy; transition authority requires complete current
  evidence and never trusts Worker acceptance claims.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`
- Modify: `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`
- Modify: `scripts/project_os_runtime/__init__.py` only if exports change
- Verify: `tests/test_project_os_runtime.py`
- Verify: `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Task 1 complete; condition authority and eligibility rules recorded.

**Authority:**
- Preauthorized local actions: edit acceptance policy and focused tests within named files; run focused proof
- Stop for: new result schema, signature service, authority registry, or unresolved condition ownership

**Steps:**
- [x] Add failing tests for missing, invalid, pending, blocked, and completed
  task state; omitted conditions; contradictory conditions; stale Git anchor;
  and missing evidence.
- [x] Add failing tests proving the approved Plan condition set cannot be
  reduced by caller input, and that missing or ambiguous condition IDs return
  `BLOCKED`.
- [x] Add failing tests for minimal `{"decision": "PASS"}`, missing controller,
  mismatched transition fields, cross-plan dependent task, repeated completion,
  incomplete prerequisite, and input mutation.
- [x] Make `evaluate_acceptance()` require exact trusted condition coverage:
  every required condition appears with boolean result; missing coverage is
  `BLOCKED`, false evidence is `FAIL`, and no condition is inferred. Keep
  required-set completeness separate from observed-result coverage.
- [x] Make task-state handling fail closed and keep completed tasks idempotent;
  never emit undefined `None → completed` transition.
- [x] Make `authorize_dependent_transition()` validate complete decision,
  accepted task and plan identity, active→completed transition, freshness,
  settlement, and prerequisite state before advancement.
- [x] Revalidate Plan/Git/evidence freshness immediately before mutation; do not
  treat structural completeness as freshness proof.
- [x] Preserve existing return shape and ownership; helper output alone never
  mutates Plan state.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_project_os_runtime.py -q`
- Expected: adversarial cases fail before implementation and pass after;
  valid active-task acceptance still passes.

**Exit Criteria:**
- No partial or contradictory decision can authorize dependent advancement;
  focused acceptance regressions pass.

### Task 3: Connect one guarded native CoS path

**Purpose:**
- Turn callable acceptance policy into one operational evidence-to-Plan
  procedure without adding workflow authority.

**Task Function:**
- Native CoS integration and freshness-guard design.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: integration requires lead-controller authority and Plan/Git reconciliation.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent mutation-ownership and stale-state review.

**Specification Coverage:**
- One lead controller gathers evidence once, evaluates acceptance, revalidates,
  and applies one canonical Plan transition.

**Required Skills:**
- `skill-backend-verification`, `skill-chief-of-staff`, `skill-executing-plans`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Inspect: `.agents/skills/skill-executing-plans/SKILL.md`
- Inspect: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:load_plan`, `prepare_plan_lanes`
- Modify: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
  as acceptance-bound lead-controller Plan mutation API, with
  `apply_plan_transitions()` as its locked low-level writer; use an authorized
  disposable fixture plan for integration proof
- Verify: `tests/test_project_os_runtime.py` and owner-specific tests

**Dependencies:**
- Task 2 complete; Task 1 identifies a real canonical Plan mutation owner.

**Authority:**
- Preauthorized local actions: wire the sole Plan preparation owner to acceptance
  policy, add freshness checks, and add focused integration proof
- Stop for: need for a second writer, unresolved revision semantics, or external
  credential dependence

**Steps:**
- [x] Bind current plan revision, task identity/state, direct dependencies,
  controller identity, Git HEAD/write scope, Worker TaskResult, artifact
  checks, verification, and settlement evidence.
- [x] Gather canonical evidence once and resolve the approved Plan/task
  condition IDs; do not infer requirements from Worker prose or caller-supplied
  subsets.
- [x] Call `evaluate_acceptance()` and retain decision plus inspected revision
  anchors as one operation result.
- [x] Re-read Plan revision, task state, Git HEAD, write scope, and dependency
  states immediately before mutation; drift returns `BLOCKED`.
- [x] Apply exactly one lead-controller Plan transition through existing workflow;
  re-read completed prerequisites before dependent advancement.
- [x] Require complete `PASS` acceptance proof and Git binding at mutation
  boundary; reject direct transition batches without controller evidence.
- [x] Serialize cooperating Plan writers with a cross-process lock so one
  revision-bound batch cannot overwrite another accepted update.
- [x] Define `active` as execution eligibility only. Assignment/activation still
  requires existing lane preparation and delivery evidence; test both Plan state
  and dispatch eligibility.
- [x] Keep deterministic mutation tests separate from externally authorized live
  probes. The writer remains inside the existing Plan preparation boundary and
  does not create a second authority or persistence service.

**Verification:**
- [x] Integration test proves accepted transition changes canonical Plan state
  once and stale revision leaves state unchanged.
- Expected: no mutation on `FAIL`/`BLOCKED`, no duplicate completion, and no
  new authority or persistence surface.

**Exit Criteria:**
- One acceptance-bound callable mutation boundary is proven through the locked
  revision-bound Plan writer; stale and unauthorized transitions stay disabled.
  A live/native CoS caller remains outside this repository boundary, so
  autonomous advancement is not claimed.

**Execution result (October 8, 2026):**
- `apply_accepted_plan_transitions()` now binds complete CoS acceptance proof,
  Git freshness, and the accepted task transition before calling the sole
  revision-bound writer. `apply_plan_transitions()` serializes cooperating
  writers, performs atomic source/dependent updates, and rejects stale
  revisions, wrong expected states, unsupported transitions, and incomplete
  prerequisites. No live/native CoS caller exists in this repository; the
  callable boundary is proven by deterministic integration tests only.

### Task 4: Prove complete negative-to-positive cycle

**Purpose:**
- Demonstrate behavior across Worker evidence, CoS decision, Plan mutation, and
  dependent eligibility.

**Task Function:**
- Disposable end-to-end behavioral validation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: exact controller and Git evidence required.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent before/after Plan and dispatch-state inspection.

**Specification Coverage:**
- Incorrect artifact cannot advance work; corrected fresh evidence advances
  exactly once; communication reflects consequence only.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py`
- Inspect: `scripts/project_os_runtime/plan_preparation.py`
- Verify: `tests/test_project_os_runtime.py`, `tests/test_herdr_parallel_dispatch.py`
- Evidence: disposable Git-tracked plan and sanitized temporary probe output

**Dependencies:**
- Task 3 operational path passes.

**Authority:**
- Preauthorized local actions: create disposable fixtures, run configured probes, and record sanitized evidence
- Stop for: provider failure, stale identity, missing settlement, or unauthorized Plan/Git mutation

**Steps:**
- [x] Start with active source task and pending dependent task.
- [x] Publish completed Worker evidence with incorrect artifact; verify CoS
  returns `FAIL` or `BLOCKED`, source remains incomplete, dependent remains
  pending, and no launch occurs.
- [x] Correct artifact through authorized continuation or new settled attempt;
  capture new revision, TaskResult identity, verification, and settlement.
- [x] Re-run CoS acceptance; verify complete fresh `PASS` and one source-task
  completion in canonical Plan.
- [x] Reconcile dependency state and verify only legitimate dependent
  advancement becomes execution-eligible.
- [x] Repeat acceptance to prove no duplicate completion or advancement.

**Verification:**
- [x] Record Plan before/after hashes or exact sanitized state, decision, task
  state, dependent state, and dispatch evidence.
- [x] Keep live/native CoS availability separate from deterministic acceptance
  correctness; a missing live probe cannot invalidate deterministic proof.
- Expected: negative path preserves `pending`; positive path advances once;
  replay is rejected or idempotently reconciled.

**Exit Criteria:**
- Full negative-to-positive cycle is proven beyond helper return values.

### Task 5: Reconcile Worker publication reliability

**Purpose:**
- Replace historical incomplete `3/5` observation with fresh bounded cohort and
  change only implicated publication boundary.

**Task Function:**
- Failure-cause classification and minimal publication correction.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: existing Worker wrapper and parser boundaries own behavior.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: cohort accounting and regression review.

**Specification Coverage:**
- Worker publishes evidence; CoS decides acceptance; no new TaskResult schema,
  retry daemon, or completion protocol.

**Required Skills:**
- `skill-systematic-debugging`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/results.py:parse_task_result`, `validate_task_result`
- Inspect: `scripts/dcode_project.py:_worker_task_result`, publication diagnostics
- Inspect: `scripts/herdr_main_launcher.py` result reconciliation
- Inspect: `scripts/herdr_parallel_dispatch.py` settlement and delivery paths
- Modify: only boundary implicated by fresh cohort evidence
- Verify: `tests/test_dcode_project.py`, `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 2 complete; acceptance cannot be reinterpreted from publication alone.

**Authority:**
- Preauthorized local actions: run bounded ordinary Worker cohort, classify sanitized failures, and patch named publication boundary
- Stop for: insufficient attribution, raw payload exposure risk, or need for new schema/retry service

**Steps:**
- [x] Include every attempt in cohort accounting or record explicit exclusion
  reason and identity.
- [x] Classify failure as missing publication, binding reconstruction,
  malformed result, insufficient proof, parser misclassification, or external
  transport failure.
- [x] Patch only existing producer/wrapper/parser owner implicated by evidence.
- [x] Add focused regression proof and rerun cohort with identical admission and
  settlement rules.
- [x] Run this validation independently of the live/native CoS cycle; do not
  block deterministic acceptance release on Worker publication or provider
  availability.

**Verification:**
- [x] Focused Worker publication suite passes.
- Expected: valid Worker-owned evidence rate improves or remains unchanged with
  no false-completion increase; inconclusive cohort stays explicit.

**Exit Criteria:**
- Fresh cohort fully reconciled and any correction is small, evidence-backed,
  and regression-tested.

### Task 6: Minimize handoffs without adding authority

**Purpose:**
- Remove duplicated context and management turns while preserving sparse,
  reference-based communication.

**Task Function:**
- Communication ownership and handoff reduction.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: cross-surface ownership review after correctness proof.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: verify no duplicated authority or mandatory new record.

**Specification Coverage:**
- Workers communicate proof; CoS communicates decisions; Secretary communicates
  attention changes; runtime communicates mechanics.

**Required Skills:**
- `skill-project-secretary`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-project-secretary/SKILL.md`
- Inspect: `scripts/project_os_runtime/secretary_adapter.py`
- Inspect: `tests/test_secretary_adapter.py`, `tests/test_secretary_events.py`
- Modify: existing handoff/Secretary surfaces only when duplicate context is
  proven by Task 4 or Task 5 evidence
- Verify: Secretary event and adapter tests plus ownership assertions

**Dependencies:**
- Task 2 complete; Task 5 evidence is optional and only required when a
  publication message is changed.

**Authority:**
- Preauthorized local actions: edit existing communication surfaces and focused tests; preserve compact references
- Stop for: new mandatory handoff document, second acceptance owner, or unmeasured polling/transport optimization

**Steps:**
- [x] Map repeated status, acknowledgment, evidence, and blocker messages by
  owner and consequence.
- [x] Replace duplicated payloads with canonical evidence references and one
  next action where source already exists.
- [x] Keep unresolved project obligations in optional Secretary docket; do not
  move task truth out of Plan/Git.
- [x] Prove normal, blocked, and accepted events retain correct ownership.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_secretary_adapter.py tests/test_secretary_events.py -q`
- Expected: no duplicate acceptance/coordination authority and no lost blocker
  consequence.

**Exit Criteria:**
- Handoff volume decreases or remains unchanged without weakening evidence or
  ownership semantics.

### Task 7: Measure coordination economics

**Purpose:**
- Decide whether Secretary assistance reduces human coordination cost after
  correctness is established.

**Task Function:**
- Matched workload measurement and guarded interpretation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: performance evidence requires identical workload and attribution.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent correctness and measurement review.

**Specification Coverage:**
- Efficiency claims require matched correctness-gated trials; unavailable
  counters or timestamps produce `INCONCLUSIVE`.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/benchmark_secretary_architecture.py`
- Inspect: `tests/test_secretary_benchmark.py`
- Inspect: `scripts/project_os_runtime/secretary_adapter.py`
- Evidence: sanitized temporary trial output and this plan evidence table

**Dependencies:**
- Task 2 complete; Task 4 and Task 6 correctness/communication evidence must be
  available before interpreting matched efficiency.

**Authority:**
- Preauthorized local actions: run matched supervised trials and record aggregate evidence
- Stop for: mismatched inputs, correctness divergence, missing attribution, or unavailable live runtime

**Steps:**
- [x] Define one genuine cross-workstream dependency and identical baseline and
  candidate inputs, order, worktree, and correctness gate.
- [x] Measure human interventions, CoS/Secretary turns, time to first useful
  Worker action, time to accepted completion, publication success, duplicate
  messages, false acceptance, duplicate execution, and unauthorized writes.
- [x] Keep Worker execution, publication, settlement, acceptance, and Secretary
  routing intervals separate.
- [x] Report correctness as a hard gate. Report human interventions,
  management turns, elapsed intervals, and publication success independently;
  report token usage and cost as `unknown` when unavailable. Do not mark the
  entire trial `INCONCLUSIVE` only because token counters are unavailable.
- [x] Do not infer savings from aggregate observation time or deterministic fake
  telemetry; keep Secretary optional until its measured benefit survives the
  correctness gate.
- [x] Keep Secretary optional unless measured benefit survives correctness and
  attribution gates.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider tests/test_secretary_benchmark.py -q`
- Expected: matched-correctness gate passes; efficiency remains `INCONCLUSIVE`
  when live counters or timestamps are unavailable.

**Exit Criteria:**
- Decision is evidence-backed or explicitly inconclusive with no automation
  expansion based on missing data.

### Task 8: Final verification and reconcile plan

**Purpose:**
- Prove implementation, maintained contracts, evidence, and explicit deferrals
  agree before closure.

**Task Function:**
- Final verification and acceptance handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final proof and plan status require controller authority.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent final plan and evidence review.

**Specification Coverage:**
- Outcomes, blockers, deferrals, ownership boundaries, and release criteria
  reconcile with current repository and Git truth.

**Required Skills:**
- `skill-verification-before-completion`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Verify: all changed files listed in this plan
- Verify: Coordination State, task ledger, evidence table, and completion criteria

**Dependencies:**
- Task 2, Task 3, Task 4, Task 5, Task 6, and Task 7 complete, explicitly blocked, or explicitly deferred.

**Authority:**
- Preauthorized local actions: run final tests and validators, inspect diff, and reconcile this plan
- Stop for: failed proof, stale generated output, unresolved P0 blocker, or unreviewed scope

**Steps:**
- [x] Run focused acceptance, runtime, Worker, Secretary, and benchmark tests.
- [x] Run full suite, repository preflight/audit, planning lifecycle, generated
  adapter sync, runtime drift, and whitespace checks.
- [x] Review diff for credentials, `.deepagents/`, temp artifacts, raw malformed
  payloads, unrelated files, and generated-source violations.
- [x] Record cohort limitations, provider gaps, unknown timestamps, and deferred
  native-path conditions explicitly.
- [x] Return `verified`, `incomplete`, or `blocked` through
  `skill-verification-before-completion`; only then may plan status change.

**Verification:**
- [x] `py -B -m pytest -p no:cacheprovider -q` — 977 passed, 1 skipped
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope preflight --plan docs/superpowers/plans/2026-10-08-trustworthy-acceptance-and-low-overhead-coordination-plan.md` — passed
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --scope audit` — passed
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-08-trustworthy-acceptance-and-low-overhead-coordination-plan.md` — passed
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — passed
- [x] `py -B scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check` — passed
- [x] `git diff --check` — passed
- Expected: required deterministic proof passes; unavailable external evidence
  is recorded `INCONCLUSIVE` or `blocked`, never upgraded to success.

**Exit Criteria:**
- Completed claims have fresh evidence, required blockers are resolved or
  explicit, and Plan plus Git remain reconciled.

## Verification

Final artifact proof requires:

- focused acceptance and transition tests;
- complete native CoS cycle evidence with Plan before/after state;
- fresh Worker cohort accounting;
- Secretary ownership and event tests;
- matched efficiency evidence or explicit `INCONCLUSIVE` disposition;
- full deterministic suite and repository validators;
- generated-surface and runtime-drift checks;
- clean scoped diff with no credentials, runtime state, or unrelated artifacts.

## Completion Criteria

The plan is ready for completion verification when:

1. acceptance rejects partial, contradictory, stale, ineligible, and incomplete decisions;
2. dependent advancement requires complete same-task, same-plan, fresh `PASS` evidence;
3. one acceptance-bound callable path revalidates and persists exactly one guarded Plan transition; missing live/native caller remains explicit and autonomous advancement stays disabled;
4. negative-to-positive cycle proves Plan state and dependent eligibility, not only helper output;
5. Worker publication evidence is reconciled from fresh bounded cohort;
6. communication changes preserve ownership and add no second authority;
7. efficiency claims use matched correctness-gated evidence and remain `INCONCLUSIVE` when attribution is unavailable;
8. focused tests, full tests, validators, generated sync, runtime drift, and final diff review pass;
9. `skill-verification-before-completion` returns `verified` before status changes to `completed`.

## Evidence Table

| Claim | Result | Evidence reference | Limitation | Next action |
| --- | --- | --- | --- | --- |
| Acceptance rejects incomplete task state | passed | Task 2 focused regressions: 26 passed | deterministic helper proof only | Task 3 integration when mutation owner exists |
| Required conditions cannot be omitted | passed | Task 2 approved-Plan condition tests | condition IDs require canonical Plan/task source | keep source structured |
| Partial PASS cannot advance dependent task | passed | minimal/inconsistent decision regressions | helper is not standalone authority | retain guarded Plan writer |
| Acceptance-bound Plan mutation persists guarded transition | passed | Task 3 acceptance-bound writer and integration test | deterministic callable boundary; no live/native CoS caller in repository | retain sole writer; keep autonomous advancement disabled |
| Negative-to-positive cycle works end to end | passed | Task 4 disposable plan cycle | live provider not required for deterministic proof | retain guarded transition |
| Worker publication improvement is justified | passed | Task 5 fresh bounded deterministic cohort: 420 passed | no attributable publication defect; no code change justified | retain current boundary |
| Handoff reduction preserves ownership | passed | Task 6 adapter/event/benchmark suite: 38 passed | no ownership defect; no code change justified | retain current handoff semantics |
| Secretary improves efficiency | inconclusive | Task 7 benchmark contract tests and explicit disposition | live matched attribution, counters, and timestamps unavailable; deterministic fake telemetry not used as savings proof | keep Secretary optional; provision live runtime only before any future efficiency claim |

### Deferred prerequisite: Secretary Live Runtime and Evidence Surface

Future efficiency validation requires a separate approved plan and owned runtime
surface. That prerequisite must define launch through existing Codex/Herdr
configuration, provider/model and runtime identity, `task_id`, `plan_revision`,
`attempt_id`, and `run_id` binding, entry/exit timestamps, CoS and Secretary
turns, human interventions, publication/settlement/acceptance outcomes, token
and cost fields or explicit `unknown`, and a sanitized receipt artifact. Until
that surface exists, matched Secretary economics remain outside this plan and
must not be inferred from deterministic telemetry.

This plan is `completed`; implementation and final verification are complete. Acceptance-bound Plan mutation now binds controller, task, proof, plan identity, and exact authorized transition batch. Task 7 is explicitly `INCONCLUSIVE` by design: native Codex reached the configured `9router` route, but the repository owns no attributable live Secretary runtime. No efficiency or savings claim was made; Secretary remains optional.
