---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: github-review-runner-lifecycle-batch
targets:
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
  - generated_agents
  - docs/superpowers/plans/2026-10-24-github-review-runner-lifecycle-batch-plan.md
---

# GitHub Review Runner Lifecycle and Batch Plan

## Goal

Harden the merged GitHub browser-review runner so its durable evidence remains
truthful across selection, submission, completion, artifact, and cleanup stages,
then expose the already-supported sequential batch transaction through the same
CLI without breaking the existing single-review invocation.

The approved scope is limited to validated follow-up findings from the review
of merged PR `#161`. Polling/backoff changes are deferred unless fresh
measurement demonstrates a material regression.

## Implementation Outcomes

### Stage-accurate lifecycle evidence

`runReviewTransaction()` records the active lifecycle stage and reports
selection/browser, submission, completion, artifacts, and cleanup failures in
the stage where they occur. Once the helper acknowledges prompt submission,
later observer or completion failures preserve `submission: "acknowledged"`
and are not relabeled as ambiguous delivery.

### Durable results before cleanup

The runner persists response content and the terminal `result.json` before
closing the review page. A cleanup failure is surfaced separately without
rewriting an already completed review into a false incomplete result; artifact
write failures remain explicit and non-successful.

### First-class sequential batch CLI

The CLI accepts a validated `--batch-file` JSON manifest containing model,
effort, and prompt-file entries. It opens one authenticated context, executes
fresh-tab transactions sequentially, allocates isolated `run-*` directories,
closes the shared context once, prints a machine-readable summary, and exits
nonzero when any review is not completed. Existing single-review flags remain
supported and mutually exclusive with batch mode.

### Canonical documentation and generated adapters stay aligned

The canonical review skill retains behavioral invariants without duplicated
selector mechanics, documents the batch CLI contract, and all generated
adapter mirrors are regenerated and checked through the repository sync tool.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `optional worktree` — execute in the clean worktree created from `origin/main`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the declared canonical source, tests, plan, and generated projections; run repository-local tests, synchronization, and validation checks; preserve unrelated artifacts in the original checkout
- User-approval actions: push, merge, publication, destructive cleanup, discard of preserved artifacts, or changing the base revision
- Parallel ownership: none; lifecycle and CLI changes share result and cleanup contracts
- Sequential fallback: complete Tasks 1–3 in order, then run Task 4 final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/review-runner-lifecycle-batch`
- Base commit: `f1f9d15a8839e67cef3aa8cb501fc0d09c5bf410`
- Expected workspace: clean worktree from `origin/main`; unrelated untracked review artifacts remain only in the original checkout
- Next action: none; implementation is verified on the isolated branch and awaits any separately authorized Git disposition
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | clean worktree | `codex` | none | focused lifecycle tests fail for the current implementation, then pass after the fix | `node --test tests/test_github_browser_review_lifecycle.mjs` — 34 passed |
| Task 2 | `completed` | clean worktree | `codex` | Task 1 | batch manifest, context reuse, output isolation, and CLI exit/summary tests | lifecycle suite plus `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py` — 41 passed in final focused suite |
| Task 3 | `completed` | clean worktree | `codex` | Task 2 | canonical docs and generated adapters synchronized | `py -B scripts/sync_agent_adapters.py --all-platforms --check` — up to date |
| Task 4 | `completed` | clean worktree | `codex` | Tasks 1–3 | full focused suite, sync check, diff check, and final status inspection | Node 34 passed; Python 41 passed; adapters up to date; diff check passed |

## Task Breakdown

### Task 1: Make transaction lifecycle classification truthful

**Purpose:**
- Preserve acknowledged submission and terminal review evidence while distinguishing completion, artifact, and cleanup failures.

**Task Function:**
- Implement and regression-test stage-aware review transaction settlement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded JavaScript lifecycle change with direct source/test ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: controller-owned focused and final verification.

**Specification Coverage:**
- The approved lifecycle correctness and persist-before-cleanup requirements.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:runReviewTransaction, createResult, main`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- `origin/main` at `f1f9d15a8839e67cef3aa8cb501fc0d09c5bf410`.

**Authority:**
- Preauthorized local actions: add focused tests and modify only the declared runner lifecycle/result code
- Stop for: a changed public result contract outside the approved lifecycle fields, a base revision change, or any required external write

**Steps:**
- [x] Step 1: Add failing tests for observer failure after acknowledged submission, artifact-write failure, and cleanup failure after terminal response persistence.
- [x] Step 2: Introduce explicit stage tracking and separate cleanup/artifact warning state without hiding the original failure.
- [x] Step 3: Persist response and terminal result before page cleanup; retain completed status when only cleanup fails.
- [x] Step 4: Run the focused lifecycle test file and reconcile result shape expectations.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — 34 passed
- Expected: new regressions fail before implementation and pass afterward; acknowledged submission is preserved; response/result artifacts exist before cleanup; cleanup is separately observable.

**Exit Criteria:**
- Transaction results identify the true failure stage, preserve delivery acknowledgement, and durably write terminal evidence before cleanup.

### Task 2: Expose validated batch execution through the CLI

**Purpose:**
- Make `runReviewBatch()` first-class without changing single-review compatibility.

**Task Function:**
- Add manifest parsing, validation, orchestration, and CLI-level regression proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded CLI schema and orchestration work coupled to Task 1 result semantics.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused Node tests and existing Python contract tests.

**Specification Coverage:**
- `--batch-file` JSON manifest, one authenticated context, sequential fresh tabs, isolated output directories, one shared-context close, JSON summary, nonzero failure semantics, and mutually exclusive single/batch modes.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:parseArguments, runReviewBatch, main`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:parseArguments, main, batch manifest helpers`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`, `tests/test_github_browser_reviews.py`

**Dependencies:**
- Task 1 terminal result and cleanup contract.

**Authority:**
- Preauthorized local actions: add manifest/CLI tests and modify only the declared runner CLI and its focused contracts
- Stop for: a need to change browser selection semantics, a new dependency, or an external authentication/publishing action

**Steps:**
- [x] Step 1: Add failing parser tests for valid manifests, invalid JSON/schema, missing prompt files, unsupported models/efforts, and single/batch exclusivity.
- [x] Step 2: Add a failing orchestration regression proving one context open, two sequential fresh-tab transactions, distinct output directories, and one context close.
- [x] Step 3: Implement manifest loading/validation and batch summary/exit behavior while retaining the normal single-review path.
- [x] Step 4: Run focused Node and Python contract tests.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — 34 passed
- [x] `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py` — 20 passed
- Expected: batch parsing rejects malformed input before browser open; valid batch uses one context and returns a JSON array/summary; exit is `0` only when every review is completed.

**Exit Criteria:**
- Users can invoke one or many reviews through the same CLI with deterministic validation, isolation, context ownership, and exit semantics.

### Task 3: Reconcile canonical documentation and generated adapters

**Purpose:**
- Document the shipped CLI contract and remove duplicated selector/reopen mechanics while preserving behavioral invariants.

**Task Function:**
- Update canonical documentation and regenerate all managed adapter projections.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation-only follow-up after behavior is proven.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository synchronization and contract tests.

**Specification Coverage:**
- Visible exact model verification, no automatic retry, read-only review, exact revision evidence, and documented batch CLI usage.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/SKILL.md`
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md`, generated adapter mirrors via `scripts/sync_agent_adapters.py`
- Verify: `tests/test_sync_agent_adapters.py`, generated adapter parity

**Dependencies:**
- Tasks 1–2 complete so documentation reflects the final result contract.

**Authority:**
- Preauthorized local actions: edit canonical skill documentation and run the repository-owned adapter synchronization command
- Stop for: generated ownership conflict, unexpected adapter drift outside this skill, or a requirement to hand-edit projections

**Steps:**
- [x] Step 1: Trim duplicated UI selector mechanics without weakening behavioral invariants.
- [x] Step 2: Add the `--batch-file` invocation and output/exit contract to canonical usage guidance.
- [x] Step 3: Run `scripts/sync_agent_adapters.py --all-platforms` and inspect the generated diff.

**Verification:**
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — adapters up to date
- [x] `py -m pytest -q tests/test_sync_agent_adapters.py tests/test_github_browser_reviews.py` — passed within the final 41-test Python suite
- Expected: canonical and generated surfaces match, and no generated file is manually authored.

**Exit Criteria:**
- Documentation and generated adapters describe the implemented lifecycle and batch behavior from one canonical source.

### Task 4: Final verification and handoff readiness

**Purpose:**
- Produce fresh evidence for the complete follow-up scope without changing unrelated repository behavior.

**Task Function:**
- Run final focused validation, inspect the diff, and reconcile plan evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence collection across Node, Python, and generated surfaces.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: verification is controller-owned.

**Specification Coverage:**
- All validated follow-up findings are implemented or explicitly deferred with evidence.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all target files, final Git diff/status, plan ledger, and generated parity output
- Modify: plan evidence/status only, unless a required check identifies an in-scope correction
- Verify: Node lifecycle tests, Python browser-review contracts, adapter sync, diff whitespace, and repository status

**Dependencies:**
- Tasks 1–3 complete.

**Authority:**
- Preauthorized local actions: run declared local verification commands and record immutable evidence in this plan
- Stop for: failed required check, unresolved scope deviation, stale plan state, or any external/destructive action

**Steps:**
- [x] Step 1: Run focused Node and Python tests.
- [x] Step 2: Run adapter sync check and `git diff --check`.
- [x] Step 3: Inspect final diff/status and record exact outcomes, deferrals, and blockers.
- [x] Step 4: Mark the plan completed only after fresh verification accepts all completion criteria.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — 34 passed
- [x] `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_sync_agent_adapters.py` — 41 passed
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — adapters up to date
- [x] `git diff --check` — passed
- Expected: all required checks pass, generated surfaces are synchronized, and only approved files are changed.

**Exit Criteria:**
- Fresh verification proves the implemented lifecycle and batch contracts, with no unresolved required task or unrecorded scope deviation.

## Verification

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_sync_agent_adapters.py`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`

These commands were rerun after the final implementation and generated-surface
sync. Polling/backoff optimization remains explicitly deferred because this
change set contains no measured request-volume or latency regression.

## Completion Criteria

The plan is ready for completion verification when:

1. transaction failures are stage-accurate and acknowledged submission is never relabeled as ambiguous after acknowledgement
2. response and terminal result artifacts are persisted before page cleanup
3. cleanup failures are separately visible without erasing a completed review result
4. `--batch-file` validates input, reuses one context, uses fresh tabs and isolated runs, and has deterministic JSON/exit semantics
5. canonical documentation and generated adapters are synchronized
6. focused tests, synchronization checks, and diff checks pass with no unrelated changes

The plan is marked `completed` after fresh verification confirmed these criteria
against repository evidence. No commit, push, PR, merge, or cleanup action was
performed in this execution.
