---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - scripts/validate_adoption_shape.py
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/prompt_templates/
  - tests/test_validate_adoption_shape.py
  - docs/superpowers/specs/2026-04-25-workstream-registry-surface-spec.md
related_features: []
related_stages: []
---

# Workstream Registry Surface Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-25-workstream-registry-surface-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a real workstream registry under `docs/intent/workstreams/` and upgrade `parent_workstream` validation so named values resolve to a real registry entry.

**Architecture:** Create a small workstream registry surface under `docs/intent/workstreams/` with a README and at least one concrete workstream doc. Update the master roadmap and planning guidance to point to the registry. Then extend `validate_adoption_shape.py` so named `parent_workstream` values in superpowers specs/plans must match a registered workstream id, while `parent_workstream: none` remains valid for intent and operating-system artifacts.

**Key Invariants:**
- `master-workstream-roadmap.md` stays the overview, not the full registry.
- `docs/intent/workstreams/` becomes the canonical registry for named workstreams.
- `parent_workstream: none` remains valid for intent and operating-system artifacts.
- Named workstream validation must be source-backed by registry docs, not a hardcoded list.

**Rollout / Revert:**  
- rollback_trigger: the registry shape is too heavy, or validator enforcement breaks valid current artifacts.  
- rollback_method: keep the registry docs, revert named-id enforcement, and retry with a looser compatibility rule.

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a workstream registry surface and upgrade parent_workstream validation to resolve named workstreams against that registry.
Reasoning: This is repo-method governance and validation work.
Invariants:
  - roadmap overview stays separate from registry detail
  - registry docs stay small and source-like
  - validator only enforces what the registry actually declares
Dependencies:
  - `docs/intent/master-workstream-roadmap.md`
  - `scripts/validate_adoption_shape.py`
  - `tests/test_validate_adoption_shape.py`
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
    - `docs/operating_system/skill-planning-dispatch.md`
    - `docs/operating_system/repo-governance.md`
    - `docs/operating_system/prompt_templates/`
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
docs/intent/workstreams/README.md
docs/intent/workstreams/<workstream-id>.md
```

## Files To Modify

```text
docs/intent/master-workstream-roadmap.md
docs/operating_system/skill-planning-dispatch.md
docs/operating_system/repo-governance.md
docs/operating_system/prompt_templates/README.md
docs/operating_system/prompt_templates/spec-prompt.md
docs/operating_system/prompt_templates/plan-prompt.md
docs/operating_system/prompt_templates/execute-prompt.md
docs/operating_system/prompt_templates/mode-migration-prompt.md
scripts/validate_adoption_shape.py
tests/test_validate_adoption_shape.py
docs/superpowers/specs/2026-04-25-workstream-registry-surface-spec.md
```

## Task 1: Add Failing Registry-Resolution Tests

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Add a helper that seeds a minimal workstream registry entry.
- [x] Step 2: Add a test showing a named `parent_workstream` fails when the registry entry is missing.
- [x] Step 3: Add a test showing a named `parent_workstream` passes when the registry entry exists.

## Task 2: Add The Registry Surface

**Files:**
- Create: `docs/intent/workstreams/README.md`
- Create: `docs/intent/workstreams/<workstream-id>.md`
- Modify: `docs/intent/master-workstream-roadmap.md`

- [x] Step 1: Add a README that explains the folder as the canonical named-workstream registry.
- [x] Step 2: Add at least one concrete workstream doc with stable frontmatter and small body shape.
- [x] Step 3: Update the master roadmap to point to the registry as the place where valid named workstream ids live.

## Task 3: Upgrade Validator And Guidance

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `docs/operating_system/skill-planning-dispatch.md`
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/operating_system/prompt_templates/spec-prompt.md`
- Modify: `docs/operating_system/prompt_templates/plan-prompt.md`
- Modify: `docs/operating_system/prompt_templates/execute-prompt.md`
- Modify: `docs/operating_system/prompt_templates/mode-migration-prompt.md`

- [x] Step 1: Load registered workstream IDs from `docs/intent/workstreams/`.
- [x] Step 2: Require named `parent_workstream` values for `change`/`workstream` artifacts to resolve to a real registry doc.
- [x] Step 3: Update the docs/prompts so users know the registry is the place to discover valid workstream IDs.

## Task 4: Complete The Spec And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-25-workstream-registry-surface-spec.md`
- Verify only

- [x] Step 1: Mark the spec completed after implementation.
- [x] Step 2: Run the targeted validator tests.
- [x] Step 3: Run the full adoption-shape suite.
- [x] Step 4: Run `scripts/validate_adoption_shape.py`.
- [x] Step 5: Run `git diff --check`.
