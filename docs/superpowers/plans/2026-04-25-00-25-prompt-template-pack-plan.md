---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/operating_system/repo-governance.md
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/README.md
  - docs/superpowers/specs/2026-04-25-prompt-template-pack-spec.md
related_features: []
related_stages: []
---

# Prompt Template Pack Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-25-prompt-template-pack-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `executing-plans` or `subagent-driven-development` to implement task-by-task.

**Goal:** Add a small prompt-template pack that users can copy to guide agents through the repo lifecycle from intent to spec, plan, execution, validation, and mode migration.

**Architecture:** Create a new `docs/operating_system/prompt_templates/` folder with a short README plus six focused prompt files. Then link that pack from the main operating-system docs and the Mode A template README so users can discover it naturally.

**Key Invariants:**
- The prompt files must reinforce the existing lifecycle, not invent a new one.
- Templates must be short and directly copyable.
- Each template must say when to use it and what output to expect.
- Prompt templates remain optional guidance, not validator-enforced repo files.

**Rollout / Revert:**  
- rollback_trigger: the prompt files become overly long, duplicate operating-system docs, or blur multiple lifecycle steps together.  
- rollback_method: trim or remove the prompt pack and restore the docs to link only to the core operating-system guides.

---

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a user-facing prompt-template pack for the repo lifecycle and link it from the main operating-system docs.
Reasoning: This is repo-method usability guidance, not product work.
Invariants:
  - Prompt templates remain short and copyable.
  - Planning lifecycle stays `intent -> workstream or operating_system -> change -> spec -> plan -> execution`.
  - Prompt templates should help users ask for the right artifact, not bypass the lifecycle.
Dependencies:
  - `docs/operating_system/planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/project_templates/mode-a/README.md`
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
    - `docs/operating_system/planning-dispatch.md`
    - `docs/operating_system/repo-governance.md`
    - `docs/operating_system/project-adoption-migration-guide.md`
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
docs/operating_system/prompt_templates/README.md
docs/operating_system/prompt_templates/intent-prompt.md
docs/operating_system/prompt_templates/spec-prompt.md
docs/operating_system/prompt_templates/plan-prompt.md
docs/operating_system/prompt_templates/execute-prompt.md
docs/operating_system/prompt_templates/validate-or-drift-prompt.md
docs/operating_system/prompt_templates/mode-migration-prompt.md
```

## Files To Modify

```text
docs/operating_system/repo-governance.md
docs/operating_system/planning-dispatch.md
docs/operating_system/project-adoption-migration-guide.md
docs/project_templates/mode-a/README.md
docs/superpowers/specs/2026-04-25-prompt-template-pack-spec.md
```

## Task 1: Add The Prompt Pack

**Files:**
- Create: `docs/operating_system/prompt_templates/*`

- [x] Step 1: Add a short `README.md` that explains the pack and the lifecycle order.
- [x] Step 2: Add focused prompt files for intent, spec, plan, execute, validate/drift, and mode migration.
- [x] Step 3: Keep each template short, copyable, and explicit about expected output.

## Task 2: Link The Pack From Core Docs

**Files:**
- Modify: `docs/operating_system/planning-dispatch.md`
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/project_templates/mode-a/README.md`

- [x] Step 1: Add a pointer from planning guidance to the prompt pack as a practical entrypoint.
- [x] Step 2: Add a governance note that the prompt pack is the copyable user-facing invocation layer.
- [x] Step 3: Link the migration prompt from the migration guide and the Mode A template README.

## Task 3: Complete The Spec And Verify

**Files:**
- Modify: `docs/superpowers/specs/2026-04-25-prompt-template-pack-spec.md`
- Verify only

- [x] Step 1: Mark the spec completed after implementation.
- [x] Step 2: Run `git diff --check`.
- [x] Step 3: Review the prompt files for consistency and brevity.
