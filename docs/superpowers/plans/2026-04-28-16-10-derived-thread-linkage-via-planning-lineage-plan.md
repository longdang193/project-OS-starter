---
layer: change
artifact_type: plan
status: completed
parent_thread: starter-adoption-experience.adoption-prompt-discoverability-without-duplication
parent_spec: docs/superpowers/specs/2026-04-28-derived-thread-linkage-via-planning-lineage-spec.md
targets:
  - docs/intent/workstreams/
  - docs/intent/workstreams/threads/
  - docs/generated/planning_lineage.yaml
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/prompt_templates/
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Derived Thread Linkage Via Planning Lineage Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-28-derived-thread-linkage-via-planning-lineage-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Keep thread files source-only by pointing users to the generated planning-lineage view for derived spec/plan linkage and enforcing that boundary in validation.

**Architecture:** Update thread-layer guidance so it no longer suggests storing linked spec/plan fields in thread files, then extend `validate_adoption_shape.py` and tests to reject `linked_spec` and `linked_plan` on thread files. Keep `docs/generated/planning_lineage.yaml` as the assembled inspection surface for downstream artifact linkage.

**Key Invariants:**
- thread files stay canonical for thread meaning only
- spec/plan linkage remains derived through `parent_thread` and `parent_spec`
- generated planning lineage remains the assembled inspection surface
- validator should block manual re-entry of derived thread linkage

---

## Task 1: Update Guidance Surfaces

- [x] Step 1: Update `docs/intent/workstreams/threads/README.md` to remove suggested `linked spec` / `linked plan` fields.
- [x] Step 2: Update surrounding planning/governance docs so they point readers to `docs/generated/planning_lineage.yaml` for assembled thread/spec/plan linkage.

## Task 2: Enforce The Source/Derived Boundary

- [x] Step 1: Extend thread validation in `scripts/validate_adoption_shape.py` to reject `linked_spec` and `linked_plan` on thread files.
- [x] Step 2: Add regression tests covering thread files that improperly define `linked_spec` or `linked_plan`.

## Task 3: Close The Loop And Verify

- [x] Step 1: Mark the spec and plan completed.
- [x] Step 2: Run `python -m pytest tests/test_validate_adoption_shape.py -q`.
- [x] Step 3: Run `python scripts/generate_planning_lineage.py`.
- [x] Step 4: Run `python scripts/validate_adoption_shape.py`.
- [x] Step 5: Run `git diff --check`.
