---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
name: github-review-runner-session-hardening
targets:
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
  - generated_agents
  - docs/superpowers/plans/2026-10-24-github-review-runner-session-hardening-plan.md
---

# GitHub Review Runner Session Hardening Plan

## Goal

Harden the repository-owned GitHub browser-review runner around failure
classification, persistent-profile ownership, visible completion evidence,
artifact settlement, and repeated selector work while preserving the existing
single authenticated context, sequential fresh-tab isolation, single
submission, no model substitution, and one cleanup owner per run.

The plan contains only findings validated against commit
`b0a9473e9a7f7071e33b8d4ed3775986bd9aec68` by source inspection and two
completed read-only browser reviews. It does not add a second browser lifecycle
owner or replace fresh-tab isolation with same-page reuse.

## Implementation Outcomes

### Truthful lifecycle and batch settlement

Selection, artifact, cleanup, and completion failures have distinct, durable
scopes. Batch execution continues only after an explicitly review-local failure,
stops on shared-context or shared-artifact failure, and reports requested,
attempted, completed, failed, and skipped entries without silently dropping
unattempted work.

### Safe authenticated-profile reuse

Persistent profile leases recover only when the recorded owner is provably dead
and the lock can be reclaimed without deleting a replacement owner's lease.
Active or ambiguous ownership remains fail-closed. Normal cleanup preserves the
same exclusive-ownership contract.

### Bounded visible completion and cleanup evidence

A completed review is accepted from stable visible assistant-turn identity and
text, stopped generation, composer readiness, conversation identity, and
interruption absence. Optional response-action controls do not hold a run open
for the full timeout. Final context-cleanup failures are persisted in the
same result artifact that the CLI reports.

### Lower-overhead selector path

Already-correct effort settings avoid locator discovery and focus work. Menu
close behavior uses one bounded hidden-state wait, while final model and effort
verification remains mandatory.

### Maintained-surface parity and regression proof

Canonical skill documentation, generated adapters, lifecycle tests, Python
runner tests, and repository contract checks describe and prove the same
behavior without adding a new orchestration or retry layer.

## Validation Consolidation

- Repository: `longdang193/project-OS-starter`.
- Reviewed revision: `b0a9473e9a7f7071e33b8d4ed3775986bd9aec68`.
- Remote evidence: local `HEAD`, `origin/main`, and `git ls-remote origin refs/heads/main` resolved to the same SHA before both reviews.
- GPT-6 High evidence: `.runtime/gpt6-live-probe/output/run-dHVsv2/result.json` and `response.md`; model and effort were visibly verified, one submission was acknowledged, completion was confirmed, and cleanup completed.
- GPT-5.6-Sol High evidence: `.runtime/gpt5-6-sol-live-probe/output/run-yU6JMQ/result.json` and `response.md`; model and effort were visibly verified, one submission was acknowledged, completion was confirmed, and cleanup completed.
- Both reviews confirmed the need to preserve one authenticated context with sequential fresh tabs. Neither review found a defect that reopens the whole browser between entries of a supported batch.
- Confirmed findings are listed below only when the cited control flow exists in the pinned source. Performance effects remain reasoned risks unless a task adds an identical before/after measurement.

### P1: Persistent profile leases can strand ownership after abnormal termination

Evidence: `run-review-prompt-cli.mjs:190-206` creates a sidecar lease with
`open(lockPath, "wx")`, records a PID, and treats every `EEXIST` as active
ownership. `:209-213` removes the lease only during normal release.

Validated impact: a crash, forced termination, or machine interruption can
leave future `--user-data-dir` runs blocked indefinitely. `closeContext()` also
releases the lease after a context-close error at `:263-292`, so uncertain
teardown can weaken the ownership guarantee.

Disposition: implement conservative owner-liveness and race-safe stale-lease
recovery; never reclaim by age alone and never reclaim ambiguous ownership.

### P1: Review-local selection failures abort otherwise healthy batches

Evidence: `run-review-prompt-cli.mjs:296-300` maps every selection-stage error
to `shared_context`, and `runReviewBatch()` stops on that value at `:445-459`.
`run-review-prompt.mjs:48-55` immediately checks menu visibility after
`Escape`, so a close animation can turn a page-local selector condition into a
shared-context stop.

Validated impact: a transient model-menu or page-local failure can tear down a
usable context and prevent later authorized reviews from running.

Disposition: classify review-local selection failures separately from proven
context loss; retain fail-closed handling for unknown failures and add one
bounded hidden-state wait after `Escape`.

### P2: Completion requires an optional response-action control

Evidence: `run-review-prompt.mjs:114-133` recognizes only `Regenerate response`
or `Rate response`; `evaluateReviewCompletion()` requires that signal at
`:136-155`, while the observer can wait 900 seconds at `:194-243`.

Validated impact: UI label or surface drift can leave stronger completion
signals satisfied while the runner consumes the full timeout and returns
`incomplete`, multiplying latency and browser-resource use in sequential runs.

Disposition: make stable new-turn identity/text, stopped generation, composer
readiness, conversation identity, and interruption absence primary completion
evidence. Keep response actions as optional corroboration or a short bounded
grace, not a 15-minute gate.

### P2: Input and batch preflight errors bypass the structured result contract

Evidence: `run-review-prompt-cli.mjs:497-506` parses the prompt or batch file
before the structured `try` at `:511`; module-level handling at `:576-582`
prints only a plain error.

Validated impact: controllers need two failure protocols and may misclassify a
missing prompt, malformed manifest, or unreadable file as a process failure.

Disposition: keep validation before browser launch but route it through the
same structured `blocked` result contract and preserve the exact failure stage.

### P2: Shared artifact failures can allow wasted later submissions

Evidence: artifact failures are assigned no scope by
`classifyFailureScope()` at `run-review-prompt-cli.mjs:296-300`, while the batch
loop stops only for `shared_context` at `:452-459`. Artifact persistence occurs
in `:401-415`.

Validated impact: a persistent shared output failure can cause later entries to
perform setup or submit prompts even though their evidence cannot be preserved.

Disposition: classify failures in the shared output root as
`shared_artifacts`, stop later entries, preserve already-written evidence, and
never retry a submitted review. Keep per-review evidence failures explicit
rather than silently treating them as success.

### P2: Final single-review context cleanup can disagree with result.json

Evidence: `run-review-prompt-cli.mjs:548-568` mutates the in-memory result after
`closeContext()` fails, but the result artifact was last persisted inside the
transaction before that final context cleanup.

Validated impact: stdout can report `incomplete` while `result.json` still says
`completed`, allowing automated consumers to accept a run the CLI rejected.

Disposition: persist the final cleanup state through the existing atomic writer
before returning the terminal result; add a regression assertion that stdout and
`result.json` agree.

### P3: Same-effort selection performs unnecessary UI work

Evidence: `select-review-model.mjs:114-154` reads the current effort, probes
multiple controls, focuses one, and only then calculates the delta.

Validated impact: repeated High-effort reviews incur avoidable DOM lookup,
hit-testing, and focus work, increasing selector failure opportunities.

Disposition: return immediately when the requested effort equals the visible
current effort, then retain independent final verification.

### P3: Early batch termination omits skipped entries from the summary

Evidence: `summarizeBatchResults()` counts only returned results at
`run-review-prompt-cli.mjs:175-184`; a stop at `:452-459` leaves later manifest
entries absent.

Validated impact: operators cannot distinguish a one-review attempt from a
completed multi-review request, complicating accounting and recovery decisions.

Disposition: preserve manifest total and report `requested_count`,
`attempted_count`, `completed_count`, `failed_count`, and `skipped_count`.

### Deferred or rejected claims

- Do not encode the exact `importModuleDynamically` VM failure as a repository
  defect; the maintained skill already defines the Node ESM runner boundary.
- Do not add adapter-specific context discovery or a second browser lifecycle
  owner without new boundary evidence.
- Do not replace fresh review tabs with same-page reuse without comparable
  latency, memory, and contamination measurements.
- Do not add automatic retries, model substitution, age-only lease deletion, or
  a general keep-open flag.
- The selector recovery branching in `select-review-model.mjs:37-68` and
  `:174-198` is retained as a lower-priority maintainability risk. It is not a
  confirmed functional defect in this plan; simplify it only if focused tests
  can preserve visible selection behavior without adding another recovery
  owner.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared canonical files, update tests and documentation, run declared local checks, run generated-surface synchronization, and preserve existing untracked probe artifacts
- User-approval actions: commit, push, PR, merge, branch/worktree deletion, and cleanup of preserved probe artifacts
- Parallel ownership: `none; tasks share the CLI lifecycle contract`
- Sequential fallback: complete Tasks 1–4 in order, then run Task 5 final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `b0a9473e9a7f7071e33b8d4ed3775986bd9aec68`
- Expected workspace: tracked plan update plus preserved untracked probe artifacts; do not stage or delete unrelated artifacts
- Next action: await explicit implementation approval, then begin Task 1
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | focused lifecycle tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | lease ownership tests | pending |
| Task 3 | `pending` | current | `unresolved` | Task 1 | completion/artifact/cleanup tests | pending |
| Task 4 | `pending` | current | `unresolved` | Task 1 | selector and effort tests | pending |
| Task 5 | `pending` | current | `unresolved` | Tasks 1–4 | full repository checks | pending |

## Task Breakdown

### Task 1: Make failure scopes and batch summaries truthful

**Purpose:**
- Prevent page-local or model-local selection failures from masquerading as
  authenticated-context loss while stopping on proven shared infrastructure
  failures.
- Report every requested batch entry, including entries that were not attempted.

**Task Function:**
- Define and test the runner's stage and batch settlement contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded lifecycle change with direct source and focused-test evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused lifecycle assertions and final repository checks.

**Specification Coverage:**
- P1 selection classification; P2 shared artifact settlement; P3 skipped-entry
  reporting; no retries or model substitution.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:classifyFailureScope`, `runReviewTransaction`, `runReviewBatch`, `summarizeBatchResults`
- Modify: the same CLI symbols and their result-schema fields
- Verify: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`

**Dependencies:**
- Current pinned source and the validation consolidation above.

**Authority:**
- Preauthorized local actions: edit the CLI and focused tests; run Node and Python focused checks
- Stop for: unresolved ownership of result fields, a required public-contract change not covered by tests, or any external Git action

**Steps:**
- [ ] Step 1: Add explicit failure scopes for review-local selection, shared context, and shared artifacts; keep unknown failures fail-closed.
- [ ] Step 2: Stop the batch on shared-context/shared-artifact failure, continue only after explicit review-local failure, and preserve submission acknowledgment without retrying.
- [ ] Step 3: Extend batch summaries with requested, attempted, completed, failed, and skipped counts while preserving existing terminal status semantics.
- [ ] Step 4: Add focused tests for page-local selection continuation, shared failure stop, artifact failure stop, and skipped-entry accounting.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: all new scope and summary assertions pass; no failed review is resubmitted.

**Exit Criteria:**
- Batch control flow and summaries identify the true failure boundary and every unattempted entry.

### Task 2: Harden persistent profile lease ownership

**Purpose:**
- Recover only demonstrably stale profile leases while preserving exclusive
  ownership for active or ambiguous owners.

**Task Function:**
- Implement and test conservative lease liveness and race handling.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-platform ownership and abnormal-termination risk require careful source-first reasoning.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic active/stale/malformed/race test matrix.

**Specification Coverage:**
- P1 stale lease recovery; no age-only deletion; no replacement-owner deletion.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:acquireProfileLease`, `releaseProfileLease`, `closeContext`
- Modify: the same lease and cleanup symbols
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 result schema and cleanup scope remain stable.

**Authority:**
- Preauthorized local actions: edit lease code and lifecycle tests; run platform-supported local process-liveness checks
- Stop for: ambiguous owner identity, platform behavior that cannot be proven on supported runners, or destructive lock removal

**Steps:**
- [ ] Step 1: Read and validate existing lease metadata when `EEXIST` occurs, including PID/profile identity and malformed-data handling.
- [ ] Step 2: Prove the owner is no longer running before attempting reclaim; preserve the lock when liveness is unknown.
- [ ] Step 3: Reclaim through an atomic race-safe operation that cannot delete a replacement lease; retain ownership when context teardown is uncertain.
- [ ] Step 4: Add tests for active owner, stale owner, malformed metadata, ambiguous liveness, reclaim race, normal release, and failed context close.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: active and ambiguous leases fail closed; only proven stale leases are reclaimed.

**Exit Criteria:**
- Abnormal termination no longer permanently poisons a reusable profile, and active ownership remains exclusive.

### Task 3: Make completion, artifact, input, and cleanup evidence consistent

**Purpose:**
- Avoid 15-minute false incompletes and ensure structured artifacts agree with
  the CLI's terminal status across preflight, persistence, and final cleanup.

**Task Function:**
- Align visible completion predicates and durable result settlement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: browser-visible state and durable evidence are tightly coupled and require focused regression proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct state-machine tests and artifact assertions.

**Specification Coverage:**
- P2 completion gate; P2 structured preflight; P2 shared artifact handling; P2 final cleanup persistence.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:evaluateReviewCompletion`, `waitForReviewCompletion`; `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:main`, `runReviewTransaction`
- Modify: completion predicate, bounded observer, structured preflight error path, artifact settlement, and final cleanup persistence
- Verify: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`, `tests/test_github_browser_reviews.py`

**Dependencies:**
- Task 1 failure scopes must be available for artifact and cleanup settlement.

**Authority:**
- Preauthorized local actions: edit canonical runner/helper code and focused tests; run local contract checks
- Stop for: a completion rule that accepts text without visible stopped/composer/context evidence, or a result artifact that cannot be written atomically

**Steps:**
- [ ] Step 1: Remove mandatory dependence on response-action controls while retaining stopped generation, composer readiness, conversation identity, new assistant turn, stable text, and interruption checks.
- [ ] Step 2: Move prompt/batch file loading and validation inside the structured result boundary without opening a browser for invalid input.
- [ ] Step 3: Persist final single-review context-cleanup failures through the existing atomic writer and keep artifact-stage failures fail-closed.
- [ ] Step 4: Add tests for changed response-action labels, bounded completion, missing prompt, malformed batch, shared artifact failure, and cleanup/result agreement.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- [ ] `python -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- Expected: terminal status, stdout, and saved artifacts agree; completion does not wait on optional controls indefinitely.

**Exit Criteria:**
- Every preflight, completion, artifact, and cleanup outcome has one structured, durable interpretation.

### Task 4: Reduce selector overhead without weakening visible verification

**Purpose:**
- Eliminate repeated same-effort locator/focus work and make menu-close timing
  resilient without introducing another browser lifecycle or retry owner.

**Task Function:**
- Simplify bounded selector transitions and preserve final visible state proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow UI-helper change with measurable DOM-operation regression proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused helper and lifecycle assertions.

**Specification Coverage:**
- P3 unchanged-effort overhead; P1 menu-close contribution to selection failure;
  model/effort verification remains mandatory.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs:setEffort`, `selectReviewModel`; `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:closeModelMenu`
- Modify: same-effort short circuit and bounded menu-close wait only
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 selection scope and Task 3 completion contracts remain stable.

**Authority:**
- Preauthorized local actions: edit selector helpers and focused tests; run local browser-helper simulations
- Stop for: any change that weakens visible model/effort verification or requires indefinite reopen/retry behavior

**Steps:**
- [ ] Step 1: Return from `setEffort()` immediately when the visible effort already equals the requested effort.
- [ ] Step 2: Wait up to the existing bounded timeout for the model menu to become hidden after `Escape`.
- [ ] Step 3: Preserve one bounded recovery transition and final `verifySelection()`; do not add general retries or page reuse.
- [ ] Step 4: Add assertions for zero focus/key operations on unchanged effort, nonzero adjustment on changed effort, hidden-menu timing, and visible final verification.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: unchanged effort performs no adjustment work; menu close tolerates its bounded animation; final selection remains visible and authoritative.

**Exit Criteria:**
- Repeated High-effort reviews avoid unnecessary selector work without changing the one-context/fresh-tab lifecycle.

### Task 5: Reconcile maintained surfaces and complete final verification

**Purpose:**
- Keep the canonical skill, generated adapters, tests, and repository contracts
  aligned with the implemented lifecycle contract.

**Task Function:**
- Synchronize maintained projections and produce fresh acceptance evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic generated-surface and repository verification.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independent final command results and clean Git evidence.

**Specification Coverage:**
- All implementation outcomes; generated parity; no unrelated artifact changes.

**Required Skills:**
- `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/SKILL.md`, `scripts/sync_agent_adapters.py`, `scripts/validate_repo_contracts.py`
- Modify: canonical documentation first, then generated adapters only through synchronization
- Verify: `generated_agents`, declared test suites, and Git inventory

**Dependencies:**
- Tasks 1–4 complete with focused proof.

**Authority:**
- Preauthorized local actions: run synchronization, contract validation, tests, diff checks, and read-only Git inspection
- Stop for: generated drift requiring hand edits, unrelated tracked changes, failed final proof, or any external publication action

**Steps:**
- [ ] Step 1: Update the canonical skill contract for failure scopes, completion evidence, lease recovery, and batch accounting.
- [ ] Step 2: Run `python scripts/sync_agent_adapters.py --all-platforms` and verify generated parity.
- [ ] Step 3: Run focused Node/Python tests and repository contract validation.
- [ ] Step 4: Run `git diff --check`, inspect staged/unstaged/untracked state, and record preserved probe artifacts without staging or deleting them.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- [ ] `python -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- [ ] `python scripts/validate_repo_contracts.py`
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `git diff --check`
- Expected: all checks pass, generated adapters match canonical sources, and unrelated probe artifacts remain untouched.

**Exit Criteria:**
- All validated findings have implementation and regression proof, maintained surfaces agree, and no unrelated workspace artifact was staged or removed.

## Verification

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `python -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- `python scripts/validate_repo_contracts.py`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. every implementation outcome is satisfied by Tasks 1–5
2. every task-local verification item passes
3. profile recovery is conservative, race-safe, and never age-only
4. selection and artifact failures expose the true stop boundary without retries or model substitution
5. completion, stdout, and durable result artifacts agree across success and failure paths
6. unchanged effort avoids unnecessary selector work while visible verification remains mandatory
7. one authenticated context and fresh-tab isolation remain the only browser lifecycle ownership model
8. canonical docs, generated adapters, tests, and validators are reconciled
9. preserved probe artifacts remain untracked and untouched
10. the plan remains `proposed` until explicit implementation approval activates it

## Known Limits And Deferred Work

- This plan does not claim that a particular VM lacks `importModuleDynamically`; only the maintained Node ESM execution boundary is established.
- This plan does not add adapter-specific context discovery, a second browser owner, or a general keep-open flag.
- Same-page reuse is deferred until comparable latency, memory, and contamination evidence exists.
- Selector recovery simplification beyond the bounded menu-close wait is deferred unless focused tests demonstrate a safe reduction.
- Final `completed` status belongs to `skill-verification-before-completion` after fresh implementation evidence; this document remains `proposed` until then.
