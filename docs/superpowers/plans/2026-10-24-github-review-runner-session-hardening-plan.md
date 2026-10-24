---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: github-review-runner-session-hardening
targets:
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - tests/test_github_browser_review_lifecycle.mjs
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - AGENTS.md
  - .agents/rules
  - generated_agents
  - docs/superpowers/plans/2026-10-24-github-review-runner-session-hardening-plan.md
---

# GitHub Review Runner Session Hardening Plan

## Goal

Harden the GitHub browser-review runner around failure classification, persistent
profile recovery, and repeated effort selection while preserving the existing
single authenticated context, sequential fresh-tab isolation, no-model-fallback,
single-submission, and cleanup ownership contracts.

This plan contains only findings validated by source inspection, focused tests,
and the completed GPT-5.6-Sol High and GPT-6 High GitHub browser reviews of
commit `e616fe8ab447452c83019d5539eb0ef77f762066`.

## Review Basis

- Repository: `longdang193/project-OS-starter`
- Reviewed revision: `e616fe8ab447452c83019d5539eb0ef77f762066`
- Base containing the merged revision: `origin/main` at `d5071a3f0bd63aba5c3b43befde103c85fb88d32`
- GPT-5.6-Sol High: verified the pinned revision and identified stale profile-lease recovery, broad selection-failure scope, and unchanged-effort selector churn as actionable findings.
- GPT-6 High: verified the pinned revision and confirmed the broad selection-failure classification; it rejected the exact VM-internal cause and external adapter capability as unproven claims.
- Local evidence: `run-review-prompt-cli.mjs:190-213`, `run-review-prompt-cli.mjs:296-300`, `run-review-prompt-cli.mjs:445-459`, `select-review-model.mjs:114-153`, and lifecycle tests covering selection failure, batch stopping, and profile exclusivity.

## Validated Findings And Disposition

### P2: Selection failures are overclassified as shared-context failures

`classifyFailureScope()` maps every transaction failure at the `selection` stage
to `shared_context`. `runReviewBatch()` stops all later manifest entries when it
sees that scope. A page-local selector failure or a model-specific unavailability
therefore terminates the shared context even when the authenticated context is
still usable. Existing tests prove the stop behavior but do not distinguish
page-local, model-specific, and context-invalid failures.

Disposition: implement a narrow failure taxonomy and continue only when the
failure is explicitly page/review-scoped or model-scoped. Unknown selection
failures remain fail-closed as `shared_context` until a health check proves the
context can safely continue. Never retry or substitute the failed review.

### P2: Persistent profile leases can remain stranded after abnormal termination

`acquireProfileLease()` creates a sidecar lock with `open(lockPath, "wx")` and
writes only PID/profile metadata. `releaseProfileLease()` removes it only on
normal cleanup. A crash, forced termination, or machine interruption can leave a
lock that blocks future reuse indefinitely; the current test covers concurrent
exclusion and normal release only.

Disposition: add conservative, explicit stale-lease recovery. Recovery must
fail closed when ownership is ambiguous, must verify the recorded owner is no
longer running using a platform-supported identity/liveness probe, must avoid
deleting a replacement owner's lock, and must preserve normal exclusive
acquisition. Do not add an unconditional age-based deletion path.

### P3: Unchanged effort still incurs selector and focus work

`setEffort()` reads the current effort, then builds and probes multiple locator
candidates and focuses a control before calculating that the requested effort
delta is zero. Sequential reviews using the same effort repeat this work without
any keypress being needed.

Disposition: return immediately after `readEffort()` when the current effort
already equals the requested effort. Keep `verifySelection()` unchanged so the
visible final state remains authoritative.

### Explicitly deferred or rejected claims

- The exact `importModuleDynamically` VM cause is not a repository-established
  defect. The maintained skill already documents that `browser_run_code_unsafe`
  is not the supported ESM runner and directs callers to the Node entry point.
- The claim that a particular external adapter cannot expose an authenticated
  context is not proven by the repository. The helper contract requires a
  `Page` for page-level operations and a `BrowserContext` only for
  `runReviewPromptInNewTab()`; adapter capability must be reported at the
  boundary, not guessed in core helpers.
- Context reuse and fresh-tab isolation are already implemented and tested. Do
  not add another browser lifecycle owner or replace fresh tabs with one page
  without measured latency and contamination evidence.
- No automatic model fallback is present or authorized. A visibly confirmed
  model-specific lockout remains blocked; an intercepted click or selector
  timeout must retain its actual failure classification.

## Implementation Outcomes

### Precise batch failure settlement

Review results distinguish model-specific unavailability, page/review-scoped
selection failures, and proven shared-context failures. The batch continues only
after an explicitly non-shared failure and stops fail-closed for unknown or
context-invalid selection failures. The failed review is never resubmitted and
the requested model is never silently replaced.

### Recoverable persistent-profile ownership

Normal lease exclusivity remains unchanged. An operator can inspect and recover
a lease left by an owner proven to be gone, while ambiguous, live, malformed, or
race-losing lease state remains protected. Lease cleanup is token/identity-safe
and covered on Windows and Linux-compatible paths.

### Lower-overhead repeated model selection

Repeated reviews at the already-selected effort avoid locator discovery and
focus work while retaining visible-state verification for model and effort.
Model-menu UI interactions use a shared five-second action/transition bound;
initial menu opening remains ten seconds and completion observation remains a
separate long-lived bound.

### Canonical and generated surfaces remain synchronized

Canonical scripts, tests, skill documentation, and every output of the
repository-owned adapter sync path are updated or verified together. No
browser-runner workaround, new context owner, or alternate model-selection
strategy is introduced.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `optional worktree` from `origin/main`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared runner, selector, tests, documentation, generated projections, and this plan; run declared repository-local tests, sync, and validation checks; preserve unrelated artifacts
- User-approval actions: push, merge, publication, destructive recovery, discard, cleanup, or changing the base revision
- Parallel ownership: none; shared result classification and lease semantics require one sequential owner
- Sequential fallback: complete Tasks 1–3 in order, synchronize generated surfaces, then run Task 4 final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `d5071a3f0bd63aba5c3b43befde103c85fb88d32`
- Expected workspace: current `main` checkout with declared implementation changes; unrelated probe artifacts remain preserved and unstaged
- Next action: implementation and verification complete; publication and merge remain separately authorized
- Blockers: none
- Adapter-specific runtime capability remains an explicit external boundary,
  not an implementation blocker.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current `main` checkout | `codex` | none | focused failure-scope tests | `54` lifecycle tests passed |
| Task 2 | `completed` | current `main` checkout | `codex` | Task 1 | lease recovery and race-safety tests | `54` lifecycle tests passed |
| Task 3 | `completed` | current `main` checkout | `codex` | Tasks 1–2 | unchanged-effort selector regression | `54` lifecycle tests passed |
| Task 4 | `completed` | current `main` checkout | `codex` | Tasks 1–3 | full repository, sync, and generated-surface validation | all final checks passed |

## Task Breakdown

### Task 1: Refine selection failure scope

**Purpose:**
- Prevent a page-local or explicitly model-scoped selection failure from being
  misreported as a broken shared browser context while preserving fail-closed
  behavior for unknown failures.

**Task Function:**
- Trace and implement the source-to-batch failure classification boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded JavaScript control-flow change with shared batch
  semantics and existing lifecycle tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused lifecycle tests plus final controller verification.

**Specification Coverage:**
- Preserve single submission, no retry, no model substitution, and shared
  context cleanup.
- Continue the batch only for explicit non-shared failures with sufficient
  evidence that the context remains usable.
- Keep unknown selection failures fail-closed.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:openReviewTab`, `runReviewPromptInNewTab`; `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs:selectReviewModel`; `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction`, `classifyFailureScope`, `runReviewBatch`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`, `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`, and `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- The helper-level failure metadata is the authoritative source for selection
  scope; the CLI must not infer scope by matching error-message text.
- Existing result schema and submission-stage ambiguity behavior remain
  authoritative.

**Authority:**
- Preauthorized local actions: edit the runner and focused lifecycle tests,
  then run declared local checks
- Stop for: a changed result contract outside this plan, uncertain context
  health semantics, external browser capability work, or base-revision change

**Steps:**
- [x] Step 1: Add explicit error metadata at the helper boundary for model
  unavailability, known page-local selector failure, proven context failure,
  and unknown selection failure; distinguish `context.newPage()` or
  authenticated-page setup failures from selector failures before they reach
  the CLI.
- [x] Step 2: Make `classifyFailureScope()` consume only that typed metadata.
  Map only proven context failures to `shared_context`; keep model/page
  failures review-scoped and preserve blocked status without retry.
- [x] Step 3: Make `runReviewBatch()` continue only after a review-scoped
  failure and stop on shared/unknown failures.
- [x] Step 4: Add boundary tests for model-specific lockout, page-local
  selection failure, unknown selection failure, and context failure, including
  attempted review order and one-time context cleanup. Do not use a generic
  injected exception as the only proof of production scope classification.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: the failed entry is never resubmitted; page/model-scoped failures
  do not terminate later authorized entries; unknown/context failures stop the
  batch; no fallback model is selected.

**Exit Criteria:**
- Failure scope matches evidence, and existing submission and cleanup
  invariants remain green.

### Task 2: Add conservative persistent-profile lease recovery

**Purpose:**
- Prevent abnormal termination from permanently blocking authenticated profile
  reuse without weakening exclusive ownership.

**Task Function:**
- Design and test safe lease inspection, recovery, and token-preserving release.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-platform lifecycle and race-safety change requiring
  careful failure handling.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused Node tests on the supported Windows and Linux
  execution paths plus repository verification.

**Specification Coverage:**
- Preserve fail-closed behavior for live or ambiguous owners.
- Recover only a lease whose owner is proven gone and whose identity has not
  changed during the recovery race.
- Keep normal acquire/release and concurrent exclusion behavior unchanged.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:acquireProfileLease`, `releaseProfileLease`, `openContext`, `closeContext`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`
- Document: `.agents/skills/skill-github-browser-reviews/SKILL.md` only if the
  recovery command or operator contract changes

**Dependencies:**
- Task 1 is complete; lease recovery must not alter batch failure settlement.

**Authority:**
- Preauthorized local actions: edit lease ownership code and focused tests,
  and run local lifecycle/contract checks
- Stop for: inability to prove owner liveness portably, unsafe PID-reuse
  handling, new runtime dependency, or destructive automatic deletion design

**Steps:**
- [x] Step 1: Extend lease metadata with an owner identity/token and enough
  evidence for a conservative liveness check.
- [x] Step 2: Add an explicit recovery path that refuses malformed, live, or
  ambiguous locks and atomically quarantines/removes only a verified stale
  owner before retrying exclusive creation.
- [x] Step 3: Make release delete only the current owner’s lease, so a delayed
  cleanup cannot remove a replacement owner’s lock.
- [x] Step 4: Add tests for live-owner exclusion, abnormal/stale-owner
  recovery, malformed metadata, PID reuse/ambiguous ownership, race loss, and
  normal release.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: active owners remain protected; stale leases can be recovered only
  through the explicit safe path; ambiguous state remains blocked; release is
  idempotent and token-safe.

**Exit Criteria:**
- A crash no longer creates an indefinite deadlock when safe recovery evidence
  exists, and no recovery path can delete another active owner’s lease.

### Task 3: Short-circuit unchanged effort selection

**Purpose:**
- Remove repeated locator discovery and focus work when the visible effort is
  already the requested effort.

**Task Function:**
- Apply the smallest selector optimization while preserving visible-state
  verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small, low-risk JavaScript change with direct regression
  coverage.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused selector tests and final suite.

**Specification Coverage:**
- Keep `readEffort()` and `verifySelection()` authoritative.
- Preserve keyboard ArrowLeft/ArrowRight behavior for nonzero deltas.
- Centralize `UI_ACTION_TIMEOUT_MS = 5000` for model-option trial/selection
  clicks and visible-control actions.
- Centralize `MENU_TRANSITION_TIMEOUT_MS = 5000` for model/effort subview
  close, reopen, and post-transition visibility waits.
- Keep `MODEL_MENU_TIMEOUT_MS = 10000` for initial menu opening and keep
  `COMPLETION_TIMEOUT_MS = 900000` plus polling backoff values unchanged.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs:openModelMenu`, `openModelList`, `setEffort`, `selectReviewModel`; `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:waitForReviewCompletion`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Tasks 1–2 are not behaviorally required, but execution remains sequential
  to keep the shared test surface single-owner.

**Authority:**
- Preauthorized local actions: edit the selector and focused tests, then run
  the selector suite
- Stop for: a changed effort-control contract or evidence that the visible
  effort can change asynchronously after `readEffort()`

**Steps:**
- [x] Step 1: Add a failing test where the requested effort equals the visible
  current effort and control lookup/focus would fail if attempted.
- [x] Step 2: Define shared five-second action and menu-transition constants;
  apply them only to model-menu interaction, close/reopen, and
  post-transition visibility operations.
- [x] Step 3: Return before control discovery when the effort delta is zero.
- [x] Step 4: Retain and test nonzero keyboard adjustments and final visible
  verification without changing completion timeout or polling backoff values.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: unchanged effort performs no keypress or control focus; changed
  effort still adjusts and verifies correctly; model-menu interactions use the
  five-second tier; initial menu opening remains ten seconds; completion and
  polling bounds remain unchanged.

**Exit Criteria:**
- Repeated same-effort selections avoid unnecessary UI work without reducing
  visible confirmation.

### Task 4: Synchronize maintained surfaces and complete verification

**Purpose:**
- Ensure the canonical change, generated adapters, documentation, and final
  repository contracts remain aligned.

**Task Function:**
- Reconcile generated surfaces and run fresh acceptance proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository synchronization and verification.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independent final command results and clean Git evidence.

**Specification Coverage:**
- Generated adapters are projections of canonical sources.
- No unrelated probe artifacts are staged or deleted.

**Required Skills:**
- `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`, `scripts/validate_repo_contracts.py`
- Modify: `AGENTS.md`, `.agents/rules`, and `generated_agents` only through the
  sync command, plus canonical documentation if Task 2 changes the operator
  contract
- Verify: `AGENTS.md`, `.agents/rules`, `generated_agents`, all declared tests,
  and Git inventory

**Dependencies:**
- Tasks 1–3 complete with focused proof.

**Authority:**
- Preauthorized local actions: run synchronization, contract validation,
  tests, and read-only Git inspection
- Stop for: generated drift that requires hand edits, unrelated modified files,
  failed final proof, or any external publication action

**Steps:**
- [x] Step 1: Run `python scripts/sync_agent_adapters.py --all-platforms --check`
  and record any pre-existing drift. Stop if the baseline is already dirty in
  an unrelated projection or cannot be attributed to the canonical sources.
- [x] Step 2: Run `python scripts/sync_agent_adapters.py --all-platforms` and
  inspect the complete declared projection set: `AGENTS.md`, `.agents/rules`,
  and `generated_agents`.
- [x] Step 3: Run focused Node tests, relevant Python tests, and repository
  contract validation.
- [x] Step 4: Run `git diff --check`, inspect staged/unstaged/untracked state,
  and confirm only declared projections and canonical sources changed.
- [x] Step 5: Record final evidence and leave publication/merge for separately
  authorized Git disposition.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs`
- [x] `python -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py`
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `git diff --check`
- Expected: all checks pass, generated projections are current, only the
  declared sync write set changes, and unrelated untracked probe artifacts
  remain preserved.

**Exit Criteria:**
- Fresh proof covers failure classification, lease recovery, unchanged effort,
  generated parity, and repository contracts with no unresolved implementation
  blocker.

## Execution Evidence

- `node --test tests/test_github_browser_review_lifecycle.mjs` — 54 passed,
  0 failed.
- `python -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py` — 20 passed, 0 failed.
- `python scripts/validate_repo_contracts.py` — passed, including planning,
  template, metadata, generated-header, runtime-drift, and repo-config checks.
- `python scripts/sync_agent_adapters.py --all-platforms --check` — passed;
  generated adapters are current.
- Node syntax checks for all three modified runner scripts — passed.
- `git diff --check` — passed; only generated-file line-ending warnings were
  reported.
- Untracked probe artifacts (`.runtime/`, `.review-profile/`,
  `.playwright-mcp/`, `node_modules/`, and probe output files) remain
  preserved and unstaged.

## Verification

- [x] Focused lifecycle suite passes after each behavior task.
- [x] Lease tests cover active, stale, malformed, ambiguous, race-losing, and
  normal-release states.
- [x] Batch tests prove later entries continue only for explicit review-scoped
  failures and stop for shared/unknown failures.
- [x] Generated adapter sync/check passes after canonical changes.
- [x] Relevant Python tests and `validate_repo_contracts.py` pass.
- [x] Final Git inventory proves no unrelated artifacts were staged, removed,
  or overwritten.

## Completion Criteria

- [x] All four tasks are completed in the plan ledger with immutable proof paths
  or command results.
- [x] Selection failure scope is evidence-based and no failed review is retried
  or silently switched to another model.
- [x] Safe profile-lease recovery exists only for proven stale ownership and
  cannot remove a replacement owner’s lock.
- [x] Same-effort selection avoids unnecessary locator/focus work while final
  visible verification remains intact.
- [x] Context reuse, fresh-tab isolation, and cleanup ownership remain unchanged
  unless fresh measurement and a separately approved plan change justify them.
- [x] External adapter/VM limitations are documented as boundary conditions,
  not encoded as speculative core workarounds.
- [x] The plan is `completed` after explicit implementation approval and fresh
  verification.

## Known Limits And Deferred Work

- This plan does not claim that a particular Playwright VM lacks
  `importModuleDynamically`; only the maintained ESM execution boundary is
  established.
- This plan does not add adapter-specific context discovery or a new browser
  lifecycle owner. Such work requires an adapter capability contract and fresh
  runtime evidence.
- Fresh-tab replacement with same-page reuse is deferred until comparable
  latency, memory, and contamination evidence exists.
- Automatic age-only lock deletion is explicitly prohibited.
