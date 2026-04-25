---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - docs/superpowers/specs/2026-04-25-roadmap-vs-execution-divergence-prompt-spec.md
related_features: []
related_stages: []
---

# Roadmap Vs Execution Divergence Prompt Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-25-roadmap-vs-execution-divergence-prompt-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `executing-plans` or `subagent-driven-development` to implement task-by-task.

**Goal:** Add a dedicated prompt template for checking divergence between upstream roadmap/workstream intent and downstream specs, plans, and execution completed so far.

**Architecture:** Create a new prompt for roadmap-vs-execution divergence review, then update the prompt-pack README and a few operating-system and roadmap docs so users can tell when they need planning-alignment review rather than generic drift or roadmap-gap review.

**Key Invariants:**
- the prompt stays distinct from generic metadata drift checks
- the prompt supports both roadmap-wide and single-workstream review
- the prompt preserves the `workstream` vs `operating_system` distinction
- the wording stays short and copyable

**Rollout / Revert:**  
- rollback_trigger: the new prompt overlaps too heavily with gap/drift prompts  
- rollback_method: remove the new prompt and keep only any wording changes that still clarify the prompt-pack map

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a roadmap-vs-execution divergence review prompt and wire it into the prompt-pack guidance.
Reasoning: This is repo-method planning guidance work.
Invariants:
  - planning-alignment review remains distinct from metadata drift review
  - roadmap and workstream docs remain upstream sources, not progress trackers
  - the prompt should support roadmap-wide and workstream-local review
Dependencies:
  - `docs/operating_system/prompt_templates/`
  - `docs/operating_system/planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/intent/master-workstream-roadmap.md`
  - `docs/intent/workstreams/`
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
    - `docs/operating_system/planning-dispatch.md`
    - `docs/operating_system/repo-governance.md`
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
docs/operating_system/prompt_templates/roadmap-vs-execution-divergence-prompt.md
```

## Files To Modify

```text
docs/operating_system/prompt_templates/README.md
docs/operating_system/prompt_templates/validate-or-drift-prompt.md
docs/operating_system/prompt_templates/roadmap-gap-prompt.md
docs/operating_system/prompt_templates/workstream-alignment-review-prompt.md
docs/operating_system/planning-dispatch.md
docs/operating_system/repo-governance.md
docs/intent/master-workstream-roadmap.md
docs/intent/workstreams/README.md
docs/superpowers/specs/2026-04-25-roadmap-vs-execution-divergence-prompt-spec.md
docs/superpowers/plans/2026-04-25-02-35-roadmap-vs-execution-divergence-prompt-plan.md
```

## Task 1: Add The Divergence Prompt

**Files:**
- Create: `docs/operating_system/prompt_templates/roadmap-vs-execution-divergence-prompt.md`

- [x] Step 1: Add a short prompt that supports roadmap-wide or single-workstream review.
- [x] Step 2: Make the comparison target explicit: roadmap/workstream intent vs specs/plans/execution so far.
- [x] Step 3: Make the expected output include divergence findings and next correction moves.

## Task 2: Clarify The Prompt Pack Map

**Files:**
- Modify: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/operating_system/prompt_templates/validate-or-drift-prompt.md`
- Modify: `docs/operating_system/prompt_templates/roadmap-gap-prompt.md`
- Modify: `docs/operating_system/prompt_templates/workstream-alignment-review-prompt.md`

- [x] Step 1: Add the new prompt to the README with a planning-alignment use case.
- [x] Step 2: Clarify `validate-or-drift` as repo/metadata drift rather than roadmap-vs-execution review.
- [x] Step 3: Clarify nearby roadmap/workstream prompts so users can choose gap review, fit review, or divergence review cleanly.

## Task 3: Update Roadmap And Governance Docs

**Files:**
- Modify: `docs/operating_system/planning-dispatch.md`
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/intent/master-workstream-roadmap.md`
- Modify: `docs/intent/workstreams/README.md`

- [x] Step 1: Mention the divergence prompt as the right entrypoint for reviewing execution against roadmap/workstream intent.
- [x] Step 2: Keep the distinction from roadmap gaps and generic drift explicit.

## Task 4: Close The Artifact Loop And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-25-roadmap-vs-execution-divergence-prompt-spec.md`
- Modify: `docs/superpowers/plans/2026-04-25-02-35-roadmap-vs-execution-divergence-prompt-plan.md`

- [x] Step 1: Mark the spec and plan completed after implementation.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
