---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/public-safe-doc-rewrite-guide.md
  - docs/operating_system/procedures/publication-workflow.md
related_features: []
related_stages: []
---

# Public-Safe Doc Rewrite Guide Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-21-public-safe-doc-rewrite-guide-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a dedicated guide that teaches how to rewrite private starter-oriented docs into public-safe, product-facing docs, and link it from the publication workflow.

**Architecture:** This work extends publication-boundary governance. It adds a new operating-system guide for public-safe document rewriting and updates the publication workflow to point maintainers at the concrete rewrite guide instead of only stating the boundary in abstract terms.

**Key Invariants:**
- Starter adoption/bootstrap docs remain private-only by default.
- Public-facing setup, usage, configuration, pipeline, and architecture docs may still be published when intentionally rewritten.
- The first implementation stays guide-only; it does not add a publication linter yet.

**Rollout / Revert:**  
- rollback_trigger: the guide becomes too prescriptive or starts treating all cross-cutting docs as private  
- rollback_method: remove or simplify the guide while preserving the existing publication-boundary rules

---

## Task 1: Record The Plan

**Files:**
- Create: `docs/superpowers/plans/2026-04-21-04-30-public-safe-doc-rewrite-guide-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Keep the first implementation doc-only and defer any publication linting.

## Task 2: Add The Rewrite Guide

**Files:**
- Create: `docs/operating_system/public-safe-doc-rewrite-guide.md`

- [x] Step 1: Explain the core rewrite principle for public-safe docs.
- [x] Step 2: Add dedicated rewrite guidance for `README.md`, `docs/setup.md`, `docs/configuration.md`, `docs/usage.md`, `docs/pipeline.md`, and `docs/architecture.md`.
- [x] Step 3: Include a concise rewrite checklist and red-flag content list.
- [x] Step 4: Keep the guide aligned with the existing private/public boundary rules.

## Task 3: Update Publication Workflow Docs

**Files:**
- Modify: `docs/operating_system/procedures/publication-workflow.md`

- [x] Step 1: Link the new guide from the publication workflow.
- [x] Step 2: Make the workflow move cleanly from policy to execution guidance.

## Task 4: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-04-30-public-safe-doc-rewrite-guide-plan.md`

- [x] Step 1: Run `git diff --check`.
- [x] Step 2: Review the new guide and publication workflow link for consistency.
- [x] Step 3: Mark the plan complete.
