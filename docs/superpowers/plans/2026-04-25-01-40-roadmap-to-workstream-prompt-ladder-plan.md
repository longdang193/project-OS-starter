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
  - docs/superpowers/specs/2026-04-25-roadmap-to-workstream-prompt-ladder-spec.md
related_features: []
related_stages: []
---

# Roadmap-To-Workstream Prompt Ladder Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-25-roadmap-to-workstream-prompt-ladder-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `executing-plans` or `subagent-driven-development` to implement task-by-task.

**Goal:** Extend the prompt-template pack so users can move from the master roadmap into the right workstream before drafting specs, plans, and execution requests.

**Architecture:** Add four upstream prompt templates that cover roadmap-to-workstream translation, workstream-to-spec routing, workstream-fit review, and roadmap-gap discovery. Then update the prompt-pack README and the main planning/governance docs so the user-facing lifecycle reads from roadmap/workstream down into spec, plan, and execution without collapsing `operating_system` into a product workstream.

**Key Invariants:**
- Prompt templates reinforce the existing planning lifecycle instead of inventing a second workflow.
- `docs/intent/master-workstream-roadmap.md` stays the overview source, not the prompt surface.
- `docs/intent/workstreams/` stays the canonical registry for named workstreams.
- The prompt ladder must preserve the `workstream` vs `operating_system` distinction.
- Prompt files stay short, copyable, and human-usable.

**Rollout / Revert:**  
- rollback_trigger: the prompt pack becomes confusing, redundant, or overly large  
- rollback_method: keep the existing prompt files, remove the new upstream prompts, and keep only the README/doc wording improvements that still help

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add upstream prompt templates that guide users from the master roadmap into the right workstream before spec/plan execution.
Reasoning: This is repo-method guidance work for planning and lifecycle invocation.
Invariants:
  - prompt templates remain guidance rather than validator-enforced artifacts
  - named workstream references stay aligned with the registry under `docs/intent/workstreams/`
  - operating-system work must remain a valid branch instead of being forced into product workstreams
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
docs/operating_system/prompt_templates/roadmap-to-workstream-prompt.md
docs/operating_system/prompt_templates/workstream-to-spec-prompt.md
docs/operating_system/prompt_templates/workstream-alignment-review-prompt.md
docs/operating_system/prompt_templates/roadmap-gap-prompt.md
```

## Files To Modify

```text
docs/operating_system/prompt_templates/README.md
docs/operating_system/prompt_templates/spec-prompt.md
docs/operating_system/prompt_templates/plan-prompt.md
docs/operating_system/prompt_templates/execute-prompt.md
docs/operating_system/prompt_templates/mode-migration-prompt.md
docs/operating_system/planning-dispatch.md
docs/operating_system/repo-governance.md
docs/superpowers/specs/2026-04-25-roadmap-to-workstream-prompt-ladder-spec.md
```

## Task 1: Add Upstream Prompt Templates

**Files:**
- Create: `docs/operating_system/prompt_templates/roadmap-to-workstream-prompt.md`
- Create: `docs/operating_system/prompt_templates/workstream-to-spec-prompt.md`
- Create: `docs/operating_system/prompt_templates/workstream-alignment-review-prompt.md`
- Create: `docs/operating_system/prompt_templates/roadmap-gap-prompt.md`

- [x] Step 1: Add a roadmap-to-workstream prompt that helps choose between a registered workstream and `operating_system`.
- [x] Step 2: Add a workstream-to-spec prompt that anchors the next spec to a valid workstream ID.
- [x] Step 3: Add a workstream-alignment review prompt that checks whether a proposed change fits the named workstream.
- [x] Step 4: Add a roadmap-gap prompt that helps identify missing durable threads in the master roadmap.

## Task 2: Rewire The Prompt Pack

**Files:**
- Modify: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/operating_system/prompt_templates/spec-prompt.md`
- Modify: `docs/operating_system/prompt_templates/plan-prompt.md`
- Modify: `docs/operating_system/prompt_templates/execute-prompt.md`
- Modify: `docs/operating_system/prompt_templates/mode-migration-prompt.md`

- [x] Step 1: Update the README so the lifecycle starts at roadmap/workstream choice before spec/plan/execution.
- [x] Step 2: Update downstream prompts so they point users back to the upstream prompts when the workstream is still unclear.
- [x] Step 3: Keep the wording short and copyable rather than turning prompt files into a process manual.

## Task 3: Update Planning And Governance Docs

**Files:**
- Modify: `docs/operating_system/planning-dispatch.md`
- Modify: `docs/operating_system/repo-governance.md`

- [x] Step 1: Point planning-dispatch to the new roadmap/workstream prompt ladder.
- [x] Step 2: Update repo-governance so the prompt pack is described as covering roadmap-to-workstream invocation as well as downstream execution prompts.

## Task 4: Close The Artifact Loop And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-25-roadmap-to-workstream-prompt-ladder-spec.md`
- Modify: `docs/superpowers/plans/2026-04-25-01-40-roadmap-to-workstream-prompt-ladder-plan.md`

- [x] Step 1: Mark the spec and plan completed after implementation.
- [x] Step 2: Run `scripts/validate_adoption_shape.py`.
- [x] Step 3: Run `git diff --check`.
- [ ] Step 4: Commit and push the prompt-ladder pass.
