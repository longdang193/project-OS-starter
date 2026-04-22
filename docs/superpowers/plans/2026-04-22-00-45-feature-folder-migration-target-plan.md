---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/mode-b-example-migration.md
  - docs/operating_system/doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Feature Folder Migration Target Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-22-feature-folder-migration-target-spec.md`  
**Type:** change  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `executing-plans` or `subagent-driven-development` to implement task-by-task.

**Goal:** Make the newer customer-style feature-folder shape the explicit migration target so agents know how to move older managed feature folders forward without guessing.

**Architecture:** This work stays in the guidance layer. It clarifies the target boundaries among `feature.source.yaml`, `<feature_id>.yaml`, `lineage.generated.yaml`, and `history.md`, and it names the kinds of older fields and formats that should not be copied forward during migration.

**Key Invariants:**
- `feature.source.yaml` stays minimal and human-owned.
- `<feature_id>.yaml` stays the generated current-state contract.
- `lineage.generated.yaml` stays the canonical evidence-oriented generated lineage artifact.
- `history.md` should use the partial-generated history pattern when the starter history model is adopted.

**Rollout / Revert:**  
- rollback_trigger: the guidance over-prescribes repo-specific details that should stay optional  
- rollback_method: keep the target folder contract and source/generated/history split, but relax the examples if they prove too narrow

---

## Task 1: Record The Plan

**Files:**
- Create: `docs/superpowers/plans/2026-04-22-00-45-feature-folder-migration-target-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Keep the first implementation guidance-first rather than adding new validation.

## Task 2: Update The Migration Guide

**Files:**
- Modify: `docs/operating_system/project-adoption-migration-guide.md`

- [x] Step 1: Add an explicit “desired migration target” section for newer customer-style feature folders.
- [x] Step 2: Explain what should stay in `feature.source.yaml` versus generated contract, lineage, and history.
- [x] Step 3: Call out older source fields and history styles that should not be copied forward unchanged.

## Task 3: Update Supporting Docs And Example

**Files:**
- Modify: `docs/operating_system/mode-b-example-migration.md`
- Modify: `docs/operating_system/doc-system-lifecycle.md`

- [x] Step 1: Update the Mode B example to prefer the newer source capability shape and partial-generated history target.
- [x] Step 2: Tighten lifecycle guidance so the source/generated/history boundary is clearer during migration.

## Task 4: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-22-00-45-feature-folder-migration-target-plan.md`

- [x] Step 1: Run `git diff --check`.
- [x] Step 2: Spot-read the migration guide, example, and lifecycle doc for consistent target-shape guidance.
- [x] Step 3: Mark the plan complete.
