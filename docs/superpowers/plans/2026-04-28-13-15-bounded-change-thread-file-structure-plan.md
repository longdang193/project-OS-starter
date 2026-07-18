---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/intent/workstreams/
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/README.md
  - docs/operating_system/prompt_templates/
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/superpowers/specs/2026-04-28-bounded-change-thread-file-structure-spec.md
related_features: []
related_stages: []
---

# Bounded Change Thread File Structure Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-28-bounded-change-thread-file-structure-spec.md`
**Type:** add
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Make bounded change threads explicit in the worktree, then update the planning prompts and guidance so users move through the thread layer naturally instead of skipping from workstream to spec.

**Architecture:** Add a lightweight `threads/` subtree beneath the workstream registry with a small README and one real example thread folder. Then update the workstream guidance, planning docs, and relevant prompts so thread files become the visible bridge between registered workstreams and downstream specs/plans.

**Key Invariants:**
- the master roadmap stays strategic rather than becoming a thread tracker
- registered workstreams remain the durable ownership layer
- thread files stay lightweight and execution-oriented
- specs and plans remain downstream bounded artifacts
- this first pass does not require an `operating_system` thread branch yet

---

## Task 1: Add The Explicit Thread Surface

- [x] Step 1: Add `docs/intent/workstreams/threads/README.md` with the folder purpose, naming rules, and lightweight thread file shape.
- [x] Step 2: Add a concrete thread folder under `docs/intent/workstreams/threads/starter-adoption-experience/`.
- [x] Step 3: Seed at least one real thread file that shows the intended schema and linkage pattern.

## Task 2: Update Workstream-Layer Guidance

- [x] Step 1: Update `docs/intent/workstreams/README.md` so it distinguishes workstream docs from thread files clearly.
- [x] Step 2: Update `docs/intent/workstreams/starter-adoption-experience.md` to point to explicit thread files instead of treating open threads as free-form bullets only.
- [x] Step 3: Update `docs/intent/workstream-coverage-and-progress-guide.md`, `docs/intent/master-workstream-roadmap.md`, and `docs/intent/README.md` so the ladder explicitly includes thread files.

## Task 3: Adjust Prompt And Governance Routing

- [x] Step 1: Update `bounded-change-thread-build-prompt.md` so its output maps directly to thread files.
- [x] Step 2: Update `workstream-to-spec-prompt.md` so it assumes a chosen thread or redirects to the thread-build step first.
- [x] Step 3: Update `parallel-bounded-change-planning-prompt.md`, the prompt-pack README, and planning/governance docs so thread files become the visible execution unit.

## Task 4: Close The Artifact Loop And Verify

- [x] Step 1: Mark the spec and plan completed.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
