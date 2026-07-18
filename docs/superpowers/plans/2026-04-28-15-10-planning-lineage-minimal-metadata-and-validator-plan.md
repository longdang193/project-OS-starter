---
layer: change
artifact_type: plan
status: completed
parent_thread: starter-adoption-experience.prompt-template-metadata-and-validation
parent_spec: docs/superpowers/specs/2026-04-28-planning-lineage-minimal-metadata-and-validator-spec.md
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - docs/intent/workstreams/threads/
  - docs/superpowers/specs/
  - docs/superpowers/plans/
  - docs/generated/planning_lineage.yaml
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/prompt_templates/spec-prompt.md
  - docs/operating_system/prompt_templates/plan-prompt.md
  - scripts/planning_lineage_support.py
  - scripts/generate_planning_lineage.py
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Planning Lineage Minimal Metadata And Validator Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-28-planning-lineage-minimal-metadata-and-validator-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Move the planning lineage model to nearest-parent metadata, add validator-backed lineage control, and generate a derived planning-lineage roll-up without re-entering upstream truth manually.

**Architecture:** Introduce a small shared planning-lineage support module plus a generator script that builds `docs/generated/planning_lineage.yaml` from the roadmap/workstream/thread/spec/plan graph. Update thread docs and prompt guidance to stop repeating redundant parents. Then upgrade `validate_adoption_shape.py` to enforce nearest-parent lineage rules and generated-lineage freshness, with focused regression tests.

**Key Invariants:**
- upstream planning truth remains canonical and human-authored
- downstream artifacts store only the nearest necessary lineage parent
- thread/workstream ancestry is derived from file placement plus referenced parents
- generated planning lineage is derived output, not a second manual truth layer
- validator enforcement should block both missing lineage and redundant lineage on the migrated surfaces

---

## Task 1: Define The New Lineage Surfaces

- [x] Step 1: Add a shared planning-lineage support module that can read workstreams, threads, specs, and plans and assemble a stable lineage graph.
- [x] Step 2: Add a generator script for `docs/generated/planning_lineage.yaml`.
- [x] Step 3: Generate and save the repo’s current planning-lineage view.

## Task 2: Migrate Lightweight Metadata And Guidance

- [x] Step 1: Remove redundant `parent_workstream` from thread-file guidance and existing thread files.
- [x] Step 2: Update workstream/thread/governance docs to describe nearest-parent lineage and the generated planning-lineage view.
- [x] Step 3: Update the spec/plan prompt guidance so specs and plans are authored from a chosen thread and plans also name the parent spec.

## Task 3: Enforce The Lineage Contract In Validation

- [x] Step 1: Extend `validate_adoption_shape.py` to validate thread metadata and path conventions against the workstream registry.
- [x] Step 2: Extend superpowers spec/plan validation to require `parent_thread` for `layer: change` artifacts and `parent_spec` for change plans, while keeping `parent_workstream: none` for true intent/operating_system artifacts in this phase.
- [x] Step 3: Reject redundant `parent_workstream` on thread files and on change-layer specs/plans after the new nearest-parent fields are present.
- [x] Step 4: Validate that `docs/generated/planning_lineage.yaml` exists when the planning-thread surface is in use and matches the derived graph.

## Task 4: Add Regression Coverage And Close The Loop

- [x] Step 1: Add tests for valid and invalid thread metadata/path conventions.
- [x] Step 2: Add tests for valid and invalid `parent_thread` / `parent_spec` relationships.
- [x] Step 3: Add a test covering generated planning-lineage freshness validation.
- [x] Step 4: Mark the spec and plan completed.
- [x] Step 5: Run `python -m pytest tests/test_validate_adoption_shape.py -q`.
- [x] Step 6: Run `python scripts/generate_planning_lineage.py`.
- [x] Step 7: Run `python scripts/validate_adoption_shape.py`.
- [x] Step 8: Run `git diff --check`.
