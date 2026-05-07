---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/README.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/prompt_templates/required-root-doc-update-prompt.md
  - docs/superpowers/specs/2026-04-28-required-root-doc-update-prompt-spec.md
related_features: []
related_stages: []
---

# Required Root Doc Update Prompt Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-28-required-root-doc-update-prompt-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a dedicated prompt for updating the validator-enforced required root docs and wire it into the prompt-pack and governing docs.

**Architecture:** Keep the new prompt lightweight and validator-aware. It should treat required root docs as cross-cutting summary surfaces, distinguish required from optional root docs, and point users back to the proper source layers rather than encouraging duplication. Then add small README/governance/doc-lifecycle references so the prompt becomes discoverable from the existing repo-control surfaces.

**Key Invariants:**
- required root docs remain cross-cutting summaries, not new source layers
- required and optional root docs stay clearly distinguished
- the prompt should reinforce validator-facing expectations without redesigning the validator
- the change stays scoped to the prompt pack and supporting operating-system docs

---

## Task 1: Write The Plan

- [x] Step 1: Review the required-root-doc prompt spec and current governing docs.
- [x] Step 2: Save this implementation plan under `docs/superpowers/plans/`.

## Task 2: Add The Prompt

- [x] Step 1: Create `docs/operating_system/prompt_templates/required-root-doc-update-prompt.md`.
- [x] Step 2: Make the prompt explicitly cover required vs optional root docs, source-layer boundaries, and validator follow-up.

## Task 3: Wire It Into The Repo-Control Surface

- [x] Step 1: Update `docs/operating_system/prompt_templates/README.md`.
- [x] Step 2: Update `docs/operating_system/repo-governance.md`.
- [x] Step 3: Update `docs/operating_system/skill-doc-system-lifecycle.md`.

## Task 4: Close The Loop

- [x] Step 1: Mark the spec and plan completed.
- [x] Step 2: Run `python scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
