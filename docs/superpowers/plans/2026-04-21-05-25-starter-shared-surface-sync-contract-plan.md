---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - repo_config/adoption-mode.yaml
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/operating_system/adoption/mode-b-example-migration.md
  - docs/adoption_guide.md
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Starter Shared-Surface Sync Contract Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-21-starter-shared-surface-sync-contract-spec.md`  
**Type:** change  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Make Mode B shared-surface sync stronger than guidance by recording starter shared-surface review in `repo_config/adoption-mode.yaml` and validating the record shape.

**Architecture:** This work extends the adoption-mode contract instead of adding a second repo config file. The simpler path is to keep the shared-surface sync record beside `adoption_mode`, so Mode B intent and Mode B starter-review state live in one machine-checkable source. Validation will enforce presence and structure of the record for managed mode without requiring byte-for-byte equality to the starter.

**Key Invariants:**
- Mode B projects must record which starter baseline they reviewed.
- Mode B projects may keep intentional local divergences, but those divergences should be reviewable.
- The first validator pass checks record presence and schema, not file equality.
- Mode A and Mode C should not be forced into the same sync-record strictness.

**Rollout / Revert:**  
- rollback_trigger: the sync-record schema proves too heavy for ordinary Mode B adoption work  
- rollback_method: relax the validator back to doc-only guidance while preserving the Mode B diff-review instructions

---

## Task 1: Record The Plan

**Files:**
- Create: `docs/superpowers/plans/2026-04-21-05-25-starter-shared-surface-sync-contract-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Choose the simpler path by storing the sync record in `repo_config/adoption-mode.yaml`.

## Task 2: Update Docs And Examples

**Files:**
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/adoption/mode-b-example-migration.md`
- Modify: `docs/adoption_guide.md`

- [x] Step 1: Describe the required Mode B shared-surface sync record.
- [x] Step 2: Show the chosen `starter_sync` shape in Mode B guidance and examples.
- [x] Step 3: Clarify that intentional divergences are allowed but should be recorded.

## Task 3: Enforce The Contract

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Validate `starter_sync` presence and shape for `managed_architecture_metadata`.
- [x] Step 2: Require baseline ref, review timestamp, and reviewed surface classes.
- [x] Step 3: Validate divergence entries when present.
- [x] Step 4: Update tests so managed-mode fixtures include the sync record and add failure coverage for missing/malformed records.

## Task 4: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-05-25-starter-shared-surface-sync-contract-plan.md`

- [x] Step 1: Run `python -m pytest tests/test_validate_adoption_shape.py -q`.
- [x] Step 2: Run `python scripts/sync_architecture_docs.py --check`.
- [x] Step 3: Run `git diff --check`.
- [x] Step 4: Mark the plan complete.
