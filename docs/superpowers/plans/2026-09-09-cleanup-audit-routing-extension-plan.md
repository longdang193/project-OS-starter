---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: cleanup-audit-routing-extension
targets:
  - .agents/skills/skill-disposable-artifact-cleanup/SKILL.md
  - tests/test_disposable_artifact_cleanup.py
  - generated_agents/codex/skills/skill-disposable-artifact-cleanup/SKILL.md
  - generated_agents/claude/skills/skill-disposable-artifact-cleanup/SKILL.md
  - generated_agents/antigravity/skills/skill-disposable-artifact-cleanup/SKILL.md
---

# Cleanup Audit And Routing Extension

## Goal

Extend cleanup auditing to classify runtime, Git, browser, and database
resources without taking ownership of their retirement. Preserve exact-path
cleanup, protected-state rules, verification order, and lifecycle owners.

## Implementation Outcomes

### Canonical contract

The cleanup skill defines exact resource identity, ownership evidence, direct
versus delegated mode, and `eligible`, `preserve`, and `blocked` results.
Delegated resources are eligible for owner action only, never proof of removal.

### Lifecycle boundaries

Herdr resources, Git worktrees, browser state, and databases route to their
producing or lifecycle owner. Direct cleanup retains current authorization,
retention, path-safety, protected-state, and post-cleanup verification rules.

### Generated consistency

Generated skill mirrors, starter-kit output, and repository contracts remain
consistent. Existing unrelated changes and untracked `.playwright-mcp/` and
`db/` artifacts remain untouched.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical skill and focused test, regenerate adapters, build and validate starter output, and run declared checks while preserving unrelated state
- User-approval actions: commits, pushes, merges, publication, process termination, destructive cleanup, deletion of existing untracked artifacts, or edits outside listed targets
- Parallel ownership: none
- Sequential fallback: canonical skill, focused tests, generated sync, final validation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `4a2ae85024a877f5c0c9e9920b9c16f1d2d60f13`
- Expected workspace: prior OpenDesign changes are committed in `4a2ae85`; preserve untracked `.playwright-mcp/` and `db/`, plus this plan, canonical skill, generated mirrors, and focused test
- Next action: perform final completion verification
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | canonical skill contract | canonical skill updated; focused contract proof passed |
| Task 2 | `completed` | current | `codex` | Task 1 | focused cleanup contract tests | `4 passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | adapter sync and mirror inspection | adapter sync and drift check passed |
| Task 4 | `completed` | current | `codex` | Task 3 | starter-kit, repository, and diff checks | `34 passed`; starter kit, repository contracts, adapter sync, deploy-aware drift, and diff checks passed |

## Task Breakdown

### Task 1: Update canonical cleanup contract

**Purpose:** Add audit-and-routing coverage without moving deletion authority.

**Task Function:** Revise ownership and lifecycle rules in the canonical skill.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation contract.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent ownership-boundary review.

**Specification Coverage:** Approved cleanup-audit routing proposal and preserved lifecycle invariants.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-disposable-artifact-cleanup/SKILL.md`, `.agents/skills/skill-finishing-a-development-branch/SKILL.md`, `scripts/herdr_main_launcher.py`
- Modify: `.agents/skills/skill-disposable-artifact-cleanup/SKILL.md`

**Dependencies:** Approved proposal; current cited lifecycle-owner procedures.

**Authority:**
- Preauthorized local actions: edit canonical cleanup skill and inspect cited sources.
- Stop for: generated-file edits, lifecycle-owner changes, weakened protections, or cleanup of unrelated artifacts.

**Steps:**
- [x] Replace path-only ownership wording with exact normalized resource identity for files, worktrees, Herdr resources, browser state, and databases.
- [x] Add candidate table for direct temporary artifacts, Herdr resources, worktrees, migration residue, browser state, databases, and persistent or legacy source.
- [x] Define `cleanup_mode: direct | delegated`; delegated `eligible` means owner-action eligibility, not deletion approval.
- [x] Name actual procedures: Herdr reconciliation only where supported, native workspace cleanup, `git worktree remove`, and producer-owned browser/database cleanup.
- [x] Preserve direct cleanup before final verification and worktree cleanup after verified Git disposition and lane retirement.
- [x] Keep missing or stale evidence, unknown delivery, blocked work, timeout, and protected state at `preserve` or `blocked`.

**Verification:** Inspect diff; no rule grants this skill authority to close sessions, retire agents, remove worktrees, delete databases, or delete browser profiles.

**Exit Criteria:** Canonical skill has executable direct and delegated rules without lifecycle ownership drift.

### Task 2: Add cleanup contract regression tests

**Purpose:** Lock routing, ownership, retention, and lifecycle boundaries.

**Task Function:** Add static source-contract tests using existing repository patterns.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small deterministic contract test.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: verify preserved prohibitions and new routing rules independently.

**Specification Coverage:** Resource identity, delegated semantics, protected state, worktree order, and supported Herdr procedure.

**Required Skills:** `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `tests/test_git_lane_lifecycle.py`, `.agents/skills/skill-disposable-artifact-cleanup/SKILL.md`
- Create: `tests/test_disposable_artifact_cleanup.py`

**Dependencies:** Task 1 complete.

**Authority:**
- Preauthorized local actions: create focused test file and run its pytest module.
- Stop for: runtime termination, external authentication, or unrelated test changes.

**Steps:**
- [x] Read canonical skill from repository root.
- [x] Assert resource identity, ownership table, cleanup modes, result values, delegated non-removal, protected databases/browser state, worktree ordering, and Herdr limits.
- [x] Run focused pytest and adjust only canonical wording or focused tests.

**Verification:** `py -m pytest tests/test_disposable_artifact_cleanup.py -q`

**Exit Criteria:** Focused tests fail on approved-boundary regressions and pass against canonical skill.

### Task 3: Regenerate maintained agent surfaces

**Purpose:** Publish canonical skill changes without direct generated-file edits.

**Task Function:** Run repository-owned adapter generation and inspect outputs.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic generator.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent generated-surface inspection.

**Specification Coverage:** `.agents/skills/` remains SSOT; all maintained mirrors match it.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`, `adapters/*/mapping.yaml`
- Modify through generator: `generated_agents/codex/skills/skill-disposable-artifact-cleanup/SKILL.md`, `generated_agents/claude/skills/skill-disposable-artifact-cleanup/SKILL.md`, `generated_agents/antigravity/skills/skill-disposable-artifact-cleanup/SKILL.md`

**Dependencies:** Task 2 passes.

**Authority:**
- Preauthorized local actions: run all-platform adapter sync and inspect output.
- Stop for: mapping drift, source mismatch, or need for manual generated edits.

**Steps:**
- [x] Run `py -B scripts/sync_agent_adapters.py --all-platforms`.
- [x] Inspect headers and transformed content.
- [x] Run `py -B scripts/sync_agent_adapters.py --all-platforms --check`.

**Verification:** Adapter check passes.

**Exit Criteria:** Generated surfaces are synchronized.

### Task 4: Run final verification

**Purpose:** Prove contract, generated, starter-kit, repository, and workspace-safety outcomes.

**Task Function:** Run focused and repository-level checks, then reconcile scope.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: fixed validation commands.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent final-scope acceptance.

**Specification Coverage:** All plan outcomes and preserved invariants.

**Required Skills:** `skill-plan-document-reviewer`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: changed canonical skill, focused tests, generated mirrors, starter output, and Git status
- Verify: `repo_config/starter-kit-manifest.json` and preserved unrelated artifacts

**Dependencies:** Tasks 1–3 complete.

**Authority:**
- Preauthorized local actions: run listed validators, build starter output, inspect diffs, preserve unrelated state.
- Stop for: failed checks, unexpected tracked changes, or any request to delete `.playwright-mcp/` or `db/`.

**Steps:**
- [x] Run focused tests: `py -m pytest tests/test_disposable_artifact_cleanup.py tests/test_git_lane_lifecycle.py tests/test_sync_agent_adapters.py tests/test_validate_agent_metadata_schema.py -q`.
- [x] Build and validate starter output: `py -B scripts/build_starter_kit.py --output-root generated_exports` and `py -B scripts/validate_starter_kit.py --output-root generated_exports`.
- [x] Run `py -B scripts/validate_repo_contracts.py --fast`.
- [x] Run `py -B scripts/validate_agent_runtime_drift.py --all-platforms`; user-local runtime mirrors deployed and drift check passed.
- [x] Run `git diff --check`; confirm only planned files changed and preserved workspace files remain untouched.

**Verification:** All repository-local commands and deploy-aware runtime drift validation pass; no unrelated workspace state changed.

**Exit Criteria:** Fresh proof supports complete scope, generated surfaces are aligned, and no unapproved cleanup or unrelated edits occurred.

## Verification

- `py -m pytest tests/test_disposable_artifact_cleanup.py tests/test_git_lane_lifecycle.py tests/test_sync_agent_adapters.py tests/test_validate_agent_metadata_schema.py -q`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `py -B scripts/build_starter_kit.py --output-root generated_exports`
- `py -B scripts/validate_starter_kit.py --output-root generated_exports`
- `py -B scripts/validate_repo_contracts.py --fast`
- `py -B scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`

## Completion Criteria

1. Canonical skill defines exact resource identity and owner routing without lifecycle retirement authority.
2. Focused tests cover routing semantics and preserved cleanup protections.
3. Generated adapter surfaces are synchronized.
4. Starter-kit and repository validation pass.
5. Existing modified files and untracked `.playwright-mcp/` and `db/` remain preserved.
6. No commit, push, merge, process termination, or destructive cleanup occurs without explicit authorization.

Fresh completion verification returned `verified`; branch disposition remains user-authorized and unchanged.
