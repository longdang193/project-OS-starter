---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/superpowers/specs/2026-04-25-managed-metadata-update-prompt-spec.md
related_features: []
related_stages: []
---

# Managed Metadata Update Prompt Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-25-managed-metadata-update-prompt-spec.md`
**Type:** add
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a dedicated prompt template for updating already-managed architecture metadata surfaces and wire it into the prompt pack and operating-system guidance.

**Architecture:** Create `managed-metadata-update-prompt.md` as a short prompt focused on already-managed repos. Then update the prompt-pack README and the nearby planning/governance docs so users can distinguish among migration, validation/drift discovery, and managed-mode update/fix work.

**Key Invariants:**
- the new prompt stays distinct from Mode A migration
- the prompt reinforces source-first edits and generated refresh later
- the prompt does not imply that generated files are hand-edited sources
- the wording stays short and copyable

**Rollout / Revert:**
- rollback_trigger: the new prompt overlaps too heavily with migration or drift prompts
- rollback_method: remove the new prompt and retain only any clarifying wording that still reduces ambiguity

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a dedicated managed-metadata update prompt and wire it into the prompt-pack guidance.
Reasoning: This is repo-method guidance work, not product work.
Invariants:
  - managed update/fix stays distinct from migration
  - source-first then generated refresh remains explicit
  - the prompt pack remains concise
Dependencies:
  - `docs/operating_system/prompt_templates/`
  - `docs/operating_system/planning/planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
Affected stages:
  - none
Affected features:
  - none
Primary lens: cross-cutting
Affected docs:
  feature_source: none
  feature_yaml: none
  feature_lineage: none
  feature_history: none
  stage_source: none
  stage_contract: none
  feature_docs:
    - none
  cross_cutting_docs:
    - none
  operating_system_docs:
    - `docs/operating_system/prompt_templates/`
    - `docs/operating_system/planning/planning-dispatch.md`
    - `docs/operating_system/governance/repo-governance.md`
    - `docs/operating_system/skill-doc-system-lifecycle.md`
  readme: none
  generated:
    - none
Generated refresh required: no
Capability IDs:
  - none
Invariant IDs:
  - none
Spec needed: yes
Plan needed: yes

## Files To Create

```text
docs/operating_system/prompt_templates/managed-metadata-update-prompt.md
```

## Files To Modify

```text
docs/operating_system/prompt_templates/README.md
docs/operating_system/prompt_templates/validate-or-drift-prompt.md
docs/operating_system/prompt_templates/mode-migration-prompt.md
docs/operating_system/planning/planning-dispatch.md
docs/operating_system/governance/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/superpowers/specs/2026-04-25-managed-metadata-update-prompt-spec.md
docs/superpowers/plans/2026-04-25-02-15-managed-metadata-update-prompt-plan.md
```

## Task 1: Add The Managed Update Prompt

**Files:**
- Create: `docs/operating_system/prompt_templates/managed-metadata-update-prompt.md`

- [x] Step 1: Add a short prompt for already-managed repos.
- [x] Step 2: Make source-first updates and generated refresh explicit.
- [x] Step 3: Make the expected output include updated sources, refreshed generated files, and validator/sync results.

## Task 2: Rewire Prompt Pack Guidance

**Files:**
- Modify: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/operating_system/prompt_templates/validate-or-drift-prompt.md`
- Modify: `docs/operating_system/prompt_templates/mode-migration-prompt.md`

- [x] Step 1: Add the new prompt to the prompt-pack README with a clear “already managed” use case.
- [x] Step 2: Clarify `validate-or-drift` as a discovery prompt, not the update/fix prompt.
- [x] Step 3: Clarify `mode-migration` as the entrypoint for Mode A to managed migration, not in-place managed updates.

## Task 3: Update Operating-System Docs

**Files:**
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`

- [x] Step 1: Mention the new managed-update prompt as the right entrypoint for already-managed metadata repairs or refresh work.
- [x] Step 2: Keep the distinction among migration, drift discovery, and managed update/fix explicit.

## Task 4: Close The Artifact Loop And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-25-managed-metadata-update-prompt-spec.md`
- Modify: `docs/superpowers/plans/2026-04-25-02-15-managed-metadata-update-prompt-plan.md`

- [x] Step 1: Mark the spec and plan completed after implementation.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
