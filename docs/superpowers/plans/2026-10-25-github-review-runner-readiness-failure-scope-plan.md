---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: github-review-runner-readiness-failure-scope
targets:
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - tests/test_github_browser_review_lifecycle.mjs
  - .agents/skills/skill-github-browser-reviews/SKILL.md
---

# GitHub Review Runner Readiness Failure-Scope Plan

## Goal

Prevent a slow or temporarily unready fresh ChatGPT tab from being reported as
shared-context corruption. Keep the authenticated context, profile lease, and
fresh-tab batch design unchanged; stop only when there is evidence that the
shared context itself cannot be used.

## Review Evidence

Both completed reviews inspected commit `961fce7ee33319521da338165170fe04b5ff519f`
with the requested model and High effort:

- GPT-5.6-Sol: `.runtime/github-review-20261025/output/run-kg7Ydn/response.md`
- GPT-6: `.runtime/github-review-20261025/output/run-9M4qvt/response.md`

Both model results were recorded as `completed`, with verified model and effort,
and cleanup status `completed` in their `result.json` files.

## Consolidated Finding

### P2: Fresh-tab readiness failures abort the shared batch

**Evidence:** `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
`openReviewTab()` creates a new page at lines 58–61, then wraps every
`openChatGPT()` failure as `shared_context` at lines 65–70. `openChatGPT()` waits
for the composer at lines 44–50, so a delayed render or page-local readiness
failure is indistinguishable from a broken authenticated context. The lifecycle
test at `tests/test_github_browser_review_lifecycle.mjs` lines 927–950 covers
page closure but does not assert a page-readiness failure scope.

**Root cause:** Page creation and page readiness are assigned the same failure
owner. `runReviewBatch()` correctly continues only for `failure_scope ===
"review"`, so the broad wrapper causes a recoverable fresh-tab problem to stop
the batch and force a later authorized run.

**Impact:** One slow or transiently unready tab can tear down the normal batch
flow, increase profile/session recovery overhead, and prevent a later review
from using the still-valid authenticated context.

**Validated recommendation:** Keep `context.newPage()` and browser/context
failures as `shared_context`. Classify the bounded composer-readiness failure
from an already-created page as `review` with a stable page-readiness reason.
Close that page, preserve exactly-once submission semantics, and allow the next
review to use a fresh tab in the same context. Do not add automatic retries,
browser reopening, model substitution, or a second lifecycle owner.

## Findings Explicitly Excluded

The following model findings are not included because they are already fixed or
not established in the current branch:

- Profile lease recovery race: the current runner no longer performs the
  read–rename–verify stale-recovery sequence; an existing lease fails closed.
- Lease release after failed owned-context shutdown: `closeContext()` releases
  the profile lease only after confirmed owned-context closure.
- Lease metadata rollback, final single-review persistence, and uncertain tab
  cleanup: current code and lifecycle tests cover these paths.
- Unbounded initial model-menu click and prompt submission actions: the current
  scripts use the shared five-second action timeout.
- Generic-alert false interruptions: generic alerts are filtered through
  `INTERRUPTION_PATTERN` and dedicated response-error selectors remain
  authoritative.
- Duplicate model-menu reopening: the current selector helper has one outer
  bounded reopen owner for `MODEL_MENU_TRANSIENT`; model absence is a distinct
  `MODEL_UNAVAILABLE` failure.
- Removing terminal response-action evidence: the current completion contract
  intentionally requires response identity plus observed generation or
  terminal response-action evidence to avoid accepting planning text as a
  completed review. Relaxing that guard is not justified by these reviews.

## Implementation Outcomes

- Page-local composer readiness failures carry `failureScope: "review"` and a
  stable readiness-stage diagnostic.
- `context.newPage()` failures remain `failureScope: "shared_context"`.
- The batch continues after a page-readiness failure without resubmitting the
  failed review or reopening the browser.
- Existing lease ownership, fresh-tab isolation, cleanup ownership, completion
  evidence, model verification, and fail-closed submission rules remain
  unchanged.
- Documentation states the distinction between page readiness and shared
  context failure.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution; the lead creates an authorized checkpoint only after task proof is accepted`
- Preauthorized local actions: edit the listed helper, tests, and canonical skill documentation; run the declared local verification; preserve unrelated untracked probe artifacts
- User-approval actions: push, merge, branch deletion, worktree cleanup, live authentication, and external publication
- Parallel ownership: `none; the helper, lifecycle tests, and skill contract share one ownership boundary`
- Sequential fallback: complete Task 1, then run the full verification gate

Implement one bounded behavior change with a focused regression suite. No
parallel write lanes are needed because the source helper, its lifecycle tests,
and its skill documentation form one ownership boundary.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/github-review-runner-lease-ui-hardening`
- Base commit: `97529ce69440d33bc18575db70f1dcfded893e54`
- Expected workspace: current branch with preserved unrelated untracked live-review artifacts
- Next action: verified; branch disposition remains separately authorized
- Blockers: none
- Approved deferral: live browser probing remains outside this plan and requires the authenticated project-specific profile

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | readiness-scope regression and full checks | 61 lifecycle tests, 25 Python tests, contract validation, adapter sync, syntax, and diff checks pass |

## Task Breakdown

### Task 1: Separate page readiness from shared-context failure

**Purpose:** Preserve the reusable authenticated context when a newly created
tab does not become ready within the existing composer-readiness bound.

**Task Function:** Implement and test failure-scope ownership at the fresh-tab
boundary.

**Specification Coverage:** GPT-5.6-Sol and GPT-6 independently validated the
page-readiness/shared-context classification defect; the plan preserves the
single-context, fresh-tab, no-resubmission contract.

**Template Profile:**
- Controller-selected: none (lead controller)

**Required Skills:** `skill-systematic-debugging`,
`skill-test-driven-development`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`:
  `openChatGPT`, `openReviewTab`, and the existing failure-scope helper usage.
- Modify `tests/test_github_browser_review_lifecycle.mjs`:
  fresh-tab readiness and batch-continuation cases.
- Modify `.agents/skills/skill-github-browser-reviews/SKILL.md`:
  the failure-scope and context-reuse contract, if the executable behavior
  changes the documented rule.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: modify the listed helper, lifecycle tests, and
  canonical skill documentation; run the declared verification commands.
- Stop for: any automatic retry, model substitution, profile-lock weakening,
  new browser lifecycle owner, or unresolved authentication classification.

**Steps:**

1. Add a stable page-readiness error path for the bounded composer wait. Keep
   the existing error message useful to operators and preserve the page-close
   cleanup in `openReviewTab()`.
2. Wrap only `context.newPage()` failures as `shared_context`. Propagate the
   page-readiness error as `review` so the batch owner can continue in the same
   authenticated context.
3. Preserve the current submission boundary: a readiness failure occurs before
   prompt submission, so it must not create an ambiguous submission or trigger
   any resubmission path.
4. Add a regression proving a fresh page whose composer never becomes visible
   closes cleanly and reports `failureScope === "review"`.
5. Add a batch regression proving that a review-scoped readiness failure does
   not reopen the browser, does not retry the failed prompt, and allows the next
   review transaction to run in the same context.
6. Keep the existing regression proving `context.newPage()` failure remains
   `shared_context` and stops the shared batch.
7. Update the skill documentation only if the final executable classification
   differs from its current wording.

**Verification:**

- `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "review tab|batch"`
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `python -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`
- `python scripts/validate_repo_contracts.py`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `git diff --check`

**Exit Criteria:**

The lifecycle suite proves that page readiness is review-scoped, context/page
creation failures remain shared-context scoped, the batch reuses one context
without resubmission, and all repository contract and generated-adapter checks
pass.

## Verification

- The RED test fails before the source patch because composer setup is classified
  as `shared_context`.
- The focused lifecycle suite passes after the patch with 61 passing tests.
- The full lifecycle suite, Python contract tests, syntax checks, adapter sync
  check, repository contract validation, and `git diff --check` must pass.
- Unrelated untracked live-review artifacts remain untouched.

## Completion Criteria

- Task 1 is marked `completed` in the coordination ledger with fresh command
  evidence.
- Page readiness and shared-context failure scopes are distinct and covered by
  regression tests.
- No retry, resubmission, model substitution, browser reopening, or profile
  lease weakening is introduced.
- Fresh verification passed; the plan is complete. Git publication or branch
  disposition remains separately authorized.

## Stop Conditions

- Stop if the implementation requires a new browser lifecycle owner, a
  keep-open mode, automatic retry, model substitution, or profile-lock
  weakening.
- Stop if authentication loss cannot be distinguished from page readiness with
  the existing visible evidence; preserve fail-closed behavior and record the
  ambiguity instead of guessing.
- Do not perform a live browser probe without the required authenticated,
  project-specific persistent profile and explicit rerun authorization.

## Handoff

After approval, execute this plan through `skill-executing-plans`. Complete fresh
verification before any branch disposition or publication action.
