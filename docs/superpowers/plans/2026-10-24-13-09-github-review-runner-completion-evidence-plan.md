---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: github-review-runner-completion-evidence
targets:
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - generated_agents/codex/skills/skill-github-browser-reviews
  - generated_agents/claude/skills/skill-github-browser-reviews
  - generated_agents/antigravity/skills/skill-github-browser-reviews
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
  - tests/test_github_browser_review_lifecycle.mjs
  - docs/superpowers/plans/2026-10-24-13-09-github-review-runner-completion-evidence-plan.md
---

# GitHub Review Runner Completion

## Goal

Make one normal `run-review-prompt-cli.mjs` invocation a bounded review transaction. The
invocation selects and visibly verifies the requested model and effort, submits exactly
once, waits for bounded visible completion, writes the response and a small result record,
and cleans up the runner-owned browser state. It returns a predictable `verified`,
`incomplete`, or `blocked` result without adding a scheduler, retry service, Git
publisher, model orchestrator, audit mode, or second lifecycle store.

## Review Basis

- The current CLI parses only browser attachment, model, effort, prompt, context, and
  `--probe-only` arguments; it has no output artifact or completion contract.
- `runReviewPromptInNewTab()` returns immediately after `submitPrompt()` observes a
  changed composer. There is no completion wait, final assistant-response extraction,
  interruption check, conversation capture, or evidence validation.
- The CLI logs a transient JSON line and then closes the owned context in `finally`, so
  the browser lifecycle ends immediately after submission rather than after review
  completion and artifact persistence.
- Existing focused tests mainly inspect source text and argument failures. They do not
  prove completion states, ambiguous submission handling, artifact persistence, or
  teardown ordering.
- Dedicated persistent-profile launch and explicit CDP attachment already exist. The
  implementation preserves those boundaries, keeps CDP opt-in, and does not add profile
  copying or CDP-port discovery.
- Revision and file-specific evidence remain part of the review prompt and caller
  acceptance workflow, not a mandatory runner argument contract. The runner does not
  discover Git state or add a GitHub API/network client.

## Implementation Outcomes

### Atomic review transaction

Normal submission performs `model/effort verification -> submission -> bounded completion
wait -> artifact persistence -> cleanup` in one process. `--probe-only` remains a
diagnostic mode and is not a mandatory precursor to normal submission. The helper still
submits at most once and ambiguous submission acknowledgement stops the transaction
without an automatic retry.

### Durable result and response artifacts

Each normal invocation writes `result.json` and `response.md` beneath `--output-dir`,
which defaults to `review-output`. `result.json` records the requested and visibly
verified model/effort, submission/completion states, conversation URL and assistant-turn
identity, response path, failure stage, and failure reason. A successful result is
`verified` when the submission is acknowledged and the newly associated visible
assistant turn completes without interruption. The caller evaluates revision-specific
GitHub evidence from the saved response.

### Bounded visible completion and evidence proof

Completion uses visible page signals together: streaming has stopped, the normal
composer/send state has returned, no interruption/error is visible, and a new final
visible assistant turn exists after the submission baseline. A bounded backoff wait
prevents a fixed high-frequency poll. The runner does not inspect connector-specific or
revision-specific evidence; those checks stay with the review workflow that owns the
prompt and acceptance decision.

### Model-picker view compatibility

The live ChatGPT model picker can expose model radio items and the thinking-effort
`Power` control in the same simple view. The selector must not switch to the model-list
view when those radios are already visible, because that view can hide the effort
control and block otherwise valid GPT-6/High selection. A focused regression test guards
this view-preserving behavior; generated adapters remain synchronized from the
canonical skill.

### Canonical skill and generated adapter consistency

The canonical browser-review skill documents the atomic normal path, diagnostic probe
boundary, dedicated profile/CDP ownership, exact result artifacts, and no-rerun rule.
Generated Codex, Claude, and Antigravity skill surfaces are regenerated from the
canonical source and checked for drift.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect and edit the named review-runner sources, tests, canonical skill, generated adapter outputs, and plan; run the declared local verification commands; install missing test dependencies only when required for those commands
- User-approval actions: push, merge, external browser submission, GitHub publication, destructive cleanup, or changes outside the named targets
- Parallel ownership: `none; the CLI, helper, documentation, generated outputs, and tests share one sequential contract`
- Sequential fallback: `Task 1 -> Task 2 -> Task 3 -> Task 4 -> Task 5`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-pane-lifecycle-plan-review`
- Base commit: `e978292`
- Expected workspace: `preserved untracked local artifacts only: .playwright-mcp/, .runtime/, node_modules/, and GPT review output files; task-owned .review-profile/ may remain from the focused probe test`
- Next action: `run focused local verification; authenticated browser smoke remains optional external evidence`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused CLI contract tests | `tests/test_github_browser_review_runner.py`: 9 passed |
| Task 2 | `completed` | current | `codex` | Task 1 | lifecycle harness tests | `tests/test_github_browser_review_lifecycle.mjs`: 5 passed |
| Task 3 | `completed` | current | `codex` | Tasks 1-2 | artifact assertions | lifecycle completion and atomic result/response writes pass |
| Task 4 | `completed` | current | `codex` | Tasks 1-3 | canonical/generated skill checks | adapter sync `--check` passed; 19 focused Python tests passed |
| Task 5 | `active` | current | `codex` | Tasks 1-4 | focused and final repository checks | local checks pass; authenticated smoke is optional and unverified |

## Task Breakdown

### Task 1: Define the CLI transaction and result contract

**Purpose:**
- Add the smallest explicit CLI contract needed to preserve review intent and produce
  durable state without making the runner responsible for Git or orchestration.

**Task Function:**
- Convert the existing argument parser and transient stdout result into a small
  artifact-backed result record with staged failure reporting.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded contract work with low implementation ambiguity after source validation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead-controller focused contract tests are sufficient

**Specification Coverage:**
- Optional `--output-dir` with a stable default, one normal invocation, terminal
  `verified|incomplete|blocked` status, an internal `running` state, and failure
  artifacts.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:parseArguments`, `main`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:USAGE`, `parseArguments`, `main`
- Modify: `tests/test_github_browser_review_runner.py`
- Verify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`

**Dependencies:**
- Current parser behavior and the result states defined in this plan.

**Authority:**
- Preauthorized local actions: edit the named CLI and focused Python test; run focused parser/help tests
- Stop for: a request to change Git publication, model orchestration, retry policy, or browser attachment ownership

**Steps:**
- [x] Step 1: Parse the browser attachment, model, effort, prompt, optional output directory, and diagnostic probe arguments; keep the output directory defaultable for ordinary use.
- [x] Step 2: Define one result object with `status` (`running|verified|incomplete|blocked`), requested/verified model and effort, `submission_attempted`, submission/completion states, conversation/turn identity, response path, failure stage, and failure reason.
- [x] Step 3: Create the output directory and atomically write `status: running` `result.json` before browser submission; update it for each terminal path without adding locks or recovery state.
- [x] Step 4: Keep stdout concise and machine-readable while retaining `response.md` and `result.json` as the durable runner output.

**Verification:**
- [x] `py -3 -m pytest tests/test_github_browser_review_runner.py -q`
- Expected: parser/help tests cover the small argument contract, probe-only exception, result fields, and nonzero incomplete/blocked contract without launching a browser.

**Exit Criteria:**
- The CLI has a documented, test-covered result schema and can persist a staged result before any send action.

### Task 2: Add bounded completion and ownership-aware lifecycle handling

**Purpose:**
- Keep the browser session alive through the final visible assistant response and close
  it only after response/evidence artifacts are durable.

**Task Function:**
- Extend the existing page helper with a bounded visible completion observation contract,
  while retaining the helper’s no-launch, no-authentication, and no-retry boundary.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: browser lifecycle behavior is high-risk but bounded to existing helper and CLI

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic lifecycle harness plus focused CLI assertions

**Specification Coverage:**
- No premature close; one submission; visible completion signals; bounded wait; explicit
  handling for interruption, timeout, and ambiguous submission; association with the
  conversation and assistant turn created by this submission.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:submitPrompt`, `runReviewPrompt`, `runReviewPromptInNewTab`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:submitPrompt`, `runReviewPrompt`, add `waitForReviewCompletion`, and add `readVisibleAssistantText`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:main` teardown and transaction sequencing
- Add: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 result writer and terminal-state names.
- Existing `selectReviewModel` visible verification remains the only model/effort selector; do not replace it with hidden DOM or page-evaluation state.

**Authority:**
- Preauthorized local actions: edit the named helper/CLI and add the deterministic lifecycle harness; run Node and focused pytest checks
- Stop for: unstable selector changes requiring a new browser integration design, or any request to add automatic retry, browser switching, or profile copying

**Steps:**
- [x] Step 1: Capture the pre-submit conversation URL and visible assistant-turn count before filling the prompt; pass a `beforeSubmit` callback into `runReviewPrompt` so the CLI persists `submission_attempted: true` immediately before the Send click.
- [x] Step 2: Preserve submit-once behavior but return an explicit acknowledgement classification. An unchanged composer or ambiguous post-click state becomes a terminal submission failure without retry.
- [x] Step 3: Add `waitForReviewCompletion(page, options)` with one bounded deadline and bounded backoff. Require no visible generating/stop state, normal composer/send state, no visible interruption/error, a stable conversation URL, and a new final visible assistant turn beyond the pre-submit baseline.
- [x] Step 4: Use `readVisibleAssistantText(page)` and capture the assistant turn associated with the new conversation/turn baseline, recording `conversation_id` and `assistant_turn_index` from visible page state without reading hidden transport state. An acknowledgement-only turn or transient idle state remains `incomplete`.
- [x] Step 5: Move owned-context cleanup after result and response persistence. Preserve explicit CDP attachment as opt-in and do not add endpoint discovery or profile copying.
- [x] Step 6: Ensure every thrown browser-stage error is converted into the result envelope before cleanup; cleanup errors must not erase the original failure stage.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: deterministic page doubles cover successful completion, ongoing generation until timeout, visible interruption, missing final assistant response, acknowledgement-before-final response, ambiguous submission, and teardown occurring after artifact persistence.
- [x] `py -3 -m pytest tests/test_github_browser_review_runner.py -q`
- Expected: CLI source/argument assertions confirm the helper is invoked once and owned browser cleanup is not on the pre-completion path.

**Exit Criteria:**
- A normal run cannot report success or close its owned context immediately after submission; every path reaches a bounded terminal result.

### Task 3: Persist review artifacts

**Purpose:**
- Retain the completed response and a small machine-readable lifecycle record without
  making the runner responsible for repository-specific acceptance policy.

**Task Function:**
- Add small atomic writers for the visible response and lifecycle result.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: artifact contract is bounded and independent of GitHub authentication

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lifecycle and artifact assertions cover the contract

**Specification Coverage:**
- No automatic retry; response and failure artifacts; no Git discovery, connector
  heuristics, or GitHub API client inside the CLI.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:main`
- Modify: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:add atomicWrite and writeResult`
- Modify: `tests/test_github_browser_review_runner.py`
- Modify: `tests/test_github_browser_review_lifecycle.mjs`

**Dependencies:**
- Task 1 result schema and Task 2 visible response/completion output.

**Authority:**
- Preauthorized local actions: edit the named CLI/tests and run artifact-focused checks
- Stop for: a request to fetch GitHub through a new network client, infer Git state inside the runner, or add automatic retries

**Steps:**
- [x] Step 1: Use atomic temp-file-plus-rename writes for `result.json`; persist `submission_attempted` before Send without adding a lock or stale-transaction recovery path.
- [x] Step 2: Write the visible assistant response verbatim to `response.md` and write `result.json` with conversation/turn identity and exact failure reason.
- [x] Step 3: Preserve partial artifacts on timeout, interruption, or ambiguous submission; never resubmit automatically.
- [x] Step 4: If the output directory or `result.json` cannot be written, emit a structured failure record to stderr with a nonzero exit code.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs`
- Expected: completion, timeout, interruption, and ambiguous-submission paths preserve `response.md`/`result.json` when writable.
- [x] `py -3 -m pytest tests/test_github_browser_review_runner.py -q`
- Expected: CLI contract tests verify the small argument contract, optional `--output-dir`, atomic-write behavior, stderr fallback, and artifact names.

**Exit Criteria:**
- The runner produces durable artifacts and cannot claim `verified` without submission acknowledgement and completion proof for a newly associated assistant turn.

### Task 4: Align the canonical skill and generated runtime surfaces

**Purpose:**
- Remove the mandatory two-process probe/submission race and make documentation match the
  implemented runner boundary.

**Task Function:**
- Update the canonical skill, regenerate adapters, and preserve the existing explicit
  model-selection and pipe-browser restrictions.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: canonical documentation and deterministic generated outputs

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing generated-surface tests and sync check

**Specification Coverage:**
- Atomic normal path; diagnostic-only `--probe-only`; dedicated profile; explicit CDP;
  Node/Playwright runner; precise `verified`, `incomplete`, and `blocked` meanings; no
  rerun without explicit authorization.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/SKILL.md:Review Procedure`, `Helper execution boundary`, `Completion Result`
- Modify: `.agents/skills/skill-github-browser-reviews/SKILL.md`
- Regenerate: `generated_agents/codex/skills/skill-github-browser-reviews`, `generated_agents/claude/skills/skill-github-browser-reviews`, `generated_agents/antigravity/skills/skill-github-browser-reviews`
- Verify: `scripts/sync_agent_adapters.py`, `tests/test_github_browser_reviews.py`

**Dependencies:**
- Tasks 1-3 establish the actual flags, result fields, and completion behavior before documentation is changed.

**Authority:**
- Preauthorized local actions: edit the canonical skill, run `py -3 scripts/sync_agent_adapters.py --all-platforms`, and run generated-surface tests
- Stop for: generated drift not attributable to the canonical skill/helper changes, or a request to hand-edit generated files

**Steps:**
- [x] Step 1: Replace the mandatory probe-before-submit wording with atomic normal preflight and diagnostic-only probe wording.
- [x] Step 2: Document the normal CLI invocation with optional `--output-dir`, terminal statuses, and artifact paths.
- [x] Step 3: Define `verified` as submission acknowledged and completion associated with the submitted conversation/assistant turn; define `incomplete` as an unproven or timed-out transaction; define `blocked` as browser-access or artifact-initialization refusal.
- [x] Step 4: Retain the dedicated authenticated profile, explicit CDP-only attachment, pipe-browser restriction, visible model/effort verification, and no-rerun authorization rules.
- [x] Step 5: Regenerate all maintained adapters from the canonical source and do not edit generated files directly.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated surfaces are synchronized after regeneration.
- [x] `py -3 -m pytest tests/test_github_browser_reviews.py -q`
- Expected: canonical and generated skill checks pass, including explicit model/effort and browser-runner boundaries.

**Exit Criteria:**
- Documentation and all generated adapter surfaces describe the same atomic runner contract without adding a second orchestrator.

### Task 5: Run integrated verification and reconcile the plan

**Purpose:**
- Prove the changed runner contract and record any environment-limited evidence before
  handoff to implementation approval.

**Task Function:**
- Execute focused and repository-level checks, inspect the diff, and reconcile plan state.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: final verification requires repository-wide contract checks

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `skill-verification-before-completion` owns final completion proof

**Specification Coverage:**
- Fresh evidence for lifecycle, artifact, documentation, generated outputs, and unchanged
  explicit browser/model-selection boundaries.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all Task 1-4 targets and `git diff --check`
- Verify: `tests/test_github_browser_review_runner.py`, `tests/test_github_browser_reviews.py`, `tests/test_github_browser_review_lifecycle.mjs`, generated adapter drift, repository status

**Dependencies:**
- Tasks 1-4 completed with their task-local proof.

**Authority:**
- Preauthorized local actions: run declared focused tests, generated-surface checks, diff checks, and repository status inspections; update this plan’s task/evidence fields
- Stop for: any required test failure, stale generated output, unexpected target change, or external authenticated browser submission without explicit user authorization

**Steps:**
- [x] Step 1: Run the lifecycle Node tests and focused Python tests.
- [x] Step 2: Run generated adapter synchronization/check and `git diff --check`.
- [ ] Step 3: If separately authorized, run one real-browser smoke test through the Node/Playwright runner with explicit profile, prompt, and output paths; verify model/effort selection, one submission, completion association, and artifact persistence.
- [x] Step 4: Inspect that no new scheduler, retry loop, GitHub API client, profile-copy path, CDP discovery path, audit mode, lock, or second result store was introduced.
- [x] Step 5: Record local verification evidence; authenticated browser smoke remains optional external evidence.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs`
- [x] `py -3 -m pytest tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py -q`
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `git diff --check`
- [ ] Optional smoke command: `node .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs --user-data-dir <authenticated-profile> --model GPT-5.6-Sol --effort High --prompt-file <review-prompt.txt> --output-dir <review-output>`
- Expected: all declared focused checks pass, generated outputs are clean, and any explicitly authorized smoke test either produces `verified` artifacts or records explicit `incomplete/blocked` browser evidence without retry.

**Exit Criteria:**
- The plan contains no unresolved required task, unsupported claim, or unrecorded scope deviation; implementation remains gated on explicit approval.

## Verification

Final artifact-level verification after implementation:

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -3 -m pytest tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py -q`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- Inspect `result.json` and `response.md` fixtures for `verified`, `incomplete`, and `blocked` paths, including preserved failure evidence.
- When explicitly authorized, inspect the real-browser smoke output; source and tests remain authoritative when no smoke run is available.

Local evidence recorded for this execution:

- `node --test tests/test_github_browser_review_lifecycle.mjs`: 5 passed.
- `py -3 -m pytest tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py -q`: focused tests passed.
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`: passed.
- `git diff --check`: passed.
- Authenticated smoke test: not run; no authenticated browser submission was authorized
  for this simplification patch.

## Completion Criteria

The implementation is ready for completion verification when:

1. one normal CLI invocation performs the complete bounded transaction and submits at most once
2. owned browser cleanup occurs only after completion and artifact handling
3. `verified` requires submission acknowledgement and completion of the newly submitted conversation/assistant turn
4. timeout, interruption, ambiguous submission, selection failure, and artifact-write failure produce explicit nonzero terminal results with preserved evidence where writable; unwritable output emits structured stderr failure
7. `--probe-only` remains diagnostic and is not required before normal submission
8. dedicated profile and explicit CDP boundaries remain intact; no profile copying or endpoint discovery is added
9. Git publication, model orchestration, scheduling, retries, and task interpretation remain outside the CLI
10. canonical skill documentation and all generated adapters are synchronized
11. focused lifecycle, contract, generated-surface, and diff checks pass with fresh output
12. any explicitly authorized real-browser smoke test is supplemental and never required for the normal local contract

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified` against implementation evidence.
