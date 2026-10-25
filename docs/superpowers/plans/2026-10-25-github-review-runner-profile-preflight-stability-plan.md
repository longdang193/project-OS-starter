---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
distribution_tier: starter_kit
name: github-review-runner-profile-preflight-stability
reviewed_repository: longdang193/project-OS-starter
reviewed_branch: main
reviewed_commit: 92711d50d6c019bab391ef784ca5c01bb824219b
reviewed_remote_ref: refs/heads/main
reviewed_remote_sha: 92711d50d6c019bab391ef784ca5c01bb824219b
targets:
  - .agents/skills/skill-github-browser-reviews/SKILL.md
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs
  - .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs
  - tests/test_github_browser_review_lifecycle.mjs
  - tests/test_github_browser_review_runner.py
  - tests/test_github_browser_reviews.py
  - tests/test_skill_github_browser_reviews.py
  - scripts/sync_agent_adapters.py
  - scripts/validate_repo_contracts.py
  - generated_agents/claude/skills/skill-github-browser-reviews/SKILL.md
  - generated_agents/codex/skills/skill-github-browser-reviews/SKILL.md
  - generated_agents/antigravity/skills/skill-github-browser-reviews/SKILL.md
---

# GitHub Review Runner Profile Preflight And Stability Plan

## Goal

Make the personal GitHub review runner fail predictably before submission and
preserve useful evidence after ambiguous or interrupted browser work. Keep the
existing architecture: one persistent browser context per batch, sequential
fresh review tabs, visible model and effort verification, exactly-once
submission, read-only review scope, and fail-closed terminal statuses.

The reviewed immutable revision is `92711d50d6c019bab391ef784ca5c01bb824219b`.
`git ls-remote origin refs/heads/main` resolves the remote branch to the same
SHA. Commit-pinned evidence links:

- [CLI/profile parsing](https://github.com/longdang193/project-OS-starter/blob/92711d50d6c019bab391ef784ca5c01bb824219b/.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs#L21-L68)
- [Lease acquisition](https://github.com/longdang193/project-OS-starter/blob/92711d50d6c019bab391ef784ca5c01bb824219b/.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs#L210-L260)
- [Composer/readiness](https://github.com/longdang193/project-OS-starter/blob/92711d50d6c019bab391ef784ca5c01bb824219b/.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs#L46-L79)
- [Acknowledgement](https://github.com/longdang193/project-OS-starter/blob/92711d50d6c019bab391ef784ca5c01bb824219b/.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs#L196-L224)
- [Completion](https://github.com/longdang193/project-OS-starter/blob/92711d50d6c019bab391ef784ca5c01bb824219b/.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs#L244-L296)
- [Final persistence](https://github.com/longdang193/project-OS-starter/blob/92711d50d6c019bab391ef784ca5c01bb824219b/.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs#L480-L536)

## Implementation Outcomes

### Deterministic project-profile admission

The normal submission path resolves one dedicated project profile, rejects the
normal Chrome `User Data` profile and ambiguous roots, and rejects unknown CLI
flags before browser launch. No credentials or absolute personal paths are
committed.

### Shared authentication and bounded lifecycle handling

After context creation, one non-submitting visible session preflight stops a
logged-out batch before it opens doomed tabs. Review-local readiness remains
bounded and visible. Model/effort checks remain per review. There is no retry,
model substitution, or hidden session inspection.

### Truthful evidence and conservative cleanup

The single send action gets a short bounded acknowledgement window; visible
terminal interruption returns immediately with partial output; final artifact
persistence failure becomes `incomplete` with a nonzero exit. The small lease
remains, with best-effort normal termination cleanup and explicit manual stale
lock recovery. No heartbeat, daemon, age-based deletion, or PID-only reclaim is
added.

### Canonical documentation and regression proof

Focused tests cover the new preflight, failure scope, acknowledgement,
interruption, lease cleanup, persistence, and parser behavior. Canonical
`.agents/skills` sources are updated first; generated adapters are refreshed
only through the existing synchronization script.

## Validated Findings Consolidation

Only findings supported by the pinned source and local evidence are included.

| ID | Severity | Finding and root cause | Impact | Attribution |
| --- | --- | --- | --- | --- |
| PF-01 | P1 | Project-specific profile is documented but not enforced: `parseArguments()` accepts any `--user-data-dir`, and launch applies it directly. | A fresh, logged-out, or personal profile reaches the composer check and fails with a generic readiness error. | Source-confirmed; GPT-5.6-Sol and GPT-6 |
| PF-02 | P1/P2 | Authentication is not a shared preflight: readiness is checked independently in each fresh tab. | A logged-out batch repeats doomed setup, making profile/auth/loading failures appear intermittent and wasting time. | Source-confirmed; GPT-5.6-Sol and GPT-6 |
| PF-03 | P2 | CDP mode bypasses owned-profile isolation and introduces separate ownership/cleanup branches. | A normal run can attach to a daily browser context; lifecycle reasoning becomes more complex. | Source-confirmed; GPT-5.6-Sol, constrained by existing CDP contract |
| PF-04 | P2 | Lease recovery can require manual intervention: malformed/dead-owner locks remain blocked and normal termination has no cleanup path. | A crash can block the next run until the operator confirms the browser is closed and performs recovery. | Source-confirmed; GPT-5.6-Sol and GPT-6 |
| PF-05 | P2 | Failure scope partly depends on Playwright error-message regexes. | Upstream wording changes can misclassify shared-context failures as review-local or vice versa. | Source-confirmed; GPT-6 |
| PF-06 | P2 | Submission acknowledgement waits exactly 250 ms before declaring unchanged composer text ambiguous. | A successful delayed clear can be falsely marked ambiguous after the one send action. | Source-confirmed; GPT-5.6-Sol and GPT-6 |
| PF-07 | P2 | Completion observation does not immediately terminate on a visible interruption. | A terminal error can consume the long timeout and lose a specific failure reason. | Source-confirmed; GPT-5.6-Sol and GPT-6 |
| PF-08 | P2 | Final `result.json` persistence can warn while retaining `completed`, so the CLI may return zero. | Durable automation state can be incomplete while the process claims success. | Source-confirmed; GPT-6 |
| PF-09 | P2 | Unknown CLI flags are silently accepted because the parser has no allow-list. | Typos such as `--outpt-dir` silently use defaults and place evidence unexpectedly. | Source-confirmed; GPT-5.6-Sol and GPT-6 |

The intermittent “composer not found” symptom is therefore a preflight and
classification problem: profile state, authentication, redirects/loading, and
selector readiness converge on one message. The fix is one small shared
visible preflight plus clearer ownership boundaries, not a browser daemon or a
large selector fallback matrix.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-verification-before-completion`, `skill-github-browser-reviews`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: `listed source/test/doc edits, focused tests, repository validation, and generated adapter synchronization`
- User-approval actions: `browser submissions, push, merge, destructive cleanup, stale-lock recovery, or edits outside listed targets`
- Parallel ownership: `none`
- Sequential fallback: `Tasks 1–4 in order, then Task 5 as the only final reconciliation lane`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/github-review-plan`
- Base commit: `bdd34f29081ec4d07732cd1fa59c5d12f9436595`
- Expected workspace: `tracked source unchanged; preserve .playwright-mcp/, .review-profile/, .runtime/, and node_modules/`
- Next action: `final verification passed; ready for separately authorized Git disposition`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | parser/profile tests | `node --test` and `pytest` passed |
| Task 2 | `completed` | current | `codex` | Task 1 | auth/scope tests | `node --test` and `pytest` passed |
| Task 3 | `completed` | current | `codex` | Task 2 | acknowledgement/interruption tests | `node --test` passed |
| Task 4 | `completed` | current | `codex` | Task 2 | lease/persistence tests | `node --test` and `pytest` passed |
| Task 5 | `completed` | current | `codex` | Tasks 1–4 | full validation | all required checks passed |

## Task Breakdown

### Task 1: Tighten profile and CLI preflight

**Purpose:**
- Admit only a dedicated project profile and reject malformed/unknown CLI input before browser launch.

**Task Function:**
- Define and enforce the smallest stable profile/argument admission contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded parser and launch-contract change with low ambiguity.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused parser and contract tests.

**Specification Coverage:**
- PF-01, PF-03, PF-09; no personal-profile fallback; preserve optional CDP compatibility.

**Required Skills:**
- `skill-code-standards`, `skill-github-browser-reviews`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:parseArguments,openContext`
- Modify: the same symbols and focused tests
- Verify: `tests/test_github_browser_review_runner.py`, `tests/test_github_browser_reviews.py`

**Dependencies:**
- Reviewed remote SHA remains `92711d50d6c019bab391ef784ca5c01bb824219b`.

**Authority:**
- Preauthorized local actions: edit the listed parser/launch code and focused tests; run local checks.
- Stop for: credentials in Git, user-specific absolute paths in Git, removal of required CDP compatibility, or unrelated CLI changes.

**Steps:**
- [x] Define one canonical project-profile policy without storing auth state.
- [x] Reject normal Chrome `User Data` roots, ambiguous paths, unknown flags, and invalid mode combinations before launch.
- [x] Document user-data-dir as the normal path; keep CDP exceptional and mutually exclusive.

**Verification:**
- [x] Invalid inputs fail before `launchPersistentContext()` or `connectOverCDP()`.

**Exit Criteria:**
- Profile and CLI admission is deterministic and has no new browser lifecycle owner.

### Task 2: Add shared authentication preflight and ownership-based failure scope

**Purpose:**
- Stop logged-out batches once and distinguish auth/profile failures from review-local readiness failures.

**Task Function:**
- Add a visible non-submitting session gate and conservative failure attribution.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lifecycle boundary change coupled to Task 1.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: injected context/page fakes cover the boundary.

**Specification Coverage:**
- PF-02 and PF-05; one context per batch; visible-only readiness; fail closed on context loss.

**Required Skills:**
- `skill-code-standards`, `skill-github-browser-reviews`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:openReviewContext,processBatch`, `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:openChatGPT,openReviewTab`
- Modify: those symbols and focused lifecycle tests
- Verify: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`

**Dependencies:**
- Task 1 establishes the admitted profile and mode.

**Authority:**
- Preauthorized local actions: add one visible probe step and ownership-boundary classification.
- Stop for: hidden DOM/network/session inspection, automatic login, retries, or a broad abstraction rewrite.

**Steps:**
- [x] Open one probe page after context creation and verify visible authenticated readiness without submitting.
- [x] Stop the batch on an explicit login wall; preserve a clear blocked result and close the probe.
- [x] Classify context/page ownership at boundaries; keep only a narrow regex fallback where unavoidable.

**Verification:**
- [x] One auth failure blocks the batch without opening/submitting every review.
- [x] Slow review readiness remains review-scoped; context loss remains shared-context scoped.

**Exit Criteria:**
- Logged-out or invalid-profile runs stop once before submission with actionable status.

### Task 3: Bound acknowledgement and terminal interruption handling

**Purpose:**
- Reduce false ambiguity and unnecessary waiting without sending a second prompt.

**Task Function:**
- Refine the single-submission observation state machine with bounded waits.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: isolated helper behavior with existing deterministic tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: in-memory page fakes cover timing and terminal states.

**Specification Coverage:**
- PF-06 and PF-07; exactly-once submission; partial evidence on interruption.

**Required Skills:**
- `skill-code-standards`, `skill-github-browser-reviews`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs:submitPrompt,waitForReviewCompletion,readVisibleInterruption`
- Modify: those helpers and `tests/test_github_browser_review_lifecycle.mjs`
- Verify: the same lifecycle test file

**Dependencies:**
- Task 2 establishes session and failure boundaries.

**Authority:**
- Preauthorized local actions: adjust bounded polling and terminal-state checks.
- Stop for: a second click/Enter, retry, resubmission, model substitution, or unbounded polling.

**Steps:**
- [x] Replace the fixed 250 ms acknowledgement sleep with a short bounded poll.
- [x] Preserve ambiguous delivery as a terminal incomplete state without resubmission.
- [x] Return immediately on visible interruption with partial assistant text and a specific reason.

**Verification:**
- [x] Delayed composer clear is acknowledged without a second send.
- [x] Visible interruption returns before the long completion deadline.

**Exit Criteria:**
- Delayed UI transitions no longer create avoidable ambiguity and terminal errors do not consume the full timeout.

### Task 4: Harden artifact finalization and lease cleanup

**Purpose:**
- Make result status truthful and reduce normal stale-lock accumulation while preserving conservative crash recovery.

**Task Function:**
- Reconcile cleanup, lease, and final persistence into one fail-closed result.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded CLI lifecycle changes with an existing lease contract.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: injected filesystem/process dependencies and lifecycle tests.

**Specification Coverage:**
- PF-04 and PF-08; retain the lease; normal cleanup; explicit manual recovery; nonzero persistence failure.

**Required Skills:**
- `skill-code-standards`, `skill-github-browser-reviews`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs:acquireProfileLease,releaseProfileLease,processReview,main`
- Modify: those symbols, tests, and `SKILL.md`
- Verify: `tests/test_github_browser_review_lifecycle.mjs`, `tests/test_github_browser_review_runner.py`

**Dependencies:**
- Tasks 2–3 establish ownership and terminal response states.

**Authority:**
- Preauthorized local actions: add best-effort normal cleanup and make final write failure terminal.
- Stop for: automatic dead-owner deletion, PID/timestamp-only reclaim, a lease daemon, or destructive artifact cleanup.

**Steps:**
- [x] Release only this invocation’s lease on normal termination when ownership is provable.
- [x] Keep ambiguous stale ownership operator-blocked and document recovery after confirming the browser is closed.
- [x] Mark final result-write failure `incomplete` and return nonzero while retaining response evidence.

**Verification:**
- [x] Normal cleanup removes only the owned lock; ambiguous ownership remains blocked.
- [x] Final persistence failure cannot yield `completed` or exit zero.

**Exit Criteria:**
- Cleanup and finalization outcomes are durable and truthful without a second ownership system.

### Task 5: Reconcile documentation, generated adapters, and final proof

**Purpose:**
- Align canonical docs, generated surfaces, tests, and repository contracts.

**Task Function:**
- Perform final source-of-truth synchronization and acceptance verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: repository-wide reconciliation and fresh command-backed proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is lead-owned.

**Specification Coverage:**
- All outcomes; canonical `.agents/skills` source of truth; generated adapters only from sync.

**Required Skills:**
- `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Inspect: all Task 1–4 changes and generated diffs
- Modify: canonical `SKILL.md`, then generated outputs through `scripts/sync_agent_adapters.py`
- Verify: all listed targets and this plan

**Dependencies:**
- Tasks 1–4 complete; no competing active plan ledger.

**Authority:**
- Preauthorized local actions: run focused/full checks, synchronize generated adapters, and record evidence.
- Stop for: generated drift, failed required proof, changed reviewed base, or unrelated workspace changes.

**Steps:**
- [x] Update canonical documentation first.
- [x] Run `python scripts/sync_agent_adapters.py --all-platforms`; inspect the generated diff.
- [x] Run final checks and apply `skill-verification-before-completion`.

**Verification:**
- [x] `node --test tests/test_github_browser_review_lifecycle.mjs` — 76 passed.
- [x] `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py` — 25 passed.
- [x] `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs` — passed.
- [x] `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs` — passed.
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check` — adapters up to date.
- [x] `python scripts/validate_repo_contracts.py --fast` — passed after plan ledger reconciliation.
- [x] `git diff --check` — passed.

**Exit Criteria:**
- Canonical/generated surfaces agree and fresh verification is `verified` without live browser resubmission.

## Fragile Bottlenecks And Deliberate Constraints

- Composer/auth detection stays visible-only and bounded; no hidden DOM,
  cookie, or transport inspection is added.
- The dedicated profile is user-managed: the runner validates the path but does
  not install Chrome, authenticate, or run a persistent browser daemon.
- Model and effort remain visibly checked per review; no selector fallback tree
  or extra model-selection path is introduced.
- Exactly-once delivery remains conservative: ambiguous acknowledgement keeps
  evidence and ends incomplete; it never retries.
- One context and sequential fresh tabs remain the only batch topology. A
  context failure stops the batch; review-local failures do not create another
  browser owner.
- Commit-pinned revision evidence remains caller-supplied; no new connector or
  remote polling service is added.
- Generated adapters remain derived surfaces and are synchronized once from
  canonical sources.
- No lease heartbeat, stale-lock daemon, PID/timestamp auto-reclaim, keep-open
  mode, retry budget, or recovery matrix is introduced.

## Verification

- `git ls-remote origin refs/heads/main` and record the observed SHA.
- `node --test tests/test_github_browser_review_lifecycle.mjs`
- `py -m pytest -q tests/test_github_browser_review_runner.py tests/test_github_browser_reviews.py tests/test_skill_github_browser_reviews.py`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt-cli.mjs`
- `node --check .agents/skills/skill-github-browser-reviews/scripts/run-review-prompt.mjs`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_repo_contracts.py --fast`
- `git diff --check`

Final completion requires fresh output, truthful task ledger state, no
unresolved required task, and `skill-verification-before-completion` returning
`verified`. Checked boxes alone are not proof.

## Completion Criteria

1. PF-01 through PF-09 are implemented or explicitly deferred with a reason.
2. The normal run admits only a dedicated project profile and rejects unknown
   flags before browser launch.
3. Authentication is checked once per persistent context before submission.
4. CDP remains exceptional compatibility, not a new normal lifecycle owner.
5. Submission remains exactly once; acknowledgement and interruption handling
   are bounded and preserve evidence.
6. Normal lease cleanup is best-effort; ambiguous stale ownership remains
   operator-blocked rather than auto-deleted.
7. Final persistence failure produces `incomplete` and a nonzero exit.
8. Canonical docs, generated adapters, tests, and validators pass fresh proof.
9. No credentials, profile contents, private outputs, or unrelated artifacts
   enter tracked files.

## Stop Conditions

- Stop if the reviewed remote SHA changes before implementation; revalidate.
- Stop if a fix requires automatic resubmission, model substitution, lower
  effort, hidden session inspection, a second browser owner, or a daemon.
- Stop if profile ownership, visible auth readiness, or post-send page/context
  ownership cannot be proven.
- Stop if generated adapters cannot be synchronized or required checks fail for
  unrelated reasons without being recorded.

## Handoff

After approval, execute through `skill-executing-plans`. Keep review outputs and
browser-profile artifacts outside tracked source. Git publication, push, pull
request creation, review, and merge remain separately authorized finishing
actions.
