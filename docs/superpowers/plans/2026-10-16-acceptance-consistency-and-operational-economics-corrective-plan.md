---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: acceptance-consistency-corrective
targets:
  - docs/superpowers/plans/2026-10-16-acceptance-consistency-and-operational-economics-corrective-plan.md
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/plan_preparation.py
  - tests/test_project_os_runtime.py
  - tests/test_plan_preparation.py
  - tests/test_evidence_release.py
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Acceptance Consistency Corrective Plan

## Review Basis

This plan adopts the supplied consolidated verdict as the current baseline.
The role hierarchy, optional Secretary boundary, bounded-wave scheduler,
removed refill behavior, managed-Secretary capability block, and existing
semantic/runtime proof boundaries remain closed unless new evidence reopens
them.

The immediate repository defect is acceptance consistency. The operational
economics comparison is deliberately moved to a separate post-merge
measurement plan so that the correctness patch has one immutable implementation
boundary and the later experiment can start from a merged corrected revision.

No new role, scheduler, workflow database, proof registry, receipt system,
managed Secretary feature, dynamic refill path, benchmark orchestrator, or
universal performance threshold is authorized by this plan.

## Goal

Make every accepted `AcceptanceDecision` internally coherent across controller,
task, proof, Git, transition, repository, checkpoint, candidate, and attempt
identities; preserve precise validation evidence through consumers; keep
semantic acceptance independent from runtime settlement; and leave a durable
handoff for a later matched operational-economics measurement.

## Implementation Outcomes

### One closed acceptance identity graph

`evaluate_acceptance()` resolves the accepted attempt identity once and writes
that resolved value into every returned projection. The shared validator
rejects independent mutations of duplicated task, plan, attempt, repository,
checkpoint, candidate, and transition identities that already exist in the
serialized decision.

The validated relationships are:

```text
controller.task_id
    = task.task_id
    = proof.task_id

controller.plan_identity
    = task.plan_identity
    = proof.plan_identity
    = proof.git.plan_identity

resolved_attempt_id
    = task.attempt_id
    = proof.attempt_id
    = proof.git.attempt_id

proof.repository_identity
    = proof.git.repository_identity

proof.checkpoint_sha
    = proof.git.acceptance_checkpoint_sha

task_transition.accepted_candidate_sha
    = proof.git.candidate_sha
```

No new field, proof schema, digest, or registry is introduced.

### One stable cross-module validator with useful failure evidence

The private cross-module validator becomes
`validate_acceptance_decision()` in `scripts.project_os_runtime.acceptance`.
Package-root export is not assumed: caller inventory must establish that
`scripts.project_os_runtime.__init__` is the intended canonical import before
adding that compatibility commitment.

Consumers retain compatibility summary reasons while returning canonical
`validation_reasons` for shared acceptance-contract failures. Consumer-specific
dependency, retention, release, and transition reasons remain separate.

### Semantic acceptance and runtime settlement remain separate

The unused `evaluate_acceptance(settlement=...)` compatibility parameter is
removed after semantic caller inventory. Runtime settlement remains explicit at
the lifecycle and evidence-release boundaries, and release-boundary wording
uses `runtime settlement` rather than `acceptance settlement`.

Filesystem evidence-release extraction is deferred; this plan changes the
boundary and compatibility parameter only.

### Post-merge measurement handoff

The completed plan records a separate follow-up question: measure topology
overhead for one identical decomposable workload through direct-controller,
single-Worker, and two-lane CoS paths. The future benchmark script is a raw-run
validator/aggregator only; existing controllers and executors perform the
runs. It must not launch CoS, dispatch Workers, own retries, or become a new
coordination owner.

## Scope Classification

- **Actual gaps in this plan:** acceptance identity closure, precise reason
  propagation, stable cross-module validator naming, settlement compatibility
  removal, and boundary documentation.
- **Already satisfied and frozen:** optional Secretary, no mandatory
  Secretary-to-CoS hop, no CoS mesh, direct/local execution, bounded executor
  path, sequential target acquisition, refill removal, common validator
  existence, managed-Secretary capability block, and canonical routing/skill
  audit.
- **Measure later, not implement here:** CoS reconstruction reuse, monitoring
  or polling reduction, integration actuation, continuation/grant sizing, and
  all other accepted-outcome economics optimizations.
- **Deferred:** physical evidence-release module extraction, managed-Secretary
  archive/retirement, broad plan-lifecycle cleanup, and benchmark orchestration.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `isolated clean worktree from c89e81fcb7679e285cc3bd9056edd0ffc7711d28; preserve dirty main untouched`
- Commit policy: `verified per-task checkpoint commits preauthorized`
- Preauthorized local actions: `create the named feature worktree, edit named source/tests/docs, run declared local validation, and record task evidence`
- User-approval actions: `push, merge, publication, external writes, branch disposition, worktree cleanup, and discarding preserved local edits`
- Parallel ownership: `none; one acceptance contract and one shared write scope`
- Sequential fallback: `Task 1 contract convergence → Task 2 independent review → Task 3 final verification and post-merge measurement handoff`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/acceptance-consistency-corrective`
- Base commit: `c89e81fcb7679e285cc3bd9056edd0ffc7711d28`
- Expected workspace: `isolated clean feature worktree; local main retains its three preserved plan edits outside this worktree`
- Next action: `after merge, create the separate post-merge operational-economics measurement plan`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated feature worktree | `codex` | none | focused acceptance/release contract suite | 117 passed, 1 skipped; checkpoint `d35d94c` |
| Task 2 | `completed` | isolated feature worktree | `codex` | Task 1 | independent contract review and focused rerun | pass; no P1/P2 findings; focused rerun 117 passed, 1 skipped |
| Task 3 | `completed` | isolated feature worktree | `codex` | Task 2 | full suite, repository validators, and handoff evidence | 1343 passed, 2 skipped; repository/config/contract/adapter/starter-kit checks passed; implementation checkpoint `d35d94c` |

## Task Breakdown

### Task 1: Converge the acceptance contract

**Purpose:**
- Deliver the complete acceptance corrective change in one bounded write scope,
  including identity closure, reason propagation, API cleanup, and focused
  proof.

**Task Function:**
- Implement and locally verify one coherent producer-validator-consumer
  acceptance contract.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded backend contract change with cross-field invariants;
  use the lowest reliable Codex profile for the active implementation lane.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independent review of producer output, validator equality,
  consumer authorization, and release-boundary behavior.

**Specification Coverage:**
- Resolve `accepted_attempt_id` once and write it to the returned task,
  acceptance proof, and nested Git proof projections.
- Validate only duplicated identities already present in the decision; do not
  add symmetry-only fields.
- Distinguish producer-input contradictions from post-production tampering:
  producer contradictions make `evaluate_acceptance()` return `BLOCKED`, while
  tampering may leave the original decision as `PASS` but must be rejected by
  the validator and every applicable consumer.
- Preserve compatibility `reason` values and add `validation_reasons` only for
  shared acceptance-contract failures.
- Remove redundant consumer checks owned by the shared validator while
  retaining dependency, retention, release, and transition-specific checks.
- Remove `settlement` and `del settlement` from `evaluate_acceptance()` after
  caller inventory; retain `runtime_settlement` at release/lifecycle boundaries.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py:validate_acceptance_decision`, `evaluate_acceptance`, `authorize_dependent_transition`, `authorize_evidence_release`
- Inspect: `scripts/project_os_runtime/__init__.py` for package-root validator callers; modify only if inventory proves that boundary is canonical
- Modify: `scripts/project_os_runtime/acceptance.py:validate_acceptance_decision`, `evaluate_acceptance`, and consumer result projections
- Modify: `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`
- Modify: `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:semantic acceptance and runtime settlement boundary`

**Dependencies:**
- Current source and tests are authoritative; preserve the existing serialized
  decision and release-record shapes unless an additive reason field is needed.

**Authority:**
- Preauthorized local actions: edit the named acceptance, consumer, test, and documentation surfaces; run focused checks; create one verified local checkpoint commit after task proof.
- Stop for: a new proof schema, digest/registry, package-root API commitment without caller evidence, changed acceptance authority, external caller incompatibility, filesystem-module extraction, or any base/workspace change.

**Steps:**
- [x] Step 1: Inventory all `evaluate_acceptance`, private-validator, release,
  and settlement callers with broad search plus bounded inspection; record the
  package-root export decision before editing `__init__.py`.
- [x] Step 2: Rename the cross-module validator to
  `validate_acceptance_decision()` and preserve its ordered, de-duplicated
  reason values.
- [x] Step 3: Close the existing equality graph across controller, task, proof,
  nested Git proof, transition, and expected consumer binding. Ensure the
  resolved attempt is projected everywhere while contradictory source values
  remain rejected.
- [x] Step 4: Update plan-transition, dependent-transition, and evidence-release
  consumers to return compatibility `reason` plus acceptance-only
  `validation_reasons`; keep aggregate release `reasons` separate.
- [x] Step 5: Remove checks duplicated by the common validator and retain only
  consumer-specific dependency, retention, resource, replay, and transition
  checks.
- [x] Step 6: Remove the semantic `settlement` compatibility parameter, rename
  release-boundary wording to `runtime settlement`, and update the runtime
  surface documentation.
- [x] Step 7: Add separate parameterized regressions for producer-input
  contradictions and post-production decision tampering. Assert that all
  applicable consumers refuse authorization and retain actionable reasons.
- [x] Step 8: Run focused backend and release suites, reconcile failures, and
  create one verified checkpoint commit containing the implementation and task
  ledger update.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py`
- Expected: resolved attempts propagate consistently; producer contradictions
  return `BLOCKED`; tampered `PASS` decisions fail shared validation and
  consumer authorization; validation reasons remain precise; release remains
  same-attempt, fail-closed, replay-safe, and idempotent.
- [x] `rg -n "evaluate_acceptance|settlement\s*=" scripts tests docs`
- Expected: every actual semantic acceptance caller is inspected, no supported
  caller supplies the removed settlement parameter, and runtime settlement
  remains only at lifecycle/release boundaries.

**Exit Criteria:**
- The acceptance producer, validator, consumers, tests, and runtime boundary
  documentation agree on one contract, and the verified checkpoint commit is
  available for independent review.

### Task 2: Independently review the acceptance contract

**Purpose:**
- Obtain one independent judgment after the combined contract change without
  creating separate review overhead for intermediate substeps.

**Task Function:**
- Review the Task 1 diff and evidence for correctness, scope containment, and
  failure-path coverage.

**Template Profile:**
- Controller-selected: `review-1`
- Selection basis: independent code-and-contract review with no write authority.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the review profile is the independent validator for this
  task; no second validator is required.

**Specification Coverage:**
- Confirm the equality graph covers only existing duplicated fields.
- Confirm producer-input contradiction and post-production tampering tests are
  separate and reach every applicable consumer.
- Confirm package-root export was conditional on caller evidence.
- Confirm semantic acceptance does not read runtime settlement and that
  release-specific settlement checks remain intact.
- Confirm no benchmark runner, new coordinator, Secretary feature, refill
  path, or unrelated architecture change entered the diff.

**Required Skills:**
- `skill-plan-document-reviewer`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py`, `scripts/project_os_runtime/plan_preparation.py`, `tests/test_project_os_runtime.py`, `tests/test_plan_preparation.py`, `tests/test_evidence_release.py`, `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: Task 1 checkpoint diff, focused test output, caller inventory, and
  plan ledger evidence

**Dependencies:**
- Task 1 checkpoint commit exists in the isolated feature worktree.

**Authority:**
- Preauthorized local actions: inspect the Task 1 diff, rerun focused tests, and record review findings in the plan evidence.
- Stop for: any P1 correctness finding, missing consumer coverage, unsupported API expansion, or scope expansion requiring implementation changes.

**Steps:**
- [x] Step 1: Inspect the diff against `c89e81fcb7679e285cc3bd9056edd0ffc7711d28`.
- [x] Step 2: Trace the producer decision through the public module validator,
  plan transition, dependent transition, and release authorization boundaries.
- [x] Step 3: Check the separate mutation regressions, settlement caller
  inventory, and focused test output.
- [x] Step 4: Record `pass`, `revise`, or `blocked` with exact findings; do not
  modify source from the review task.

**Verification:**
- [x] `git diff c89e81fcb7679e285cc3bd9056edd0ffc7711d28 -- scripts/project_os_runtime tests docs/operating_system/runtime/runtime-surfaces.md`
- Expected: only the named acceptance contract, consumer, test, documentation,
  and plan-ledger surfaces changed; no benchmark or orchestration surface is
  introduced.
- [x] `py -3 -m pytest -q tests/test_project_os_runtime.py tests/test_plan_preparation.py tests/test_evidence_release.py`
- Expected: focused proof remains green after independent review inspection.

**Exit Criteria:**
- Independent review returns no unresolved P1/P2 issue, or Task 1 is reopened
  with a recorded finding and fresh focused proof.

### Task 3: Run final verification and record the measurement handoff

**Purpose:**
- Prove the corrective plan is complete and record the exact post-merge
  measurement question without implementing it here.

**Task Function:**
- Reconcile implementation, review, validators, generated surfaces, and next
  action into durable plan evidence.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: final verification requires controller authority and fresh
  repository evidence.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently confirm final claims and absence of stale
  required work.

**Specification Coverage:**
- Final checks cover the full repository once, after focused checks have passed.
- Starter-kit generation uses an explicit temporary output root and does not
  leave ambiguous generated workspace state.
- The next action names a separate post-merge measurement plan based on the
  immutable merged correction revision.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `docs/superpowers/plans/2026-10-16-acceptance-consistency-and-operational-economics-corrective-plan.md`
- Verify: all Task 1 source/tests/docs and generated starter-kit surfaces

**Dependencies:**
- Task 2 independent review passes.

**Authority:**
- Preauthorized local actions: run final local verification, build/validate the starter kit under the named temporary output root, and update plan evidence/status.
- Stop for: any failed required check, stale plan ledger, unresolved review finding, generated drift, or a request to perform push/merge/cleanup.

**Steps:**
- [x] Step 1: Run the full test suite once after focused proof and independent
  review pass.
- [x] Step 2: Run planning, repository-contract, adapter-drift, and generated
  starter-kit validation against the isolated feature worktree.
- [x] Step 3: Record the exact verification results, checkpoint SHA, review
  result, deviations, and blockers in the plan ledger.
- [x] Step 4: Record the next action: a separate post-merge measurement plan
  using one identical decomposable workload and existing execution owners.

**Verification:**
- [x] `py -3 -m pytest -q`
- Expected: the complete repository test suite passes once at the verified
  Task 1 checkpoint.
- [x] `py -3 scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-16-acceptance-consistency-and-operational-economics-corrective-plan.md`
- Expected: the plan ledger, task contracts, dependencies, authority, and
  completion evidence are valid.
- [x] `py -3 scripts/validate_repo_config.py`
- [x] `py -3 scripts/validate_repo_contracts.py`
- [x] `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [x] `py -3 scripts/build_starter_kit.py --output-root .tmp-tests/acceptance-consistency-starter-kit`
- [x] `py -3 scripts/validate_starter_kit.py --output-root .tmp-tests/acceptance-consistency-starter-kit`
- [x] `git diff --check`
- Expected: all required repository, generated-surface, plan, and whitespace
  checks pass without modifying preserved local main edits.

**Exit Criteria:**
- Fresh full-suite and validator evidence proves the acceptance correction is
  complete; the plan records the immutable checkpoint and independent review;
  the post-merge measurement is explicitly a separate next action.

## Post-Merge Measurement Handoff

This is not an implementation task in the current plan. After the corrective
change is merged, create a separate measurement plan from that immutable main
revision.

The experiment should ask one question: **what topology overhead does the same
workload incur?** Use one identical decomposable workload through:

```text
Arm A — direct_controller
One controller performs the whole workload sequentially.

Arm B — single_worker
One bounded Worker performs the same whole workload.

Arm C — cos_two_lane
The identical workload is split into exactly two predeclared independent lanes
with disjoint ownership.
```

The future plan must keep the same base revision, objective, final files,
acceptance criteria, verification commands, controllable provider/model, and
environment. It must define provenance before execution for launches,
subprocesses, attempts/retries, completion delay, messages, interventions,
evidence reads, unresolved resources, review/integration sessions, and
attributable cost. Unsupported metrics remain `unavailable`.

The future `benchmark_operational_comparison.py`, if justified after the
protocol is approved, may validate and aggregate controller-produced raw
records. It must not launch CoS, dispatch Workers, own retries, or decide task
scope. Raw JSONL observations, a machine-readable summary, and a report must be
retained only after sanitization/redaction review.

## Verification

Use this section for final artifact-level verification only.

- `py -3 -m pytest -q`
- `py -3 scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-16-acceptance-consistency-and-operational-economics-corrective-plan.md`
- `py -3 scripts/validate_repo_config.py`
- `py -3 scripts/validate_repo_contracts.py`
- `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- `py -3 scripts/build_starter_kit.py --output-root .tmp-tests/acceptance-consistency-starter-kit`
- `py -3 scripts/validate_starter_kit.py --output-root .tmp-tests/acceptance-consistency-starter-kit`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. acceptance producer and consumer projections share one closed identity graph,
   including resolved attempt propagation;
2. producer-input contradictions and post-production tampering are separately
   tested and rejected at the correct boundary;
3. every consumer preserves canonical validation reasons alongside compatibility
   summaries without duplicating the common identity graph;
4. semantic acceptance no longer accepts settlement input, runtime settlement
   remains explicit at release/lifecycle boundaries, and documentation matches;
5. the independent review has no unresolved P1/P2 finding;
6. the full test suite, planning validators, repository contracts, adapter drift,
   and starter-kit checks pass at one verified checkpoint;
7. the plan itself records its checkpoint, review evidence, deviations, blockers,
   and separate post-merge measurement handoff; and
8. no deferred architecture item is silently reopened.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified` from fresh evidence.
Branch publication, merge, cleanup, and worktree disposition remain separate
authorized actions.
