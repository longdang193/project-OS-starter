---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/prompt_templates/
  - docs/superpowers/specs/
  - docs/superpowers/plans/
  - docs/superpowers/specs/2026-04-25-master-roadmap-alignment-guidance-spec.md
related_features: []
related_stages: []
---

# Master Roadmap Alignment Guidance Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-25-master-roadmap-alignment-guidance-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Make “follow the master roadmap” explicit in planning docs and prompt templates so downstream artifacts clearly align to a roadmap thread or explicitly justify `parent_workstream: none`.


**Key Invariants:**
- `docs/intent/master-workstream-roadmap.md` remains the top-down bridge from intent into durable workstreams.
- `operating_system` remains a parallel branch, not a fake workstream.
- `parent_workstream: none` remains valid for true operating-system work.
- This pass strengthens guidance only; no validator enforcement is added.

**Rollout / Revert:**
- rollback_trigger: the wording becomes repetitive or forces artificial roadmap mapping onto clearly operating-system work.
- rollback_method: trim the guidance and restore the looser wording while keeping the spec for a later, better-calibrated pass.

---

## Triage

Layer: operating_system
Feature type: MODIFY
Summary: Strengthen planning and prompt guidance so downstream work explicitly names the roadmap thread it follows or explains why it is operating-system work.
Reasoning: This is repo-method guidance in the operating-system layer.
Invariants:
  - roadmap alignment should be explicit
  - downstream artifacts should not treat `parent_workstream` as filler
  - guidance should remain practical, not bureaucratic
Dependencies:
  - `docs/intent/master-workstream-roadmap.md`
  - `docs/operating_system/planning/planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/prompt_templates/`
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
    - `docs/operating_system/planning/planning-dispatch.md`
    - `docs/operating_system/governance/repo-governance.md`
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

## Files To Modify

```text
docs/operating_system/planning/planning-dispatch.md
docs/operating_system/governance/repo-governance.md
docs/operating_system/prompt_templates/spec-prompt.md
docs/operating_system/prompt_templates/plan-prompt.md
docs/operating_system/prompt_templates/execute-prompt.md
docs/operating_system/prompt_templates/mode-migration-prompt.md
docs/operating_system/prompt_templates/README.md
docs/superpowers/specs/2026-04-25-master-roadmap-alignment-guidance-spec.md
```

## Task 1: Tighten Planning Guidance

**Files:**
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/operating_system/governance/repo-governance.md`

- [x] Step 1: Add explicit guidance that product-direction work should name the roadmap thread it follows.
- [x] Step 2: Add explicit guidance that `parent_workstream: none` should be intentional for operating-system work.
- [x] Step 3: Keep the wording practical and avoid implying validator enforcement.

## Task 2: Tighten Prompt Templates

**Files:**
- Modify: `docs/operating_system/prompt_templates/spec-prompt.md`
- Modify: `docs/operating_system/prompt_templates/plan-prompt.md`
- Modify: `docs/operating_system/prompt_templates/execute-prompt.md`
- Modify: `docs/operating_system/prompt_templates/mode-migration-prompt.md`
- Modify: `docs/operating_system/prompt_templates/README.md`

- [x] Step 1: Ask the user/agent to name the roadmap thread the work follows when one exists.
- [x] Step 2: Ask for an explicit operating-system justification when the work should use `parent_workstream: none`.
- [x] Step 3: Keep the prompts short and copyable.

## Task 3: Complete The Spec And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-25-master-roadmap-alignment-guidance-spec.md`
- Verify only

- [x] Step 1: Mark the spec completed after implementation.
- [x] Step 2: Run `git diff --check`.
- [x] Step 3: Review the changed docs/prompts for clarity and repetition.
