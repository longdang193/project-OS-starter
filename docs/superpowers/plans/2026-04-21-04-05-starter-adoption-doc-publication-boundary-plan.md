---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - .agents/skills/skill-private-public-repo-governance/SKILL.md
  - docs/operating_system/procedures/publication-procedure.md
  - repo_config/publication-config.json
related_features: []
related_stages: []
---

# Starter Adoption Doc Publication Boundary Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-21-starter-adoption-doc-publication-boundary-spec.md`
**Type:** add
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Clarify that starter adoption/bootstrap docs are private-only by default and harden the publication boundary so future public allowlists do not accidentally leak them.

**Architecture:** This work is publication-boundary governance. It updates the private/public governance skill, the publication workflow doc, and the repo publication config so starter adoption docs are explicitly treated as private repo onboarding material rather than product-facing public docs.

**Key Invariants:**
- The private repo remains the development source of truth.
- Product-facing setup/usage docs may still be public when intentionally curated.
- Starter adoption/bootstrap guidance remains private-only by default.
- Publication rules remain allowlist-first.

**Rollout / Revert:**
- rollback_trigger: the new rule accidentally classifies ordinary product-facing docs as private
- rollback_method: remove the explicit starter-adoption boundary entries while preserving the broader private/public governance model

---

## Task 1: Record The Plan

**Files:**
- Create: `docs/superpowers/plans/2026-04-21-04-05-starter-adoption-doc-publication-boundary-plan.md`

- [x] Step 1: Record the implementation plan from the approved spec.
- [x] Step 2: Choose the stronger defense-in-depth path by updating both docs and config.

## Task 2: Update Governance Guidance

**Files:**
- Modify: `.agents/skills/skill-private-public-repo-governance/SKILL.md`
- Modify: `docs/operating_system/procedures/publication-procedure.md`

- [x] Step 1: Add starter adoption/bootstrap docs to the private-only examples in the skill.
- [x] Step 2: Clarify that product-facing setup/usage docs may still be public when rewritten for the public mirror.
- [x] Step 3: Add the same boundary to the publication workflow doc with `docs/adoption_guide.md` as the explicit example.

## Task 3: Add Config Defense In Depth

**Files:**
- Modify: `repo_config/publication-config.json`

- [x] Step 1: Add `docs/adoption_guide.md` to the forbidden publish paths.
- [x] Step 2: Keep the config aligned with the allowlist-first model rather than broadening publication scope.

## Task 4: Verify And Close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-04-05-starter-adoption-doc-publication-boundary-plan.md`

- [x] Step 1: Run repo config validation if applicable.
- [x] Step 2: Run `git diff --check`.
- [x] Step 3: Review diffs for consistent private/public language across skill, docs, and config.
- [x] Step 4: Mark the plan complete.
