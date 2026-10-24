---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: github-review-findings-consolidated
targets:
  - scripts/herdr_main_launcher.py
  - scripts/project_os_runtime/submission_gate.py
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - tests/test_herdr_main_launcher.py
  - tests/test_submission_gate.py
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
---

# GitHub Review Findings — Consolidated Implementation Plan

## Goal

Harden the repository-owned GitHub browser-review workflow and Herdr dispatch
boundary so verified evidence identifies the complete assistant response,
browser model selection is confirmed from visible UI state, failed
pre-submission attempts remain retryable, auto-pane discovery is observational
until ownership is acquired, and concurrent or failed runs cannot leak tabs or
overwrite durable review artifacts.

This plan is based on checked-out revision
`4f13a8a8128e385b071ba07d3c8f50fcbfa03911`, the supplied review evidence for
`47d4af1a54c1016e3c0e0b9fe67bb5e92aff0f2b` and
`db2b2a5ae0a045f5e3132310a58e3708c249ec59`, and direct inspection of current
source and tests. Repository-side CGW retirement is accepted as an existing
policy/test boundary; external `9router` deployment state is outside this plan.

## Implementation Outcomes

### Submission gate preserves admission semantics

Codex startup, start confirmation, and pane revalidation remain in admission.
The gate enters delivery only immediately before prompt transport. Definite
startup or confirmation failure settles as `not_delivered`; transport or
post-submission ambiguity remains `delivery_uncertain`. A failed
pre-submission operation can be reclaimed after its admission lease expires,
without weakening the existing fail-closed rule for uncertain delivery.

### Auto-pane discovery is read-only before ownership

Candidate inspection never invokes `release-agent` before the allocation or
pane-ownership lock is held. Stale idle-agent state is returned as
candidate-local evidence, then revalidated and cleaned up only inside the
authoritative locked path. Candidate rejection, global snapshot failure, and
replacement allocation retain their current meanings.

### Browser evidence and artifacts are unambiguous

Completion tracking counts logical top-level assistant messages, extracts the
complete visible response, and records the matching stable identity. Model
selection and interruption detection use visible, scoped UI state. Newly opened
tabs and attached browser connections are cleaned up on failure, and default
output allocation isolates simultaneous runs while retaining run identity.

### Canonical and generated surfaces stay synchronized

Browser helper edits occur in `.agents/skills/skill-github-browser-reviews` and
are propagated with `scripts/sync_agent_adapters.py`; `generated_agents/` is
never edited as canonical source. Focused tests cover the changed contracts.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit canonical source and tests, run repository-local synchronization and validation commands, and preserve unrelated workspace changes
- User-approval actions: push, merge, publication, destructive cleanup, discard of preserved user changes, or changing the selected base revision
- Parallel ownership: none; tasks share launcher contracts, generated browser surfaces, and final verification
- Sequential fallback: complete Tasks 1–5 in order, then run Task 6 final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-pane-lifecycle-plan-review`
- Base commit: `4f13a8a8128e385b071ba07d3c8f50fcbfa03911`
- Expected workspace: preserve all tracked edits present at plan creation, including the `.agents/` browser-review sources, generated adapter mirrors, browser-review tests, and the edit in `tests/test_github_browser_review_lifecycle.mjs`, plus all untracked local review/runtime artifacts; do not reset, clean, or overwrite them
- Next action: none; implementation and verification complete
- Blockers: none; stop if the preserved test edit changes the requested terminal-status contract or if the base revision changes

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | current | `lead controller` | none | focused Herdr and submission-gate tests | `283 passed` |
| Task 2 | `complete` | current | `lead controller` | Task 1 | focused auto-pane lock and mutation tests | `24 passed` |
| Task 3 | `complete` | current | `lead controller` | Task 2 | browser completion, model, and interruption tests | `15 Node + 19 Python passed; adapters synchronized` |
| Task 4 | `complete` | current | `lead controller` | Task 3 | browser cleanup and concurrent-output tests | `18 Node + 19 Python passed; adapters synchronized` |
| Task 5 | `complete` | current | `lead controller` | Task 4 | synchronized canonical/generated surfaces | `40 Python passed; adapter check passed; 19 Node passed` |
| Task 6 | `complete` | current | `lead controller` | Task 5 | final focused test and contract checks | `324 Python + 19 Node passed; adapter check and diff check passed` |

## Validation Consolidation

The following findings are validated by current source and are in scope:

- P1: `prepare_model_submission()` advances the Codex gate before startup and
  `_confirm_codex_start()`, so a definite non-submission failure can be treated
  as delivery uncertainty or remain unsettled.
- P1: `_inspect_auto_candidate()` reaches `_herdr_pane()`, whose stale-idle
  branch can execute `release-agent` before allocation or pane ownership.
- P1: completion selection counts nested Markdown roots as assistant turns and
  extracts only the last matched node.
- P2: model lookup does not restrict `findModelOption()` to visible radios or
  exact labels.
- P2: interruption detection treats ordinary response prose containing
  `try again` as an interruption.
- P2: `runReviewPromptInNewTab()` can throw after creating a page before the
  caller receives the page handle, and attached CDP cleanup does not release
  the client connection.
- P2: default CLI invocations share fixed `result.json` and `response.md`
  paths without an ownership boundary.

Excluded from implementation scope:

- CGW retirement: repository-side retirement is already represented by policy,
  validation, and tests; the external owner was not verified.
- Retirement-policy projection consolidation: the duplicate is documented as an
  intentional synchronized projection and parity-tested.
- Serial pane-inspection reduction and shared snapshot refactoring: repetition
  is visible, but no workload or latency evidence validates a regression or a
  safe optimization boundary.

### Task 1: Repair the Codex submission-gate phase boundary

**Purpose:** Keep definite pre-prompt failures retryable without changing the
gate’s fail-closed treatment of uncertain delivery.

**Task Function:** Align launcher phase transitions with the actual prompt
delivery boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded Python control-flow change with high correctness impact and existing focused tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task-local tests and final controller verification.

**Specification Coverage:**
- Admission remains active through Codex start and `_confirm_codex_start`.
- Delivery preparation occurs immediately before `_submit_codex_prompt` while pane ownership is held.
- Startup/start-confirmation failure settles `not_delivered`; transport timeout and unknown prompt result remain `delivery_uncertain`.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:claim_model_submission`, `prepare_model_submission`, `settle_model_submission`, `emit_failure`, `dispatch_verified`, `main`
- Inspect: `scripts/project_os_runtime/submission_gate.py:claim_submission`, `prepare_submission`, `settle_submission`
- Modify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`, `tests/test_submission_gate.py`

**Dependencies:** Existing gate schema and `delivery_uncertain` tests remain authoritative.

**Authority:**
- Preauthorized local actions: edit launcher/gate modules and focused tests, then run declared Python tests
- Stop for: changed gate-state semantics, required external runtime, or base-revision change

**Steps:**
- [x] Move `prepare_submission` out of pre-start `dispatch_verified`.
- [x] Call it immediately before every `_submit_codex_prompt`, including reused-agent delivery under pane ownership.
- [x] Add tests for nonzero startup and failed start confirmation: `not_delivered`, no prompt submission, and later reclaimable admission.
- [x] Retain tests proving uncertain delivery remains blocked.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_main_launcher.py tests/test_submission_gate.py` — `283 passed`
- Expected: definite pre-submission failure settles `not_delivered` and a later admission claim succeeds; uncertain delivery remains blocked.

**Exit Criteria:** No Codex path marks delivery before prompt transport begins.

### Task 2: Make auto-pane candidate discovery observational

**Purpose:** Prevent candidate inspection from mutating an unowned pane or racing another launcher.

**Task Function:** Separate candidate evidence collection from authorized stale-agent cleanup.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded Python locking/state-machine change with concurrency risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing lock and candidate tests prove the boundary without an external Herdr session.

**Specification Coverage:**
- Discovery-time `_herdr_pane` is read-only.
- Stale idle-agent state is returned as candidate evidence, not cleaned up.
- Cleanup occurs only after lock acquisition and sequence/identity revalidation.
- Candidate-local rejection and global snapshot failure retain their meanings.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_herdr_pane`, `_release_stale_idle_agent`, `_inspect_auto_candidate`, `_resolve_target_selector`, `_allocation_lock`, `_pane_ownership_lock`, `_run_with_pane_ownership`
- Modify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:** Task 1 complete; pane-state changes must not be hidden behind submission failure handling.

**Authority:**
- Preauthorized local actions: edit candidate inspection, locked cleanup, and focused Herdr launcher tests
- Stop for: external Herdr command changes, lock-order changes outside the launcher, or base-revision change

**Steps:**
- [x] Add explicit read-only discovery behavior or split inspection from mutation.
- [x] Return stale-idle-agent evidence with pane and agent identity needed for revalidation.
- [x] Re-read and revalidate inside the locked allocation/ownership path before `release-agent`.
- [x] Add command-recording coverage proving discovery emits no state-changing command and authorized cleanup does.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_main_launcher.py -k "candidate or pane_safety or allocation or ownership"` — `24 passed`
- Expected: unowned discovery never emits `release-agent`; locked cleanup preserves fail-closed identity checks.

**Exit Criteria:** Every auto-selection `release-agent` call is dominated by the required lock and revalidation path.

### Task 3: Correct browser completion and visible model-state evidence

**Purpose:** Prevent false completion, truncated response artifacts, stale model confirmation, and prose-triggered interruption reports.

**Task Function:** Replace ambiguous DOM aggregation with one scoped visible-response snapshot.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded JavaScript helper change with deterministic fixtures and generated adapter synchronization.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: Node lifecycle tests and adapter parity checks.

**Specification Coverage:**
- Count logical top-level assistant messages; nested Markdown roots do not increment turns.
- Extract complete visible text from the selected message and compare stable message/conversation identity.
- Restrict model lookup and verification to visible radios with exact normalized labels.
- Detect interruption from dedicated visible error UI, not response prose such as `try again`.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:ASSISTANT_TURN_SELECTOR`, `readVisibleAssistantTurns`, `readVisibleAssistantText`, `readVisibleInterruption`, `readCompletionSnapshot`, `waitForReviewCompletion`
- Inspect/modify: `.agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs:findModelOption`, `selectModel`, `verifySelection`
- Modify tests: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_reviews.py`
- Regenerate: all three `generated_agents/*/skills/skill-github-browser-reviews` mirrors

**Dependencies:** Tasks 1–2 complete; no live authenticated browser is required.

**Authority:**
- Preauthorized local actions: edit canonical browser helpers/tests, run adapter synchronization, and run focused Node/Python tests
- Stop for: an unrepresentable ChatGPT UI contract, direct generated-file edits, or base-revision change

**Steps:**
- [x] Use `[data-message-author-role="assistant"]` visible containers as the primary logical-message selector. Use the visible Markdown-root selector only when no assistant containers exist, and never union both selectors; read fallback text only from the selected fallback root.
- [x] Define one logical visible assistant-message snapshot supplying count, selected identity, complete text, URL, conversation ID, generation state, composer readiness, and interruption UI.
- [x] Compute stability and `assistant_turn_index` from logical messages only.
- [x] Use visible exact-label radio lookup and re-read checked state after selection.
- [x] Replace broad interruption phrase matching with dedicated visible error-state locators.
- [x] Add fixtures for nested Markdown, multiple response sections, prior turns, hidden duplicate radios, prefix-sharing labels, and legitimate `try again` prose.
- [x] Run `py -B scripts/sync_agent_adapters.py --all-platforms` and verify parity.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — `19 passed`
- [x] `py -m pytest -q tests/test_github_browser_reviews.py tests/test_github_browser_review_runner.py` — `19 passed`
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — adapters up to date
- Expected: complete intended response is captured, hidden/ambiguous model rows cannot confirm selection, normal prose cannot trigger interruption, and generated mirrors match canonical source.

**Exit Criteria:** Completion, model, and interruption evidence derive from one visible, logically scoped UI state.

### Task 4: Close failed browser resources and isolate review artifacts

**Purpose:** Ensure created tabs and attached clients are released on failure, and concurrent invocations cannot overwrite evidence.

**Task Function:** Make resource ownership and output ownership explicit in the Node runner.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded Node lifecycle and filesystem-contract change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: unit fixtures can exercise thrown setup paths and parallel output allocation without a real browser.

**Specification Coverage:**
- New-tab helpers close a created page if preparation/submission throws before returning it.
- Attached CDP cleanup disconnects the client without closing the user-owned browser; owned persistent contexts still close.
- Every invocation treats `--output-dir` as a parent directory and creates one unique run child beneath it; result metadata records that run identity.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:openReviewTab`, `runReviewPromptInNewTab`, `probeReviewModelInNewTab`
- Inspect/modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:parseArguments`, `openContext`, `closeContext`, `createResult`, `main`
- Modify tests: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`
- Regenerate: all three generated browser-review mirrors

**Dependencies:** Task 3 complete. Preserve and inspect the uncommitted lifecycle-test edit; do not reset it.

**Authority:**
- Preauthorized local actions: edit canonical Node runner/helpers and focused tests, synchronize adapters, and use temporary test directories
- Stop for: deleting/overwriting preserved artifacts, changing external-browser ownership semantics, or base-revision change

**Steps:**
- [x] Wrap new-tab preparation in ownership-aware `try/finally` logic.
- [x] Extend `closeContext` to close owned contexts and disconnect attached CDP clients; close the created page exactly once when still open.
- [x] Treat `--output-dir` as a parent directory, create a unique run child with `mkdtemp`, and include that child identity in result metadata and `response_path`; do not write final artifacts directly into the shared parent.
- [x] Add tests for setup failure after `newPage`, submission failure before page return, attached disconnect, persistent close, and two simultaneous runs with distinct artifacts.
- [x] Synchronize all generated browser-review adapters.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — `19 passed`
- [x] `py -m pytest -q tests/test_github_browser_review_runner.py` — `19 passed`
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — adapters up to date
- Expected: every created resource is closed or disconnected on failure, the external browser remains open, and concurrent runs have distinct artifact paths.

**Exit Criteria:** No helper-created page becomes unreachable to cleanup and default runs cannot share fixed final artifact paths.

### Task 5: Reconcile contracts and generated surfaces

**Purpose:** Bring tests, generated adapters, and source contracts into one consistent state without discarding user work.

**Task Function:** Resolve contract drift after implementation and prove canonical ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: repository consistency and generated-surface reconciliation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final contract checks and focused tests.

**Specification Coverage:**
- `.agents` owns browser helper behavior; generated mirrors are synchronized.
- Tests assert the settled terminal-status and artifact contract.
- The preserved user edit is incorporated or recorded as a stop condition, never silently discarded.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews`, `generated_agents/*/skills/skill-github-browser-reviews`, `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`
- Modify: canonical `.agents` sources and only tests whose assertions contradict the settled contract
- Verify: `scripts/sync_agent_adapters.py`, `tests/test_sync_agent_adapters.py`, browser-review tests

**Dependencies:** Tasks 1–4 complete.

**Authority:**
- Preauthorized local actions: reconcile assertions and regenerate derived adapters without deleting preserved artifacts
- Stop for: conflict between the preserved test edit and the terminal-status contract, or unclear generated-file ownership

**Steps:**
- [x] Inspect the preserved lifecycle-test diff and retain its intent when it matches the settled runner contract.
- [x] Correct only stale assertions covering status, output metadata, cleanup ownership, or visible-state semantics.
- [x] Run synchronization and parity checks; confirm no generated mirror has an unowned manual change.

**Verification:**
- [x] `py -m pytest -q tests/test_sync_agent_adapters.py tests/test_github_browser_reviews.py tests/test_github_browser_review_runner.py` — `40 passed`
- Expected: canonical/generated ownership and browser-review contract tests agree, with preserved user changes still present unless explicitly reconciled.

**Exit Criteria:** No stale test or generated adapter asserts a superseded contract, and no unrelated workspace artifact is removed.

### Task 6: Final verification and handoff readiness

**Purpose:** Produce fresh evidence that the consolidated fixes work together.

**Task Function:** Run the smallest complete validation set and reconcile outcomes with this plan.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence collection across Python and Node surfaces.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is controller-owned for this proposed plan.

**Specification Coverage:**
- All seven findings have focused regression proof.
- Backend failure paths have direct boundary, state, and retry evidence.
- Generated surfaces are synchronized and unrelated workspace changes remain.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all target files, final Git status, and generated parity output
- Modify: none unless a verification failure identifies an in-scope correction
- Verify: launcher, gate, browser lifecycle, synchronization, and repository-contract tests

**Dependencies:** Tasks 1–5 complete.

**Authority:**
- Preauthorized local actions: run declared local verification commands and record results in this plan
- Stop for: failed required check, unrecorded scope deviation, destructive cleanup, or missing evidence

**Steps:**
- [x] Run focused Python tests for launcher, gate, browser-runner contracts, browser-review skill contracts, and adapter synchronization.
- [x] Run focused Node lifecycle tests.
- [x] Run adapter synchronization in check mode and `git diff --check`.
- [x] Inspect final diff/status to confirm preserved user artifacts and no generated-source violations.
- [x] Record command output, deviations, blockers, and deferred recommendations; mark the plan `completed` after execution and verification.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_main_launcher.py tests/test_submission_gate.py tests/test_github_browser_reviews.py tests/test_github_browser_review_runner.py tests/test_sync_agent_adapters.py` — `324 passed`
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — `19 passed`
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check` — adapters up to date
- [x] `git diff --check` — passed
- Expected: all required checks pass, generated adapters are synchronized, and the final diff contains only approved implementation and reconciled test changes.

**Exit Criteria:** Fresh verification covers every in-scope finding with no unresolved required task, failed required check, stale status, or unrecorded scope deviation.

## Verification

- `py -m pytest -q tests/test_herdr_main_launcher.py tests/test_submission_gate.py tests/test_github_browser_reviews.py tests/test_github_browser_review_runner.py tests/test_sync_agent_adapters.py`
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`

These commands are final-artifact checks only and are not run while drafting
this proposed plan. Completion may be marked only after
`skill-verification-before-completion` returns `verified` against fresh output.

## Completion Criteria

The plan is ready for completion verification when:

1. all seven validated findings have implementation tasks and focused proof
2. the gate distinguishes definite non-delivery from uncertain delivery
3. auto-pane discovery has no unowned state-changing Herdr operation
4. browser completion and model evidence use visible, logically scoped state
5. failed browser resources and concurrent artifacts have explicit ownership
6. canonical and generated surfaces are synchronized
7. preserved user changes, deviations, blockers, and final commands are recorded

The plan remains `proposed` until approved execution follows this breakdown and
`skill-verification-before-completion` confirms repository evidence.
