---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: github-review-runner-preflight-hardening
targets:
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
  - generated_agents/claude/skills/skill-github-browser-reviews
  - generated_agents/codex/skills/skill-github-browser-reviews
  - generated_agents/antigravity/skills/skill-github-browser-reviews
---

# GitHub Review Runner Preflight Hardening Plan

## Goal

Harden the GitHub Browser Reviews runner against the validated findings from the
GPT-5.6-Sol High and GPT-6 High reviews of commit
`4b7821099032b3c751fb92be08977bab0aa7e715`, while preserving the existing
personal-workflow architecture:

- one dedicated project profile per run;
- one authenticated Playwright context;
- sequential fresh tabs for multiple models;
- exactly-once submission with no automatic retry or model substitution;
- read-only GitHub review prompts;
- fail-closed context and lease ownership; and
- durable review evidence whenever the runner has enough state to write it.

The explicitly skipped finding, “Composer readiness is treated as
GitHub-review readiness,” is out of scope for this plan.

## Implementation Outcomes

### Immutable review provenance is admission-controlled

Single and batch invocations require a repository identifier, a full commit SHA,
and at least one commit-pinned GitHub file URL. The runner validates every
GitHub `/blob/` URL in the submitted prompt against the declared repository and
SHA before opening the browser, and persists the normalized URL set in every
review result. The runner remains responsible for metadata validation; the
controller remains responsible for judging whether the assistant response proves
that it read the requested revision.

### Profile and context selection remain project-scoped and deterministic

Owned-profile launch validates the profile at the browser-launch boundary, not
only during CLI parsing. A canonical, case-normalized `owner-repository`
project key is derived from the declared GitHub repository and compared with the
terminal profile directory name in both CLI and direct API paths; the caller
cannot make an arbitrary key satisfy the check. Exceptional CDP mode refuses
implicit context selection when more than one browser context is available.

### Failure handling stays bounded and evidence-preserving

Submission uses an explicit internal dispatch state:
`not_dispatched`, `possibly_dispatched`, or `acknowledged`. A control that is
missing before the send action starts is `not_dispatched`; once the send action
has been invoked, any uncertain outcome, including a click/Enter exception, is
`possibly_dispatched` until visible acknowledgement proves `acknowledged`.
Only `not_dispatched` skips the long completion observer. The public result keeps
the existing submission values (`not_started`, `attempted`, `acknowledged`, or
`ambiguous`); `incomplete` remains a result status, not a submission value.
Preflight failures and completion-observation failures persist structured
results and one bounded capture of recoverable visible evidence before cleanup.

### Documentation, tests, and generated adapters remain aligned

Canonical skill text, lifecycle tests, runner contract tests, and generated
adapter projections describe the same admission, failure, evidence, and stop
behavior. No new browser owner, retry engine, hidden-state probe, account
registry, or security subsystem is introduced.

## Validated Findings Consolidation

The following findings are retained because they are supported by the pinned
source and by one or both completed model reviews. The skipped GitHub-app
readiness finding is intentionally excluded. Line references in this table refer
to the pre-patch revision reviewed by the models; the task steps below are the
authoritative corrected implementation scope.

| Severity | Validated finding | Source evidence | Model attribution |
| --- | --- | --- | --- |
| P1 | Standalone review completion can succeed without structured repository, commit-SHA, and pinned-URL provenance. | `run-review-prompt-cli.mjs:23-33,140-145,676-710,777-778`; `SKILL.md:44-46,206-208` | GPT-5.6-Sol and GPT-6 |
| P2 | Exported owned-profile setup bypasses the CLI-only project-profile validator. | `run-review-prompt-cli.mjs:68-70,96-113,332-360` | GPT-6 |
| P2 | Profile validation is convention-based and does not bind the profile to the declared project. | `run-review-prompt-cli.mjs:96-113`; `SKILL.md:166-170` | GPT-5.6-Sol |
| P2 | CDP mode silently selects context index `0` when multiple contexts exist and no index is supplied. | `run-review-prompt-cli.mjs:19,65-82,332-340` | GPT-5.6-Sol |
| P2 | A dead-owner profile lease blocks future runs without an explicit, bounded operator recovery path. | `run-review-prompt-cli.mjs:244-270`; `SKILL.md:232-237` | GPT-5.6-Sol |
| P2 | A failed send click can hold the profile for the full 15-minute completion timeout. | `run-review-prompt.mjs:13-15,226-260,283-285`; `run-review-prompt-cli.mjs:538-550` | GPT-6 |
| P2 | Browser preflight failures occur before per-review result allocation and therefore may exist only in stdout. | `run-review-prompt-cli.mjs:450-475,691-710` | GPT-6 |
| P2 | Completion-observation exceptions can leave available visible response evidence unpersisted. | `run-review-prompt-cli.mjs:538-550` | GPT-6 |
| P1 | The plan's pre-dispatch versus post-click split does not define a reliable dispatch signal and could violate exactly-once handling after a click/Enter exception. | `run-review-prompt.mjs:226-260,348-376`; plan `:188-192` | GPT-5.6-Sol |
| P2 | The plan's project key can remain arbitrary unless it is deterministically derived from the declared owner/repository. | `run-review-prompt-cli.mjs:96-113`; plan `:151-153` | GPT-5.6-Sol |
| P2 | Requiring one valid pinned URL does not reject additional conflicting or unpinned `/blob/` URLs in the same prompt. | plan `:151-153` | GPT-5.6-Sol |
| P2 | The proposed preflight artifact boundary cannot preserve visible evidence after `preflightAuthenticatedContext()` and `openReviewContext()` close their pages or context. | `run-review-prompt.mjs:71-88`; `run-review-prompt-cli.mjs:355-364` | GPT-5.6-Sol |
| P2 | `tests/test_github_browser_review_runner.py` is executed by Task 4 but is not owned by a task that updates its new required arguments. | plan `:139-142,214-217,266-274`; `tests/test_github_browser_review_runner.py:77-117` | GPT-5.6-Sol |

The prior test-coverage observation is not included as a standalone finding:
`tests/test_github_browser_review_lifecycle.mjs` already provides behavioral
coverage beyond the source-shape assertions in
`tests/test_github_browser_reviews.py`. The implementation tasks below extend
that behavioral suite only for the retained contracts. The latest review also
identified two plan omissions that are addressed directly in the task steps:
batch failures must retain the existing per-review `run-*` artifact layout, and
multiple review URLs must use one normalized array represented by repeatable
`--review-url` arguments, batch `review_urls`, and direct-API `reviewUrls`.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the listed canonical scripts/tests/docs, run focused checks, regenerate generated adapters, and run repository validation commands
- User-approval actions: push, merge, external publication, destructive recovery, and deletion of preserved review artifacts
- Parallel ownership: none; canonical scripts and lifecycle tests share control-flow contracts and must be edited serially
- Sequential fallback: execute Tasks 1 through 4 in order in the current workspace

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/github-review-plan-preflight-hardening`
- Base commit: `4b7821099032b3c751fb92be08977bab0aa7e715`
- Expected workspace: `tracked changes limited to the plan, canonical scripts, tests, and generated adapters; preserve existing untracked .playwright-mcp/, .review-profile/, .runtime/, and node_modules/ artifacts`
- Next action: `commit and publish the completed implementation when separately authorized`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | provenance/profile/CDP lifecycle tests | 81 lifecycle tests passed; parser contract tests passed |
| Task 2 | `completed` | current | `codex` | Task 1 | bounded submission and evidence-preservation tests | lifecycle dispatch/evidence tests passed |
| Task 3 | `completed` | current | `codex` | Tasks 1–2 | canonical docs and adapter synchronization checks | canonical skill regenerated to all three adapters |
| Task 4 | `completed` | current | `codex` | Task 3 | full focused verification suite and `git diff --check` | fresh verification recorded below |

## Task Breakdown

### Provenance and admission

**Status:** completed

- Require repository, full commit SHA, and commit-pinned review URLs for single and batch reviews.
- Derive and enforce the repository-specific project key for owned profiles.
- Reject ambiguous CDP context selection when multiple contexts are attached.
- Proof: lifecycle and runner contract tests pass.

### Dispatch and evidence

**Status:** completed

- Classify dispatch as `not_dispatched`, `possibly_dispatched`, or `acknowledged` without resubmission.
- Persist bounded visible evidence and per-review artifacts across preflight, submission, completion, and cleanup failures.
- Proof: lifecycle dispatch, evidence, cleanup, and batch tests pass.

### Documentation and adapters

**Status:** completed

- Update the canonical GitHub Browser Reviews skill with provenance, project-profile, CDP, dispatch, and evidence rules.
- Regenerate Claude, Codex, and Antigravity adapter projections from the canonical source.
- Proof: source-shape tests and adapter synchronization checks pass.

### Final verification

**Status:** completed

- Run focused Node/Python tests, syntax checks, repository contract validation, adapter drift checks, and `git diff --check`.
- Preserve existing untracked runtime artifacts without modifying or deleting them.
- Proof: all required checks pass from the final tracked state.

### Task 1: Gate provenance and owned-profile/context admission

**Purpose:** Make immutable review metadata and browser ownership prerequisites explicit and enforce them at the shared launch boundary.

**Task Function:** Implement the smallest source-level contract change that validates review provenance, binds the owned profile to the declared project key, validates direct API use, and rejects ambiguous CDP context selection.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** P1 provenance; P2 direct profile-validator bypass; P2 project/profile binding; P2 implicit CDP context selection; P2 stale-lease recovery UX.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect and modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`: `VALUE_ARGUMENTS`, `parseArguments`, `validateProjectProfilePath`, the canonical repository/project-key helper, `readBatchReviews`, `acquireProfileLease`, `openContext`, `openReviewContext`, and single-review construction in `main`.
- Extend `tests/test_github_browser_review_lifecycle.mjs` with direct API, provenance, profile-key, prompt-URL consistency, and multi-context CDP cases.
- Update `tests/test_github_browser_review_runner.py` for the new required provenance/project-key arguments and preserve its parser-error assertions.
- Update `.agents/skills/skill-github-browser-reviews/SKILL.md` only after executable behavior is settled.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: add bounded CLI/manifest provenance fields, reuse existing path validation, add deterministic project-key checks, and add isolated lifecycle tests without network access or browser submissions.
- Stop for: a design requiring a profile registry, account discovery, symlink database, automatic retry, hidden browser state, or a second context owner.

**Steps:**
1. Add one canonical provenance validator that requires `repository`, a 40-character hexadecimal `commit_sha`, and one or more URLs matching `https://github.com/OWNER/REPOSITORY/blob/FULL_SHA/PATH`; reject branch URLs, malformed URLs, repository mismatches, and SHA mismatches before `openReviewContext()`.
2. Expose the same provenance contract for single-review arguments and batch entries. Normalize `reviewUrls` as an array: accept repeatable `--review-url` values for the CLI, `review_urls` arrays in manifests, and `reviewUrls` arrays for direct callers. Extract every GitHub `/blob/` URL from the prompt and require each one to match the declared repository and full SHA; require at least one declared URL and reject any conflicting or unpinned target URL.
3. Add `--project-key` as a required owned-profile argument, but derive the expected value from the declared repository using one canonical case-normalized `owner-repository` helper. Require the terminal profile directory name and supplied key to equal that derived value, and pass the same repository/project-key check from `openReviewContext()`/`openContext()` so direct library callers cannot bypass it. Keep the check string-based and deterministic; do not add a profile registry or filesystem-wide discovery.
4. Keep stale lease handling fail-closed, but include the exact lock path and the non-destructive operator command `Remove-Item -LiteralPath '<resolved lock path>'` in the stale-lease error after the recorded PID is confirmed dead. The runner must never execute that command or remove the lock automatically.
5. Preserve whether `--context-index` was explicitly supplied. In CDP mode, fail with a blocked context-selection error when multiple contexts exist and no explicit index is present; retain index `0` only when exactly one context exists.
6. Add focused tests for valid/invalid provenance, every-prompt-URL consistency, direct owned-profile setup, repository-derived project-key mismatch, same-repository-name/different-owner separation, stale-lease error guidance, one-context CDP defaulting, and multi-context CDP rejection.

**Verification:**
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`

**Exit Criteria:** The runner cannot start a review with missing or internally inconsistent provenance, conflicting prompt targets, an unbound owned profile, or an ambiguous multi-context CDP selection, and all new admission cases pass without launching a real browser.

### Task 2: Bound send-failure waits and preserve failure evidence

**Purpose:** Prevent pre-dispatch UI failures from consuming the full completion timeout and ensure preflight/completion failures leave durable diagnostics.

**Task Function:** Refine transaction state classification and artifact persistence without changing exactly-once submission semantics.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** P2 failed-send timeout; P2 preflight artifact loss; P2 completion-evidence loss.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`: `submitPrompt`, `runReviewPrompt`, and `waitForReviewCompletion` boundary behavior.
- Modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`: `runReviewTransaction`, `main`, `persist`, and cleanup/error handling.
- Extend `tests/test_github_browser_review_lifecycle.mjs` with pre-dispatch failure, ambiguous acknowledgement, preflight failure, and partial-evidence cases.

**Dependencies:** Task 1 for the result/provenance shape and context admission contract.

**Authority:**
- Preauthorized local actions: adjust bounded state classification, allocate result artifacts before shared-context preflight, preserve best-effort visible evidence, and add dependency-injected tests.
- Stop for: retrying a prompt, sending a second prompt, changing the 15-minute successful-response budget for valid in-flight reviews, or treating arbitrary text as proof of completion.

**Steps:**
1. Implement the explicit internal dispatch state machine: `not_dispatched` before the send action is invoked, `possibly_dispatched` immediately when the action is invoked or its outcome is uncertain, and `acknowledged` only after visible acknowledgement. A click/Enter exception after invocation remains `possibly_dispatched`; do not infer `not_dispatched` from a thrown UI action. Map these states to the existing public submission values without introducing `incomplete` as a submission value.
2. Observe completion at most once for `possibly_dispatched` and `acknowledged`; only `not_dispatched` returns promptly without the long observer. Preserve the 15-minute valid in-flight response budget and never retry or resubmit.
3. Allocate the batch output root and every review's existing `run-*` result directory before owned-context preflight. Persist one initial per-review blocked/incomplete result plus a batch summary when shared context creation or authentication preflight fails; retain the failure scope and precise stage in both forms.
4. Before `preflightAuthenticatedContext()` or `openReviewContext()` closes a page/context after a failure, capture one bounded visible-evidence record containing the current URL and recoverable visible login/composer/error text. Attach it to the structured error and persist it before cleanup. When completion observation or evidence extraction throws after a page is retained, make one bounded best-effort visible capture and persist any available assistant text, message identity, URL, and failure reason. Do not retry observation indefinitely.
5. Add lifecycle tests proving that controls missing before send do not call the long completion observer, click/Enter exceptions after invocation observe at most once, ambiguous acknowledgement observes at most once, shared-context preflight writes every per-review `result.json` plus the batch summary, preflight evidence survives cleanup, and partial completion evidence survives an extraction exception.

**Verification:**
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`

**Exit Criteria:** Failure paths remain exactly-once, bounded, and fail-closed while producing a result artifact and every recoverable piece of visible evidence.

### Task 3: Align canonical documentation, tests, and generated adapters

**Purpose:** Make the canonical skill and generated platform projections describe the implemented contracts without duplicating or contradicting ownership rules.

**Task Function:** Update the canonical skill and its maintained behavioral/source-shape tests, then regenerate all adapter projections from canonical sources.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** Documentation alignment; generated-surface ownership; personal-workflow simplicity; skipped-finding exclusion.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/SKILL.md`.
- Modify `tests/test_github_browser_reviews.py` only for canonical wording/contract assertions that changed.
- Keep `tests/test_github_browser_review_runner.py` aligned with the finalized CLI contract; Task 1 owns argument behavior, while Task 3 updates only documentation/source-shape assertions if wording changes.
- Regenerate, never hand-edit, the projections under `generated_agents/claude/skills/skill-github-browser-reviews`, `generated_agents/codex/skills/skill-github-browser-reviews`, and `generated_agents/antigravity/skills/skill-github-browser-reviews` using `python scripts/sync_agent_adapters.py --all-platforms`.

**Dependencies:** Tasks 1–2.

**Authority:**
- Preauthorized local actions: update canonical documentation, extend contract assertions, regenerate declared adapter projections, and run drift checks.
- Stop for: editing generated adapter files directly, adding the skipped GitHub-app readiness requirement, or introducing a new browser lifecycle owner/profile registry.

**Steps:**
1. Document the required provenance fields, all-prompt-URL consistency rule, repository-derived `--project-key`/profile relationship, explicit CDP selection rule, dispatch state machine, pre-dispatch timeout boundary, per-review batch artifact timing, and the printed stale-lease recovery command.
2. Keep the documentation explicit that controller-side revision evidence remains distinct from runner completion and that no automatic retry or resubmission is allowed.
3. Update source-shape assertions only where canonical wording or required symbols changed.
4. Run `python scripts/sync_agent_adapters.py --all-platforms` and verify the three generated surfaces match the canonical skill and scripts.

**Verification:**
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `py -B scripts/validate_repo_contracts.py`
- `py -m pytest -q tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`

**Exit Criteria:** Canonical documentation, tests, and all generated adapters express the same bounded workflow and no generated drift remains.

### Task 4: Run final verification and reconcile the plan

**Purpose:** Prove the integrated behavior from the final tracked state and leave a truthful handoff for execution.

**Task Function:** Run fresh focused and repository contract checks, inspect the diff, and reconcile the plan ledger without marking implementation complete.

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Specification Coverage:** Final proof, source/test/generated-surface consistency, preserved untracked artifacts, and stop-condition compliance.

**Required Skills:** `skill-verification-before-completion`

**Files And Symbols:**
- Inspect all task-owned files and `docs/superpowers/plans/2026-10-25-14-57-github-review-runner-preflight-hardening-plan.md`.
- Do not modify `.playwright-mcp/`, `.review-profile/`, `.runtime/`, or `node_modules/`.

**Dependencies:** Task 3.

**Authority:**
- Preauthorized local actions: run final checks, inspect tracked diff, update this plan’s task ledger/evidence, and record failed or skipped proof.
- Stop for: stale base SHA, unrelated tracked changes, required test failure, generated drift, or any request to rerun the completed browser reviews.

**Steps:**
1. Run the full focused proof set from the Verification section.
2. Run `git diff --check` and inspect `git status --short` to confirm only plan/source/test/generated changes are tracked and preserved runtime artifacts remain untouched.
3. Reconcile task states and evidence from fresh command output; leave `status: proposed` until the plan is explicitly approved for execution.

**Verification:**
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`
- `py -B scripts/validate_repo_contracts.py`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`

**Exit Criteria:** Fresh proof is recorded, retained findings map to executable tasks, the skipped finding remains out of scope, and the plan is ready for explicit approval and execution.

## Verification

The implementation executor must run these commands after Tasks 1–3 and before
changing this plan to a terminal state:

- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/select-review-model.mjs`
- `py -B scripts/validate_repo_contracts.py`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`

No live GitHub browser review is part of implementation proof. The completed
read-only review artifacts remain preserved under
`.runtime/github-review-20261025-final/` and must not be resubmitted.

## Observed Proof

- `node --test tests/test_github_browser_review_lifecycle.mjs` — 81 passed, 0 failed.
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py` — 25 passed, 0 failed.
- Node syntax checks passed for `run-review-prompt-cli.mjs`, `run-review-prompt.mjs`, and `select-review-model.mjs`.
- `py -B scripts/validate_repo_contracts.py` — repository contract validation passed.
- `python scripts/sync_agent_adapters.py --all-platforms --check` — all generated adapters are up to date.
- `git diff --check` — no whitespace errors.
- Existing untracked review/runtime artifacts were preserved and not modified by the implementation.

## Completion Criteria

1. Single and batch reviews reject missing or inconsistent repository, SHA, or pinned-URL provenance before browser launch.
2. Every completed result persists model, effort, prompt hash, repository, full commit SHA, and pinned review URLs.
3. Owned-profile launch validates the profile in both CLI and exported API paths and rejects a project-key mismatch.
4. CDP mode rejects implicit context choice when multiple contexts are available.
5. Pre-dispatch send failures do not consume the full completion timeout, and no failure path resubmits.
6. Preflight and completion failures persist structured result artifacts plus all recoverable visible evidence.
7. Canonical skill documentation and all generated adapters match the implemented behavior.
8. Focused tests, syntax checks, repository contracts, adapter drift checks, and `git diff --check` pass from the final tracked state.
9. The skipped GitHub-app readiness finding is not implemented and is not reintroduced through generated documentation.
10. `skill-verification-before-completion` can return `verified` from fresh command output before the plan is marked completed.

## Stop Conditions

- Stop if the requested behavior requires automatic resubmission, model substitution, lower effort, a second browser/context owner, hidden-state inspection, or broad retry logic.
- Stop if a profile path cannot be proven to be project-specific without adding a registry or external account-identification service.
- Stop if a result artifact cannot be persisted safely; preserve stdout and report `incomplete` rather than claiming verified evidence.
- Stop if the base commit changes before implementation begins; reconcile this plan and rerun source-level validation against the new immutable revision.
- Stop if the generated adapter synchronization command produces drift or requires hand edits.

## Handoff

After approval, execute through `skill-executing-plans`. Keep the completed browser-review artifacts read-only and preserved as evidence; do not rerun the model submissions unless the user explicitly authorizes a new review.
