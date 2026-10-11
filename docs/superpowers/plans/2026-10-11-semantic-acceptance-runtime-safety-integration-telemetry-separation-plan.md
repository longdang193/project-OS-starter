---
layer: change
artifact_type: plan
contract_version: "1"
status: proposed
template_id: implementation-plan
name: semantic-acceptance-delivery-a
distribution_tier: starter_kit
targets:
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - tests/test_evidence_release.py
  - docs/operating_system/runtime/runtime-surfaces.md
---

## Goal

Deliver the smallest safe architectural improvement first:

> A verified immutable candidate can receive CoS `PASS` and advance the
> canonical Plan without waiting for unrelated runtime settlement, while any
> unresolved runtime owner remains quarantined from conflicting reuse.

Semantic acceptance, runtime safety, GitHub integration, and telemetry remain
separate decisions, but only the acceptance boundary is mandatory in this
delivery. Existing TaskResult v1, lifecycle terminology, Secretary `READY`,
and GitHub integration behavior remain unchanged unless the acceptance-path
inventory proves a concrete dependency.

## Implementation Outcomes

### Delivery A: semantic acceptance and accepted-candidate consequence

CoS evaluates the existing result/evidence contract and returns only
`PASS`, `FAIL`, or `BLOCKED` for the semantic task criteria. A verified Git
candidate establishes immutable artifact identity; it does not prove an
external side effect that is itself part of the task criteria. Settlement,
cleanup, pane/session observation, provider telemetry, and Secretary economics
do not block semantic `PASS` unless the task explicitly requires that evidence.

The accepted consequence records the candidate identity and binds downstream
dependency release to that accepted candidate or a descendant of it, rather
than whatever later exists in the predecessor worktree.

### Runtime safety is preserved, not renamed

Runtime owners continue to decide reuse, retry, retirement, cleanup, and
quarantine using the existing lifecycle and attempt facts. `authorize_evidence_release()`
remains stricter than semantic acceptance. The delivery must not create a new
runtime state machine, rename lifecycle states, weaken stale-attempt rejection,
or permit native fallback after ambiguous managed delivery.

### Deferred work is explicitly non-blocking

WorkerResult v2, v1 retirement, `READY` to `PROBE_READY` naming, telemetry
availability/attribution changes, Secretary economics, reconciliation-phase
deletion, and GitHub integration refactoring are deferred. They may become
separate deliveries only after measured value or a concrete acceptance-path
dependency is demonstrated.

## Scope Boundaries

- Do not modify Herdr, Codex, 9router, or any upstream provider.
- Do not change `scripts/project_os_runtime/results.py`,
  `scripts/dcode_project.py`, `scripts/project_os_runtime/attempt.py`,
  `scripts/project_os_runtime/reconciliation.py`, or Secretary telemetry code
  unless Task 1 finds a concrete acceptance-path defect that cannot be fixed in
  the declared Delivery A files.
- Do not migrate WorkerResult, lifecycle names, or live-probe disposition names
  in this delivery.
- Do not modify GitHub integration merely because it exists in the architecture;
  verify that it already consumes semantic `cos_pass` independently.
- Do not treat an immutable candidate as proof of an unresolved required
  deployment, migration, issue creation, API mutation, or other external side
  effect.
- Do not relax evidence-release, quarantine, ownership, recovery, or cleanup
  safety requirements.
- Preserve all unrelated tracked and untracked changes in the current checkout.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-using-git-worktrees`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-requesting-code-review`, `skill-verification-before-completion`
- Isolation: clean dedicated worktree created from freshly verified `main`; original dirty checkout remains untouched
- Commit policy: checkpoint commits are permitted only after task-local proof and plan-ledger update; no push or merge without explicit approval
- Preauthorized local actions: create the declared worktree, transfer and hash-check this reviewed plan, checkpoint only that plan, inspect source/tests, edit declared Delivery A files, run bounded tests/validators, and create local checkpoint commits
- User-approval actions: push, PR publication, merge, destructive cleanup, compatibility deletion, upstream changes, or edits outside declared Delivery A scope
- Parallel ownership: `none`; all acceptance-to-consequence changes share one sequential lane
- Sequential fallback: execute Tasks 1–6 in order; if a proof gate fails, record the blocker and stop rather than starting deferred deliveries

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/semantic-acceptance-delivery-a`
- Base commit: `332002e3e8674d957e7ba9df56472fc3c940fb37` (`origin/main` after activation revalidation; local `main` was stale and remains untouched)
- Expected workspace: `new clean dedicated worktree; existing dirty checkout preserved and not used for implementation`
- Next action: `create or attach the clean Delivery A worktree, transfer and checkpoint this reviewed plan, revalidate main, then complete Task 1`
- Blockers: `none for planning; live Secretary capability is not a Delivery A prerequisite`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | dedicated | `unresolved` | none | fresh base, plan checkpoint, and caller inventory | pending |
| Task 2 | `pending` | dedicated | `unresolved` | Task 1 | immutable-candidate acceptance contract | pending |
| Task 3 | `pending` | dedicated | `unresolved` | Task 2 | settlement decoupled end-to-end | pending |
| Task 4 | `pending` | dedicated | `unresolved` | Task 3 | Plan consequence and dependency binding | pending |
| Task 5 | `pending` | dedicated | `unresolved` | Task 3, Task 4 | runtime safety non-regression matrix | pending |
| Task 6 | `pending` | dedicated | `unresolved` | Task 4, Task 5 | combined suite and independent review | pending |

## Task Breakdown

### Task 1: Fresh base and acceptance-path inventory

**Purpose:**
- Start from a verified Git base and prove the smallest source scope before editing.

**Task Function:**
- Establish source-first caller, consumer, and dependency evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: worktree ownership and acceptance authority stay with the lead controller.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: inventory is validated by source-wide search and baseline tests.

**Specification Coverage:**
- Delivery A only; no unrelated schema, telemetry, lifecycle, or integration migration.
- Full acceptance-to-consequence chain must be inventoried.

**Required Skills:**
- `skill-using-git-worktrees`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`
- Inspect: `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`
- Inspect: `scripts/project_os_runtime/acceptance.py:authorize_evidence_release`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Inspect: `scripts/project_os_runtime/attempt.py:attempt_decision`, `derive_lifecycle_state`
- Inspect: `scripts/project_os_runtime/reconciliation.py:reconcile`
- Inspect: `scripts/herdr_parallel_dispatch.py` managed-delivery fallback paths
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`, and relevant reconciliation tests

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: create the clean worktree, transfer and hash-check this reviewed plan, checkpoint only that plan, inspect source/tests/history, run read-only baseline checks, and record caller inventory in this plan
- Stop for: stale or mismatched base, unapproved scope expansion, missing candidate-binding owner, or any safety invariant that cannot be preserved

**Steps:**
- [ ] Step 1: Verify `main` and `origin/main`; create the dedicated worktree from the chosen verified base and leave the dirty checkout untouched.
- [ ] Step 2: Copy only this reviewed plan into the dedicated worktree, compare its SHA-256 with the source copy, stage only the plan, and create the initial coordination checkpoint before activating the first task.
- [ ] Step 3: Run baseline acceptance, plan-preparation, evidence-release, and relevant reconciliation tests.
- [ ] Step 4: Inventory the complete chain: `evaluate_acceptance()` → `apply_accepted_plan_transitions()` → accepted Plan consequence → `authorize_dependent_transition()` → accepted prerequisite preparation → dependent launch input.
- [ ] Step 5: Inventory all uses of settlement in that chain and prove whether
  `authorize_evidence_release()` is independently stricter.
- [ ] Step 6: Confirm current integration already treats `cos_pass` as semantic
  input and does not need modification; record the result rather than changing it.

**Verification:**
- [ ] `git status --short --branch`
- [ ] `python -m pytest tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py -q`
- [ ] `python scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-11-semantic-acceptance-runtime-safety-integration-telemetry-separation-plan.md`
- Expected: clean dedicated worktree on verified base, baseline tests pass, and every acceptance-path caller is classified.

**Exit Criteria:**
- The exact Delivery A write set and settlement-coupled callers are known; no
  WorkerResult, telemetry, lifecycle-name, or GitHub refactor is required to
  begin acceptance work.

### Task 2: Define the immutable-candidate semantic boundary

**Purpose:**
- Make candidate identity and task-specific semantic evidence the acceptance boundary.

**Task Function:**
- Specify and encode the distinction between immutable artifact proof and external-effect proof.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest reliable executor after Task 1 confirms the write set.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: independent review is deferred to Task 6; local tests cover the contract here.

**Specification Coverage:**
- Immutable candidate may pass without unrelated cleanup or telemetry.
- Mutable workspace alone is insufficient.
- Required external effects remain semantic evidence when the task requires them.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`
- Inspect: `scripts/project_os_runtime/acceptance.py:RELEASE_BINDING_FIELDS`
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit acceptance logic and focused acceptance tests within the Delivery A scope
- Stop for: any change to worker result schema, runtime lifecycle ownership, evidence-release authority, or external-provider behavior

**Steps:**
- [ ] Step 1: Define the minimum semantic proof as task/attempt binding,
  candidate identity, required criteria, publication, freshness, write scope,
  verification, and CoS authority.
- [ ] Step 2: Ensure immutable candidate identity is explicit in the acceptance
  proof and distinguish it from the mutable predecessor workspace.
- [ ] Step 3: Ensure a required unresolved external side effect remains
  `BLOCKED`, while missing pane/session observation alone has no semantic effect.
- [ ] Step 4: Keep worker-reported status advisory; independently valid evidence
  controls `PASS`, `FAIL`, or `BLOCKED`.

**Verification:**
- [ ] Focused tests cover immutable candidate, mutable workspace only, stale/wrong attempt, missing evidence, false criterion, and unresolved required external effect.
- Expected: no valid immutable candidate is blocked by unrelated runtime or telemetry facts, and no mutable workspace is accepted as an artifact.

**Exit Criteria:**
- The acceptance proof answers only whether the bound candidate satisfies the
  task criteria and preserves the distinction between artifact and side effect.

### Task 3: Remove universal settlement dependency from the acceptance path

**Purpose:**
- Allow semantic acceptance and its consequence chain to proceed without waiting
  for unrelated runtime settlement, while retaining compatibility only where an
  existing consumer demonstrably needs it.

**Task Function:**
- Remove the root coupling once and update all shared callers in the acceptance chain.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: shared backend behavior with direct acceptance authority.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: local boundary tests; independent review occurs at Task 6.

**Specification Coverage:**
- `evaluate_acceptance()` no longer requires settlement for semantic `PASS`.
- `authorize_dependent_transition()` and Plan transition authorization agree with that boundary.
- `authorize_evidence_release()` remains stricter.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/project_os_runtime/acceptance.py:evaluate_acceptance`
- Modify if Task 1 proves coupled: `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`
- Modify if Task 1 proves coupled: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Modify if required by the inventory: `scripts/project_os_runtime/acceptance.py:authorize_evidence_release`, `release_authorized_evidence`
- Verify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: edit only the inventoried acceptance-to-consequence callers and their focused tests; retain a clearly labeled compatibility field only when a live consumer requires it
- Stop for: removing stale-attempt, candidate, write-scope, publication, or evidence-release checks; changing runtime owner facts; or adding a new ledger/state machine

**Steps:**
- [ ] Step 1: Remove `settlement_proven` and `resource_settled` as universal
  semantic prerequisites from `evaluate_acceptance()`.
- [ ] Step 2: Remove the same prerequisites from Plan transition and dependent
  transition authorization only where Task 1 proves they are incorrectly coupling
  semantic advancement; do not weaken evidence-release authorization.
- [ ] Step 3: Keep any temporary settlement field compatibility-only, document
  its consumer, and ensure it cannot change semantic `PASS`.
- [ ] Step 4: Make evidence release consume a fresh, authoritative, same-attempt
  settlement/retirement proof from the runtime owner rather than relying on the
  original acceptance-time settlement snapshot; keep retention, ownership,
  recovery, and consumer-release checks unchanged.
- [ ] Step 5: Prove no external/provider calls are introduced into semantic evaluation.

**Verification:**
- [ ] `python -m pytest tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py -q`
- Expected: valid candidate with unsettled runtime can pass and advance its
  accepted consequence; a later same-attempt settlement permits safe release,
  while wrong-attempt or stale settlement remains rejected.

**Exit Criteria:**
- The full acceptance-to-consequence chain is settlement-independent for
  semantic advancement, with evidence release still independently strict.

### Task 4: Persist accepted candidate identity and bind dependent work

**Purpose:**
- Prevent downstream tasks from consuming later mutations in the predecessor worktree.

**Task Function:**
- Make the accepted Plan consequence carry the candidate reference used by dependents.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: Plan transition ownership is canonical and must remain single-writer.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: local transition tests plus Task 6 independent review.

**Specification Coverage:**
- `PASS(C)` persists candidate identity before dependency release.
- Dependent work consumes `accepted_candidate_sha` or a verified descendant.
- Later workspace mutations do not alter the accepted consequence.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify if required: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Modify if required: `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`
- Inspect: `scripts/project_os_runtime/plan_preparation.py:_accepted_prerequisites`
- Inspect: `scripts/herdr_parallel_dispatch.py:verify_launch_bindings`
- Verify: `tests/test_plan_preparation.py`, `tests/test_project_os_runtime.py`, existing accepted-prerequisite launch tests

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: edit accepted-consequence persistence and dependency binding only; update focused Plan transition tests
- Stop for: consuming mutable workspace state, creating a second Plan/task ledger, or releasing a dependency without candidate identity and plan binding

**Steps:**
- [ ] Step 1: Persist the accepted candidate SHA and its existing plan/task/attempt
  binding in the canonical Plan consequence.
- [ ] Step 2: Update the existing accepted-prerequisite preparation boundary
  (`_accepted_prerequisites`) to derive or validate each `accepted_revision`
  against the persisted plan/task/attempt-bound consequence, not an independently
  supplied commit merely contained by the dependent worktree.
- [ ] Step 3: Reuse `verify_launch_bindings` as an ancestry/containment check,
  not as the source of accepted-candidate identity.
- [ ] Step 4: Ensure old Worker mutations after acceptance cannot modify the
  accepted consequence and cannot make the workspace reusable while ownership is uncertain.
- [ ] Step 5: Test idempotent repeated transition attempts, restart-and-prepare
  behavior, and mismatched/stale candidate rejection including substitution of
  an unrelated commit already contained by the dependent worktree.

**Verification:**
- [ ] `python -m pytest tests/test_plan_preparation.py tests/test_project_os_runtime.py -q`
- Expected: accepted candidate identity is persisted and dependent work cannot
  advance from an unrelated or later workspace mutation.

**Exit Criteria:**
- Plan advancement and dependency release are bound to the accepted candidate,
  with one canonical Plan writer and no mutable-workspace shortcut.

### Task 5: Prove runtime safety remains independent

**Purpose:**
- Verify that semantic `PASS` does not permit unsafe resource reuse or destructive cleanup.

**Task Function:**
- Run non-regression proof and escalate any concrete shared runtime defect exposed by Tasks 1–4.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: use the lowest reliable executor for the bounded runtime proof.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: independent review is reserved for Task 6.

**Specification Coverage:**
- Old Worker may remain active while `PASS(C)` remains valid.
- Unknown ownership quarantines the workspace/resource from reuse.
- Harmless cleanup failure affects reconciliation, not semantic correctness.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/attempt.py:attempt_decision`, `derive_lifecycle_state`, `settlement_decision`
- Inspect: `scripts/project_os_runtime/reconciliation.py:_retire`, `_prune`
- Inspect: `scripts/herdr_parallel_dispatch.py` ambiguous managed-delivery handling
- Modify: none under the current plan; any runtime-owner patch requires a scope amendment before editing
- Verify: `tests/test_reconciliation.py`, `tests/test_project_os_reconciliation.py`, `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Tasks 3–4 complete.

**Authority:**
- Preauthorized local actions: inspect runtime ownership and add focused regression proof; do not modify inspected runtime owners without an explicit scope amendment recorded in this plan
- Stop for: lifecycle renaming, native fallback after ambiguous delivery, unsafe reuse, destructive cleanup without ownership proof, or scope expansion into telemetry

**Steps:**
- [ ] Step 1: Prove accepted immutable candidate plus live Worker leaves reuse blocked/quarantined.
- [ ] Step 2: Prove harmless cleanup failure yields reconciliation work without changing semantic `PASS`.
- [ ] Step 3: Prove missing pane/session observation does not invalidate candidate acceptance but preserves resource quarantine when ownership is uncertain.
- [ ] Step 4: Prove ambiguous Herdr delivery never causes duplicate native fallback; if this fails, stop and request a scope amendment rather than editing runtime/dispatch code under this plan.

**Verification:**
- [ ] `python -m pytest tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_herdr_parallel_dispatch.py -q`
- Expected: unsafe resource actions remain blocked or quarantined and existing lifecycle facts remain authoritative.

**Exit Criteria:**
- Delivery A has fresh proof that semantic acceptance and runtime safety are
  independent without introducing a second runtime state machine.

### Task 6: Combined regression, independent review, and completion proof

**Purpose:**
- Prove the first milestone end-to-end with one compact review surface.

**Task Function:**
- Reconcile implementation, tests, docs, plan state, and review findings.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and Git evidence remain controller-owned.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: one independent review after the combined suite, not one validator per task.

**Specification Coverage:**
- Delivery A boundary matrix and measurable simplification gates.
- No deferred delivery is a completion prerequisite.

**Required Skills:**
- `skill-requesting-code-review`, `skill-verification-before-completion`, `skill-backend-verification`

**Files And Symbols:**
- Verify: all Delivery A targets and their tests
- Inspect: `scripts/project_os_runtime/results.py`, `scripts/project_os_runtime/attempt.py`, `scripts/project_os_runtime/reconciliation.py`, and Secretary telemetry code for unintended changes
- Update: this plan’s coordination state and task evidence only after proof is accepted

**Dependencies:**
- Tasks 4 and 5 complete.

**Authority:**
- Preauthorized local actions: run the combined suite, source-wide diff/reuse checks, one independent review, bounded review fixes within Delivery A, and final local verification
- Stop for: unresolved review finding, stale base, failed required proof, unapproved scope, or any request to merge/push without explicit authorization

**Steps:**
- [ ] Step 1: Run the compact Delivery A boundary matrix.
- [ ] Step 2: Check the simplification gates: false acceptance `0`, stale/wrong-attempt acceptance `0`, unsafe reuse `0`, duplicate fallback `0`, identical semantic outcome with telemetry present/unavailable, zero external calls in semantic evaluation, zero wait for harmless cleanup, one authoritative writer per fact, and zero new ledgers/global readiness states.
- [ ] Step 3: Request one independent review of the exact Delivery A diff; fix only justified findings and rerun affected proof.
- [ ] Step 4: Run final verification and record deferred B/C work as deferred, not blocked Delivery A work.

**Verification:**
- [ ] `python -m pytest tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_herdr_parallel_dispatch.py -q`
- [ ] `python scripts/validate_repo_contracts.py`
- [ ] `git diff --check`
- Expected: the combined suite passes, the review is clean or justified fixes are applied, and Delivery A is independently verifiable.

**Exit Criteria:**
- A verified immutable candidate can pass and advance the canonical Plan without
  unrelated settlement/telemetry, dependent work consumes the accepted
  candidate, runtime reuse remains safe, and no deferred migration was pulled
  into the first delivery.

## Deferred Deliveries

### Delivery B: reporting boundary

Not required for Delivery A. If later justified, measure and implement
Secretary probe semantics, telemetry availability and attribution as two axes,
economics reporting, and live capability evidence. A missing Secretary receipt
must block only Secretary-attributed claims; independently attributable 9router
provider observations remain reportable at their supported attribution level.

### Delivery C: optional simplification

Not required for Delivery A. Consider WorkerResult v2, legacy schema retirement,
unused `accept`/`verify` phase deletion, `READY` naming migration, or other
compatibility removal only after source-wide inventory and measured value prove
the migration reduces burden, errors, payload complexity, or ambiguity.

## Verification

- `python -m pytest tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_herdr_parallel_dispatch.py -q`
- `python scripts/validate_repo_contracts.py`
- `git diff --check`
- Source-wide search confirming no Delivery B/C files changed as part of Delivery A.
- Fresh live probes are optional evidence for Delivery A and cannot block or
  promote its semantic result; if run, preserve their actual capability status.

## Completion Criteria

The plan is ready for completion verification when:

1. `evaluate_acceptance()` distinguishes immutable candidate proof from mutable workspace state and required external effects
2. valid semantic evidence can produce `PASS` without unrelated settlement or telemetry
3. Plan consequence persistence records the accepted candidate identity
4. dependent transition authorization consumes the accepted candidate or verified descendant
5. evidence release remains stricter and independently guarded
6. runtime reuse, quarantine, recovery, and ambiguous-delivery safety remain proven
7. the compact boundary suite and one independent review pass
8. Delivery B and Delivery C remain explicitly deferred unless separately approved

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified` against fresh repository evidence.
