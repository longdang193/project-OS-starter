---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-doc-system-lifecycle/SKILL.md
  - docs/superpowers/specs/2026-04-28-skill-alignment-to-planning-lineage-model-spec.md
related_features: []
related_stages: []
---

# Skill Alignment To Planning Lineage Model Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-28-skill-alignment-to-planning-lineage-model-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Align the four planning-related skills to the repo's current planning-lineage model so they stop teaching the older workstream-to-spec shortcut and old downstream metadata assumptions.


**Key Invariants:**
- skills should match the current docs and prompt ladder
- execution maps should remain orchestration artifacts, not plans
- change-layer lineage should use nearest-parent fields instead of redundant downstream ancestry
- this pass should stay limited to the four directly affected skills

---

## Task 1: Write The Alignment Plan

- [x] Step 1: Review the skill-alignment spec and the current planning/governance docs.
- [x] Step 2: Save this implementation plan under `docs/superpowers/plans/`.

## Task 2: Align The Planning Skills

- [x] Step 1: Update `.agents/skills/skill-brainstorming/SKILL.md` so its ladder includes thread files, spec sets, and execution maps where appropriate.
- [x] Step 3: Update `.agents/skills/skill-writing-plans/SKILL.md` so plan provenance and metadata mention `parent_thread`, `parent_spec`, and execution-map context.
- [x] Step 4: Update `.agents/skills/skill-doc-system-lifecycle/SKILL.md` so source-of-truth placement includes execution maps and derived planning-lineage inspection.

## Task 3: Close The Loop

- [x] Step 1: Mark the spec and plan completed.
- [x] Step 2: Run `python scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
