---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/specs/2026-04-27-upstream-to-downstream-planning-prompt-ladder-spec.md
related_features: []
related_stages: []
---

# Upstream-To-Downstream Planning Prompt Ladder Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-27-upstream-to-downstream-planning-prompt-ladder-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add construction-oriented prompts that build the planning structure top-down: master roadmap, registered workstream set, and bounded change threads.

**Architecture:** Add three new build prompts to the prompt pack, then update the prompt-pack README plus planning/governance docs so users can distinguish construction prompts from routing and review prompts.

**Key Invariants:**
- prompts build planning structure from upstream to downstream
- prompts remain distinct from review/routing prompts
- master roadmap stays strategic
- bounded change threads remain the execution-capable unit

---

## Task 1: Add Construction Prompts

- [x] Step 1: Add `master-workstream-roadmap-build-prompt.md`.
- [x] Step 2: Add `registered-workstream-set-build-prompt.md`.
- [x] Step 3: Add `bounded-change-thread-build-prompt.md`.

## Task 2: Update Prompt-Pack Guidance

- [x] Step 1: Update the prompt-pack README to include the construction prompts and distinguish construction/routing/review roles.
- [x] Step 2: Update planning/governance docs to mention the top-down build path.

## Task 3: Close The Artifact Loop And Verify

- [x] Step 1: Mark the spec completed.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
