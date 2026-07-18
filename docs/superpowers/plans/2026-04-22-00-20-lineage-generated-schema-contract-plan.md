---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - tools/docs/generate_architecture_metadata.py
  - scripts/validate_adoption_shape.py
  - tests/test_architecture_metadata_generation.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Lineage Generated Schema Contract Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-22-lineage-generated-schema-contract-spec.md`
**Type:** change
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Make the `lineage.generated.yaml` schema explicit and validator-enforced so managed repos cannot carry legacy summary-style lineage artifacts while claiming starter alignment.

**Architecture:** This work sharpens the source/generated contract around feature-local lineage. `feature.source.yaml` remains the human-owned semantic source, `<feature_id>.yaml` remains the generated current-state feature contract, and `lineage.generated.yaml` becomes an explicitly canonical evidence-oriented generated artifact. Validation should reject older summary-style lineage shapes that look plausible but encode a different artifact contract.

**Key Invariants:**
- `lineage.generated.yaml` is generated, never human-owned.
- Managed repos should use one canonical lineage schema.
- The canonical lineage file is evidence-oriented and capability-keyed.
- Legacy top-level summary keys in `lineage.generated.yaml` are invalid in managed mode.

**Rollout / Revert:**
- rollback_trigger: validator enforcement proves too brittle for repos already carrying canonical lineage files
- rollback_method: keep the doc clarifications, relax the validator to warnings temporarily, and refine the shape checks before re-enabling hard failures

---

## Task 1: Record The Plan

**Files:**
- Create: `docs/superpowers/plans/2026-04-22-00-20-lineage-generated-schema-contract-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Keep the first validator pass shape-based rather than trying to fully validate every nested evidence detail.

## Task 2: Update Docs

**Files:**
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`

- [x] Step 1: Describe `lineage.generated.yaml` as the canonical generated feature-local lineage evidence artifact.
- [x] Step 2: Clarify that older summary-style lineage shapes are invalid in managed mode.
- [x] Step 3: Tie migration guidance to the canonical generator and validator path.

## Task 3: Enforce The Schema

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `tools/docs/generate_architecture_metadata.py`

- [x] Step 1: Add shape validation for managed `lineage.generated.yaml` files.
- [x] Step 2: Reject legacy top-level keys and list-shaped `capabilities`.
- [x] Step 3: Require the generated header and canonical top-level keys.
- [x] Step 4: Clarify generator ownership comments for the canonical lineage schema.

## Task 4: Add Regression Coverage

**Files:**
- Modify: `tests/test_architecture_metadata_generation.py`
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Assert the current generator writes the canonical lineage shape and header.
- [x] Step 2: Add validator failures for missing lineage header, missing top-level keys, legacy top-level keys, and list-shaped capabilities.

## Task 5: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-22-00-20-lineage-generated-schema-contract-plan.md`

- [x] Step 1: Run `python -m pytest tests/test_architecture_metadata_generation.py tests/test_validate_adoption_shape.py -q`.
- [x] Step 2: Run `python scripts/sync_architecture_docs.py --check`.
- [x] Step 3: Run `git diff --check`.
- [x] Step 4: Mark the plan complete.
