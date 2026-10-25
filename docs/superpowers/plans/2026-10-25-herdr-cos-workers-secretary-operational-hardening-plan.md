---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: herdr-cos-workers-secretary-operational-hardening
targets:
  - scripts/herdr_parallel_dispatch.py
  - scripts/project_os_runtime/admission.py
  - scripts/project_os_runtime/acceptance.py
  - scripts/project_os_runtime/reconciliation.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/project_os_runtime/submission_gate.py
  - scripts/herdr_main_launcher.py
  - scripts/secretary_live_runtime.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_benchmark_dispatch.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_project_os_runtime.py
  - tests/test_acceptance_handoff.py
  - tests/test_reconciliation.py
  - tests/test_project_os_reconciliation.py
  - tests/test_secretary_live_runtime.py
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - docs/superpowers/specs/2026-08-30-cos-canonical-work-coordination-spec.md
---

# Herdr CoS Workers Secretary Operational Hardening Plan

## Goal

Implement only the source-validated operational and correctness fixes from the
completed sequential `GPT-5.6-Sol` High and `GPT-6` High GitHub reviews of
`longdang193/project-OS-starter` at immutable commit
`ee0bb2898b582db60ccaf5553fae0ac037f09ca1`.

The implementation must preserve the personal-use architecture and its existing
safety boundaries: CoS remains the acceptance authority, Herdr remains the
transport and target-observation layer, worker execution remains bounded by the
attempt contract, receipts remain evidence rather than coordination truth, and
no automatic replay of an uncertain started attempt is introduced.

Review evidence is preserved at:

- `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter\review-output\2026-10-25-herdr-cos-workers-secretary\run-qit1l9\response.md`
- `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter\review-output\2026-10-25-herdr-cos-workers-secretary\run-VBfsNO\response.md`
- `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter\review-output\2026-10-25-herdr-cos-workers-secretary\batch-result.json`

The tracked workspace had no code changes to publish before review; the reviewed
remote `main` was already at the stated commit. The untracked review/runtime
artifacts remain outside the implementation scope.

## Implementation Outcomes

### Dispatch accounts for every admitted or deferred lane

`run_parallel()` schedules capacity-deferred lanes when admitted capacity is
released, without replaying a lane that already started. If interruption,
capacity, or a coordinator failure leaves a lane unstarted, the result and CLI
exit status identify the incomplete batch instead of reporting success. Parallel
admission keys concrete pane resources by session and pane; the literal `auto`
selector remains unresolved only during provisional admission, then the resolved
`(session, pane)` is atomically checked and reserved before side effects begin.
Receipt correlation requires complete mandatory assignment, task, and attempt
identity. Runtime Grant mismatch is a verification failure even when the
underlying process and resource cleanup are settled.

### Acceptance and integration use one evidence authority

Acceptance cannot emit an operationally authorized `PASS` that its own validator
would reject for missing assignment or checkpoint binding. Runtime Grant
verification and acceptance validation produce explicit, machine-readable
failure states. A repository policy that is explicitly bound and requires zero
checks is eligible without fabricated check evidence; configured required checks
remain strict and current.

### All material waits respect bounded operation ownership

Secretary launcher subprocesses, Herdr Git preflight commands, and evidence-file
locks have bounded deadlines. Timeout or lock contention preserves available
output and returns an explicit uncertain/reconciliation state; it never hangs the
caller indefinitely or silently claims retirement.

### Secretary avoids unnecessary workspace recreation without weakening isolation

The default Secretary probe first attempts the existing verified Herdr target
selection path. It creates a workspace only when no compatible target can be
verified, and it closes only a workspace created by that invocation. A malformed
unrelated pane record cannot poison every target-selection attempt: ambiguous
candidate reuse remains forbidden, while a fresh independently verified
allocation remains available. Dirty-workspace fingerprinting remains exact for
relevant identity, but unrelated oversized or unreadable artifacts do not make
previously persisted evidence permanently unrecoverable when a safe recovery
binding exists.

### Contracts, tests, and specifications stay aligned

Focused regression tests cover each changed failure mode, including deferred
scheduling, identity correlation, timeout classification, zero-check policies,
workspace reuse, malformed snapshots, and fingerprint recovery. The two owning
coordination specifications describe the resulting semantics without adding a
new coordinator, daemon, registry, browser owner, or retry path.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: `source inspection, focused code and test edits, owning-spec edits, declared Python checks, repository validation, and diff inspection`
- User-approval actions: `commit, push, pull request creation or update, merge, deletion of review/runtime artifacts, and changes outside the listed targets`
- Parallel ownership: `none`
- Sequential fallback: `dispatch correctness -> acceptance/reconciliation -> bounded waits and locks -> Secretary/Herdr reuse and recovery -> specification reconciliation -> final verification`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `ee0bb2898b582db60ccaf5553fae0ac037f09ca1` (reviewed source baseline)
- Plan commit: `050292dc691145ef78b0107fb5bafe5c813cb9f3`
- Expected workspace: `implementation changes remain within declared targets; preserve untracked .playwright-mcp, .review-profile, .runtime, node_modules, and review-output artifacts`
- Next action: `run fresh completion verification before any plan-status transition; commit/push remain separately authorized`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused dispatch and identity tests | `135 passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | acceptance, handoff, and reconciliation tests | `81 passed` |
| Task 3 | `completed` | current | `codex` | Tasks 1–2 | timeout and lock-contention tests | `89 dispatch passed; launcher timeout and lock contention passed` |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | Secretary/Herdr reuse and recovery tests | `516 passed, 2 skipped; verified reuse had zero workspace allocation` |
| Task 5 | `completed` | current | `codex` | Tasks 1–4 | specification, repository, and final verification checks | `733 passed, 2 skipped; repository/planning validators and diff check passed` |

## Validated Findings And Decisions

The following findings were retained because the completed model responses cited
the pinned revision and the source supports the stated behavior. Model
attribution is retained for auditability; implementation is not required to
reproduce model wording.

| Severity | Finding | Source evidence | Decision |
| --- | --- | --- | --- |
| P1 | Capacity-deferred lanes can be skipped while the CLI exits successfully. | `scripts/project_os_runtime/admission.py:69-70`; `scripts/herdr_parallel_dispatch.py:1065-1066`, `1117-1124`, `1144-1152`, `1190-1195` | Add bounded scheduling of never-started deferred lanes and explicit incomplete-batch exit evidence. `[GPT-5.6-Sol]` |
| P1 | Acceptance can emit `PASS` without fields required by its validator. | `scripts/project_os_runtime/acceptance.py:127-154`, `196-319` | Share required binding validation before authorization. `[GPT-6]` |
| P1 | Grant mismatch is recorded but can leave dispatch successful. | `scripts/herdr_parallel_dispatch.py:994-1029`, `1190-1195` | Set explicit verification failure and include it in exit classification while preserving settled capacity. `[GPT-6]` |
| P2 | Pane admission uses only the pane token, so session boundaries and `auto` selectors collide. | `scripts/herdr_parallel_dispatch.py:364-396`; launcher ownership is session-plus-pane scoped at `scripts/herdr_main_launcher.py:810-813` | Use resolved `(session, pane)` identity; do not treat `auto` as a concrete pane. `[GPT-5.6-Sol]` |
| P2 | Missing receipt identity fields count as matching. | `scripts/herdr_parallel_dispatch.py:713-733` | Require non-empty mandatory identity values. `[GPT-6]` |
| P2 | Secretary launcher subprocess can block before cleanup. | `scripts/secretary_live_runtime.py:3709-3716`, `3798-3814` | Add a deadline-derived subprocess watchdog and uncertain-ownership result. `[GPT-6]` |
| P2 | Git preflight commands are not bounded by the dispatch deadline. | `scripts/herdr_parallel_dispatch.py:221-250`, `772-793` | Pass remaining budget into each Git subprocess and classify timeout as launch uncertainty. `[GPT-6]` |
| P2 | Evidence release can block indefinitely on an OS lock. | `scripts/project_os_runtime/results.py:27-52`; `scripts/project_os_runtime/acceptance.py:541-543` | Add bounded non-blocking lock acquisition and preserve evidence on contention. `[GPT-5.6-Sol]` |
| P2 | Verified zero-check repository policies are blocked by `bool(latest)`. | `scripts/project_os_runtime/reconciliation.py:58-66`, `81-84`, `197-231` | Treat an explicitly bound empty required-check set as satisfied. `[GPT-6]` |
| P2 | Dirty-workspace uncertainty can make persisted evidence unrecoverable. | `scripts/secretary_live_runtime.py:2136-2206`, `343-350`, `3232-3249` | Restrict identity uncertainty to bound workspace inputs and add safe persisted-evidence recovery. `[GPT-6]` |
| P2 | A malformed unrelated pane can block all automatic target selection. | `scripts/herdr_main_launcher.py:1063-1082`, `1284-1312` | Isolate malformed records and allow only a new independently verified allocation. `[GPT-5.6-Sol, GPT-6]` |
| P3 | Secretary creates and closes a workspace for every default auto probe. | `scripts/secretary_live_runtime.py:668-702`, `3798-3814`, `3900-3901` | Reuse verified targets before creation; close only invocation-owned workspaces. `[GPT-5.6-Sol, GPT-6]` |
| P3 | A shared discovery budget lets one slow pane starve later candidates. | `scripts/herdr_main_launcher.py:132-133`, `974-1001`, `1084-1109` | Add per-candidate caps and preserve the allocation reserve. `[GPT-5.6-Sol]` |

Out of scope: production-scale orchestration, durable runtime registries,
background daemons, expanded concurrency, automatic retries of uncertain work,
new browser/context owners, model substitution, and unrelated cleanup of
untracked artifacts.

## Task Breakdown

### Task 1: Correct dispatch admission, scheduling, and receipt evidence

**Purpose:**
- Ensure every lane is either executed, explicitly deferred/incomplete, or rejected with a truthful terminal result, while preserving no-replay semantics.

**Task Function:**
- Root-cause correction for Herdr parallel admission and settlement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared dispatch ownership, high correctness impact, and no safe disjoint writer split.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests and source-level proof are lead-owned for this bounded task.

**Specification Coverage:**
- Covers capacity accounting, session/pane ownership, complete receipt correlation, grant verification, and truthful CLI exit state.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/admission.py:classify_admission`; `scripts/herdr_parallel_dispatch.py:admit_lanes`, `run_parallel`, `_receipt_correlation_matches`, `run_lane`, `main`
- Modify: `scripts/project_os_runtime/admission.py:classify_admission`; `scripts/herdr_parallel_dispatch.py:admit_lanes`, `run_parallel`, `_receipt_correlation_matches`, `run_lane`, `main`
- Verify: `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_attempt_contract.py`

**Dependencies:**
- Reviewed base `ee0bb2898b582db60ccaf5553fae0ac037f09ca1`
- Existing admission and lifecycle tests remain the behavioral baseline.

**Authority:**
- Preauthorized local actions: edit the listed dispatch/admission symbols and their focused tests; run the declared dispatch test commands.
- Stop for: any need to alter worker ownership, introduce automatic replay, change the attempt contract, or modify files outside Task 1 ownership.

**Steps:**
- [x] Step 1: Add one canonical resource-key helper that uses `(session, pane)` for concrete selectors and represents `auto` as unresolved during provisional admission; before any lane side effect, resolve the selector and atomically check/reserve the concrete `(session, pane)` through the existing ownership mechanism. A collision defers or rejects only the never-started lane, and the reservation is released at settlement. Update duplicate/conflict admission and tests for cross-session, auto-selector, post-resolution collision, and reservation-release cases. If existing launcher semantics already provide the atomic check/reservation, cite that mechanism instead of adding a registry.
- [x] Step 2: Replace one-shot admission submission with a bounded pending-deferred queue. Submit only never-started deferred lanes as admitted futures complete; record `refilled` lanes and leave interrupted/unstarted lanes explicitly deferred. Do not resubmit a lane after `run_lane()` starts.
- [x] Step 3: Make `_receipt_correlation_matches()` reject absent mandatory assignment/task/attempt identities; set `failure_kind="grant_mismatch"` when grant evidence is unverified; include grant verification and remaining deferred lanes in the CLI exit classification.
- [x] Step 4: Update existing deferred/refill, grant-digest, stale-assignment, timeout, callback, and CLI exit tests; add assertions for exact result fields and event ordering.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_attempt_contract.py`
- Expected: deferred lanes are either refilled exactly once or reported incomplete, missing identities never correlate, grant mismatch is non-zero, and existing sibling/timeout evidence remains intact.

**Exit Criteria:**
- Dispatch results account for all lanes, no started attempt is replayed, and focused dispatch tests pass.

### Task 2: Unify acceptance validation and repository check policy

**Purpose:**
- Remove contradictory acceptance authority and allow only explicitly verified zero-check policies without weakening configured-check validation.

**Task Function:**
- Contract convergence across CoS acceptance and reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: canonical acceptance/reconciliation ownership and direct contract evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing acceptance and reconciliation suites provide direct boundary proof.

**Specification Coverage:**
- Covers CoS acceptance authority, assignment/checkpoint binding, review/current-head reconciliation, and zero-required-check policy semantics.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance.py:validate_acceptance_decision`, `evaluate_acceptance`; `scripts/project_os_runtime/reconciliation.py:RemotePrEvidence.checks_current`, `checks_satisfy_policy`, `_integrate`
- Modify: `scripts/project_os_runtime/acceptance.py:validate_acceptance_decision`, `evaluate_acceptance`; `scripts/project_os_runtime/reconciliation.py:checks_current`, `checks_satisfy_policy`
- Verify: `tests/test_project_os_runtime.py`, `tests/test_acceptance_handoff.py`, `tests/test_reconciliation.py`, `tests/test_project_os_reconciliation.py`

**Dependencies:**
- Task 1 result fields and grant verification remain stable.
- Existing acceptance handoff remains the only transition-authorizing caller.

**Authority:**
- Preauthorized local actions: edit the listed acceptance/reconciliation symbols and their focused tests; run the declared acceptance and reconciliation commands.
- Stop for: any change that grants acceptance authority to Herdr, workers, Secretary, or a new runtime registry.

**Steps:**
- [x] Step 1: Extract or reuse one binding-validation path so `evaluate_acceptance()` cannot construct an authorized `PASS` with missing assignment or checkpoint proof required by `validate_acceptance_decision()`.
- [x] Step 2: Preserve the existing `BLOCKED` versus `FAIL` distinction and ensure every returned decision is validated before `task_transition.authorized` becomes true.
- [x] Step 3: Change `checks_current` so a policy-bound empty `required_checks` set is satisfied when there are no ambiguous required checks; retain head-SHA and successful-conclusion checks for every named required check.
- [x] Step 4: Add regression cases for missing assignment/checkpoint fields, accepted handoff rejection, bound zero-check policy, missing policy source, stale required checks, and old-head evidence.

**Verification:**
- [x] `py -m pytest -q tests/test_project_os_runtime.py tests/test_acceptance_handoff.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py`
- Expected: no authorized `PASS` fails the canonical validator, zero-check policy passes only with a valid bound policy, and configured checks remain strict.

**Exit Criteria:**
- Acceptance and reconciliation have one consistent evidence contract with focused regression coverage.

### Task 3: Bound subprocess and evidence-lock waits

**Purpose:**
- Keep launcher, Git preflight, and evidence publication/release operations inside their declared deadlines and preserve an explicit recovery state on timeout.

**Task Function:**
- Deadline and failure-boundary hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-module runtime ownership and material backend failure behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct mocked subprocess/lock tests and backend verification remain lead-owned.

**Specification Coverage:**
- Covers attempt deadline containment, worker/launcher observation boundaries, evidence preservation, and reconciliation-required failure handling.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:run_probe`; `scripts/herdr_parallel_dispatch.py:launch_preflight`, `run_lane`; `scripts/project_os_runtime/results.py:evidence_path_lock`; all current lock consumers in `acceptance.py`, `secretary_results.py`, and `submission_gate.py`
- Modify: `scripts/secretary_live_runtime.py:run_probe`; `scripts/herdr_parallel_dispatch.py:launch_preflight`; `scripts/project_os_runtime/results.py:evidence_path_lock`; lock-boundary callers in `scripts/project_os_runtime/acceptance.py`, `scripts/project_os_runtime/secretary_results.py`, and `scripts/project_os_runtime/submission_gate.py`
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_project_os_runtime.py`, `tests/test_acceptance_handoff.py`

**Dependencies:**
- Task 1 defines the dispatch failure fields that timeout and verification states must use.
- Task 2 defines the acceptance/reconciliation state that preserves uncertain evidence.

**Authority:**
- Preauthorized local actions: edit the listed timeout/lock boundaries and tests; add only the smallest exception/result plumbing needed to preserve existing evidence contracts.
- Stop for: any unbounded wait, blind cleanup claim, automatic retry, or deletion of evidence after timeout/lock contention.

**Steps:**
- [x] Step 1: Derive the Secretary launcher subprocess timeout from the active attempt/probe deadline, catch `TimeoutExpired`, preserve partial stdout/stderr and submission evidence, and return `reconciliation_required`/unknown ownership before the existing cleanup path.
- [x] Step 2: Pass remaining dispatch time into each `git merge-base --is-ancestor` subprocess in `launch_preflight`; convert timeout to a deterministic blocker and prevent later checks from exceeding the deadline.
- [x] Step 3: Extend `evidence_path_lock()` with bounded non-blocking acquisition using the same timeout contract on Windows and POSIX. Add an explicit lock-timeout error/result; make release callers preserve the artifact and report deferred release instead of hanging.
- [x] Step 4: Test launcher timeout, Git timeout, lock contention, successful release, idempotent publication, cleanup verification, and preservation of partial evidence.

**Verification:**
- [x] `py -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_project_os_runtime.py tests/test_acceptance_handoff.py`
- Expected: every forced timeout returns within the declared bound, preserves evidence, reaches cleanup/reconciliation, and never reports confirmed retirement without proof.

**Exit Criteria:**
- No reviewed material wait can block indefinitely outside its declared attempt/operation deadline.

### Task 4: Reuse verified Herdr targets and narrow Secretary uncertainty

**Purpose:**
- Remove unnecessary workspace/window recreation while preserving isolation, ownership-aware cleanup, and fail-closed handling of ambiguous targets.

**Task Function:**
- Cross-component target-selection and recovery optimization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared Herdr/Secretary behavior, operational overhead, and existing integration tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing Herdr and Secretary mocks can prove reuse, allocation, cleanup, and latency-bound behavior.

**Specification Coverage:**
- Covers target ownership, auto selector semantics, workspace lifecycle, malformed snapshot handling, dirty-workspace identity, and bounded discovery economics.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_resolve_target_selector`, `_inspect_auto_candidate`, allocation refresh validation; `scripts/secretary_live_runtime.py:_prepare_herdr_target`, `_create_herdr_workspace`, `run_probe`, `_read_only_workspace_identity`, `ResolvedRequest`
- Modify: `scripts/herdr_main_launcher.py:_resolve_target_selector` and allocation refresh validation; `scripts/secretary_live_runtime.py:_prepare_herdr_target`, `run_probe`, `_read_only_workspace_identity`, reuse decision helpers
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Task 1 establishes session/pane identity semantics.
- Task 3 provides timeout behavior used by target discovery and probe launch.
- Existing workspace-close verification remains authoritative for invocation-owned resources.

**Authority:**
- Preauthorized local actions: edit the listed Herdr/Secretary target and fingerprint symbols and their focused tests; run deterministic mock-based operational checks.
- Stop for: reuse of an unverified/ambiguous pane, global cleanup of user workspaces, or a new long-lived browser/window owner.

**Steps:**
- [x] Step 1: Route Secretary auto/auto probe resolution through the existing verified Herdr candidate-selection semantics, preserving named-session behavior and creating a workspace only after compatible reuse is exhausted.
- [x] Step 2: Set `workspace_created` and `workspace_id` only for the current invocation's allocation; keep the existing `finally` close path limited to that owned workspace and retain unknown cleanup evidence when close verification fails.
- [x] Step 3: Change malformed snapshot handling so malformed records that cannot be tied to the requested workspace are excluded from candidate reuse and trigger a fresh independently verified allocation path rather than poisoning every auto launch. Never reuse an ambiguous record.
- [x] Step 4: Add per-candidate discovery caps while retaining the five-second total and one-second allocation reserve; prioritize focused/likely reusable candidates before stale candidates.
- [x] Step 5: Make dirty-workspace identity uncertainty local to relevant request/output inputs. When persisted native evidence has a valid binding and only unrelated oversized/unreadable artifacts are uncertain, preserve the safe recovery path; retain hard blocking for uncertainty in the bound workspace inputs.
- [x] Step 6: Add mock assertions for zero workspace-create/close calls on verified reuse, one create/close pair on allocation, malformed unrelated snapshot fallback, per-candidate timeout behavior, and fingerprint recovery. Record command-count/elapsed-time evidence for the same probe workload before and after the change.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py`
- Expected: repeated auto probes reuse a verified target without workspace recreation, allocation remains isolated and owned, malformed snapshots do not cause false global failure, and discovery stays within total and per-candidate bounds.
- [x] Operational metric inspection: compare the existing mock probe workload with the changed workload; require zero create/close calls on the verified-reuse case, unchanged cleanup proof, and no increase in launcher command count for the reused case.

**Exit Criteria:**
- Secretary avoids unnecessary target recreation while all reused and allocated resources retain explicit ownership and cleanup evidence.

### Task 5: Reconcile specifications and perform final verification

**Purpose:**
- Make the owning specifications match the implemented contracts and produce fresh repository-level proof before handoff.

**Task Function:**
- Durable contract reconciliation and completion verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: canonical documentation ownership and final evidence review.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is lead-owned and command-backed.

**Specification Coverage:**
- Covers the dispatch specification's queued/sequential capacity semantics, deadline and retry boundaries, evidence/continuation boundary, and the CoS canonical coordination specification's acceptance and ownership rules.

**Required Skills:**
- `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`, `docs/superpowers/specs/2026-08-30-cos-canonical-work-coordination-spec.md`, all changed source/tests, Git status
- Modify: the two listed specifications only where their current text conflicts with the implemented deferred scheduling, evidence verification, timeout, target-reuse, and zero-check semantics
- Verify: all task-owned files and generated/test contracts

**Dependencies:**
- Tasks 1–4 complete with focused proof accepted.

**Authority:**
- Preauthorized local actions: update the two owning specifications, run final declared checks, inspect diff/status, and reconcile this plan's task ledger.
- Stop for: specification text that would weaken fail-closed ownership, any unrecorded source/test drift, or any need to delete preserved review/runtime artifacts.

**Steps:**
- [x] Step 1: Update the dispatch specification to state that never-started capacity-deferred lanes may be bounded-refilled, started attempts are never replayed automatically, and leftover deferred lanes produce explicit incomplete evidence.
- [x] Step 2: Update the CoS specification to state that acceptance uses one canonical binding validator and that verified zero-check policies are distinct from unavailable check evidence.
- [x] Step 3: Run focused suites from Tasks 1–4, repository contract validation, syntax checks, planning validation, and whitespace validation.
- [x] Step 4: Confirm the tracked diff contains only declared targets and preserved untracked review/runtime artifacts remain untouched. Keep plan status `proposed` until a later execution and verification workflow proves completion; an unimplemented P1/P2 finding cannot be closed as a generic execution deferral.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_project_os_runtime.py tests/test_acceptance_handoff.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py`
- [x] `py -B scripts/validate_repo_contracts.py`
- [x] `py -B scripts/validate_planning_lifecycle.py`
- [x] `git diff --check`
- Expected: all focused tests and repository checks pass; no untracked review/runtime artifact is deleted or modified by cleanup.

**Exit Criteria:**
- Every retained finding has an implemented outcome, focused proof, and owning-spec alignment. A finding may leave this plan only through an explicit user-approved re-scope that removes it from the retained findings; an unimplemented P1/P2 finding remains open and prevents completion.

## Verification

Run after implementation and before changing this plan to `completed`:

- `py -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_project_os_runtime.py tests/test_acceptance_handoff.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py tests/test_secretary_live_runtime.py tests/test_secretary_live_pilot.py`
- `py -B scripts/validate_repo_contracts.py`
- `py -B scripts/validate_planning_lifecycle.py`
- `git diff --check`

These commands are final implementation proof, not evidence that the proposed
plan itself is complete. A later execution must also run
`skill-verification-before-completion` against fresh outputs before setting
`status: completed`.

## Completion Criteria

The plan is ready for completion verification when:

1. Every retained P1–P3 finding has an implemented correction. An explicit user-approved re-scope may remove a finding from the retained set before completion verification; a generic execution deferral does not satisfy this criterion, and an unresolved P1/P2 finding prevents completion.
2. No started attempt is automatically replayed; never-started deferred work is either bounded-refilled or reported incomplete.
3. Acceptance, grant, receipt, and reconciliation evidence have one consistent authority and truthful exit states.
4. All material subprocess, Git, discovery, and evidence-lock waits are deadline-bounded.
5. Secretary reuses a verified target before creating a workspace and closes only invocation-owned resources.
6. Malformed snapshots and dirty-workspace uncertainty cannot cause unsafe reuse or permanent loss of safely bound persisted evidence.
7. Focused tests, repository validation, planning validation, and `git diff --check` pass from the implementation base.
8. The two owning specifications match the final behavior.
9. `skill-verification-before-completion` returns `verified` from fresh evidence before plan status changes to `completed`.

## Stop Conditions

- Stop if the reviewed base commit changes before implementation begins; reconcile the plan against the new immutable revision.
- Stop if a proposed change requires automatic retry of an uncertain started attempt, a second coordination authority, a new browser/window owner, hidden-state assumptions, or weakening exact identity checks.
- Stop if a timeout cannot prove process/resource retirement; preserve evidence and return reconciliation-required state.
- Stop if a lock timeout would delete or overwrite evidence; preserve the artifact and surface contention.
- Stop if a malformed target cannot be proven unrelated to the requested workspace; do not reuse it and use only the independently verified allocation path.
- Stop if execution discovers a contract or interface conflict not resolved by the listed owning specifications; use `skill-spec-drafting` before changing this plan.

## Handoff

After approval, activate the plan through `skill-executing-plans` with one lead
controller and the task order in the ledger. Keep the completed GitHub review
artifacts read-only and preserved. Do not rerun the completed model submissions
unless the user explicitly authorizes a new GitHub review. Use
`skill-verification-before-completion` before changing plan status to
`completed`; Git commit, push, pull request, merge, and cleanup remain separate
explicitly authorized actions.

