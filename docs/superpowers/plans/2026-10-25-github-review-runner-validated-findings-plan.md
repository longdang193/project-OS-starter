---
layer: change
artifact_type: plan
status: proposed
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

### Account readiness and documentation match executable behavior

The authenticated-profile contract distinguishes composer readiness from visible
account identity. Strict unattended operation can require an expected visible
account marker without inspecting credentials or cookies. Tests and canonical
skill documentation describe the final recovery, evidence, and stop behavior.

## Validated Findings Consolidation

Only findings supported by the pinned source and independently observed in both
or one completed model response are included below. The model attribution is
preserved for auditability; implementation decisions must follow source and test
truth.

| Severity | Validated finding | Source evidence | Model attribution |
| --- | --- | --- | --- |
| P1 | Post-send acknowledgement failure closes the only page before the caller can preserve evidence. | `run-review-prompt.mjs:189-209,299-307`; `run-review-prompt-cli.mjs:368-423` | GPT-6; source-confirmed |
| P1 | Existing profile leases are rejected without stale-owner recovery, despite the documented recovery expectation. | `run-review-prompt-cli.mjs:191-202,219-231`; `SKILL.md:221-225` | GPT-5.6-Sol and GPT-6; source-confirmed |
| P1 | Visible composer readiness does not establish the expected signed-in account or GitHub integration. | `run-review-prompt.mjs:39-51`; `run-review-prompt-cli.mjs:266-269` | GPT-5.6-Sol; source-confirmed safety gap |
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
- Preauthorized local actions: modify only the listed runner, selector, tests, and canonical skill documentation; run declared local checks; preserve existing untracked review/profile/runtime artifacts
- User-approval actions: push, merge, publication, authentication/profile changes, destructive stale-lock recovery, live browser submissions, reruns, discard, and cleanup outside task-owned outputs
- Parallel ownership: `none; all tasks share the runner lifecycle and result contract`
- Sequential fallback: complete Tasks 1–4 in order, then run Task 5 as the single final verification gate

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `c163271b437046c61daab974a190dc9bc4764d57`
- Expected workspace: `main` with preserved untracked `.playwright-mcp/`, `.review-profile/`, `.runtime/`, and `node_modules/`; no tracked implementation changes at plan creation
- Next action: reconcile this proposed plan with the existing active `2026-10-25-github-review-runner-lease-ui-hardening-plan.md`, then activate exactly one ledger before implementation
- Blockers: `overlapping active runner-hardening plan must be reconciled before either plan becomes active`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | transaction and cleanup lifecycle tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | lease, batch-accounting, and provenance tests | pending |
| Task 3 | `pending` | current | `unresolved` | Task 1 | completion, failure-scope, and timeout tests | pending |
| Task 4 | `pending` | current | `unresolved` | Tasks 1–3 | authenticated readiness contract and documentation tests | pending |
| Task 5 | `pending` | current | `unresolved` | Tasks 1–4 | final repository and test verification | pending |

## Task Breakdown

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
- [ ] Step 1: Add failing tests for post-click acknowledgement failure, response persistence before page close, and page-close failure after a terminal response.
- [ ] Step 2: Transfer ownership of a page after the send attempt to the transaction owner, or attach the page/evidence handle to the thrown error so the transaction can capture visible URL, response, and completion state before cleanup.
- [ ] Step 3: Persist `submission: ambiguous` and all available visible evidence without issuing a second send.
- [ ] Step 4: Record cleanup uncertainty separately from the original review failure. Stop the batch when tab ownership cannot be proven safe; do not claim shared-context loss unless context health is actually unavailable.
- [ ] Step 5: Add regressions proving the next review is never started while an uncertain prior tab may still be generating.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "submission|cleanup|batch"`
- Expected: ambiguous sends preserve artifacts, no prompt is resubmitted, and uncertain cleanup stops safely with explicit evidence.

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
- [ ] Step 1: Add tests for live, malformed, dead, replacement-owner, and metadata-publication-failure locks.
- [ ] Step 2: Preserve exclusive creation and token-checked release. On an existing lock, parse and validate ownership; reclaim only through a proven atomic compare-and-reclaim path with PID-reuse protection. Otherwise retain the lock and return an operator-actionable blocked state.
- [ ] Step 3: Add manifest-indexed results with `requested_count`, `attempted_count`, `completed_count`, `failed_count`, and `skipped_count`; record every unattempted review with its model, effort, index, and stop reason.
- [ ] Step 4: Persist sanitized request provenance per run: prompt source/hash plus structured repository, full commit SHA, and reviewed file URLs supplied by the controller. Do not parse or trust free-form model/effort text inside prompts.
- [ ] Step 5: Update the skill contract and Python schema tests for the final result fields and operator recovery procedure.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "profile lease|batch|result"`
- [ ] `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- Expected: no active/replacement/malformed lock is clobbered; dead-owner handling is either race-safe or explicitly blocked; all requested reviews remain accounted for.

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
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:readVisibleAssistantTurns,readVisibleAssistantMessage,waitForReviewCompletion`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs:setEffort`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:assistant fallback and completion evidence`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:classifyFailureScope`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 cleanup and terminal-state contract.

**Authority:**
- Preauthorized local actions: add focused UI/completion/failure-scope tests and modify only the declared selector, observer, and classifier symbols.
- Stop for: hidden DOM/network-state inspection, automatic retries, changed polling backoff, or accepting response text without defensible turn association.

**Steps:**
- [ ] Step 1: Add explicit `UI_ACTION_TIMEOUT_MS` to effort focus and keyboard operations.
- [ ] Step 2: Add multi-container and mixed user/assistant fallback fixtures. Accept fallback content only when it maps to a visible assistant boundary; otherwise return incomplete with the reason.
- [ ] Step 3: Preserve explicit shared-context failures through submission and completion. Distinguish page-local review errors from browser disconnects or closed contexts.
- [ ] Step 4: Keep the existing fast-response completion path and interruption checks; do not require response-action buttons when other finality evidence is sufficient.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "effort|completion|interruption|context|fallback"`
- Expected: bounded UI actions fail within the documented budget, incomplete fallback evidence fails closed, and context loss stops the shared batch.

**Exit Criteria:**
- Completion and failure classification remain observable, bounded, and conservative without adding a second browser or retry state machine.

### Task 4: Add explicit authenticated-profile readiness and align documentation

**Purpose:**
- Prevent a project-specific persistent profile logged into the wrong account from being treated as fully verified while preserving privacy and compatibility.

**Task Function:**
- Add a visible, controller-supplied account-identity preflight and document its limits.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded UI contract and documentation change with privacy constraints.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: mocked visible-page tests and contract validation.

**Specification Coverage:**
- Authenticated ChatGPT composer, expected account/profile identity, dedicated project profile, and fail-closed readiness.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:openChatGPT`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:openReviewContext,parseArguments`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:visible session preflight`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:CLI/manifest readiness option`
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md:authenticated-profile contract`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`, `tests/test_skill_github_browser_reviews.py`

**Dependencies:**
- Tasks 1–3 result and readiness contracts.

**Authority:**
- Preauthorized local actions: add visible-readiness tests and modify only the declared preflight, CLI schema, and skill documentation.
- Stop for: reading credentials/cookies, relying on hidden DOM/network state, requiring an unavailable account identifier, or weakening the existing composer readiness failure path.

**Steps:**
- [ ] Step 1: Define an optional expected visible account marker supplied by the controller or batch manifest; do not infer identity from the profile path alone.
- [ ] Step 2: Verify the marker once before the first review tab. Record `account_identity: verified|unverified` in structured output.
- [ ] Step 3: Require the marker for strict unattended `verified` workflows while retaining a compatibility mode that reports unverified rather than falsely claiming identity.
- [ ] Step 4: Document that composer visibility proves readiness only, not account identity or GitHub connector availability.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "authenticated|account|readiness"`
- [ ] `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`
- Expected: matching visible identity passes, missing/mismatched identity fails closed for strict mode, and no credential or hidden-state inspection occurs.

**Exit Criteria:**
- The runner can distinguish “composer ready” from “expected account visibly verified,” and the skill documentation matches the executable contract.

### Task 5: Reconcile generated surfaces and run the final proof gate

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
- Tasks 1–4 completed and the overlapping active plan reconciled.

**Authority:**
- Preauthorized local actions: run final local checks, synchronize generated agent adapters when required, and update this plan’s ledger/evidence.
- Stop for: stale base SHA, unresolved overlapping plan ownership, failed required proof, live browser rerun requests, or unrelated workspace cleanup.

**Steps:**
- [ ] Step 1: Run the focused Node lifecycle tests and Python contract tests.
- [ ] Step 2: Run syntax, repository-contract, generated-adapter, and diff checks.
- [ ] Step 3: Reconcile all task evidence, blockers, skipped checks, and changed result fields in the plan.
- [ ] Step 4: Apply `skill-verification-before-completion` to fresh command output; do not mark the plan complete from checked boxes alone.

**Verification:**
- [ ] Final commands in the Verification section pass from the reconciled base.
- Expected: all required proof is fresh, tracked changes are scoped, untracked review artifacts remain untouched, and no live review is resubmitted.

**Exit Criteria:**
- The plan has a truthful terminal ledger, fresh proof, no unresolved required task, and an explicit publication decision left to the authorized Git workflow.

## Verification

Run after implementation and plan reconciliation:

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- `node --check .agents/skills/skill-github-browser_reviews/scripts/run-review-prompt.mjs`
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
7. account identity is visibly verified for strict unattended operation without credential inspection
8. focused tests, contract tests, syntax checks, adapter synchronization, repository validation, and `git diff --check` pass
9. the overlapping active plan is reconciled and only one coordination ledger is authoritative
10. `skill-verification-before-completion` returns `verified` from fresh evidence

The plan remains `proposed` until the lead reconciles the overlapping active
plan and explicitly activates this ledger. No commit, push, live browser rerun,
or external publication is implied by saving this plan.

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


