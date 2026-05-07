---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/specs/2026-04-27-roadmap-level-completion-checklist-spec.md
related_features: []
related_stages: []
---

# Roadmap-Level Completion Checklist Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-27-roadmap-level-completion-checklist-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a short strategic completeness checklist to the master roadmap without turning it into a task tracker.

**Architecture:** Add a `Roadmap-Level Completion Checklist` section to the master roadmap, then update the workstream coverage/progress guide and nearby planning/governance docs so the ownership split stays clear: roadmap checklist for completeness, workstream docs for progress, specs/plans for execution.

**Key Invariants:**
- the checklist remains strategic rather than execution-oriented
- detailed progress stays out of the roadmap
- supporting docs reinforce the split clearly

---

## Task 1: Add The Checklist

- [x] Step 1: Add a short roadmap-level completion checklist to `docs/intent/master-workstream-roadmap.md`.
- [x] Step 2: Keep the checklist focused on coverage/completeness, not progress.

## Task 2: Clarify Ownership In Supporting Docs

- [x] Step 1: Update `docs/intent/workstream-coverage-and-progress-guide.md` to point to the checklist as a strategic coverage aid.
- [x] Step 2: Update `docs/operating_system/skill-planning-dispatch.md` and `docs/operating_system/governance/repo-governance.md` so the roadmap checklist is clearly separated from progress tracking.

## Task 3: Close The Artifact Loop And Verify

- [x] Step 1: Mark the spec completed.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
