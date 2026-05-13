---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: publication-file-only-allowlist-guard
parent_thread: 27f7d4ad-ca3d-4fa5-8794-8a5db66c4c93
targets:
  - scripts/publish_public_repo.ps1
  - docs/superpowers/plans/audit/20260513-1358-publicpath-scan-failure/report.md
  - docs/superpowers/plans/audit/20260513-1358-publicpath-scan-failure/manifest.yaml
related_features:
  - publication-boundary-hardening
related_stages:
  - publish-public-repo
---

## Goal

Add strict pre-copy guard in publication pipeline so `publicPaths` accepts only explicit files, blocking directory-level allowlists that caused private-reference scan failures and leak-risk drift.

## Key Deliverables

### Deliverable 1: File-only `publicPaths` contract enforced in publish pipeline

`publish_public_repo.ps1` rejects non-existent paths and directory entries in `publicPaths` before copy begins, with clear actionable error text naming offending entry.

### Deliverable 2: Regression-safe verification captured

Verification proves: (1) valid file-level config still exports, (2) temporary directory-level entry fails early at new guard, and (3) existing private-reference scanner contract remains active.

### Deliverable 3: Audit bundle updated with post-fix outcome evidence

Audit report and manifest include bounded fix path, verification commands/results, and final disposition update grounded in produced evidence.

## Task/Wave Breakdown

### Task 1: Implement bounded file-only allowlist guard

**Purpose:**
- Add minimal guardrail to prevent directory-level `publicPaths` drift at source.

**Files:**
- Inspect: `scripts/publish_public_repo.ps1`
- Modify: `scripts/publish_public_repo.ps1`
- Verify: `scripts/publish_public_repo.ps1`

**Preconditions:**
- Worktree contains full repo surfaces (`scripts/`, `repo_config/`, `docs/`).
- Current publication behavior and scanner flow confirmed from audit evidence.

**Steps:**
- [ ] Step 1: Add helper assertion that each configured `publicPaths` entry exists and is a file (not directory).
- [ ] Step 2: Invoke assertion in the `foreach ($relativePath in $publicPaths)` loop before `Copy-PublicPath`.
- [ ] Step 3: Keep all existing scanner/forbidden/required checks unchanged.

**Verification:**
- [ ] `git diff -- scripts/publish_public_repo.ps1` shows only guard function + call-site edits.

**Exit Criteria:**
- Script fails early with explicit message when `publicPaths` contains directory path.

### Task 2: Validate behavior and scan for related patterns

**Purpose:**
- Prove fix addresses trigger while preserving valid behavior; classify similar risks.

**Files:**
- Inspect: `repo_config/publication-config.json`
- Modify: `repo_config/publication-config.json` (temporary local verification edit only, reverted)
- Verify: `scripts/publish_public_repo.ps1`

**Preconditions:**
- Task 1 complete.
- Safe local verification path available.

**Steps:**
- [ ] Step 1: Run publication script with current config and capture success/fail status.
- [ ] Step 2: Temporarily add directory entry (e.g., `scripts`) to `publicPaths`; run publication; confirm early guard failure.
- [ ] Step 3: Revert temporary config change; run targeted search for similar broad allowlist patterns and classify `confirmed | likely | risk` with fix-now/defer decisions.

**Verification:**
- [ ] Commands and outputs captured under audit evidence paths.

**Exit Criteria:**
- Original failure mode blocked at config-guard boundary; no permanent config drift introduced.

### Task 3: Update audit bundle and completeness gate

**Purpose:**
- Record post-fix outcomes with traceable evidence and run canonical audit gate.

**Files:**
- Inspect: `docs/operating_system/templates/audit-report-with-evidence-template.md`
- Modify: `docs/superpowers/plans/audit/20260513-1358-publicpath-scan-failure/report.md`
- Modify: `docs/superpowers/plans/audit/20260513-1358-publicpath-scan-failure/manifest.yaml`
- Verify: `scripts/audit_check.py`

**Preconditions:**
- Task 2 evidence artifacts exist and are hashed.
- Python interpreter path available in executing workspace.

**Steps:**
- [ ] Step 1: Update report sections (`Fix And Verification`, `Risk And Disposition`, `Completion Checklist`) with concrete outcomes.
- [ ] Step 2: Append new evidence artifact records with SHA256 in `manifest.yaml`.
- [ ] Step 3: Run audit completeness gate and capture pass/fail details.

**Verification:**
- [ ] `python scripts/audit_check.py docs/superpowers/plans/audit/20260513-1358-publicpath-scan-failure`

**Exit Criteria:**
- Audit gate passes, or exact missing items documented with minimal next action.

## Verification

- `git diff -- scripts/publish_public_repo.ps1`
- `./scripts/publish_public_repo.ps1` (current config)
- `./scripts/publish_public_repo.ps1` (temporary directory-entry repro)
- `python scripts/audit_check.py docs/superpowers/plans/audit/20260513-1358-publicpath-scan-failure`

## Completion Criteria

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`
