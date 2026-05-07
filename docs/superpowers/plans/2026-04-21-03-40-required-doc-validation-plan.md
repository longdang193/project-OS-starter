---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/setup.md
  - docs/configuration.md
  - docs/usage.md
  - docs/pipeline.md
  - docs/architecture.md
  - docs/adoption_guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Required Doc Validation Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-21-required-doc-validation-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add lightweight validation for the five required root project docs so they are checked for basic structure, semantic coverage, and placeholder-only content instead of path presence alone.

**Architecture:** This work extends the existing adoption-shape validator. `scripts/validate_adoption_shape.py` remains the primary enforcement layer for required-doc presence and new structure/content checks, while `tools/docs/generate_architecture_metadata.py` continues to own optional frontmatter validation when markdown docs choose to use frontmatter.

**Key Invariants:**
- Required root docs stay human-authored and frontmatter remains optional by default.
- Validation should catch obvious stubs without becoming a style-grading system.
- Semantic checks should stay transparent and easy to understand.
- The normal sync/check path remains the canonical enforcement surface.

**Rollout / Revert:**  
- rollback_trigger: lightweight semantic checks produce noisy false failures for short but real docs  
- rollback_method: remove or relax the required-doc semantic heuristics while preserving path-presence checks and existing frontmatter validation

---

## Task 1: Create The Plan

**Files:**
- Create: `docs/superpowers/plans/2026-04-21-03-40-required-doc-validation-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Keep the implementation intentionally light: H1, substantive content, placeholder rejection, and per-doc semantic keyword coverage.

## Task 2: Add Tests And Validator Logic

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Add failing tests for heading-only required docs.
- [x] Step 2: Add failing tests for placeholder-only required docs.
- [x] Step 3: Add failing tests for required docs that lack semantic subject coverage.
- [x] Step 4: Implement the smallest validator block that enforces H1, substantive content, placeholder rejection, and semantic coverage.
- [x] Step 5: Keep error messages file-specific and readable.

## Task 3: Update Guidance Docs

**Files:**
- Modify: `docs/adoption_guide.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/repo-governance.md`

- [x] Step 1: Document that required root docs are validated for more than path presence.
- [x] Step 2: Clarify that frontmatter remains optional for required root docs unless they participate in architecture linkage.
- [x] Step 3: Tell adopters to replace starter stubs with real project guidance before the first project commit.

## Task 4: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-03-40-required-doc-validation-plan.md`

- [x] Step 1: Run focused validator tests.
- [x] Step 2: Run `python scripts/sync_architecture_docs.py --check`.
- [x] Step 3: Run `git diff --check`.
- [x] Step 4: Review diffs for consistency across validator, tests, and governance docs.
- [x] Step 5: Mark the plan complete.
