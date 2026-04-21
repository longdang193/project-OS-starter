---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - README.md
  - docs/adoption_guide.md
  - docs/intent/README.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Required Project Folder Surface Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-21-required-project-folder-surface-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `executing-plans` or `subagent-driven-development` to implement task-by-task.

**Goal:** Enforce a lean required project folder surface, add `docs/intent/` validation, and document the minimum file expectations for required folders.

**Architecture:** This work extends repo-shape governance. It keeps the existing required root docs under `docs/`, adds required-folder validation in `scripts/validate_adoption_shape.py`, and updates the governance/adoption docs so required folders are paired with clear file expectations rather than existing as empty structural tokens.

**Key Invariants:**
- `docs/intent/` remains the source of project purpose and must not be collapsed into `README.md`.
- Required folder enforcement should remain lean and stable, not force conditional architecture folders into every repo.
- If a folder is required, the repo docs should describe the minimum files or file types expected inside it.
- The normal sync/check path remains the canonical enforcement surface.

**Rollout / Revert:**  
- rollback_trigger: required-folder validation creates noisy failures for the starter or for legitimate minimal repos  
- rollback_method: remove the new required-folder validator block and tests, keep the documentation-only guidance, and preserve the root-doc checks

---

## Task 1: Create The Plan And Choose The Lean Intent Rule

**Files:**
- Create: `docs/superpowers/plans/2026-04-21-03-05-required-project-folder-surface-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Choose the initial intent-file rule as "folder exists and contains at least one markdown file" instead of a hard-coded anchor filename.

## Task 2: Add Validator Coverage And Tests

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Add failing tests for missing required folders.
- [x] Step 2: Add a failing test for `docs/intent/` existing without any markdown files.
- [x] Step 3: Implement the smallest validator rule that enforces the required folder surface.
- [x] Step 4: Implement the intent-layer content rule.
- [x] Step 5: Keep validator messages explicit about the missing folder or missing markdown file.

## Task 3: Update Governance And Adoption Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/adoption_guide.md`
- Modify: `docs/intent/README.md`
- Modify: `docs/operating_system/doc-system-lifecycle.md`
- Modify: `docs/operating_system/repo-governance.md`

- [x] Step 1: Add the required folder surface to the bootstrap/adoption guidance.
- [x] Step 2: Document the minimum expected file(s) or file types inside each required folder.
- [x] Step 3: Clarify which folders remain conditional rather than globally required.
- [x] Step 4: Confirm the docs remain aligned with the current source-of-truth model.

## Task 4: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-03-05-required-project-folder-surface-plan.md`

- [x] Step 1: Run focused validator tests.
- [x] Step 2: Run `python scripts/sync_architecture_docs.py --check`.
- [x] Step 3: Run `git diff --check`.
- [x] Step 4: Review diffs for consistency across validator, tests, and governance docs.
- [x] Step 5: Mark the plan complete.
