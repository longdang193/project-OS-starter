---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
name: github-browser-review-runner-hardening
parent_spec: none
targets:
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
  - generated_agents/
---

# GitHub Browser Review Runner Hardening

## Goal

Harden the GitHub Browser Reviews workflow against the validated failure modes
found in the read-only review of `longdang193/project-OS-starter` at immutable
commit `6238753e689746b7a9e957e21b2630743ce619d2`.

The implementation must preserve the existing read-only, exactly-once,
dedicated-profile, sequential-fresh-tab workflow while preventing false
terminal evidence, stranded leases, invalid direct-library submissions, and
avoidable batch-wide timeout amplification.

Validated review basis:

- `GPT-5.6-Sol`, High, completed run `run-fPEXw3`.
- `GPT-6`, High, completed run `run-7a8xgF`.
- Both reviews verified the same repository, pinned commit, model effort, and
  completion state. Full outputs remain under
  `.runtime/github-review/6238753e689746b7a9e957e21b2630743ce619d2/`.

## Implementation Outcomes

### Durable terminal evidence

- A failure writing `batch-result.json` never rewrites completed per-review
  `result.json` files as `skipped`.
- A final per-review artifact write failure cannot leave durable state claiming
  `completed` when cleanup or finalization was not durably recorded.
- Partial artifact allocation is finalized as blocked/not-dispatched evidence
  instead of leaving indefinite `running` records.

### Safe lifecycle and provenance

- Lease acquisition, setup cleanup, signal cleanup, browser ownership, and
  lease release share one failure-aware lifecycle boundary.
- `runReviewBatch()` validates every supplied review before the first
  submission, including repository/project identity and commit-pinned file
  URLs, not only the CLI manifest path.
- Commit-pinned blob URLs require a non-empty file path after the full SHA.
- Profile validation and lease identity use one canonical physical profile
  identity, including symlink/junction handling.

### Bounded batch behavior and evidence association

- Page-local failures remain review-scoped when the shared context is healthy.
- Shared model/composer/completion infrastructure failures stop the batch
  rather than repeating the same long timeout for every review.
- Ambiguous dispatch uses a shorter evidence-observation bound without ever
  resubmitting automatically.
- Completion evidence remains associated with one stable conversation identity.

### Maintained surfaces and proof

- Canonical skill documentation describes the strengthened lifecycle,
  provenance, artifact states, and failure-scope contract.
- Existing lifecycle, runner, skill, and generated-surface checks cover the
  new invariants.
- Generated agent mirrors are regenerated from `.agents/skills`; they are not
  edited directly.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: `edit the listed canonical skill, runner, test, and plan files; run focused Node/Python tests, adapter sync/checks, repository validators, and git diff checks`
- User-approval actions: `push, merge, publication, destructive recovery, credential/profile changes, and edits outside the listed targets`
- Parallel ownership: `none; runner and lifecycle changes share symbols and must be integrated sequentially`
- Sequential fallback: `complete Tasks 1 through 4 in order, then run Task 5 as the single fan-in verification and generated-surface reconciliation step`

## Task Breakdown

### Task 1: Unify review-definition and profile provenance validation

**Purpose:**
- Make the direct library batch API enforce the same repository, project,
  commit, URL, prompt, model, effort, and profile invariants as the CLI before
  any review submission.

**Task Function:**
- Contract hardening and input-validation consolidation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: direct validation boundary is bounded and source-coupled;
  delegation would add coordination without reducing risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused lifecycle and runner tests provide independent proof.

**Specification Coverage:**
- Direct-library batching must not bypass provenance or project isolation.
- Every reviewed URL must identify an exact commit-pinned file.
- Profile validation and lease identity must use the same physical target.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:readBatchReviews`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:validateReviewProvenance`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewBatch`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:validateProjectProfilePath`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:normalizeGitHubBlobUrl`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewBatch`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:validateProjectProfilePath`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`
- Verify: `tests/test_github_browser_review_runner.py`

**Dependencies:**
- None; current source and the pinned review findings are the authority.

**Authority:**
- Preauthorized local actions: `edit the validation and profile-identity symbols and add focused unit/lifecycle assertions in the listed tests`
- Stop for: `a changed public invocation contract, new credential requirement, network authentication, or any need to alter unrelated profile-management code`

**Steps:**
- [ ] Step 1: Extract one shared review-definition validation path used by
  single-review CLI input, batch manifests, and direct `runReviewBatch()` calls;
  require the attached/expected project key and reject mixed project keys
  before the first transaction.
- [ ] Step 2: Tighten `normalizeGitHubBlobUrl()` to require a non-empty path
  after the full 40-character commit SHA while preserving repository/SHA
  normalization and prompt URL-set checks.
- [ ] Step 3: Resolve the physical profile identity once for validation,
  lease naming, and browser launch; handle an existing profile with
  `realpath()` and a not-yet-created profile through its nearest existing
  parent without accepting normal Chrome-profile aliases.
- [ ] Step 4: Add negative tests for a direct-library mixed-repository batch,
  commit-only blob URLs, and symlink/junction aliases; retain positive tests
  for the existing derived profile path and pinned file URL.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: provenance, URL, and profile-identity tests pass; no browser is
  opened for invalid definitions.
- [ ] `pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- Expected: CLI and canonical-skill contracts remain satisfied.

**Exit Criteria:**
- All review definitions are rejected or accepted consistently before the
  first submission, and the exact-file/project/profile invariants have focused
  regression coverage.

### Task 2: Make setup, artifact allocation, and terminal persistence failure-safe

**Purpose:**
- Preserve truthful per-review evidence across lease/setup failures, partial
  artifact allocation, cleanup failures, and aggregate-summary write failures.

**Task Function:**
- Lifecycle state-machine hardening and durable artifact settlement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the changes cross shared cleanup and result-persistence
  symbols; one owner avoids inconsistent terminal-state semantics.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: injected-failure tests can deterministically prove every
  terminal path.

**Specification Coverage:**
- Exactly-once submission evidence must remain durable and truthful.
- Cleanup and lease failures must be observable and fail closed.
- Aggregate persistence failure must not mutate already-settled review records.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:openContext`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:openReviewContext`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:closeContext`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:allocateReviewArtifacts`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:persistBatchSummary`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:openContext`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:openReviewContext`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:main`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 complete so all allocated reviews carry validated provenance and a
  single project identity.

**Authority:**
- Preauthorized local actions: `edit lifecycle/result settlement symbols and add deterministic injected-failure tests using existing dependency seams`
- Stop for: `a new persisted state machine, incompatible result-schema migration, deletion of existing evidence, or destructive cleanup of pre-existing runtime artifacts`

**Steps:**
- [ ] Step 1: Establish setup cleanup as soon as a profile lease is acquired;
  ensure launch/preflight failures release the lease and close owned context
  without suppressing the cleanup cause, while preserving fail-closed
  ambiguity when ownership cannot be proven.
- [ ] Step 2: Move batch artifact allocation inside the protected controller
  boundary; if allocation partially succeeds, finalize created run records as
  blocked with `dispatch_state: not_dispatched` and emit an artifact-stage
  batch failure without pretending a browser failure occurred.
- [ ] Step 3: Change per-review settlement so `completion: confirmed` may be
  persisted before cleanup, but `status: completed` is written only after
  cleanup and the final durable result write succeed. A failed final write
  must leave the last durable state nonterminal and diagnostic.
- [ ] Step 4: Separate `persistBatchSummary()` errors from browser/context
  errors. Preserve all original per-review results, return nonzero/incomplete,
  and record the aggregate-write failure without rewriting results as skipped.
- [ ] Step 5: Keep one lifecycle owner for context close and lease release;
  remove any duplicate signal/cleanup owner introduced during the change.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: injected launch, preflight, lease-release, partial-allocation,
  final-result-write, and batch-summary-write failures preserve truthful
  per-review state and never produce false `skipped` outcomes.
- [ ] `pytest -q tests/test_github_browser_review_runner.py`
- Expected: owned-profile and batch failure contracts remain fail-closed.

**Exit Criteria:**
- Every setup, transaction, cleanup, and aggregate-persistence failure has a
  durable, non-contradictory result or an explicit blocked condition; no lease
  or artifact path is silently abandoned.

### Task 3: Correct failure scope and bound batch-wide timeout amplification

**Purpose:**
- Distinguish review-local tab failures from shared-context failures and stop
  repeating known systemic UI failures across every remaining batch entry.

**Task Function:**
- Failure taxonomy, bounded observation, and sequential batch control.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: classification and batch continuation share one contract and
  must be changed together.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lifecycle tests can simulate page/context health and timeout
  outcomes without live browser access.

**Specification Coverage:**
- Page-local closure must not cancel a healthy shared context.
- Shared selector/composer/completion failures must stop the batch.
- Ambiguous dispatch must never resubmit and must have a shorter observation
  bound than normal confirmed generation.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:withFailureScope`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/waitForReviewCompletion`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/runReviewPromptInNewTab`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewBatch`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:withFailureScope`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:waitForReviewCompletion`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewBatch`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 2 complete so failure results and skipped entries are durably truthful.

**Authority:**
- Preauthorized local actions: `edit failure classification, bounded completion observation, and batch continuation logic plus isolated lifecycle tests`
- Stop for: `automatic retry/resubmission, a new browser lifecycle owner, unbounded polling, or a change that weakens fail-closed handling of ambiguous dispatch`

**Steps:**
- [ ] Step 1: Replace message-only shared-context inference with structured
  failure codes and a context-health decision; classify a closed/crashed tab
  as review-scoped when the shared context is still usable.
- [ ] Step 2: Mark missing shared composer/model/completion infrastructure as
  shared-context/systemic and stop the batch after the first confirmed shared
  failure; keep genuinely model-specific or page-readiness failures
  review-scoped.
- [ ] Step 3: Add a distinct bounded ambiguity-observation timeout for a send
  acknowledgement failure when no new assistant turn, generation, or visible
  dispatch evidence exists. Preserve `possibly_dispatched` and never call
  submission again.
- [ ] Step 4: Preserve the existing normal completion timeout for confirmed or
  visibly active generations and retain visible interruption handling.
- [ ] Step 5: Add tests for healthy-context page closure, systemic selector
  failure, repeated batch entries, ambiguous send, and no-resubmission proof.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: page-local failures continue only when safe, systemic failures
  stop the batch, ambiguous sends finish within the shorter bound, and no test
  observes a second submission attempt.

**Exit Criteria:**
- A single recoverable tab failure no longer cancels an otherwise healthy
  batch, while shared UI failures cannot multiply the full completion timeout
  across all remaining entries.

### Task 4: Bind completion to one conversation and align canonical documentation

**Purpose:**
- Prevent a visible response from another conversation from being accepted as
  the review result and document the strengthened contracts for maintainers.

**Task Function:**
- Evidence-association hardening and canonical method documentation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation must be updated with the final code contract,
  not independently invented.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: source-level lifecycle tests and skill contract tests prove
  the documented invariants.

**Specification Coverage:**
- Completion evidence must cite the stable review conversation.
- Canonical `.agents/skills` sources own behavior and generated mirrors derive
  from them.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:runReviewPrompt`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/evaluateReviewCompletion`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/waitForReviewCompletion`
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`
- Verify: `tests/test_skill_github_browser_reviews.py`

**Dependencies:**
- Tasks 1 through 3 complete; documentation must describe the final result and
  failure-state contracts.

**Authority:**
- Preauthorized local actions: `edit completion-association logic and canonical skill documentation, then extend focused contract tests`
- Stop for: `new public review-request wording, private credential/profile details, or direct edits to generated adapter mirrors`

**Steps:**
- [ ] Step 1: Bind the first post-submit conversation identity to the review
  baseline and require it to remain stable through completion; any unexpected
  identity switch returns incomplete rather than confirmed.
- [ ] Step 2: Document the shared validation boundary, lifecycle ownership,
  artifact settlement semantics, failure-scope categories, ambiguity timeout,
  and stable conversation evidence in `SKILL.md`.
- [ ] Step 3: Update skill contract tests for the new documented invariants
  without weakening the existing explicit-invocation, read-only, model,
  effort, pinned-revision, and no-retry requirements.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: conversation-identity mismatch is incomplete and stable identity
  is confirmed only with the expected assistant turn.
- [ ] `pytest -q tests/test_github_browser_reviews.py`
- Expected: canonical skill text contains the strengthened lifecycle and
  evidence requirements and still rejects forbidden legacy paths.

**Exit Criteria:**
- Source behavior, tests, and canonical skill documentation agree on stable
  completion association and the strengthened fail-closed workflow.

### Task 5: Regenerate mirrors and run final repository verification

**Purpose:**
- Reconcile generated agent surfaces and produce fresh evidence that the
  implementation is complete without directly editing generated files.

**Task Function:**
- Generated-surface reconciliation and final verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final fan-in is repository-wide and must remain under one
  acceptance owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository validators and focused tests provide independent
  final evidence.

**Specification Coverage:**
- Canonical source remains the SSOT.
- Generated adapters match canonical skill sources.
- Final status must be based on fresh checks, not task checkboxes alone.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`
- Modify: `generated_agents/` via `scripts/sync_agent_adapters.py` only
- Verify: `generated_agents/codex/skills/skill-github-browser-reviews/`
- Verify: `generated_agents/claude/skills/skill-github-browser-reviews/`
- Verify: `generated_agents/antigravity/skills/skill-github-browser-reviews/`
- Verify: `docs/superpowers/plans/2026-10-25-github-browser-review-runner-hardening-plan.md`

**Dependencies:**
- Tasks 1 through 4 complete.

**Authority:**
- Preauthorized local actions: `run the approved adapter sync/check, focused tests, repository validators, and git diff checks; update only generated mirrors produced by the sync script`
- Stop for: `publication, push, destructive cleanup, generated drift requiring manual edits, or any unrelated failing test outside this plan's changed surfaces`

**Steps:**
- [ ] Step 1: Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [ ] Step 2: Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check` and inspect that only expected canonical/generated files differ.
- [ ] Step 3: Run focused Node and Python tests for the review runner and skill.
- [ ] Step 4: Run repository contract validation and `git diff --check`.
- [ ] Step 5: Reconcile any generated or test failures against current source;
  do not weaken validators or edit generated mirrors manually.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: lifecycle regression suite passes.
- [ ] `pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- Expected: runner and skill contract suites pass.
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated adapters are in sync.
- [ ] `py -3 scripts/validate_repo_contracts.py --repo-root .`
- Expected: repository contract validation passes.
- [ ] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- All required tests and validators pass, generated mirrors match canonical
  sources, no unrelated scope is introduced, and the plan remains `proposed`
  until an implementation executor and final verifier produce fresh evidence.

## Verification

Use this section for final artifact-level verification only.

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_repo_contracts.py --repo-root .`
- `git diff --check`

Expected final evidence:

- No false `skipped`, stale `completed`, or orphaned `running` records under
  injected persistence/cleanup failures.
- Invalid direct-library review definitions fail before submission.
- Profile aliases cannot bypass validation or lease identity.
- Page-local failures do not stop a healthy batch; systemic failures stop it
  without multiplying long completion waits.
- Ambiguous dispatch remains exactly-once and bounded.
- Completion evidence stays on one conversation identity.
- Canonical and generated skill surfaces are synchronized.

## Completion Criteria

The plan is ready for completion verification when:

1. Tasks 1 through 5 have fresh task-local evidence and no unresolved required
   task remains.
2. All validated high- and medium-severity findings in the review basis are
   either implemented and proven or explicitly recorded as deferred with an
   owner and reason.
3. Existing read-only, exactly-once, dedicated-profile, model/effort,
   pinned-revision, and no-retry invariants remain covered by tests.
4. Canonical skill sources, runner scripts, tests, generated mirrors, and
   repository validators agree.
5. No browser credentials, private profile data, runtime output, or review
   transcripts are added to tracked source files.
6. `skill-verification-before-completion` runs the final commands above and
   returns `verified` before the plan status changes from `proposed`.

Lower-priority review suggestions about exact model-label matching, broad
visible-page diagnostic capture, and pre-browser remote reachability checks are
not included in this minimum hardening plan. They remain optional follow-up
work unless implementation reveals a concrete failure or the owner expands
scope.
