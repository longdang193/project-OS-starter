---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/public-safe-doc-rewrite-guide.md
  - docs/operating_system/procedures/publication-procedure.md
  - .agents/skills/skill-private-public-repo-governance/SKILL.md
related_features: []
related_stages: []
---

# Public Mirror Sanitization Contract Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-21-public-mirror-sanitization-contract-spec.md`
**Type:** change
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Revise publication guidance so the public mirror preserves reproducible structure and sanitizes private payloads instead of trimming too many files away.

**Architecture:** This work is publication-boundary governance. It updates the rewrite guide, publication workflow, and private/public governance skill so publication decisions use a three-mode model: keep as-is, keep and sanitize, or omit entirely. The guidance should preserve structural fidelity when file paths, schema keys, headings, or artifact slots help the public mirror remain credible and reproducible.

**Key Invariants:**
- The private repo remains the development source of truth.
- The public repo remains a curated downstream mirror.
- Private payloads must not leak into the public mirror.
- Public publication guidance should preserve reproducible structure whenever that structure is safe to reveal.
- Omission should be intentional, not the default response to every private reference.

**Rollout / Revert:**
- rollback_trigger: the new guidance becomes confusing enough that maintainers cannot tell when to sanitize versus omit
- rollback_method: revert to the simpler rewrite guide while preserving the private/public boundary and the existing forbidden-path safeguards

---

## Task 1: Record The Plan

**Files:**
- Create: `docs/superpowers/plans/2026-04-21-05-00-public-mirror-sanitization-contract-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Keep this first implementation in the docs/governance layer rather than adding config or validator changes.

## Task 2: Update The Rewrite Guide

**Files:**
- Modify: `docs/operating_system/public-safe-doc-rewrite-guide.md`

- [x] Step 1: Introduce the keep / sanitize / omit decision model.
- [x] Step 2: Add a reproducibility-oriented principle that preserves structure when safe.
- [x] Step 3: Add concrete sanitization patterns such as empty arrays, redacted values, and short public-safe summaries.
- [x] Step 4: Clarify file-level, section-level, and field-level sensitivity.

## Task 3: Update Publication Governance

**Files:**
- Modify: `docs/operating_system/procedures/publication-procedure.md`
- Modify: `.agents/skills/skill-private-public-repo-governance/SKILL.md`

- [x] Step 1: Update the workflow doc so publication review asks whether a file should be kept, sanitized, or omitted.
- [x] Step 2: Warn against over-trimming files whose visible structure supports reproducibility.
- [x] Step 3: Update the governance skill to teach the same three-mode classification and sanitization preference.

## Task 4: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-05-00-public-mirror-sanitization-contract-plan.md`

- [x] Step 1: Run `git diff --check`.
- [x] Step 2: Spot-read the updated guide, workflow, and skill for consistent language.
- [x] Step 3: Mark the plan complete.
