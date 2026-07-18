---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/superpowers/execution_maps/
  - docs/operating_system/prompt_templates/
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/specs/2026-04-28-execution-maps-artifact-class-spec.md
related_features: []
related_stages: []
---

# Execution Maps Artifact Class Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-28-execution-maps-artifact-class-spec.md`
**Type:** add
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add `docs/superpowers/execution_maps/` as a distinct orchestration artifact class and wire the missing prompt ladder from thread set to spec set to execution map.

**Architecture:** Create the new execution-maps folder with a README and one small template example. Add the two missing prompts for thread-set spec coverage and spec-set orchestration. Then update prompt-pack and planning/governance docs so execution maps sit cleanly between spec sets and bounded implementation plans.

**Key Invariants:**
- execution maps remain orchestration artifacts, not specs
- execution maps remain orchestration artifacts, not implementation plans
- execution maps do not duplicate structural lineage already present in `docs/generated/planning_lineage.yaml`
- the prompt ladder stays split between spec-set construction and execution orchestration

---

## Task 1: Add The Execution Maps Surface

- [x] Step 1: Add `docs/superpowers/execution_maps/README.md` with purpose, boundary, metadata, and body-shape guidance.
- [x] Step 2: Add one example/template execution-map artifact that shows the intended shape.

## Task 2: Add The Missing Prompt Pair

- [x] Step 1: Add `thread-set-to-spec-set-prompt.md`.
- [x] Step 2: Add `spec-set-execution-map-prompt.md`.
- [x] Step 3: Update the prompt-pack README so the ladder includes spec-set coverage and execution-map orchestration explicitly.

## Task 3: Align Planning And Governance Docs

- [x] Step 2: Update `repo-governance.md` so the artifact boundary around execution maps is explicit.

## Task 4: Close The Loop And Verify

- [x] Step 1: Mark the spec and plan completed.
- [x] Step 2: Run `python scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
