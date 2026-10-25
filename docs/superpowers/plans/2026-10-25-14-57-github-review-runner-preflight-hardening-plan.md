---
layer: change
artifact_type: plan
status: proposed
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
and at least one commit-pinned GitHub file URL. The runner validates that the
metadata agrees before opening the browser and persists the same values in every
review result. The runner remains responsible for metadata validation; the
controller remains responsible for judging whether the assistant response proves
that it read the requested revision.

### Profile and context selection remain project-scoped and deterministic

Owned-profile launch validates the profile at the browser-launch boundary, not
only during CLI parsing. The profile is checked against the declared project
key without adding a registry or cross-project discovery layer. Exceptional CDP
mode refuses implicit context selection when more than one browser context is
available.

### Failure handling stays bounded and evidence-preserving

A send click failure is not treated as a possible dispatched request unless the
runner has evidence that dispatch may have occurred. Ambiguous acknowledgement
continues to observe exactly once, but a pre-dispatch failure returns promptly.
Preflight failures and completion-observation failures persist structured
results and best-effort visible evidence before cleanup.

### Documentation, tests, and generated adapters remain aligned

Canonical skill text, lifecycle tests, runner contract tests, and generated
adapter projections describe the same admission, failure, evidence, and stop
behavior. No new browser owner, retry engine, hidden-state probe, account
registry, or security subsystem is introduced.

## Validated Findings Consolidation

The following findings are retained because they are supported by the pinned
source and by one or both completed model reviews. The skipped GitHub-app
readiness finding is intentionally excluded.

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

The prior test-coverage observation is not included as a standalone finding:
`tests/test_github_browser_review_lifecycle.mjs` already provides behavioral
coverage beyond the source-shape assertions in
`tests/test_github_browser_reviews.py`. The implementation tasks below extend
that behavioral suite only for the retained contracts.

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
- Branch: `main`
- Base commit: `4b7821099032b3c751fb92be08977bab0aa7e715`
- Expected workspace: `tracked clean; preserve existing untracked .playwright-mcp/, .review-profile/, .runtime/, and node_modules/ artifacts`
- Next action: `approve this plan, then activate Task 1`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | provenance/profile/CDP lifecycle tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | bounded submission and evidence-preservation tests | pending |
| Task 3 | `pending` | current | `unresolved` | Tasks 1–2 | canonical docs and adapter synchronization checks | pending |
| Task 4 | `pending` | current | `unresolved` | Task 3 | full focused verification suite and `git diff --check` | pending |

### Task 1: Gate provenance and owned-profile/context admission

**Purpose:** Make immutable review metadata and browser ownership prerequisites explicit and enforce them at the shared launch boundary.

**Task Function:** Implement the smallest source-level contract change that validates review provenance, binds the owned profile to the declared project key, validates direct API use, and rejects ambiguous CDP context selection.

**Template Profile:**
- Controller-selected: `unresolved`

**Specification Coverage:** P1 provenance; P2 direct profile-validator bypass; P2 project/profile binding; P2 implicit CDP context selection; P2 stale-lease recovery UX.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect and modify `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`: `VALUE_ARGUMENTS`, `parseArguments`, `validateProjectProfilePath`, `readBatchReviews`, `acquireProfileLease`, `openContext`, `openReviewContext`, and single-review construction in `main`.
- Extend `tests/test_github_browser_review_lifecycle.mjs` with direct API, provenance, profile-key, and multi-context CDP cases.
- Update `.agents/skills/skill-github-browser-reviews/SKILL.md` only after executable behavior is settled.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: add bounded CLI/manifest provenance fields, reuse existing path validation, add deterministic project-key checks, and add isolated lifecycle tests without network access or browser submissions.
- Stop for: a design requiring a profile registry, account discovery, symlink database, automatic retry, hidden browser state, or a second context owner.

**Steps:**
1. Add one canonical provenance validator that requires `repository`, a 40-character hexadecimal `commit_sha`, and one or more URLs matching `https://github.com/OWNER/REPOSITORY/blob/FULL_SHA/PATH`; reject branch URLs, malformed URLs, repository mismatches, and SHA mismatches before `openReviewContext()`.
2. Expose the same provenance contract for single-review arguments and batch entries; require the prompt to contain the declared full SHA and at least one declared pinned URL so the structured metadata and submitted request cannot silently diverge.
3. Add `--project-key` as a required owned-profile argument, require the terminal profile directory name to match it, and pass the same `projectKey` check from `openReviewContext()`/`openContext()` so direct library callers cannot bypass it. Keep the check string-based and deterministic; do not add a profile registry or filesystem-wide discovery.
4. Keep stale lease handling fail-closed, but include the exact lock path and the non-destructive operator command `Remove-Item -LiteralPath '<resolved lock path>'` in the stale-lease error after the recorded PID is confirmed dead. The runner must never execute that command or remove the lock automatically.
5. Preserve whether `--context-index` was explicitly supplied. In CDP mode, fail with a blocked context-selection error when multiple contexts exist and no explicit index is present; retain index `0` only when exactly one context exists.
6. Add focused tests for valid/invalid provenance, direct owned-profile setup, project-key mismatch, stale-lease error guidance, one-context CDP defaulting, and multi-context CDP rejection.

**Verification:**
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`

**Exit Criteria:** The runner cannot start a review with missing or internally inconsistent provenance, an unbound owned profile, or an ambiguous multi-context CDP selection, and all new admission cases pass without launching a real browser.

### Task 2: Bound send-failure waits and preserve failure evidence

**Purpose:** Prevent pre-dispatch UI failures from consuming the full completion timeout and ensure preflight/completion failures leave durable diagnostics.

**Task Function:** Refine transaction state classification and artifact persistence without changing exactly-once submission semantics.

**Template Profile:**
- Controller-selected: `unresolved`

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
1. Distinguish a send-control failure before a dispatch signal from a post-click acknowledgement timeout. Mark both as non-success, but only observe completion after the latter; return the former immediately with `submission: ambiguous` or `incomplete` according to the existing exactly-once contract.
2. Allocate the batch/run result directory before owned-context preflight, persist the initial blocked/incomplete result, and update it with the precise failure stage when context creation or authentication preflight fails.
3. When completion observation or evidence extraction throws after a page is retained, make one bounded best-effort visible snapshot attempt and persist any available assistant text, message identity, URL, and failure reason before cleanup. Do not retry observation indefinitely.
4. Add lifecycle tests proving that pre-dispatch failures do not call the long completion observer, ambiguous acknowledgement still observes at most once, preflight failures write `result.json`, and partial evidence survives a completion-extraction exception.

**Verification:**
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`

**Exit Criteria:** Failure paths remain exactly-once, bounded, and fail-closed while producing a result artifact and every recoverable piece of visible evidence.

### Task 3: Align canonical documentation, tests, and generated adapters

**Purpose:** Make the canonical skill and generated platform projections describe the implemented contracts without duplicating or contradicting ownership rules.

**Task Function:** Update the canonical skill and its maintained behavioral/source-shape tests, then regenerate all adapter projections from canonical sources.

**Template Profile:**
- Controller-selected: `unresolved`

**Specification Coverage:** Documentation alignment; generated-surface ownership; personal-workflow simplicity; skipped-finding exclusion.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Modify `.agents/skills/skill-github-browser-reviews/SKILL.md`.
- Modify `tests/test_github_browser_reviews.py` only for canonical wording/contract assertions that changed.
- Regenerate, never hand-edit, the projections under `generated_agents/claude/skills/skill-github-browser-reviews`, `generated_agents/codex/skills/skill-github-browser-reviews`, and `generated_agents/antigravity/skills/skill-github-browser-reviews` using `python scripts/sync_agent_adapters.py --all-platforms`.

**Dependencies:** Tasks 1–2.

**Authority:**
- Preauthorized local actions: update canonical documentation, extend contract assertions, regenerate declared adapter projections, and run drift checks.
- Stop for: editing generated adapter files directly, adding the skipped GitHub-app readiness requirement, or introducing a new browser lifecycle owner/profile registry.

**Steps:**
1. Document the required provenance fields, `--project-key`/profile relationship, explicit CDP selection rule, pre-dispatch timeout boundary, artifact timing, and the printed stale-lease recovery command.
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
- Controller-selected: `unresolved`

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
