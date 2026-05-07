---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/README.md
  - docs/operating_system/prompt_templates/thread-set-to-spec-set-prompt.md
  - docs/operating_system/prompt_templates/spec-set-execution-map-prompt.md
  - docs/operating_system/prompt_templates/spec-prompt.md
  - docs/operating_system/prompt_templates/plan-prompt.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/execution_maps/README.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-planning-dispatch/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-doc-system-lifecycle/SKILL.md
  - docs/superpowers/specs/2026-04-28-spec-authoring-map-and-implementation-execution-map-spec.md
related_features: []
related_stages: []
---

# Spec-Authoring Map And Implementation Execution Map Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-28-spec-authoring-map-and-implementation-execution-map-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Refine the planning ladder so the repo teaches two orchestration phases: spec-authoring orchestration before detailed specs, and implementation execution orchestration after approved detailed specs.

**Architecture:** Keep one `docs/superpowers/execution_maps/` folder, but differentiate the two orchestration phases through prompt names, README wording, planning/governance docs, and skill guidance. Add one new prompt for the spec-authoring-map step, narrow the current spec-set execution-map prompt to the implementation phase, and update all affected ladders so they no longer compress both phases into one generic execution-map concept.

**Key Invariants:**
- complete spec set remains separate from detailed specs
- spec-authoring maps remain orchestration artifacts, not specs
- implementation execution maps remain orchestration artifacts, not plans
- prompts, repo-control docs, and skills should all teach the same refined ladder

---

## Task 1: Write The Plan

- [x] Step 1: Review the spec and the currently published prompt ladder.
- [x] Step 2: Save this implementation plan under `docs/superpowers/plans/`.

## Task 2: Update The Prompt Surface

- [x] Step 1: Tighten `thread-set-to-spec-set-prompt.md` so it stops at complete spec coverage.
- [x] Step 2: Add a dedicated spec-authoring-map prompt.
- [x] Step 3: Rewrite `spec-set-execution-map-prompt.md` so it clearly means implementation execution after approved detailed specs.
- [x] Step 4: Update `spec-prompt.md`, `plan-prompt.md`, and the prompt-pack README to teach the refined ladder.

## Task 3: Update Repo-Control Docs And Skills

- [x] Step 1: Update `skill-planning-dispatch.md`, `repo-governance.md`, and `docs/superpowers/execution_maps/README.md`.
- [x] Step 2: Update the four planning-related skills so they distinguish spec-authoring orchestration from implementation orchestration.

## Task 4: Close The Loop

- [x] Step 1: Mark the spec and plan completed.
- [x] Step 2: Run `python scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
