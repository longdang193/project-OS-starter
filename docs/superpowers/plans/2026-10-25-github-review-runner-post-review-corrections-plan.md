---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: github-review-runner-post-review-corrections
reviewed_repository: longdang193/project-OS-starter
reviewed_branch: main
reviewed_commit: c89313709dc810f35b89256ddb709fc84b7be525
targets:
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - tests/test_github_browser_review_lifecycle.mjs
  - generated_agents/antigravity/skills/skill-github-browser-reviews
  - generated_agents/claude/skills/skill-github-browser-reviews
  - generated_agents/codex/skills/skill-github-browser-reviews
---

# GitHub Review Runner Post-Review Corrections Plan

## Goal

Apply only source-confirmed corrections from the sequential GPT-5.6-Sol High
and GPT-6 High reviews of `c89313709dc810f35b89256ddb709fc84b7be525`, while
preserving read-only review scope, immutable revision provenance, exactly-once
submission, one authenticated browser context, sequential fresh tabs, and
fail-closed behavior.

Review evidence:

- `C:\tmp\project-os-github-review-c89313709dc810f35b89256ddb709fc84b7be525\output\run-fkqWQw\response.md`
- `C:\tmp\project-os-github-review-c89313709dc810f35b89256ddb709fc84b7be525\output\run-er3Opp\response.md`
- `C:\tmp\project-os-github-review-c89313709dc810f35b89256ddb709fc84b7be525\output\batch-result.json`

## Implementation Outcomes

### Provenance and preflight compatibility

Markdown-formatted commit-pinned GitHub blob links are tokenized into their
individual URLs before the existing exact repository/SHA/set checks run. Batch
repository/project-key consistency is validated before artifact allocation or
browser setup. Dedicated profiles remain required, while unrelated ancestor
directories named `Default`, `Profile N`, or `User Data` no longer cause false
rejection when the actual `github-review/<project>` structure is valid.

### Stable lifecycle recovery

When an ambiguous send is followed by a confirmed new stable assistant response,
the runner promotes the result to acknowledged/completed without resubmission.
Selection failures preserve bounded visible evidence before page cleanup.
Confirmed completion is not observed a second time after a response-artifact
failure. Signal cleanup shares one close promise, preserves SIGINT/SIGTERM exit
status, and lets batch ownership use the same close function.

### Maintained surfaces and proof

The direct CDP library example documents its required repository/project identity.
Focused lifecycle regressions cover each changed contract. Canonical skill files
are synchronized to Claude, Codex, and Antigravity adapter outputs.

No validated defect was found in normal batch browser reuse: one authenticated
context and fresh review-local tabs remain the safer evidence boundary than
reusing a conversation tab. No retry, model substitution, authentication
weakening, or revision-pin relaxation was added.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-github-browser-reviews`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-writing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: `source inspection, focused edits, adapter synchronization, declared tests, syntax checks, and diff validation`
- User-approval actions: `commit, push, pull request, merge, and cleanup of unrelated untracked artifacts`
- Parallel ownership: `none`
- Sequential fallback: `inspect source -> patch canonical files -> add regression proof -> sync adapters -> verify`

## Task Breakdown

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | lead controller | review outputs | lifecycle and provenance tests | `node --test tests/test_github_browser_review_lifecycle.mjs` |
| Task 2 | `completed` | current | lead controller | Task 1 | adapter parity and Python contracts | `pytest -q tests/test_github_browser_reviews.py tests/test_github_browser_review_runner.py tests/test_sync_agent_adapters.py` |
| Task 3 | `completed` | current | lead controller | Tasks 1–2 | syntax, diff, and final state inspection | `node --check`, `git diff --check`, sync check |

### Task 1: Patch confirmed runner defects

**Purpose:** Remove deterministic false failures and redundant work without weakening safety invariants.

**Task Function:** Root-cause correction with focused regression proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: direct source/test ownership and bounded local changes.

**Specification Coverage:** Preserve exact provenance, no retry, stable completion evidence, shared context ownership, and durable artifacts.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:extractPromptGitHubBlobUrls, validateProjectProfilePath, installTerminationCleanup, runReviewBatch, runReviewTransaction, allocateReviewArtifacts, main`
- Inspect/modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:runReviewPromptInNewTab`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:** Completed model reviews against the pinned commit; canonical sources are authoritative.

**Authority:**
- Preauthorized local actions: source edits and focused Node tests.
- Stop for: authentication, external publication, destructive cleanup, or a required behavior change not covered by source evidence.

**Steps:**
- [x] Split Markdown link label/target URL candidates before exact provenance validation.
- [x] Validate batch identity before allocation/browser setup and assign missing review indexes during allocation.
- [x] Preserve selection evidence, avoid duplicate completion observation, and promote confirmed ambiguous responses without resubmission.
- [x] Share signal/context close ownership and preserve signal exit status.
- [x] Add focused regressions for every changed branch.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — `99 passed, 0 failed`.

**Exit Criteria:** Confirmed findings no longer reproduce and unchanged safety tests remain green.

### Task 2: Align documentation and generated adapters

**Purpose:** Keep the canonical skill contract executable and prevent adapter drift.

**Task Function:** Maintained-surface reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: canonical source ownership and deterministic synchronization.

**Specification Coverage:** Direct CDP callers supply `projectKey` and `repository`; ambiguous-response recovery and browser ownership are documented accurately.

**Required Skills:** `skill-github-browser-reviews`

**Files And Symbols:**
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md`
- Regenerate: `generated_agents/antigravity/skills/skill-github-browser-reviews`, `generated_agents/claude/skills/skill-github-browser-reviews`, `generated_agents/codex/skills/skill-github-browser-reviews`
- Verify: `scripts/sync_agent_adapters.py`, `tests/test_github_browser_reviews.py`, `tests/test_github_browser_review_runner.py`, `tests/test_sync_agent_adapters.py`

**Dependencies:** Task 1 source behavior is settled.

**Authority:**
- Preauthorized local actions: canonical documentation edits, adapter sync, and contract tests.
- Stop for: generated output that cannot be derived from canonical sources or unrelated generated drift.

**Steps:**
- [x] Update direct-library batch invocation requirements and confirmed ambiguous-response behavior.
- [x] Run `python scripts/sync_agent_adapters.py --all-platforms`.
- [x] Run `python scripts/sync_agent_adapters.py --check --all-platforms`.

**Verification:**
- [x] `pytest -q tests/test_github_browser_reviews.py tests/test_github_browser_review_runner.py tests/test_sync_agent_adapters.py` — `41 passed`.

**Exit Criteria:** Canonical and all maintained generated adapter surfaces match.

### Task 3: Final verification and handoff

**Purpose:** Reconcile the dirty workspace, preserved artifacts, and fresh evidence before any Git disposition.

**Task Function:** Completion verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final local evidence and ownership audit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: verification is controller-owned for this local patch.

**Specification Coverage:** All required outcomes are implemented, tested, documented, and synchronized.

**Required Skills:** `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed canonical/generated files, tests, Git status, and preserved untracked artifacts.
- Verify: `git diff --check`, Node syntax, adapter sync check.

**Dependencies:** Tasks 1–2 complete.

**Authority:**
- Preauthorized local actions: declared verification commands and read-only status/diff inspection.
- Stop for: failed required proof, unexpected scope, or any attempt to delete unrelated untracked artifacts.

**Steps:**
- [x] Run Node syntax checks for both canonical helper scripts.
- [x] Run focused lifecycle and Python contract suites.
- [x] Run adapter sync check and `git diff --check`.
- [x] Confirm `.playwright-mcp/`, `.review-profile/`, `.runtime/`, and `node_modules/` remain untouched and untracked.

**Verification:**
- [x] `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs` — passed.
- [x] `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs` — passed.
- [x] `python scripts/sync_agent_adapters.py --check --all-platforms` — adapters up to date.
- [x] `git diff --check` — passed.

**Exit Criteria:** Fresh evidence proves the implementation is complete; Git publication remains a separate explicitly authorized action.

## Verification

- `node --test tests/test_github_browser_review_lifecycle.mjs` — `99 passed`.
- `pytest -q tests/test_github_browser_reviews.py tests/test_github_browser_review_runner.py tests/test_sync_agent_adapters.py` — `41 passed`.
- `python scripts/sync_agent_adapters.py --check --all-platforms` — up to date.
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs` — passed.
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs` — passed.
- `git diff --check` — passed.

## Completion Criteria

1. All model-attributed findings retained in the plan are source-confirmed and patched or documented.
2. No retry, resubmission, profile migration, browser-context duplication, or revision-pin weakening was introduced.
3. Focused regression proof passes for lifecycle, provenance, batch ordering, cleanup, evidence, and artifact accounting.
4. Canonical and generated skill surfaces are synchronized.
5. Unrelated untracked artifacts remain preserved and outside the patch scope.
6. Commit, push, pull-request, merge, and cleanup remain outside this plan's local verification boundary.
