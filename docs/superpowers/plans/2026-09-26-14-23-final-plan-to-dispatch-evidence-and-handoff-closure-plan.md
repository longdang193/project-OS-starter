---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
name: final-plan-to-dispatch-evidence-and-handoff-closure
targets:
  - scripts/project_os_runtime/plan_preparation.py
  - tests/test_plan_preparation.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-09-26-13-36-final-plan-to-dispatch-closure-plan.md
  - docs/superpowers/plans/2026-09-26-14-23-final-plan-to-dispatch-evidence-and-handoff-closure-plan.md
---

# Final Plan-to-Dispatch Evidence and Handoff Closure

## Verdict Review

The supplied verdict is supported by merged `origin/main` at
`e90bd2fecd9a4f2ff82557e87c9bf2780f399165`.

Current source confirms two residual issues:

- `PlanGraph` extracts only `Required skills` from `Execution Approach`, while
  `_worker_brief()` labels that value as all applicable shared constraints.
- The evidence fixture derives `manual_lane` from `dict(plan_lane)` and counts
  generated descriptor keys as manual plan-owned inputs.

The verdict is correct to require one final closure patch. It is not correct to
expand scope into scheduler, lifecycle, admission, authority, retry, memory,
or intra-invocation optimization work. Those remain follow-up work after this
plan closes the evidence and handoff contracts.

## Goal

Close plan-to-dispatch handoff and evidence contracts without changing
preparation ownership, lifecycle, authority, freshness, settlement, recovery,
or acceptance behavior.

## Objective

Finish plan-to-dispatch closure with two bounded corrections:

1. Deliver deterministic canonical plan-wide execution constraints to workers.
2. Make comparison evidence measure independently authored caller inputs and
   label fixture-only zeros and timing limitations accurately.

Preserve existing preparation ownership, `PreparedLane`, admission, launch
freshness, lifecycle, settlement, recovery, acceptance, descriptor-file
compatibility, concurrency limits, and direct execution.

## Implementation Outcomes

### Complete shared-constraint handoff

Replace the single `PlanGraph.required_skills` channel with one ordered
`PlanGraph.shared_constraints` collection of `(label, value)` pairs. Parse only
these named bullets from the canonical `Execution Approach` section, in this
fixed order:

1. `Required skills`
2. `Preauthorized local actions`
3. `User-approval actions`
4. `Parallel ownership`

`Parallel ownership` is current plan format's shared-write/ownership field.
Ignore `Mode`, `Coordination`, `Isolation`, `Commit policy`, `Sequential
fallback`, `Next action`, `Blockers`, review history, and arbitrary prose.

Render each parsed constraint once under `Applicable explicit shared
constraints`. Keep task-local `Authority`, `Verification`, and `Exit Criteria`
inside the selected task section. Do not add semantic extraction, retrieval,
LLM summarization, or a second authority layer.

### Defensible outcome evidence

Build manual and plan inputs independently. Count caller-owned selectors,
runtime-binding fields, and manual plan-derived execution fields at their input
boundaries. Exclude generated fields such as assignment IDs, hashes, normalized
grant projections, plan provenance, and binding digests from manual-savings
claims unless the caller explicitly supplied them.

Compare final launcher/runtime semantics, but label fake-worker model calls,
missing-context events, and recovery paths as fixture invariants. Keep measured
timing as descriptive because manual and plan paths have different freshness
and provenance validation contracts. Do not claim token savings, production
latency savings, fewer real-world context requests, or fewer production
recovery events.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `clean managed worktree rooted at origin/main`
- Base commit: `e90bd2fecd9a4f2ff82557e87c9bf2780f399165`
- Commit policy: `no commits during execution; commit only after verification returns verified and user authorizes Git disposition`
- Preauthorized local actions: inspect and edit listed source/tests/docs/plan files, create the named clean worktree, run listed local checks, synchronize generated runtime surfaces through approved scripts, and record measured evidence
- User-approval actions: commit, push, pull request, merge, external authentication, destructive cleanup, discard, and edits outside listed targets
- Parallel ownership: `none`; parser, launcher payload, evidence fixture, and plan reconciliation overlap
- Sequential fallback: `Task 1, then Task 2, then Task 3 and final verification`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/final-plan-to-dispatch-evidence-and-handoff-closure`
- Expected workspace: `clean managed worktree from origin/main; preserve unrelated checkout artifacts and do not delete or rewrite them`
- Next action: `execute Task 1: add deterministic shared-constraint projection`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | isolated worktree | `codex` | none | shared constraints parse and reach final launcher payload exactly once | pending |
| Task 2 | `pending` | same worktree | `codex` | Task 1 | independent manual baseline and corrected evidence record pass | pending |
| Task 3 | `pending` | same worktree | `codex` | Task 2 | full tests, validators, generated-surface checks, and plan reconciliation pass | pending |

Only the lead controller updates this ledger. A checked item records accepted
proof, not activity.

## Scope Boundaries

Preserve one plan-preparation owner, existing `PreparedLane` fields, runtime
authority ownership, admission states, launch-bound freshness, lifecycle and
settlement facts, recovery rules, CoS acceptance, descriptor compatibility,
concurrency limits, direct execution, and current CI workflows.

Do not implement readiness/brief deduplication, duplicate plan-load removal,
runtime-fact reuse, Git subprocess consolidation, runtime-binding reduction,
ready-task projections, task-specific freshness, experience handoff,
topology-aware execution, persistent scheduling, learned routing, general
memory, or a new worker-context subsystem.

## Task Breakdown

### Task 1: Project canonical shared execution constraints

**Purpose:**
- Make final worker handoff complete without broad prose extraction or a new authority owner.

**Task Function:**
- Extend canonical plan parsing and worker-brief composition at the existing plan-preparation owner.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small deterministic parser and payload change with direct launcher-contract impact.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused payload assertions and final source/contract validators.

**Specification Coverage:**
- Required skills, preauthorized actions, user-approval actions, and parallel ownership are parsed only from named canonical bullets.
- Shared constraints reach the worker once and preserve source order.
- Task-local `Authority`, `Verification`, and `Exit Criteria` are not duplicated.
- Later tasks, peer sections, history, and planning-only metadata stay absent.
- Existing `PreparedLane` and runtime-binding ownership remain unchanged.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/plan_preparation.py:PlanGraph`, `parse_plan`, `prepare_task`, `_bounded_task_text`, `_worker_brief`, `_prepare_plan_lanes`
- Inspect: `scripts/project_os_runtime/lane.py:PreparedLane`, `prepare_lane`
- Modify: `scripts/project_os_runtime/plan_preparation.py:PlanGraph`, `parse_plan`, `prepare_task`, `_worker_brief`, `_prepare_plan_lanes`
- Modify: `tests/test_plan_preparation.py` canonical plan fixture and final launcher-payload regression
- Modify: `docs/operating_system/runtime/runtime-surfaces.md` worker-handoff boundary if source contract wording requires reconciliation

**Dependencies:**
- `origin/main` at `e90bd2fecd9a4f2ff82557e87c9bf2780f399165`
- Existing `_section()` and `_task_contracts()` parsing helpers
- Existing `_launcher_command()` and fake launcher seams

**Authority:**
- Preauthorized local actions: edit named parser, worker-brief, runtime-doc, and focused test surfaces; run focused tests and source validators
- Stop for: arbitrary prose extraction, semantic retrieval, `PreparedLane` schema changes, admission/lifecycle changes, or new context infrastructure

**Steps:**
- [ ] Step 1: Replace `PlanGraph.required_skills` with ordered `shared_constraints` derived from the four exact `Execution Approach` bullet labels; preserve empty-field omission and fixed order.
- [ ] Step 2: Update `prepare_task()` and `_worker_brief()` to use the shared collection, render one labeled bullet per constraint, and avoid duplicate task-local contract sections.
- [ ] Step 3: Extend the active plan fixture with all four canonical fields plus unrelated planning metadata, then capture the final `--task` value through the existing launcher seam.
- [ ] Step 4: Assert presence of plan goal, complete selected task contract, accepted prerequisite revision, all four shared constraints, and non-duplicative required proof; assert absence of later tasks, unrelated sections, histories, and duplicate `Purpose`, `Authority`, `Verification`, and `Exit Criteria`.

**Verification:**
- `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py`
- Expected: final worker payload contains every allowlisted shared constraint once and no unrelated plan text.

**Exit Criteria:**
- Canonical plan input delivers complete deterministic worker instructions without changing runtime authority or lane schemas.

### Task 2: Correct independent measurement and historical evidence

**Purpose:**
- Prove coordination-input reduction without treating copied descriptors or generated keys as manual savings.

**Task Function:**
- Replace the derived manual arm in the existing evidence fixture, classify input fields, and reconcile the completed closure plan.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one bounded evidence fixture owns comparison semantics and historical plan correction.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused test assertions plus fresh full-suite and validator output.

**Specification Coverage:**
- Manual descriptor is independently authored and never copied from `plan_lane`.
- Plan selectors, runtime-binding fields, manual plan-derived fields, and generated fields are separate categories.
- Final semantic execution inputs remain equivalent where expected.
- Fake-worker zeros are fixture properties, not production claims.
- Timing asymmetry is recorded without a latency conclusion.
- Completed plan evidence states the corrected claim and measured values.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `tests/test_plan_preparation.py:test_manual_and_plan_inputs_record_equivalent_dispatch_evidence`, `_binding`, `_active_plan`
- Inspect: `scripts/project_os_runtime/lane.py:_REQUIRED_FIELDS`, `prepare_lane`
- Modify: `tests/test_plan_preparation.py` independent manual baseline, field-category counters, semantic-equivalence assertions
- Modify: `docs/superpowers/plans/2026-09-26-13-36-final-plan-to-dispatch-closure-plan.md` evidence table and claim wording only

**Dependencies:**
- Task 1 shared-constraint payload is complete
- Existing `run_parallel()`, `run_parallel_from_plan()`, and fake `Popen` seam
- Existing `PreparedLane` contract remains unchanged

**Authority:**
- Preauthorized local actions: edit the named evidence fixture and completed plan evidence; run focused/full tests and validators
- Stop for: copied treatment data, invented counts, production-performance claims, live model calls, or new instrumentation services

**Steps:**
- [ ] Step 1: Author `manual_descriptor` directly with the legacy lane inputs required by `prepare_lane()`, including explicit task, executor/profile, dependency, grant, capability, runtime, and plan-derived values; do not derive it from `plan_lane`.
- [ ] Step 2: Count selectors separately from top-level runtime-binding fields and manual plan-derived execution fields; exclude assignment IDs, hashes, normalized grants, provenance, binding digests, and other generated bookkeeping.
- [ ] Step 3: Run manual and canonical plan inputs through the same fake launcher, compare task/runtime/grant/capability/write-scope/resource/prerequisite semantics, and record dispatch commands, launcher subprocesses, fake model calls, fake context events, fake recovery paths, preparation operations, and measured preparation-to-launch-check time.
- [ ] Step 4: Update the completed closure plan to state exact observed categories and values, label fake-worker zeroes as fixture invariants, explain validation asymmetry, and claim only elimination of identified plan-derived caller reconstruction.

**Verification:**
- `python -m pytest -q tests/test_plan_preparation.py::test_manual_and_plan_inputs_record_equivalent_dispatch_evidence -s`
- `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py`
- Expected: independent inputs converge semantically; no extra fake launch/model/context/recovery step appears; evidence excludes generated-field savings claims.

**Exit Criteria:**
- Evidence proves the narrow coordination-input claim and makes no unsupported production latency or token claim.

### Task 3: Reconcile contracts and close plan

**Purpose:**
- Prove implementation, documentation, generated runtime surfaces, and historical evidence agree before completion.

**Task Function:**
- Run final checks, update the plan ledger, and set completed status only after fresh verification returns `verified`.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: sequential fan-in task with no independent write owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository validators and CI provide independent contract evidence.

**Specification Coverage:**
- Focused and broad tests pass.
- Planning, repository-contract, adapter-sync, and runtime-drift checks pass.
- Runtime documentation and completed-plan evidence match source behavior.
- No generated surface drifts after canonical changes.
- No P1 optimization enters this closure.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all files listed in this plan and current `origin/main` history
- Modify: `docs/superpowers/plans/2026-09-26-14-23-final-plan-to-dispatch-evidence-and-handoff-closure-plan.md` ledger/status only after proof

**Dependencies:**
- Tasks 1 and 2 complete
- `origin/main` remains the base

**Authority:**
- Preauthorized local actions: run listed checks, synchronize approved generated runtime surfaces, reconcile this plan, and inspect Git state
- Stop for: any failed required check, stale generated output, unrelated dirty change, or scope expansion

**Steps:**
- [ ] Step 1: Run focused tests, full `python -m pytest -q`, planning lifecycle validation, repository contract validation, adapter sync check, runtime drift check, and `git diff --check`.
- [ ] Step 2: Inspect final changed-file scope, confirm no `TODO`/`TBD`/placeholder text, and confirm all plan targets have one canonical owner.
- [ ] Step 3: Record exact command outputs and any approved environmental deviation; only then mark Task 3 and plan frontmatter `status: completed`.

**Verification:**
- `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py`
- `python -m pytest -q`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`
- Existing `repo-contracts.yml` and `runtime-contracts.yml` checks on Ubuntu and Windows
- Expected: all checks pass; no new workflow is added.

**Exit Criteria:**
- Final handoff, evidence, runtime docs, generated surfaces, and plan status agree with current source and fresh verification.

## Verification

- `python -m pytest -q tests/test_plan_preparation.py tests/test_herdr_parallel_dispatch.py`
- `python -m pytest -q`
- `python scripts/validate_planning_lifecycle.py --repo-root . --strict`
- `python scripts/validate_repo_contracts.py --repo-root .`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`
- Existing `repo-contracts.yml` and `runtime-contracts.yml` checks on Ubuntu and Windows

Expected: all checks pass; no generated surface drifts; no new workflow is added.

## Completion Criteria

### Handoff

- Full selected task contract reaches worker.
- Plan goal and accepted prerequisite identities reach worker.
- Four canonical shared execution constraints reach worker exactly once.
- No task-local section is duplicated.
- No arbitrary prose, unrelated history, or planning-only metadata reaches worker.

### Measurement

- Manual baseline is independently authored.
- Caller-supplied selectors and fields are counted at input boundaries.
- Manual plan-derived values are listed explicitly.
- Generated/provenance fields are excluded from savings claims.
- Semantic execution inputs remain equivalent where expected.
- Fake-worker zeros are labeled fixture invariants.
- Timing caveats state validation-contract asymmetry and avoid latency claims.

### Architecture

No changes to `prepare_plan_lanes` ownership, `PreparedLane`, admission,
freshness, lifecycle, settlement, recovery, acceptance, descriptor
compatibility, concurrency, direct execution, scheduler, or durable state.

## Follow-up, Not Closure Gate

After this plan is verified and merged, consider a separate plan for
intra-invocation deduplication in this order: build `PreparedTask` once, read
and parse the plan once, reuse stable runtime facts while rechecking mutable
facts, then measure duplicate Git subprocesses before consolidating them.
Runtime-binding reduction, ready-task projections, task-specific freshness,
experience handoff, topology-aware execution, persistent scheduling, learned
routing, and general memory remain deferred.

## Handoff

Use `skill-plan-document-reviewer` before approval. After approval, hand off to
`skill-executing-plans`. Completion requires fresh `verified` output from
`skill-verification-before-completion`; Git disposition remains a separate
explicit authorization.
