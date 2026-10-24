---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: github-review-runner-lease-ui-hardening
targets:
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - .agents/skills/skill-github-browser-reviews/SKILL.md
---

# GitHub Review Runner Lease and UI Hardening Plan

## Goal

Harden the GitHub Browser Reviews Node/Playwright runner so one authenticated
browser context and sequential fresh-tab reviews remain reliable under slow UI
rendering, failed cleanup, concurrent profile acquisition, and model-menu
transitions. Preserve exactly-once submission, fail-closed status reporting,
read-only review behavior, and the existing no-second-browser lifecycle.

## Implementation Outcomes

### Exclusive profile ownership remains truthful

Profile lease creation, stale recovery, and release will not remove, overwrite,
or release another process's active ownership. A metadata publication failure
created by the current process will not leave a self-created malformed lock
that permanently blocks the profile.

### Browser actions and completion observation are bounded

Model-menu actions, prompt submission, composer readiness, and menu transitions
use explicit bounded waits. Completion confirmation relies on stable assistant
turn, response text, generation cessation, composer readiness, conversation
identity, and scoped interruption evidence rather than nonessential response
buttons.

### Cleanup and artifacts are authoritative

Uncertain page or context ownership stops a batch without resubmission. Final
cleanup state is persisted after cleanup attempts so `result.json`, console
status, and cleanup evidence agree.

### Regression proof covers the failure boundaries

Focused Node lifecycle tests cover lease races, metadata-write rollback,
cleanup lease retention, bounded UI actions, delayed composer readiness,
completion without response-action buttons, scoped alerts, menu recovery, and
batch stopping. Existing Python contract tests and adapter checks remain green.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`; the lead creates an authorized checkpoint only after task proof is accepted
- Preauthorized local actions: edit the listed canonical scripts, tests, and skill documentation; run the declared local tests, static checks, and approved authenticated live probe; preserve unrelated untracked review artifacts
- User-approval actions: push, merge, branch deletion, worktree cleanup, destructive lock recovery, authentication changes, and external publication
- Parallel ownership: `none; all implementation tasks share runner lifecycle contracts and tests`
- Sequential fallback: complete Tasks 1–5 in order, then run Task 6 as the single final verification gate

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `961fce7ee33319521da338165170fe04b5ff519f`
- Expected workspace: `main` with preserved untracked live-review artifacts; no tracked implementation changes at plan creation
- Next action: publish the completion-quiescence fix, then run the final authorized live probe
- Blockers: `the prior rerun correctly failed closed; final probe must verify generation-observed completion`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | lease lifecycle tests | 60 lifecycle tests pass; lease race, rollback, malformed-lock, and token-release cases pass |
| Task 2 | `completed` | current | `codex` | Task 1 | cleanup and persistence tests | cleanup persistence, lease retention, and shared-context stop cases pass |
| Task 3 | `completed` | current | `codex` | none | bounded action and readiness tests | bounded UI actions, composer readiness, and submission cases pass |
| Task 4 | `completed` | current | `codex` | Task 3 | completion and interruption tests | completion without response-action buttons and scoped alert handling pass |
| Task 5 | `completed` | current | `codex` | Tasks 2–4 | model-menu and batch ownership tests | one bounded recovery owner and transition-aware close cases pass; canonical skill text already aligned |
| Task 6 | `active` | current | `codex` | Tasks 1–5 | full local suite, adapter check, live probe | local checks pass; probes correctly failed closed on missing response identity; finality now also requires observed generation and needs one final authorized probe |

## Task Breakdown

### Task 1: Make profile lease ownership atomic and rollback-safe

**Purpose:** Remove the confirmed lease races and self-created malformed-lock failure without weakening fail-closed handling of pre-existing ambiguous locks.

**Task Function:** Implement the profile lease ownership contract and its deterministic concurrency proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** GPT-6 stale-recovery race; GPT-5.6-Sol metadata-write rollback finding; exclusive ownership invariant.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`: `acquireProfileLease`, `recoverStaleProfileLease`, `restoreQuarantinedLease`, `releaseProfileLease`.
- Modify `tests/test_github_browser_review_lifecycle.mjs`: lease acquisition, stale recovery, and release tests near the existing lease cases.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: edit the listed lease code and lifecycle tests; use temporary directories and injected test hooks or child-process orchestration for deterministic interleavings; run focused Node tests.
- Stop for: inability to prove an atomic ownership transition, a need to delete an unknown lock, or a behavior change that permits reclaiming malformed/live ownership.

**Steps:**
- [x] Trace the current open/write/rename/remove sequence and identify the exact ownership token available at each transition.
- [x] Add rollback for a lock file created by the current acquisition attempt when metadata publication fails; preserve malformed pre-existing locks as blocked.
- [x] Replace read–rename–verify recovery with a protocol that never moves or overwrites a lock after another owner can acquire it; fail closed when the transition cannot be proven safe.
- [x] Keep release token-checked and ensure a failed or ambiguous release does not remove another owner’s lock.
- [x] Add deterministic tests for metadata-write failure, stale recovery racing with a new lease, live-owner protection, malformed-lock blocking, and token-mismatched release.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "lease|profile"` — covered by the full 60-test lifecycle run.
- [x] Inspect the resulting lock path and metadata in each temporary-directory test; no test removes a lock it did not create.

**Exit Criteria:** Every lease transition has a proven owner, unsafe recovery fails closed, and the focused lease suite passes.

### Task 2: Preserve ownership through failed cleanup and persist final status

**Purpose:** Prevent the runner from releasing a profile lease or publishing stale completion after browser/context cleanup remains uncertain.

**Task Function:** Align context cleanup, single-review final persistence, and batch cleanup classification.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** GPT-6 failed-shutdown lease release; GPT-6 single-run result persistence; GPT-6 uncertain page cleanup continuation.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`: `closeContext`, `runReviewTransaction`, `runReviewBatch`, `markCleanupFailure`, `persistCleanupFailure`, and `main` cleanup handling.
- Modify `tests/test_github_browser_review_lifecycle.mjs`: context cleanup, result persistence, and batch continuation tests.

**Dependencies:** Task 1.

**Authority:**
- Preauthorized local actions: edit cleanup and persistence code plus focused lifecycle tests; inject context/page close failures and result writers.
- Stop for: any path that releases an owned profile lease after uncertain context termination, overwrites a completed artifact without preserving its response, or silently resubmits a review.

**Steps:**
- [x] Release an owned profile lease only after the owned persistent context closes successfully; retain the lease and report cleanup failure when termination is uncertain.
- [x] Reconcile and persist the final single-review result after context cleanup, including `status`, `cleanup_status`, `cleanup_warning`, `failure_stage`, and `failure_reason`.
- [x] Classify a failed `page.close()` as shared-context/ownership uncertainty unless closure is explicitly known to be harmless; stop the batch before creating another review tab.
- [x] Preserve completed response artifacts and never resubmit a review solely because cleanup failed.
- [x] Add regression tests asserting both in-memory and persisted results become `incomplete` and that the profile lease remains present after failed context shutdown.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "cleanup|persist|batch"` — covered by the full 60-test lifecycle run.
- [x] Assert the second review is not attempted after uncertain page ownership.

**Exit Criteria:** Lease retention, final artifact state, and batch stopping are consistent across owned-context and attached-context cleanup failures.

### Task 3: Bound Playwright actions and delayed composer readiness

**Purpose:** Eliminate indefinite action waits and avoid aborting a healthy shared context solely because ChatGPT rendered slowly.

**Task Function:** Centralize UI action/readiness timeout tiers without changing completion polling backoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** GPT-5.6-Sol unbounded initial model-menu click; GPT-6 unbounded submission actions; both models’ delayed composer readiness finding.

**Required Skills:** `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`: `openModelMenu`, `openModelList`, `selectModel`, `reopenModelMenu`.
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`: `openChatGPT`, `submitPrompt`, `closeModelMenu`, and timeout constants.
- Modify `tests/test_github_browser_review_lifecycle.mjs`: fake locator/page behavior for delayed readiness and non-actionable controls.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: edit UI timeout usage and focused tests; keep `MODEL_MENU_TIMEOUT_MS` at 10 seconds, UI actions/transitions at 5 seconds, and completion timeout/backoff unchanged.
- Stop for: any retry loop without a single bounded attempt, any automatic resubmission after ambiguous submission, or any global timeout increase that changes completion polling behavior.

**Steps:**
- [x] Add explicit `UI_ACTION_TIMEOUT_MS` to the initial model-menu click, prompt fill, send click, and Enter fallback; preserve the existing model-menu opening and transition tiers.
- [x] Add a bounded composer readiness wait after navigation, with a distinct readiness timeout/error that does not automatically classify a delayed render as shared-context corruption.
- [x] Add explicit bounds to Playwright operations that wait for locator state or text during submission and completion snapshot reads where the current runner has no configured default timeout.
- [x] Keep one context and one profile lease for the batch; do not reopen the browser or add a keep-open lifecycle owner.
- [x] Add tests proving permanently non-actionable controls fail within the action tier and delayed composer readiness succeeds within the readiness tier.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "timeout|composer|submission|model-menu"` — covered by the full 60-test lifecycle run.
- [x] Confirm completion polling constants remain unchanged by the UI timeout patch.

**Exit Criteria:** Every submission/UI action has a bounded wait, delayed composer rendering is handled without unnecessary browser teardown, and exactly-once submission remains enforced.

### Task 4: Make completion and interruption evidence resilient

**Purpose:** Confirm completed reviews from essential visible response state instead of fragile or unrelated UI controls.

**Task Function:** Refine completion predicates and interruption classification while preserving fail-closed ambiguity handling.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** GPT-6 response-action dependency and broad-alert findings.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`: `INTERRUPTION_UI_SELECTOR`, `readVisibleInterruption`, `readCompletionSnapshot`, `evaluateReviewCompletion`, `waitForReviewCompletion`.
- Modify `tests/test_github_browser_review_lifecycle.mjs`: completion predicate, alert, and completion polling cases.

**Dependencies:** Task 3.

**Authority:**
- Preauthorized local actions: edit completion/interruption logic and focused tests; use mocked visible DOM states only for local regression proof.
- Stop for: accepting a response without a new assistant turn, stable nonempty response text, conversation identity, composer readiness, or generation cessation.

**Steps:**
- [x] Remove `responseActionsReady` as an unconditional completion requirement while retaining it as optional diagnostic evidence if useful.
- [x] Apply `INTERRUPTION_PATTERN` to generic alerts and keep dedicated response-error selectors authoritative; ignore unrelated visible alerts.
- [x] Preserve the existing bounded polling deadline, exponential backoff, partial-response capture, and `incomplete` result for ambiguous completion.
- [x] Update existing tests that currently require response-action visibility and add cases for completed responses without those buttons and unrelated alerts.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "completion|interruption|alert"` — covered by the full 60-test lifecycle run.
- [x] Verify a generic unrelated alert does not consume the full completion timeout when the response is otherwise complete.

**Exit Criteria:** Completion is robust across supported response-control variants, while genuine response interruptions and ambiguous response association remain fail-closed.

### Task 5: Consolidate model-menu recovery ownership and documentation

**Purpose:** Remove overlapping recovery owners and align the skill contract with the final cleanup and timeout semantics.

**Task Function:** Simplify one bounded model-menu recovery path and update the canonical skill documentation.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** GPT-5.6-Sol and GPT-6 overlapping recovery finding; GPT-5.6-Sol final menu-close finding; documented timeout and ownership invariants.

**Required Skills:** `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`: `openModelList`, `selectModel`, `selectReviewModel`.
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`: `closeModelMenu`.
- Modify `tests/test_github_browser_review_lifecycle.mjs`: one-recovery and menu-transition cases.
- Modify `.agents/skills/skill-github-browser-reviews/SKILL.md`: batch lifecycle, timeout, cleanup, and completion evidence wording.

**Dependencies:** Tasks 2–4.

**Authority:**
- Preauthorized local actions: edit the listed model-menu helper, tests, and canonical skill documentation; run focused Node and documentation contract tests.
- Stop for: more than one retry owner, an unbounded reopen loop, or documentation that promises behavior not covered by tests.

**Steps:**
- [x] Make `selectReviewModel` the sole owner of one bounded reopen transition; let model absence and visible-selection mismatch use distinct failure types.
- [x] Use the existing bounded hidden-state wait for final menu closure instead of immediate `isVisible()` polling.
- [x] Preserve visible model and High-effort verification after the transition.
- [x] Confirm `SKILL.md` describes the single recovery owner, bounded action tiers, final cleanup persistence, and stop-on-uncertain-tab ownership contract.
- [x] Add a test proving one deterministic unavailable-model failure does not trigger two reopen sequences.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs --test-name-pattern "model|menu|selection"` — covered by the full 60-test lifecycle run.
- [x] `py -m pytest -q tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py` — covered by the full 46-test Python run.

**Exit Criteria:** Model selection has one bounded recovery owner, menu closure is transition-aware, and the documented lifecycle matches executable behavior.

### Task 6: Run complete verification and an authorized live probe

**Purpose:** Produce fresh evidence that the hardening works across local contracts and the real authenticated browser boundary.

**Task Function:** Reconcile all task proof, run the complete test set, and perform one read-only sequential live probe after the implementation is committed and pushed by an explicitly authorized workflow.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** All validated findings and the existing one-context/fresh-tab operational contract.

**Required Skills:** `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect all changed runner scripts, tests, `SKILL.md`, Git status, and generated-surface checks.
- Modify none unless a declared verification failure identifies an in-scope correction.

**Dependencies:** Tasks 1–5.

**Authority:**
- Preauthorized local actions: run declared tests, static checks, adapter synchronization checks, and record evidence in the plan.
- Stop for: failed required check, missing authenticated browser capability, revision mismatch, unexpected tracked changes, or any request to rerun/resubmit without explicit authorization.

**Steps:**
- [x] Run focused Node tests, Python contract tests, adapter synchronization check, `node --check` on all three runner scripts, and `git diff --check`.
- [x] Confirm generated adapter surfaces were refreshed from canonical scripts and pass the synchronization check.
- [ ] For the live probe, record the immutable pushed SHA and verify `origin/main` resolves to it before opening ChatGPT.
- [ ] In one authenticated Node/Playwright context, run GPT-5.6-Sol High then GPT-6 High in fresh tabs without reopening the browser; verify model, effort, pinned revision, exactly-once submission, completion, cleanup, and artifact status for each review.
- [ ] Record full diagnostics and classify the final result as `verified`, `incomplete`, or `blocked`; never infer completion from submission acknowledgment alone.

**Live-probe anomaly and correction:** The first probe against `52302be80ba55218cd071d9acd8806416ae5cbba` reported both transactions as completed, but each saved only an initial planning sentence and had no `assistant_message_id`. The completion predicate accepted stable nonempty text without response identity. The first correction required a nonempty assistant message identity; the authorized rerun then failed closed for both models, while GPT-6’s preserved final text confirmed a second gap: an identified intermediate planning turn could still pass when generation was never observed. The current correction requires both response identity and observed generation before confirmation. All prior artifacts remain diagnostic evidence, not completion proof.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — 60 tests passed.
- [x] `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py tests/test_sync_agent_adapters.py` — 46 tests passed.
- [x] `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs` — passed.
- [x] `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs` — passed.
- [x] `node --check .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs` — passed.
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — adapters synchronized.
- [x] `git diff --check` — passed.
- [ ] Live probe artifacts contain matching immutable SHA, requested/verified model and effort, confirmed completion, and cleanup status for both fresh-tab reviews.

**Exit Criteria:** All local checks pass, the live probe has complete immutable-revision evidence or an explicit blocked/incomplete result, no unrelated artifacts were removed, and `skill-verification-before-completion` accepts the fresh proof.

## Verification

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py tests/test_sync_agent_adapters.py`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- One explicitly authorized sequential GPT-5.6-Sol High then GPT-6 High read-only live probe using one authenticated Node/Playwright context and fresh tabs.

These commands are final-artifact checks only and are not run while drafting
this proposed plan. Completion may be marked only after
`skill-verification-before-completion` returns `verified` against fresh output.

## Completion Criteria

The plan is ready for completion verification when:

1. profile lease ownership is atomic or safely fail-closed under concurrent acquisition and metadata-write failure
2. failed browser/context cleanup retains uncertain ownership and persists the final terminal result
3. Playwright UI actions and composer readiness have explicit bounded waits without changing completion polling backoff
4. completion evidence no longer depends on nonessential response-action labels and unrelated alerts do not block valid completion
5. model-menu recovery has one bounded owner and final closure waits for the hidden transition
6. focused Node tests, Python contract tests, syntax checks, adapter synchronization, and `git diff --check` pass
7. the final authorized live probe provides immutable-SHA, model, effort, exactly-once submission, completion, and cleanup evidence for both models; prior probes remain `incomplete` because response identity or generation-observation evidence was missing
8. preserved untracked review artifacts and unrelated user work remain untouched

The plan remains `proposed` until approved execution follows this breakdown and
`skill-verification-before-completion` confirms repository evidence.
