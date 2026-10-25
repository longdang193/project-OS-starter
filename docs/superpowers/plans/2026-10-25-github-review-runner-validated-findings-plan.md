---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: github-review-runner-validated-findings
reviewed_repository: longdang193/project-OS-starter
reviewed_branch: main
reviewed_commit: c163271b437046c61daab974a190dc9bc4764d57
targets:
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
  - generated_agents/claude/skills/skill-github-browser-reviews/SKILL.md
  - generated_agents/claude/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - generated_agents/claude/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - generated_agents/claude/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - generated_agents/codex/skills/skill-github-browser-reviews/SKILL.md
  - generated_agents/codex/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - generated_agents/codex/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - generated_agents/codex/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - generated_agents/antigravity/skills/skill-github-browser-reviews/SKILL.md
  - generated_agents/antigravity/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - generated_agents/antigravity/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - generated_agents/antigravity/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
---

# GitHub Review Runner Validated Findings Plan

## Goal

Harden the GitHub Browser Reviews workflow and Node/Playwright runner against the
source-confirmed failure modes found by the completed GPT-5.6-Sol High and GPT-6
High reviews of commit `c163271b437046c61daab974a190dc9bc4764d57`. Preserve the
existing one authenticated context, sequential fresh-tab execution, exactly-once
submission, read-only scope, fail-closed behavior, and durable per-review
artifacts without adding another browser lifecycle owner or broad retry logic.

The review source is pinned to:

- `https://github.com/longdang193/project-OS-starter/tree/c163271b437046c61daab974a190dc9bc4764d57`
- `.runtime/github-review-20261025/output/run-vQhxo9/response.md`
- `.runtime/github-review-20261025/output/run-pbsWTk/response.md`
- `.runtime/github-review-20261025/batch-summary.json`

## Implementation Outcomes

### Exactly-once review evidence survives ambiguous delivery

A send attempt that cannot be locally acknowledged is recorded as `ambiguous`
without resubmission. The runner preserves the best visible conversation,
completion, response, and cleanup evidence available after the attempt, and
persists terminal status before releasing the tab or profile lease.

### Profile ownership and batch accounting are deterministic

Persistent-profile ownership remains exclusive and fail-closed for malformed,
live, or ambiguous locks. A stale lock is reclaimed only through a race-safe,
provable path; otherwise the runner reports an operator-actionable blocked state.
Batch output accounts for every requested review, including skipped reviews, and
stores enough immutable request provenance to compare model results reliably.

### UI and failure boundaries remain bounded and simple

Model/effort actions use explicit bounded timeouts. Completion fallback accepts
only a defensible assistant-turn boundary or fails incomplete. Browser-context
loss is not misreported as a recoverable review-local error. No new browser,
keep-open, automatic retry, hidden-state, or model-substitution path is added.

### Documentation matches executable behavior

Tests and canonical skill documentation describe the final recovery, evidence,
and stop behavior without adding an unproven account-identity or integration
marker requirement.

## Validated Findings Consolidation

Only findings supported by the pinned source and independently observed in both
or one completed model response are included below. The model attribution is
preserved for auditability; implementation decisions must follow source and test
truth.

| Severity | Validated finding | Source evidence | Model attribution |
| --- | --- | --- | --- |
| P1 | Post-send acknowledgement failure closes the only page before the caller can preserve evidence. | `run-review-prompt.mjs:189-209,299-307`; `run-review-prompt-cli.mjs:368-423` | GPT-6; source-confirmed |
| P1 | Existing profile leases are rejected without stale-owner recovery, despite the documented recovery expectation. | `run-review-prompt-cli.mjs:191-202,219-231`; `SKILL.md:221-225` | GPT-5.6-Sol and GPT-6; source-confirmed |
| P2 | Page cleanup uncertainty is hidden or promoted directly to shared-context failure, creating unsafe continuation or unnecessary batch aborts. | `run-review-prompt.mjs:58-72,299-307`; `run-review-prompt-cli.mjs:329-339,441-448,475-482` | GPT-5.6-Sol and GPT-6; source-confirmed |
| P2 | Shared-context stop leaves unattempted manifest entries absent from the batch summary. | `run-review-prompt-cli.mjs:176-185,475-482` | GPT-5.6-Sol and GPT-6; source-confirmed |
| P2 | Markdown fallback may accept incomplete or weakly associated assistant content. | `run-review-prompt.mjs:6-7,87-129` | GPT-6; source-confirmed risk |
| P2 | Submission/completion browser failures are always classified as review-local. | `run-review-prompt-cli.mjs:319-322` | GPT-6; source-confirmed |
| P2 | Run artifacts do not structurally retain revision and prompt provenance sufficient for independent comparison. | `run-review-prompt-cli.mjs:82-103,405-408` | GPT-5.6-Sol and GPT-6; source-confirmed design gap |
| P3 | Effort focus/keyboard operations omit the documented five-second interaction timeout. | `select-review-model.mjs:169-175`; `SKILL.md:233-236` | GPT-5.6-Sol and GPT-6; source-confirmed |

The plan does not treat generic model commentary about undocumented ChatGPT DOM
behavior as a confirmed defect unless a focused source or regression test proves
it. It also does not authorize another live review submission.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`; the lead creates an authorized checkpoint only after task proof is accepted
- Preauthorized local actions: modify only the listed canonical runner, selector, tests, skill documentation, and generated adapter surfaces; run declared local checks; preserve existing untracked review/profile/runtime artifacts
- User-approval actions: push, merge, publication, authentication/profile changes, destructive stale-lock recovery, live browser submissions, reruns, discard, and cleanup outside task-owned outputs
- Parallel ownership: `none; all tasks share the runner lifecycle and result contract`
- Sequential fallback: complete Task 0, then Tasks 1–3 in order, then run Task 4 as the single final verification gate

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/github-review-plan`
- Base commit: `e3ea9da18dac5594f18b080bf17730f71507f397`
- Execution base commit: `e3ea9da18dac5594f18b080bf17730f71507f397`
- Reviewed source commit: `c163271b437046c61daab974a190dc9bc4764d57`
- Expected workspace: current branch with preserved untracked `.playwright-mcp/`, `.review-profile/`, `.runtime/`, and `node_modules/`; no tracked implementation changes at activation
- Next action: hand off the verified branch to the explicitly authorized Git finishing workflow
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `completed` | current | `codex` | none | predecessor ledger reconciled and ownership transferred | predecessor marked `superseded`; successor is sole active ledger |
| Task 1 | `completed` | current | `codex` | Task 0 | transaction and cleanup lifecycle tests | 68 lifecycle tests passed; ambiguous evidence and cleanup ownership verified |
| Task 2 | `completed` | current | `codex` | Task 1 | lease, batch-accounting, and provenance tests | lease, skipped-accounting, provenance, and Python contract tests passed |
| Task 3 | `completed` | current | `codex` | Task 1 | completion, failure-scope, context-loss, and timeout tests | bounded effort, fallback, and submission/completion context-loss tests passed |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | final repository and test verification | 68 Node tests, 46 Python tests, syntax, repository, adapter, planning, and diff checks passed |

## Task Breakdown

### Task 0: Reconcile the predecessor coordination ledger

**Purpose:**
- Ensure exactly one active ledger owns the shared runner files before implementation begins.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead-owned coordination reconciliation in the current workspace.

**Authority:**
- Preauthorized local actions: update the two Git-tracked plan ledgers only.
- Stop for: unresolved ownership, unexpected tracked changes, or a base/branch mismatch.

**Files And Symbols:**
- Modify: `docs/superpowers/plans/2026-10-25-github-review-runner-lease-ui-hardening-plan.md:status and Task 6 ledger`
- Verify: `docs/superpowers/plans/2026-10-25-github-review-runner-validated-findings-plan.md:Coordination State`

**Steps:**
- [x] Step 1: Mark the predecessor plan `superseded` and transfer its unfinished Task 6 ownership to this plan.
- [x] Step 2: Activate this plan as the sole authoritative ledger.

**Exit Criteria:**
- The predecessor is no longer active, this plan is active, and no two ledgers own the same runner files.

### Task 1: Preserve post-send evidence and make cleanup uncertainty explicit

**Purpose:**
- Ensure an acknowledged, ambiguous, or failed post-send transaction leaves a durable and truthful artifact without resubmission or page leaks.

**Task Function:**
- Implement transaction ownership transfer and failure settlement at the send/cleanup boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: localized JavaScript lifecycle change with high correctness risk and direct test ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead controller accepts focused lifecycle evidence.

**Specification Coverage:**
- Exactly-once submission, ambiguous delivery, persist-before-cleanup, read-only scope, and fail-closed batch continuation.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:submitPrompt,runReviewPromptInNewTab`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:submitPrompt,runReviewPromptInNewTab`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction,markCleanupFailure,runReviewBatch`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Current result fields and completion observer behavior at base commit `c163271b437046c61daab974a190dc9bc4764d57`.

**Authority:**
- Preauthorized local actions: add focused lifecycle tests and modify only the declared transaction/cleanup symbols.
- Stop for: any automatic retry, second browser lifecycle owner, changed model-selection semantics, or unresolved ownership after a send attempt.

**Steps:**
- [x] Step 1: Add failing tests for post-click acknowledgement failure, response persistence before page close, and page-close failure after a terminal response.
- [x] Step 2: Transfer ownership of a page after the send attempt to the transaction owner, or attach the page/evidence handle to the thrown error so the transaction can capture visible URL, response, and completion state before cleanup.
- [x] Step 3: Persist `submission: ambiguous` and all available visible evidence without issuing a second send.
- [x] Step 4: Record cleanup uncertainty separately from the original review failure. Stop the batch when tab ownership cannot be proven safe; do not claim shared-context loss unless context health is actually unavailable.
- [x] Step 5: Add regressions proving the next review is never started while an uncertain prior tab may still be generating.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "submission|cleanup|batch"`
- Expected: ambiguous sends preserve artifacts, no prompt is resubmitted, and uncertain cleanup stops safely with explicit evidence — passed.

**Exit Criteria:**
- Every send-attempt path has one owner, one terminal artifact settlement, and one cleanup decision; no response is silently discarded or duplicated.

### Task 2: Make profile leases, batch accounting, and provenance deterministic

**Purpose:**
- Prevent a dead profile owner from permanently blocking future work and make skipped reviews and revision provenance explicit in structured output.

**Task Function:**
- Implement race-safe lease settlement and complete manifest-indexed result accounting.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: filesystem concurrency and public result-contract work requiring careful failure classification.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused Node lifecycle and Python contract tests are sufficient.

**Specification Coverage:**
- Dedicated persistent profile per project, fail-closed ownership, stale recovery, complete batch accounting, immutable commit evidence, and artifact comparison.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:acquireProfileLease,releaseProfileLease,summarizeBatchResults,runReviewBatch,createResult`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:acquireProfileLease,releaseProfileLease,summarizeBatchResults,runReviewBatch,createResult`
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md:lease recovery and evidence requirements`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`, `tests/test_github_browser_reviews.py`

**Dependencies:**
- Task 1 terminal result and cleanup fields.
- Reconciliation with the existing active lease-hardening plan before changing the ledger or public result shape.

**Authority:**
- Preauthorized local actions: add lease/accounting/provenance tests and modify only the declared CLI result/lease code and canonical skill documentation.
- Stop for: unsafe lock deletion, PID-only reclamation, silent result-shape incompatibility, or any external profile/authentication mutation.

**Steps:**
- [x] Step 1: Add tests for live, malformed, dead, replacement-owner, and metadata-publication-failure locks.
- [x] Step 2: Preserve exclusive creation and token-checked release. On an existing lock, parse and validate ownership; retain stale ownership for operator-confirmed recovery rather than deleting by PID/timestamp heuristic.
- [x] Step 3: Add manifest-indexed results with `requested_count`, `attempted_count`, `completed_count`, `failed_count`, and `skipped_count`; record every unattempted review with its model, effort, index, and stop reason.
- [x] Step 4: Persist sanitized request provenance per run: prompt source/hash plus structured repository, full commit SHA, and reviewed file URLs supplied by the controller. Do not parse or trust free-form model/effort text inside prompts.
- [x] Step 5: Update the skill contract and Python schema tests for the final result fields and operator recovery procedure.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "profile lease|batch|result"`
- [x] `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- Expected: no active/replacement/malformed lock is clobbered; dead-owner handling is explicitly blocked; all requested reviews remain accounted for — passed.

**Exit Criteria:**
- A failed batch is fully reconcilable from its structured artifacts, and profile recovery cannot remove another owner or rely on an unsafe PID/timestamp heuristic.

### Task 3: Harden bounded UI actions, completion fallback, and failure scope

**Purpose:**
- Keep browser interaction bounded while preventing truncated assistant evidence and unsafe continuation after context loss.

**Task Function:**
- Refine visible completion and failure classification without adding hidden-state inspection or retry branches.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: localized UI-state logic with direct source and regression proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic lifecycle tests and syntax checks.

**Specification Coverage:**
- Five-second model/effort interaction bound, stable assistant evidence, interruption handling, and shared-context failure classification.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs:setEffort`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:readVisibleAssistantTurns,readVisibleAssistantMessage,waitForReviewCompletion,runReviewPromptInNewTab`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs:setEffort`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:assistant fallback and completion evidence`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:classifyFailureScope,runReviewTransaction`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 cleanup and terminal-state contract.

**Authority:**
- Preauthorized local actions: add focused UI/completion/failure-scope/context-loss tests and modify only the declared selector, observer, classifier, and typed context-loss symbols.
- Stop for: hidden DOM/network-state inspection, automatic retries, changed polling backoff, or accepting response text without defensible turn association.

**Steps:**
- [x] Step 1: Add explicit `UI_ACTION_TIMEOUT_MS` to effort focus and keyboard operations.
- [x] Step 2: Add multi-container and mixed user/assistant fallback fixtures. Accept fallback content only when it maps to a visible assistant boundary; otherwise return incomplete with the reason.
- [x] Step 3: Preserve explicit shared-context failures through submission and completion. Distinguish page-local review errors from browser disconnects or closed contexts.
- [x] Step 4: Keep the existing fast-response completion path and interruption checks; do not require response-action buttons when other finality evidence is sufficient.
- [x] Step 5: Add submission-time and completion-time context-disconnect regressions proving typed browser-context loss is not wrapped as a review-local failure.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "effort|completion|interruption|context|fallback"`
- Expected: bounded UI actions fail within the documented budget, incomplete fallback evidence fails closed, and context loss stops the shared batch — passed.

**Exit Criteria:**
- Completion and failure classification remain observable, bounded, and conservative without adding a second browser or retry state machine.

### Task 4: Reconcile generated surfaces and run the final proof gate

**Purpose:**
- Prove the implementation plan’s outcomes against current repository truth without rerunning the live browser review.

**Task Function:**
- Reconcile plan-owned sources, generated adapters, tests, and final static evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: repository-wide verification with no independent implementation lane.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is lead-owned and command-backed.

**Specification Coverage:**
- Generated-surface synchronization, source/test authority, immutable review provenance, and completion evidence.

**Required Skills:**
- `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Inspect: all task-owned files and the active-plan reconciliation record
- Modify: only generated surfaces required by the canonical synchronization command
- Verify: `docs/superpowers/plans/2026-10-25-github-review-runner-validated-findings-plan.md`

**Dependencies:**
- Tasks 1–3 completed and the predecessor plan reconciled.

**Authority:**
- Preauthorized local actions: run final local checks, synchronize the exact generated adapter targets listed in the plan from canonical sources, and update this plan’s ledger/evidence.
- Stop for: stale base SHA, unresolved overlapping plan ownership, failed required proof, live browser rerun requests, or unrelated workspace cleanup.

**Steps:**
- [x] Step 1: Run the focused Node lifecycle tests and Python contract tests.
- [x] Step 2: Run syntax, repository-contract, generated-adapter, planning, and diff checks; stop on generated-surface drift.
- [x] Step 3: Reconcile all task evidence, blockers, skipped checks, and changed result fields in the plan.
- [x] Step 4: Apply `skill-verification-before-completion` to fresh command output; do not mark the plan complete from checked boxes alone.

**Verification:**
- [x] Final commands in the Verification section pass from the reconciled base.
- Expected: all required proof is fresh, tracked changes are scoped, untracked review artifacts remain untouched, and no live review is resubmitted.

**Exit Criteria:**
- The plan has a truthful terminal ledger, fresh proof, no unresolved required task, and an explicit publication decision left to the authorized Git workflow.

## Verification

Run after implementation and plan reconciliation:

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`
- `py -B scripts/validate_repo_contracts.py`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`

These are final-artifact checks only. They are not run while drafting this
proposed plan. A live GitHub browser review is not part of this plan’s proof;
the completed review artifacts already provide the model-analysis evidence.

## Completion Criteria

The plan is ready for completion verification when:

1. every validated P1–P3 finding has an implemented, source-aligned outcome or an explicit documented deferral
2. ambiguous submissions preserve evidence and never trigger resubmission
3. profile lease recovery is race-safe or explicitly operator-blocked, never PID/timestamp-only
4. batch summaries account for requested, attempted, completed, failed, and skipped reviews
5. result artifacts retain immutable prompt/revision provenance and verified model/effort values
6. completion fallback and failure scope remain conservative, bounded, and tested
7. focused tests, contract tests, syntax checks, adapter synchronization, repository validation, and `git diff --check` pass
8. the predecessor plan is reconciled and only one coordination ledger is authoritative
9. `skill-verification-before-completion` returns `verified` from fresh evidence

The predecessor plan is superseded and this ledger is active. No live browser
rerun or external publication is implied by the plan; Git publication remains
an explicitly authorized finishing action.

## Stop Conditions

- Stop if a proposed fix requires automatic resubmission, model substitution,
  lower reasoning effort, a second browser/context owner, hidden-state
  inspection, or unsafe stale-lock deletion.
- Stop if a page or context owner cannot be proven after a send attempt; preserve
  artifacts and report the ambiguity instead of continuing.
- Stop if the reviewed base SHA changes before implementation begins; reconcile
  the plan and rerun source-level validation against the new immutable revision.
- Stop if the existing active runner-hardening plan cannot be reconciled without
  two competing task ledgers.

## Handoff

After approval and plan reconciliation, execute through
`skill-executing-plans`. Keep the completed browser-review artifacts read-only
and preserved as evidence; do not rerun the completed model submissions unless
the user explicitly authorizes a new review.


