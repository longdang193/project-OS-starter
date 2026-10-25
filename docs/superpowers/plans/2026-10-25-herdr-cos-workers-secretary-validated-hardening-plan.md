---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
distribution_tier: project
name: herdr-cos-workers-secretary-validated-hardening
targets:
  - scripts/herdr_main_launcher.py
  - scripts/project_os_runtime/capabilities.py
  - scripts/project_os_runtime/results.py
  - scripts/benchmark_secretary_architecture.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_evidence_release.py
  - tests/test_secretary_benchmark.py
  - tests/test_benchmark_operational_comparison.py
  - tests/test_secretary_live_runtime.py
  - docs/usage.md
  - docs/configuration.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - README.md
---

# Herdr CoS Workers Secretary Validated Hardening Plan

## Goal

Correct only the source-validated operational bottlenecks and lifecycle
classification defects identified by the completed sequential `GPT-5.6-Sol`
High and `GPT-6` High GitHub reviews of
`longdang193/project-OS-starter` at immutable commit
`9a90cba3498d1290601bb0702c4c8671b0dfe6a5`.

The implementation must preserve the personal-use architecture and its safety
boundaries: CoS remains the acceptance authority, Herdr remains the target and
transport boundary, worker execution remains bounded by its existing contracts,
uncertain started attempts are reconciled rather than replayed, and ownership
locks and identity checks remain fail-closed.

The earlier review-run anomaly (`Prompt was not visibly entered`) was traced to
formatted-prompt handling and fixed before this review at commit `9a90cba`, with
regression coverage in `tests/test_github_browser_review_lifecycle.mjs`. The
rerun is independently verified and is evidence for this plan, not an
additional implementation target.

Review evidence is preserved read-only at:

- `review-output/github-review-9a90cba-20261025-rerun/batch-result.json`
- `review-output/github-review-9a90cba-20261025-rerun/run-Oz5Bht/response.md`
- `review-output/github-review-9a90cba-20261025-rerun/run-WbH38S/response.md`
- `review-output/github-review-8cb8a92-20261025-plan-review/run-5PA6Qp/response.md`
- `review-output/github-review-8cb8a92-20261025-plan-review/run-5PA6Qp/result.json`

Both reviews report `status=completed`, `submission_attempted=true`, verified
requested model and `High` effort, and the same pinned commit SHA.

## Implementation Outcomes

### Semantic results survive optional lifecycle-observability gaps

DeepAgents structured `reported_completed` and `reported_failed` results remain
available to CoS even when a receipt or cleanup observation is missing. Lifecycle
uncertainty remains explicit and can still require reconciliation; it no longer
erases a valid semantic result. A nonzero pane command exit is classified from
available receipt and task-result evidence before being labelled transport or
delivery failure.

### Codex submission and reuse report truthful capability and lifecycle state

An asynchronous Codex `submitted` result always requires later reconciliation
until execution and task evidence are observed. Reused Codex agents are eligible
only when their effective MCP capability/configuration fingerprint is compatible
with the new assignment. Same-capability reuse remains supported, and unreachable
completion code is either removed or moved behind an explicit observer-owned
path.

### Auto-targeting retains safety while reducing avoidable work

Discovery, lock acquisition, and replacement allocation have separate bounded
budgets. A pane created but not yet verified is represented explicitly and is
never silently retried or reused. Candidate discovery returns the inspected state
for the preferred candidate, while one final ownership-locked verification remains
the authoritative pre-dispatch check.

### Settled artifacts and performance evidence have bounded maintenance cost

Result directories are removed only after durable settlement is proven; unresolved
or ambiguous evidence is retained in an explicit recovery state with bounded
cleanup. The deterministic Secretary contract benchmark remains intact and gains
an optional, separately named live measurement mode that reports real launcher
latency and resource evidence without claiming an improvement absent a baseline.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: `edit declared source, test, and documentation targets; run declared local checks; preserve review/runtime artifacts`
- User-approval actions: `commit, push, pull request creation or update, merge, deletion of review/runtime artifacts, or edits outside declared targets`
- Cleanup exception: Task 4 may delete only task-owned `herdr-result-*` directories
  after its publication, ownership, identity, and settlement gates succeed;
  review artifacts and unrelated runtime artifacts remain approval-protected.
- Parallel ownership: `none; all runtime behavior changes converge on scripts/herdr_main_launcher.py`
- Sequential fallback: `Task 1`, then `Task 2`, then `Task 3`, then `Task 4`, then `Task 5`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/herdr-cos-workers-secretary-plan-review-20261025`
- Reviewed source commit: `9a90cba3498d1290601bb0702c4c8671b0dfe6a5`
- Base commit: `8cb8a92fcdbe3ae975ad1ce918a8315f6aca3e81` (the pushed plan and generated-adapter correction commit)
- Reconciliation: comparison of `9a90cba` to `8cb8a92` found no change to the
  declared runtime, test, or documentation target set; `8cb8a92` adds the
  pushed plan and generated GitHub-review adapter corrections only.
- Expected workspace: `source remains at the pushed plan commit; preserve untracked .playwright-mcp, .pr-body.md, .review-profile, .runtime, node_modules, and review-output artifacts`
- Next action: `approve this plan, then start Task 1 from the base commit after reconciling implementation changes against the reviewed source commit`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | focused DeepAgents lifecycle tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | focused Codex reuse/submission tests | pending |
| Task 3 | `pending` | current | `unresolved` | Task 2 | target-resolution and subprocess-count tests | pending |
| Task 4 | `pending` | current | `unresolved` | Task 3 | artifact-retention and live-measurement tests | pending |
| Task 5 | `pending` | current | `unresolved` | Tasks 1–4 | repository, plan, focused-suite, and diff checks | pending |

## Validated Findings And Decisions

| Severity | Validated finding | Root cause and impact | Decision | Attribution |
| --- | --- | --- | --- | --- |
| P1 | Confirmed DeepAgents task results are downgraded when the lifecycle receipt is missing. | `_classify_deepagents_outcome()` initializes `unknown` and promotes success/failure only inside the confirmed-receipt branch. A valid structured task result can therefore become `unknown` and wait through receipt grace. | Separate semantic task-result classification from receipt/cleanup settlement; retain reconciliation when lifecycle proof is incomplete. | `GPT-5.6-Sol`, `GPT-6` |
| P1 | Codex asynchronous submission reports `reconciliation_required=false` without observing execution or task result. | The active prompt-submit branch sets `status=submitted`, unknown execution/result/cleanup, exit `0`, and an explicit false override; completion helpers are not assigned in that path. | Mark submitted-only results as reconciliation-required; remove or explicitly isolate unreachable completion handling. | `GPT-5.6-Sol`, independently confirmed by `GPT-6` |
| P1 | Reused Codex agents do not prove effective MCP capability compatibility. | Reuse checks identity/profile/provider/model and idle state, but the existing process keeps its startup MCP configuration while the next assignment may request a different selection. | Add a stable capability/configuration fingerprint to reuse eligibility; preserve compatible reuse and allocate a replacement otherwise. | `GPT-6` |
| P1 | A nonzero DeepAgents pane command exit can be classified as `not_delivered` before worker evidence is inspected. | `_main_body()` returns on command nonzero before receipt/task-result observation, conflating transport/start failure with worker execution failure. | Inspect existing evidence first and distinguish transport, start, execution, and uncertain delivery states. | `GPT-6` |
| P2 | Auto-pane lock acquisition consumes the same one-second reserve needed for protected allocation. | The allocation deadline starts before `_allocation_lock()` and all post-lock snapshot/split/validation calls use the remaining time. Contention can leave no allocation budget. | Give lock acquisition and post-lock allocation separate bounded budgets and represent `created_unverified` explicitly. | `GPT-5.6-Sol`, `GPT-6` |
| P2 | Candidate discovery and Codex reuse perform redundant pane checks and subprocess calls. | Discovery inspects every candidate before preference ordering; launch preparation and the locked dispatch path re-inspect the selected pane, with an extra locked callback on reuse. | Order candidates first, carry the inspected state forward, and retain exactly one authoritative ownership-locked verification/submission boundary. | `GPT-5.6-Sol`, `GPT-6` |
| P3 | DeepAgents result directories have no settled-artifact retention policy. | Each non-dry-run task creates `herdr-result-*` under the system temp directory, and the launcher has no settlement-linked cleanup or bounded retention. | Remove settled directories only after durable evidence is preserved; retain unresolved evidence under explicit recovery policy with bounded age/count cleanup. | `GPT-5.6-Sol`, `GPT-6` |
| P3 | The Secretary architecture benchmark is deterministic contract data, not latency/resource evidence. | Baseline and target metrics are hard-coded; `run_contract_benchmark()` repeats fixtures and reports `live=false`, `latency_ms=null`, and `not_attempted`. | Keep contract mode; add optional live trace mode using existing launcher performance evidence and no invented pass threshold. | `GPT-5.6-Sol`, `GPT-6` |

### Explicitly rejected or out of scope

- No browser/window lifecycle rewrite: the reviewed files contain no browser-window
  creation or recreation path; the relevant reusable resource is a Herdr pane.
- No new scheduler, registry, persistent orchestration service, or coordination
  authority.
- No weakening of ownership locks, exact identity binding, Git evidence, cleanup
  proof, or fail-closed uncertainty.
- No automatic retry of an uncertain started attempt.
- The single-model direct DeepAgents assignment-ID concern is not retained as a
  validated finding for this plan because it was not independently corroborated
  by the second completed review; revisit only with a focused contract review.

## Task Breakdown

### Task 1: Decouple DeepAgents semantic results from lifecycle settlement

**Purpose:**
- Make valid structured worker outcomes useful without treating missing optional
  receipt/cleanup evidence as proof of acceptance or successful settlement.
- Classify nonzero pane command exits from all already-available evidence before
  asserting `not_delivered`.

**Task Function:**
- DeepAgents lifecycle-state and evidence-classification correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared launcher contract, high correctness risk, and direct
  source/test evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused existing launcher tests plus backend boundary checks.

**Specification Coverage:**
- Preserve independent delivery, execution, observation, task-result, and cleanup
  fields; preserve fail-closed reconciliation; do not discard confirmed structured
  results; do not replay uncertain attempts.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_read_deepagents_task_result`, `_classify_deepagents_outcome`, `_deepagents_completion_evidence`, `_main_body`
- Modify: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome` and the DeepAgents nonzero-exit branch in `_main_body`
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_secretary_live_runtime.py`, `docs/operating_system/runtime/runtime-surfaces.md`

**Dependencies:**
- Review evidence at `9a90cba` and the existing lifecycle/result contract are the
  source of truth.
- Do not change receipt schema or acceptance ownership unless current tests prove
  the shared classifier requires a contract adjustment.

**Authority:**
- Preauthorized local actions: edit the listed DeepAgents classifier/dispatch surfaces and focused tests/docs needed to preserve the existing evidence contract.
- Stop for: any change that treats missing evidence as acceptance, retries a started attempt, changes receipt ownership, or requires a new coordination store.
- Rollback/idempotency: classification changes must be observational and idempotent for an already-started attempt; if evidence remains ambiguous, preserve the attempt and return reconciliation-required rather than replaying or deleting it.

**Steps:**
- [ ] Step 1: Reproduce both cases with focused unit inputs: confirmed structured completed/failed task result plus missing receipt, and nonzero pane command plus available receipt/task-result evidence.
- [ ] Step 2: Refactor classification so semantic result state is derived independently, while `reconciliation_required`, cleanup state, and launcher exit remain driven by lifecycle proof.
- [ ] Step 3: Change the nonzero DeepAgents path to observe bounded evidence before final classification; emit transport/start/execution/uncertain failure kinds without asserting `not_delivered` when execution is possible.
- [ ] Step 4: Add regression assertions for result preservation, receipt-grace short-circuit after terminal structured evidence, and no retry/replay behavior.

**Verification:**
- [ ] `py -m pytest -q tests/test_herdr_main_launcher.py -k "deepagents_classification or deepagents_completion or deepagents_pane_run_failure"`
- Expected: confirmed semantic results remain visible; missing lifecycle proof remains explicit; nonzero exits are not falsely labelled `not_delivered` when worker evidence exists.

**Exit Criteria:**
- Every DeepAgents terminal path distinguishes semantic task result from lifecycle settlement and preserves enough evidence for later reconciliation.

### Task 2: Make Codex asynchronous submission and reuse capability-safe

**Purpose:**
- Prevent a submission acknowledgement from being mistaken for completion.
- Prevent a reused Codex process from carrying unauthorized or missing MCP
  capabilities into a new assignment.
- Remove dead completion branching or make it explicitly observer-owned.

**Task Function:**
- Codex lifecycle contract and capability-compatible reuse correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: P1 correctness and capability-isolation risk in the shared launcher.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing Codex completion and pane-safety tests cover the same
  helper boundaries.

**Specification Coverage:**
- Transport acknowledgement is delivery evidence only; runtime completion and
  task evidence remain separate; MCP access is deliberate rather than inherited;
  compatible reuse remains allowed.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_inspect_auto_candidate`, `_resolve_target_selector`, `_run_with_pane_ownership`, `_codex_completion_snapshot`, `_classify_codex_completion_snapshot`, `_main_body`; `scripts/project_os_runtime/capabilities.py:capability_digest`, `scripts/project_os_runtime/results.py:publish_task_result`
- Modify: reuse eligibility/fingerprint plumbing and the active Codex prompt-submit branch in `scripts/herdr_main_launcher.py`; extend the canonical capability helpers in `scripts/project_os_runtime/capabilities.py` rather than creating a second authority
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_herdr_attempt_contract.py`, `tests/test_secretary_live_runtime.py`, `README.md`, `docs/usage.md`, `docs/configuration.md`

**Dependencies:**
- Task 1 establishes the evidence-separation pattern and must not be bypassed.
- Preserve existing `capability_digest()` and MCP-selection normalization rather
  than introducing a second capability authority. The effective reuse binding
  must be a canonical combined digest over the normalized local capability
  evidence and the selected MCP capability/configuration evidence; it must not
  hash local capabilities alone. If either side lacks stable evidence, reuse
  is ineligible and the diagnostics must report the missing-evidence reason.

**Authority:**
- Preauthorized local actions: edit the listed Codex reuse/submission helpers and their focused contract tests/docs; remove only demonstrably unreachable dispatch code.
- Stop for: capability checks that use hidden process state, any reuse without exact identity evidence, or any change that treats submitted as accepted/completed.
- Rollback/idempotency: if the combined capability fingerprint cannot be derived or does not match, preserve the existing process and allocate a replacement; never mutate a running pane to force compatibility, and never resubmit a submitted-only attempt.

**Steps:**
- [ ] Step 1: Trace the active Codex dispatch path and record which completion helpers have external tests/callers before deleting or relocating branches.
- [ ] Step 2: Define the canonical combined effective capability fingerprint in `scripts/project_os_runtime/capabilities.py`, including normalized local capabilities, selected MCP configuration, and fail-closed behavior when stable evidence is unavailable; expose the digest in stable reusable-agent evidence, then include it in pane reuse eligibility and diagnostics.
- [ ] Step 3: Set `reconciliation_required=true`, unknown execution/task/cleanup, and a non-success lifecycle state for submitted-only asynchronous results; keep confirmed completion classification separate.
- [ ] Step 4: Remove unreachable completion assignments/branches only after preserving helper APIs used by tests or the Secretary observer path; add mismatch, compatible-reuse, and submitted-only regression tests.

**Verification:**
- [ ] `py -m pytest -q tests/test_herdr_main_launcher.py -k "codex_completion or codex_prompt_result or pane_safety or reused_codex or mcp_selection"`
- [ ] `py -m pytest -q tests/test_secretary_live_runtime.py -k "observe_submitted_codex or runtime_snapshot"`
- Expected: same-capability idle agents reuse; mismatched capability fingerprints do not; submitted-only responses require reconciliation; observer helpers remain testable.

**Exit Criteria:**
- Codex lifecycle state and effective capability state are truthful at the active dispatch boundary without adding a new process or coordinator.

### Task 3: Split target deadlines and collapse redundant pane inspection

**Purpose:**
- Reduce Herdr subprocess and pane-query overhead while keeping one authoritative
  ownership-locked validation immediately before side effects.
- Prevent lock contention from consuming the entire protected allocation budget.

**Task Function:**
- Herdr target-resolution latency and bounded allocation optimization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: both models identified the same shared deadline and redundant
  inspection path; correctness depends on preserving the final lock.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing target-selector and ownership-lock tests expose timing,
  state-carrying, and race-sensitive behavior.

**Specification Coverage:**
- Auto discovery remains bounded and fail-closed; candidate-local failures remain
  isolated; replacement allocation is serialized; created-but-unverified panes are
  never silently reused or split again.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_allocation_lock`, `_resolve_target_selector`, `_inspect_auto_candidate`, `_run_with_pane_ownership`, `resolve_launch`
- Modify: deadline budgeting, candidate ordering/state return, and reuse-path ownership/submission consolidation in `scripts/herdr_main_launcher.py`
- Verify: `tests/test_herdr_main_launcher.py`, `docs/configuration.md`, `docs/operating_system/procedures/runtime-adapter-procedure.md`

**Dependencies:**
- Task 2 defines the capability-compatible reuse result carried through target
  resolution.
- The final ownership lock and identity validation remain mandatory.

**Authority:**
- Preauthorized local actions: edit target discovery/allocation/reuse timing and focused tests/docs, reusing existing Herdr commands and lock mechanisms only.
- Stop for: removal of the final ownership check, unbounded discovery/allocation, automatic split retry after uncertain creation, or a new pane/window registry.
- Rollback/idempotency: a `created_unverified` allocation is terminal for that allocation attempt and remains in recovery state; do not retry, reuse, or split it automatically. A timed-out lock or allocation leaves no claimed replacement unless ownership and identity proof completed.

**Steps:**
- [ ] Step 1: Add deterministic tests that force lock contention, slow discovery, successful split, and split-created-but-unverified outcomes.
- [ ] Step 2: Separate discovery, lock acquisition, and post-lock allocation deadlines; make the allocation result explicitly carry `created_unverified` when verification cannot complete.
- [ ] Step 3: Sort candidates by current preference before inspection, return the selected inspected state, and treat it as advisory until one final ownership-locked check.
- [ ] Step 4: Merge the reuse-path final verification and prompt submission into one locked callback; retain diagnostic evidence without a second lock acquisition or duplicate pane query.
- [ ] Step 5: Compare subprocess counts and elapsed phases before/after using existing performance evidence; do not claim a performance win without measured evidence.

**Verification:**
- [ ] `py -m pytest -q tests/test_herdr_main_launcher.py -k "target_selector or pane_ownership or resolve_launch or pane_safety or auto_codex"`
- Expected: lock wait does not consume all protected allocation time; unverified allocations are explicit; final validation remains exactly once at the side-effect boundary for reuse.

**Exit Criteria:**
- Auto targeting remains bounded and race-safe while eliminating the confirmed redundant probes and deadline coupling.

### Task 4: Bound settled result-artifact retention and add live benchmark mode

**Purpose:**
- Stop successful personal-use runs from accumulating unbounded temporary result
  directories while preserving unresolved recovery evidence.
- Add a small empirical measurement path for the optimization claims without
  replacing the deterministic contract benchmark.

**Task Function:**
- Resource-retention policy and measured performance evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: P3 operational overhead and evaluation gap; lower risk after
  lifecycle behavior is stable.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing benchmark contract and operational-comparison schemas
  can validate provenance and unavailable-metric handling.

**Specification Coverage:**
- Evidence is retained until durable settlement; unresolved evidence remains
  recoverable; deterministic fixtures do not masquerade as latency measurements.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_main_body` result-directory creation and settlement paths; `scripts/benchmark_secretary_architecture.py:run_contract_benchmark`; existing performance evidence helpers in `scripts/herdr_main_launcher.py`
- Modify: launcher-owned result-artifact retention and the separately named live benchmark mode in `scripts/benchmark_secretary_architecture.py`; use `scripts/project_os_runtime/results.py:publish_task_result` as the canonical publication predicate and ownership boundary
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_evidence_release.py`, `tests/test_secretary_benchmark.py`, `tests/test_benchmark_operational_comparison.py`

**Dependencies:**
- Task 1 defines when settlement is durable enough to remove artifacts.
- Task 3 provides the target-resolution and reuse evidence to measure.
- Reuse `performance.total_duration_ms`, phase evidence, and
  `subprocess_counts`; do not add a new benchmark service.

**Authority:**
- Preauthorized local actions: edit launcher-owned retention and benchmark fixture/live-mode code plus focused tests and README benchmark documentation.
- Stop for: deleting unresolved evidence, claiming an optimization from deterministic rows, inventing a universal latency threshold, or adding persistent benchmark infrastructure.

**Steps:**
- [ ] Step 1: Define settled, unresolved, and ambiguous artifact states and the owner of each directory. Publication is durable only after `publish_task_result()` in `scripts/project_os_runtime/results.py` succeeds and the assignment/attempt evidence binds that result to the task; preserve unresolved directories under explicit recovery retention.
- [ ] Step 2: Remove or archive only task-owned `herdr-result-*` directories after the canonical publication predicate and settlement proof succeed; already absent is idempotent success, foreign or identity-mismatched directories are preserved, ambiguous publication is preserved, and no deletion rollback is assumed. All publication, ownership, and identity gates must complete before deletion. Add bounded age/count cleanup for retained recovery artifacts without touching unrelated temp files.
- [ ] Step 3: Keep `contract` mode unchanged and add a distinct live/trace mode that executes the existing bounded launcher/test-double path and records real latency, subprocess count, pane allocation/reuse, and reconciliation frequency.
- [ ] Step 4: Feed only real samples into the existing operational-comparison schema; mark missing metrics unavailable and document that the target owner must set any pass threshold after baseline capture.

**Verification:**
- [ ] `py -m pytest -q tests/test_herdr_main_launcher.py -k "result_file or receipt or cleanup"`
- [ ] `py -m pytest -q tests/test_evidence_release.py -k "publish_task_result or result"`
- [ ] `py -m pytest -q tests/test_secretary_benchmark.py tests/test_benchmark_operational_comparison.py`
- Expected: settled artifacts are cleaned only after proof, unresolved artifacts remain recoverable, contract mode stays deterministic, and live mode never reports fabricated latency/resource improvements.

**Exit Criteria:**
- Repeated personal-use runs have bounded settled-artifact overhead and an honest, reproducible measurement path for future optimization decisions.

### Task 5: Reconcile canonical documentation and complete final verification

**Purpose:**
- Align runtime contracts and user-facing guidance with the corrected lifecycle,
  capability, target, retention, and benchmark behavior.

**Task Function:**
- Specification reconciliation and final evidence review.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation must follow verified implementation, not lead it.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository and planning validators plus focused runtime suites.

**Specification Coverage:**
- Keep canonical docs consistent with source and tests; preserve personal-use
  scope and explicit non-goals.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `README.md`, `docs/usage.md`, `docs/configuration.md`, `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: only the statements that conflict with the verified implementation from Tasks 1–4
- Verify: all declared targets, `scripts/validate_repo_contracts.py`, and `scripts/validate_planning_lifecycle.py`

**Dependencies:**
- Tasks 1–4 complete with fresh focused proof.
- The GitHub review artifacts remain read-only and are not regenerated.

**Authority:**
- Preauthorized local actions: reconcile the listed canonical docs and run final repository/planning/diff validation without changing preserved review/runtime artifacts.
- Stop for: undocumented behavior changes, generated-surface drift, a new acceptance authority, or any failed proof that is being papered over by documentation edits.

**Steps:**
- [ ] Step 1: Update docs to state that submitted-only Codex work requires reconciliation, capability-compatible reuse is required, and pane reuse—not browser-window recreation—is the optimization scope.
- [ ] Step 2: Document independent semantic result versus lifecycle settlement, nonzero-exit classification, bounded artifact retention, and deterministic versus live benchmark modes.
- [ ] Step 3: Run the final focused suites and repository/planning validators; inspect the diff for undeclared targets and preserved untracked review evidence.
- [ ] Step 4: Leave this plan `proposed` until a later execution and fresh verification workflow proves the implementation; do not mark it completed from plan-authoring evidence alone.

**Verification:**
- [ ] `py -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_benchmark.py tests/test_benchmark_operational_comparison.py`
- Expected: all focused behavior and measurement-contract tests pass, and documentation matches source/test truth.

**Exit Criteria:**
- All eight retained findings have an executable implementation task, a focused proof path, a named owner, and an explicit non-goal where applicable.

## Verification

Run after implementation and before changing this plan to `completed`:

- `py -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_benchmark.py tests/test_benchmark_operational_comparison.py`
- `py -B scripts/validate_repo_contracts.py`
- `py -B scripts/validate_planning_lifecycle.py`
- `git diff --check`
- `node --test tests/test_github_browser_review_lifecycle.mjs`

The GitHub review lifecycle test is a regression guard for the already-fixed
formatted-prompt anomaly; the model reviews must not be resubmitted as part of
implementation verification.

For the live benchmark, record baseline and post-change samples from the same
environment and workload, including `total_duration_ms`, phase durations,
`subprocess_counts`, target allocation/reuse counts, and reconciliation rate.
No universal pass threshold is invented here; the plan owner sets a task-specific
budget after the baseline is captured. Correctness and reconciliation evidence
remain mandatory even when a measurement is faster.

## Completion Criteria

The plan is ready for completion verification when:

1. Every retained P1–P3 finding has an implemented correction or an explicit
   user-approved re-scope; an unresolved P1 finding prevents completion.
2. Semantic worker results, lifecycle settlement, delivery, and acceptance are
   represented independently and truthfully.
3. Submitted-only Codex work cannot be mistaken for observed completion, and
   reused agents cannot cross capability boundaries.
4. All target discovery, lock, allocation, subprocess, and artifact-retention
   waits are bounded and preserve uncertainty when proof is incomplete.
5. No started attempt is automatically replayed and no unresolved evidence is
   deleted.
6. The deterministic benchmark remains honest and live measurements use only real
   samples with provenance.
7. Focused tests, repository validation, planning validation, and diff checks pass
   from the reviewed base or a recorded reconciled successor.
8. `skill-verification-before-completion` returns `verified` from fresh evidence
   before plan status changes to `completed`.

## Stop Conditions

- Stop if the reviewed base commit changes before implementation begins; reconcile
  every finding against the new immutable revision.
- Stop if a fix requires a new coordinator, browser/window owner, scheduler,
  registry, automatic retry, or weakened identity/ownership proof.
- Stop if a timeout or cleanup path cannot prove process retirement or artifact
  settlement; preserve evidence and return reconciliation-required state.
- Stop if capability compatibility cannot be derived from an existing canonical
  selection/fingerprint without hidden process-state assumptions.
- Stop if live benchmark evidence is unavailable; retain the deterministic contract
  benchmark and report metrics as unavailable rather than inventing results.
- Stop if a documentation conflict reveals an unresolved interface or ownership
  decision; use `skill-spec-drafting` before changing this plan.

## Handoff

After approval, activate this plan through `skill-executing-plans` with one lead
controller and the task order in the ledger. Use `skill-verification-before-completion`
before changing status to `completed`. Keep the completed GitHub review artifacts
read-only and preserved. Git commit, push, pull request, merge, and cleanup remain
separate explicitly authorized actions.
