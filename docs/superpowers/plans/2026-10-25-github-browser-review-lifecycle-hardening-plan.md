---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
---

# GitHub Browser Review Lifecycle Hardening Plan

## Goal

Harden the GitHub browser-review runner against confirmed lifecycle and evidence failures found by source validation after both requested model reviews completed. Preserve exactly-once submission, one authenticated browser context per batch, fresh review-tab isolation, pinned GitHub provenance, and fail-closed terminal statuses while preventing submitted work, cleanup state, or batch accounting from being lost or misclassified.

Review basis:

- Current source commit: `53c328e9097f6442d545ff8cc4570bb8cd0e531b`.
- Historical `GPT-5.6-Sol / High` review: completed and recorded against `33abcd9c77139ed8463aeb46e32d8651e0bdbacb`; the preserved response evidence is partial, so it is not used for unique finding attribution.
- Current `GPT-6 / High` review: completed and verified against `53c328e9097f6442d545ff8cc4570bb8cd0e531b`; full output is preserved in the local review artifacts.
- Validated source surfaces: `.agents/skills/skill-github-browser-reviews/SKILL.md`, `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`, `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`, and `tests/test_github_browser_review_lifecycle.mjs`.

## Validated Findings

1. **P1 — Ambiguous dispatch uses the 15-second ambiguity deadline even after generation becomes visible.** `runReviewTransaction()` passes `AMBIGUOUS_DISPATCH_TIMEOUT_MS` to completion observation for a possibly dispatched request, while `waitForReviewCompletion()` never promotes the deadline after visible generation starts. A valid long-running review can be marked incomplete and its tab closed.
2. **P1 — A post-submit checkpoint failure skips response preservation.** After the page is assigned to the transaction, a persistence failure at the acknowledged-dispatch checkpoint does not carry `error.reviewPage`; the catch path therefore skips bounded completion observation and closes the owned page.
3. **P1 — Final persistence can leave stale durable success evidence.** The transaction persists `status: completed` before page cleanup, then changes only the in-memory result when the final persistence write fails. `result.json` can therefore disagree with the returned result.
4. **P1 — Single-review browser initialization errors can be masked.** Single-review mode reaches the browser-stage catch without a `runOutputDir`, then calls `relative(process.cwd(), reviews[0].runOutputDir)`, which can throw a secondary argument error instead of persisting the intended blocked result.
5. **P2 — Shared-context health classification relies on `context.pages()` as a connection probe.** A Playwright context can expose the synchronous page accessor after the underlying connection is lost, so the disconnected-context branch can be misclassified as review-local failure.
6. **P2 — The documented direct CDP batch API does not provide the identity required by `validateReviewBatch()`.** CDP attachments return no repository/project metadata, while the documented `runReviewBatch({ attached, reviews, outputDir })` shape depends on either attached metadata or explicit identity.
7. **P2 — Profile-key derivation is lossy.** `owner/repository` is flattened with a single hyphen, so distinct repositories such as `foo-bar/baz` and `foo/bar-baz` can map to the same persistent profile directory.
8. **P2 — Setup cleanup failures are suppressed.** Profile-lease release and preflight context cleanup errors are discarded, leaving resource ownership uncertain and making later profile blocks difficult to diagnose.
9. **P2 — Batch context-cleanup failures do not persist the aggregate `batch-result.json`.** Per-review cleanup state is attempted, but the main cleanup-error branch reconstructs an aggregate result without calling `persistBatchSummary()`.
10. **P3 — `attempted_count` is derived from non-skipped status rather than dispatch state.** Reviews blocked during partial artifact allocation are counted as attempted even though they never reached submission.

Excluded as non-findings: browser/context recreation, fresh-tab isolation, model/effort selection internals outside the reviewed files, request-level provenance validation, and exactly-once submission behavior. These were either supported by the current control flow or outside the requested source scope.

## Implementation Outcomes

### Reliable post-dispatch observation
Ambiguous dispatches receive a short acknowledgement window only until dispatch evidence is found; once a generation or equivalent response association is visible, observation uses the normal completion deadline without resubmitting. Any persistence error after acknowledged dispatch preserves the existing page and attempts bounded completion evidence before teardown.

### Consistent durable terminal evidence
Review artifacts never publish a durable terminal success state before cleanup and final persistence are settled. Returned results and `result.json` agree on status, cleanup state, failure scope, and evidence-integrity failures. Single-review browser-stage failures always produce a structured result when artifact allocation is possible, without secondary path errors.

### Explicit context and resource ownership
Persistent-profile and CDP attachments expose a common validated context descriptor. Disconnected shared contexts are classified as shared-context failures using explicit owner state or connection-loss evidence. Setup and teardown failures preserve both the primary error and cleanup uncertainty.

### Collision-safe identity and accurate batch accounting
Profile binding prevents lossy repository-key collisions without silently copying or deleting credentials. Batch summaries persist on every handled terminal path and distinguish transactions started, submission attempts, and acknowledged dispatches from reviews that were blocked before dispatch.

### Maintained generated surfaces and regression proof
Canonical skill and runner sources remain authoritative; generated adapter mirrors are refreshed only through `scripts/sync_agent_adapters.py`. Focused lifecycle tests cover every corrected failure path, including on-disk artifact assertions and shared-context/CDP metadata behavior.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-writing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution` unless separately authorized after fresh verification
- Preauthorized local actions: inspect source/tests, edit canonical runner/skill/test files, regenerate declared adapter mirrors, run focused and repository contract checks, and preserve local diagnostics
- User-approval actions: commit, push, pull-request publication, merge, profile migration, credential movement, or destructive cleanup
- Parallel ownership: `none`; `run-review-prompt.mjs`, `run-review-prompt-cli.mjs`, tests, and generated mirrors have shared lifecycle contracts and must be serialized
- Sequential fallback: execute Tasks 1–7 in order in the current workspace; stop at any failed task-local proof or unresolved profile migration decision

## Coordination State

Omitted because this is an inline sequential plan with no delegated or parallel work.

## Task Breakdown

### Task 1: Establish failing lifecycle regression coverage

**Purpose:**
- Convert every validated finding into a focused failing test or assertion before changing production behavior.

**Task Function:**
- Reproduce the confirmed lifecycle failures and define the smallest observable contracts for recovery, persistence, cleanup, and accounting.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source-first debugging and test design in one small Node test surface.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: task-local assertions are reviewed by the lead controller and final verification.

**Specification Coverage:**
- Findings 1–10 above; preserve exactly-once submission and fail-closed lifecycle states.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `tests/test_github_browser_review_lifecycle.mjs`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction, runReviewBatch, main, summarizeBatchResults, classifyFailureScope`
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:waitForReviewCompletion`
- Modify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Current source remains at `53c328e9097f6442d545ff8cc4570bb8cd0e531b` or a declared equivalent base.
- Existing tests and mocks are authoritative for injection seams; do not broaden browser integration scope.

**Authority:**
- Preauthorized local actions: add focused tests and test doubles only in the declared test file; run the focused Node suite.
- Stop for: a behavior decision not derivable from current lifecycle contracts, a required external browser credential, or a test that cannot demonstrate the defect without changing production code first.

**Steps:**
- [ ] Step 1: Add a failing test showing an ambiguous dispatch that becomes visibly generating must receive the normal completion budget rather than the 15-second ambiguity budget.
- [ ] Step 2: Add failing tests for post-submit checkpoint persistence failure preserving the owned page, final persistence failure updating durable `result.json`, and single-review context-open failure producing a structured blocked result.
- [ ] Step 3: Add failing tests for disconnected-context classification, CDP batch identity requirements, cleanup-error composition, batch aggregate persistence, collision-safe profile binding, and explicit attempted/submission/acknowledged counts.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: new tests fail for the intended missing behavior while existing unrelated tests remain green.

**Exit Criteria:**
- Every included finding has a deterministic regression assertion or is explicitly covered by an existing test extended with the missing durable-state assertion.

### Task 2: Fix post-dispatch completion observation and preservation

**Purpose:**
- Ensure an acknowledged or visibly active review is observed to completion without retrying or closing its page prematurely.

**Task Function:**
- Simplify the completion deadline state machine and preserve the owned page across post-dispatch artifact failures.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-risk lifecycle behavior with a single canonical runner owner.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused Node regression proof and final source reconciliation.

**Specification Coverage:**
- Findings 1 and 2; exactly-once submission, one context, fresh review tab, and bounded observation remain unchanged.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:waitForReviewCompletion, runReviewPromptInNewTab`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:waitForReviewCompletion`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 failing tests define the observable deadline and preservation contracts.
- Do not change the single-tab-per-review policy or introduce a resubmission path.

**Authority:**
- Preauthorized local actions: edit the two canonical runner modules and their focused tests; run Node tests.
- Stop for: a change that requires a new model-selection contract, browser profile migration, or retry behavior.

**Steps:**
- [ ] Step 1: Separate ambiguity detection from completion observation. Keep the short deadline only until dispatch/generation evidence is observed; promote to the normal completion deadline once generation is visible or an associated new assistant turn is established.
- [ ] Step 2: When a post-submit checkpoint or artifact write fails after the transaction owns `page` and dispatch is not `not_dispatched`, invoke bounded completion observation from the local page regardless of `error.reviewPage` metadata.
- [ ] Step 3: Preserve the artifact error separately from completion evidence; never overwrite a confirmed response with a misleading review-local failure, and never resubmit.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: ambiguous visible generation completes under the normal deadline; checkpoint failure still captures completion evidence; exactly-once assertions remain green.

**Exit Criteria:**
- A valid long-running response cannot be classified incomplete solely because acknowledgement was ambiguous or a checkpoint write failed after dispatch.

### Task 3: Make transaction artifacts durable and single-review failures structured

**Purpose:**
- Align returned and persisted results and prevent browser-stage error handling from masking the original failure.

**Task Function:**
- Establish a clear terminal-state ordering for review results and allocate single-review artifacts before browser initialization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared artifact contract across single and batch modes.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: on-disk result assertions plus focused failure injection.

**Specification Coverage:**
- Findings 3 and 4; durable evidence must remain fail-closed and cleanup status must be explicit.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction, main, createResult, persistCleanupFailure`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction, main`
- Modify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 2 establishes whether completion evidence is available before finalization.
- Artifact writes must remain atomic and existing per-review paths must be preserved.

**Authority:**
- Preauthorized local actions: change local result-state ordering, allocation timing, and focused tests; run direct artifact-state verification.
- Stop for: any requirement to delete or rewrite existing review artifacts, move credentials, or claim success when final persistence cannot be proven.

**Steps:**
- [ ] Step 1: Allocate the single-review run directory before `openContextForReview()` or guard the browser-stage catch so `undefined` never reaches `relative()`; persist a structured blocked result whenever allocation succeeded.
- [ ] Step 2: Introduce an internal nonterminal completion-confirmed state or equivalent in-memory sequencing so `status: completed` is not durably written until page cleanup and final result persistence have succeeded.
- [ ] Step 3: On final persistence failure, preserve an explicit artifact-integrity failure and make the on-disk result either atomically reflect that failure or remain clearly nonterminal; add assertions against both returned and persisted JSON.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: browser-open failures return structured blocked results; final persistence failures cannot leave stale durable `status: completed` evidence.
- [ ] Direct inspection of generated `result.json` fixtures confirms `status`, `cleanup_status`, `failure_stage`, and `failure_reason` agree with the returned result.

**Exit Criteria:**
- Every single-review terminal path has an allocated or explicitly unavailable artifact outcome, and no durable artifact claims completed work after an unresolved cleanup/persistence failure.

### Task 4: Normalize context ownership, health, and cleanup diagnostics

**Purpose:**
- Make persistent-profile and CDP execution paths share the same identity and resource-ownership contract.

**Task Function:**
- Replace inferred connection health with explicit owner state and preserve primary plus cleanup failures without unsafe recovery.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-mode lifecycle contract with bounded API changes.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: injected context/browser mocks and direct batch API tests.

**Specification Coverage:**
- Findings 5, 6, and 8; fail closed on unknown context ownership and retain cleanup uncertainty.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:openContext, openReviewContext, closeContext, classifyFailureScope, isContextHealthy, runReviewBatch`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:context descriptor and failure classification`
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md:CDP/programmatic batch invocation and cleanup diagnostics`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 defines the required mock behavior and failure evidence.
- The CLI’s persistent profile lease remains the ownership mechanism; no automatic stale-lock deletion is added.

**Authority:**
- Preauthorized local actions: normalize metadata fields, add explicit connection-health state, compose cleanup errors, update canonical documentation, and add tests.
- Stop for: a need to attach to an unauthenticated browser, retry context creation, delete a lease, or broaden CDP permissions.

**Steps:**
- [ ] Step 1: Return a common attached-context descriptor from persistent-profile and CDP paths containing repository/project identity, ownership, browser/context handles, and explicit connection state.
- [ ] Step 2: Require explicit repository/project identity for direct CDP `runReviewBatch()` calls when the attachment cannot prove it; update the documented invocation and preserve fail-closed validation.
- [ ] Step 3: Track context closure/disconnection explicitly and use known connection-loss errors plus owner state for shared-context classification instead of treating `context.pages()` as a health probe.
- [ ] Step 4: Preserve setup cleanup failures alongside primary errors, mark lease/resource state uncertain, and ensure final cleanup diagnostics survive structured result persistence.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: disconnected contexts classify as shared-context failures; CDP calls without identity fail clearly before dispatch; primary and cleanup errors are both observable.

**Exit Criteria:**
- All context attachment modes expose the same required identity and cleanup semantics, and no cleanup failure is silently discarded.

### Task 5: Prevent profile identity collisions without unsafe migration

**Purpose:**
- Stop distinct repositories from silently sharing a persistent profile while preserving the explicit profile-path and credential-safety boundary.

**Task Function:**
- Design and implement a collision-resistant binding check with a controlled compatibility path for existing profiles.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: identity and credential-isolation risk requires conservative fail-closed behavior.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: deterministic collision fixtures and existing-profile compatibility tests.

**Specification Coverage:**
- Finding 7; no automatic credential copy, profile deletion, or silent legacy migration.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:deriveProjectKey, validateProjectProfilePath, openContext`
- Inspect: `.agents/skills/skill-github-browser-reviews/SKILL.md:dedicated profile derivation and profile ownership`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:profile identity validation`
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md:profile binding and migration instructions`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 4’s common context descriptor must retain the normalized repository identity.
- The current required profile path contract must be reviewed before changing path names; default behavior must not silently move credentials.

**Authority:**
- Preauthorized local actions: add deterministic collision tests, binding metadata validation, and documentation for a controlled migration path.
- Stop for: changing the required derived profile path without explicit contract approval, copying browser credentials, deleting old profiles, or silently accepting an ambiguous legacy directory.

**Steps:**
- [ ] Step 1: Add regression fixtures proving the current flattening collision and define the canonical repository identity that must be bound to a profile.
- [ ] Step 2: Implement either an unambiguous derived key or an explicit profile binding marker, preserving the current path contract only when the marker proves the requested repository; ambiguous legacy profiles fail closed with an operator-directed migration message.
- [ ] Step 3: Document the one-time operator migration procedure without automating credential movement or destructive cleanup.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: colliding repository identifiers cannot launch against one another’s profile; valid existing profiles remain usable through the documented compatibility path.

**Exit Criteria:**
- Profile identity is collision-safe or explicitly blocked when identity cannot be proven, with no automatic credential migration.

### Task 6: Persist batch terminal state and separate lifecycle counts

**Purpose:**
- Make batch-level durable evidence complete on cleanup failures and make accounting reflect actual lifecycle progress.

**Task Function:**
- Centralize aggregate summary finalization and derive counts from explicit lifecycle fields.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic batch state/accounting change with existing helper seams.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused batch fixtures and on-disk summary assertions.

**Specification Coverage:**
- Findings 9 and 10; preserve per-review artifacts, skipped semantics, and exactly-once accounting.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewBatch, summarizeBatchResults, settleArtifactAllocationFailure, persistBatchSummary, main`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:batch finalization and counters`
- Modify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 3 establishes artifact-integrity semantics.
- Task 4 establishes shared-context cleanup error propagation.

**Authority:**
- Preauthorized local actions: update batch aggregation, counters, and focused tests; run direct batch failure simulations.
- Stop for: changing submission policy, treating skipped work as attempted, or discarding per-review artifacts to simplify aggregation.

**Steps:**
- [ ] Step 1: Route successful batches, artifact-allocation failures, shared-context failures, and cleanup failures through one aggregate-summary finalization path that always attempts `batch-result.json` persistence.
- [ ] Step 2: Preserve per-review cleanup/error state when aggregate persistence fails and expose aggregate persistence failure independently.
- [ ] Step 3: Replace derived `attempted_count` with explicit counts for transactions started, submissions attempted, and acknowledged dispatches; retain compatibility fields only if current consumers require them and document their semantics.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: every handled batch terminal path writes an aggregate summary or records an explicit artifact failure; partial allocation reports zero submission attempts for never-dispatched reviews.

**Exit Criteria:**
- Batch durable evidence and lifecycle accounting are consistent across success, skip, block, cleanup-failure, and artifact-failure paths.

### Task 7: Refresh generated surfaces and complete repository verification

**Purpose:**
- Reconcile canonical source, generated adapters, documentation, tests, and repository contracts before implementation handoff.

**Task Function:**
- Perform generated-surface synchronization and fresh final verification without changing unrelated files.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository maintenance and validation.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: repository validators and focused test output.

**Specification Coverage:**
- Generated-surface rule, source/test authority, and all implementation outcomes.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-writing-plans`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/`
- Modify through sync only: `generated_agents/antigravity/skills/skill-github-browser-reviews/`, `generated_agents/claude/skills/skill-github-browser-reviews/`, `generated_agents/codex/skills/skill-github-browser-reviews/`
- Verify: `scripts/sync_agent_adapters.py`, `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`

**Dependencies:**
- Tasks 1–6 complete with focused tests passing.
- Canonical files are the only hand-edited source for generated adapter content.

**Authority:**
- Preauthorized local actions: run canonical sync, validators, focused tests, and diff checks; inspect and report any unrelated drift.
- Stop for: generated drift outside the declared skill, failing repository contracts, unrelated working-tree modifications, or any request to publish/merge without separate authorization.

**Steps:**
- [ ] Step 1: Run `py -3 scripts/sync_agent_adapters.py --all-platforms`; do not edit generated mirrors directly.
- [ ] Step 2: Run focused lifecycle tests and the relevant Python contract/adapter/planning validators.
- [ ] Step 3: Review `git diff --check`, generated headers, changed-file scope, and the final result-artifact contract.

**Verification:**
- [ ] `node --test tests/test_github_browser_review_lifecycle.mjs`
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `py -3 scripts/validate_repo_contracts.py --fast`
- [ ] `py -3 scripts/validate_planning_lifecycle.py`
- [ ] `git diff --check`
- Expected: all checks pass; only declared canonical, generated, test, and documentation surfaces differ.

**Exit Criteria:**
- The implementation handoff contains fresh proof for all corrected lifecycle paths, generated adapters are synchronized, and no commit/push/merge is claimed without explicit follow-up authorization.

## Verification

## Execution Record

- Tasks 1–6 executed in the current workspace with focused regression coverage for completion promotion, post-submit evidence preservation, durable terminal status, single-review setup failures, shared-context classification, CDP identity, profile binding, setup cleanup diagnostics, batch aggregate persistence, and explicit lifecycle counts.
- Canonical runner and skill documentation were updated; generated adapter mirrors were refreshed with `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- Fresh proof currently passes: `node --test tests/test_github_browser_review_lifecycle.mjs`, `py -3 scripts/sync_agent_adapters.py --all-platforms --check`, `py -3 scripts/validate_repo_contracts.py --fast`, `py -3 scripts/validate_planning_lifecycle.py`, and `git diff --check`.
- Unrelated local artifacts preserved: `.playwright-mcp/`, `.review-profile/`, `.runtime/`, and `node_modules/`.

Use this section for final artifact-level verification only.

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `py -3 scripts/validate_planning_lifecycle.py`
- `git diff --check`
- Expected: focused lifecycle tests, repository contracts, planning lifecycle, generated-adapter drift, and whitespace checks all pass against the implemented candidate.

## Completion Criteria

The plan is ready for completion verification when:

1. all ten validated findings have either an implemented regression fix or an explicitly approved residual-risk decision;
2. ambiguous and acknowledged post-dispatch work is observed without resubmission or premature page closure;
3. returned results and durable per-review/batch artifacts agree on terminal status and cleanup/resource uncertainty;
4. persistent-profile and CDP paths share explicit identity and context-ownership semantics;
5. profile collisions fail closed or use an approved collision-safe binding without automatic credential migration;
6. batch summaries and lifecycle counts accurately distinguish blocked, skipped, started, attempted, and acknowledged work;
7. canonical skill sources, generated adapters, tests, and documentation are synchronized; and
8. fresh final verification records command output and any remaining blocker before branch disposition.

The plan may be marked `completed` only after `skill-verification-before-completion` performs fresh final verification and records the exact implementation candidate SHA and evidence paths. Push, pull-request creation, merge, profile migration, and destructive cleanup remain separate explicitly authorized actions.
