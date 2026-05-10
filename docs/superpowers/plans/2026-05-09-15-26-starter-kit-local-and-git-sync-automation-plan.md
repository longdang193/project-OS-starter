---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: starter-kit-local-and-git-sync-automation
parent_workstream: none
targets:
  - scripts/sync_local_starter_kit_repo.ps1
  - scripts/build_starter_kit.py
  - scripts/validate_starter_kit.py
  - scripts/validate_repo_contracts.py
  - repo_config/starter-kit-manifest.json
  - repo_config/starter-kit-closure.json
  - docs/operating_system/runtime/runtime-surfaces.md
  - tests/test_starter_kit_generation.py
  - tests/test_validate_repo_contracts.py
related_features: []
related_stages: []
---

# Implementation Plan Template

## Goal

Add one canonical workflow that updates both local generated starter-kit output and sibling `project-OS-starter-kit` git repo in one safe path, with validation and parity checks that prevent target confusion, partial sync drift, and runtime/manifest generation mismatch.

## Key Deliverables

Use this section for final implementation outcomes only.
Do not restate task-by-task execution details or local verification steps here.

### Canonical starter-kit sync command

Deliver a source-owned script that runs source-repo validation, adapter sync, starter-kit rebuild, starter-kit validation, full-tree mirror sync into sibling `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit`, parity verification, and optional git commit/push for sibling repo.

### Guardrails against repeat drift

Deliver validation coverage that proves starter-kit shipped surfaces, generated runtime root instruction files, and sibling repo sync expectations remain aligned, so future updates fail fast before partial or ambiguous publication.

## Task/Wave Breakdown

Use `Task` for directly executable implementation slices.
Use `Wave` only when plan truly needs orchestration across multiple related tasks.

Within each task:
- `Purpose` owns bounded outcome
- `Files` owns touched-surface inventory
- `Preconditions` owns prerequisites
- `Steps` owns execution sequence
- `Verification` owns task-local proof
- `Exit Criteria` owns task completion gate

Do not duplicate final artifact verification commands here unless a command is truly both task-local and final.

### Task 1: Define canonical sync contract

**Purpose:**
- Lock exact semantics for “update starter kit” so future work always means rebuild generated export, sync sibling repo, and optionally publish git updates.

**Files:**
- Inspect: `repo_config/starter-kit-manifest.json`
- Inspect: `repo_config/starter-kit-closure.json`
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md`
- Inspect: `scripts/build_starter_kit.py`
- Inspect: `scripts/validate_starter_kit.py`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `repo_config/starter-kit-closure.json`
- Verify: `tests/test_starter_kit_generation.py`

**Preconditions:**
- Current source repo state is clean or intentionally tracked.
- Source repo remains canonical owner of starter-kit generation logic.
- Sibling repo path is confirmed: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit`.

**Steps:**
- [ ] Step 1: Confirm source-owned versus generated-owned boundaries for starter-kit publication, including root docs, `.agents`, `docs`, `repo_config`, `scripts`, and `tests`.
- [ ] Step 2: Update runtime/closure docs so they explicitly distinguish generated export path from sibling repo sync target and define “full-tree sync” as default behavior.
- [ ] Step 3: Review starter-kit manifest expectations against runtime-surface docs and adapter-generated root instruction outputs so contract language matches actual generated surfaces.

**Verification:**
- [ ] `pytest tests/test_starter_kit_generation.py -q`
- [ ] Manual inspection confirms docs name both paths exactly and do not imply partial directory sync.

**Exit Criteria:**
- Contract text clearly defines source export path, sibling repo path, and required full-tree sync semantics.

### Task 2: Implement full-tree local sync script

**Purpose:**
- Create one executable command that performs end-to-end local starter-kit refresh and sibling repo sync without manual piecemeal copy operations.

**Files:**
- Inspect: `scripts/build_starter_kit.py`
- Inspect: `scripts/validate_starter_kit.py`
- Inspect: `scripts/validate_repo_contracts.py`
- Modify: `scripts/sync_local_starter_kit_repo.ps1`
- Verify: `scripts/sync_local_starter_kit_repo.ps1`
- Verify: `generated_exports/project-OS-starter-kit`

**Preconditions:**
- Task 1 complete.
- Sibling repo exists locally and is accessible.
- Script contract decides whether commit/push is default or behind explicit flags.

**Steps:**
- [ ] Step 1: Create PowerShell script that runs, in order: repo-config validation, adapter sync, repo-contract validation, starter-kit build, starter-kit validation.
- [ ] Step 2: Add full-tree mirror sync from `project-OS-starter/generated_exports/project-OS-starter-kit` into `project-OS-starter-kit`, covering root docs plus `.agents`, `docs`, `repo_config`, `scripts`, and `tests`.
- [ ] Step 3: Add clear flags for dry-run / no-push / push behavior, and fail fast when sibling repo has unrelated dirty state or required paths are missing.

**Verification:**
- [ ] Run script in no-push mode against local sibling repo.
- [ ] Confirm synchronized file set includes both `docs/operating_system/templates` and `tests` without manual follow-up copies.
- [ ] Confirm script exits non-zero if a prerequisite validator step fails.

**Exit Criteria:**
- One source-owned script can rebuild and sync full starter-kit tree locally in one command.

### Task 3: Add parity and failure-gate validation

**Purpose:**
- Prevent future mismatches between manifest expectations, generated runtime surfaces, and sibling repo publication by adding explicit validation gates.

**Files:**
- Inspect: `scripts/validate_starter_kit.py`
- Inspect: `scripts/validate_repo_contracts.py`
- Inspect: `adapters/claude/mapping.yaml`
- Inspect: `adapters/gemini/mapping.yaml`
- Inspect: `adapters/codex/mapping.yaml`
- Modify: `scripts/validate_starter_kit.py`
- Modify: `scripts/validate_repo_contracts.py`
- Modify: `tests/test_starter_kit_generation.py`
- Modify: `tests/test_validate_repo_contracts.py`
- Verify: `generated_agents/antigravity/GEMINI.md`
- Verify: `generated_agents/claude/CLAUDE.md`
- Verify: `generated_agents/codex/AGENTS.md`

**Preconditions:**
- Task 2 complete.
- Root-doc generation paths remain canonical generated surfaces.

**Steps:**
- [ ] Step 1: Add validator logic or helper checks that assert manifest-required shipped surfaces exist in generated export after adapter sync and build.
- [ ] Step 2: Add parity checks that compare generated export against sibling repo target after sync, or expose a reusable comparison routine the sync script can call.
- [ ] Step 3: Expand tests to cover missing generated root instruction files, partial-sync detection, and sibling parity failure cases.

**Verification:**
- [ ] `pytest tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py -q`
- [ ] Negative-path test proves validation fails when expected generated root docs are absent.
- [ ] Negative-path test proves sync/parity check fails when sibling repo remains stale in `templates` or `tests`.

**Exit Criteria:**
- Repo has automated checks for runtime/manifest parity and post-sync sibling parity.

### Task 4: Add publish-safe sibling git automation

**Purpose:**
- Make local sync and git publication one bounded workflow so “update both local and git of the kit” becomes repeatable and low-risk.

**Files:**
- Inspect: `scripts/sync_local_starter_kit_repo.ps1`
- Modify: `scripts/sync_local_starter_kit_repo.ps1`
- Verify: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit`

**Preconditions:**
- Tasks 2 and 3 complete.
- Sibling repo remote and branch expectations are known.

**Steps:**
- [ ] Step 1: Add optional git phase for sibling repo: status check, stage synced changes, commit with standard message, push `main`.
- [ ] Step 2: Add safety gates that stop publish when sibling repo contains unrelated dirty files or parity verification has not passed.
- [ ] Step 3: Add concise operator output showing what was rebuilt, what was synced, what was committed, and what was pushed.

**Verification:**
- [ ] Dry-run mode shows intended git actions without mutating sibling repo.
- [ ] No-push mode commits locally without remote publication.
- [ ] Push mode updates sibling repo remote only after successful validation and parity checks.

**Exit Criteria:**
- Single workflow can update both sibling local repo state and sibling git remote safely.

## Verification

Use this section for final artifact-level verification only.
Do not copy every task-local proof here.

- `python scripts/hooks/run_validator.py --fast`
- `pytest tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py -q`
- `powershell -ExecutionPolicy Bypass -File scripts/sync_local_starter_kit_repo.ps1 -NoPush`
- `powershell -ExecutionPolicy Bypass -File scripts/sync_local_starter_kit_repo.ps1 -Push`
- `git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit" status --short`
- `git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit" log -n 1 --oneline`

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
