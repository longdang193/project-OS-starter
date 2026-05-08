---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: prompt-schema-update-plan
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/plan-prompt.md
  - docs/operating_system/prompt_templates/spec-prompt.md
  - docs/operating_system/prompt_templates/thread-set-to-spec-set-prompt.md
  - docs/operating_system/prompt_templates/workstream-alignment-review-prompt.md
  - docs/operating_system/prompt_templates/spec-set-execution-map-prompt.md
  - docs/operating_system/prompt_templates/spec-set-to-spec-authoring-map-prompt.md
  - docs/operating_system/prompt_templates/bounded-change-thread-build-prompt.md
  - docs/operating_system/prompt_templates/registered-workstream-set-build-prompt.md
  - docs/operating_system/prompt_templates/master-workstream-roadmap-build-prompt.md
  - docs/operating_system/prompt_templates/README.md
  - docs/generated/planning_lineage.yaml
related_features: []
related_stages: []
---

# Implementation Plan Template

## Goal

Update planning prompt templates so they explicitly reflect the hardened planning schema and current lineage rules, especially canonical identity fields, allowed lineage fields, operating-system exceptions, and generated-lineage lookup guidance.

## Key Deliverables

### Prompt inventory and schema-gap audit

Review planning-facing prompt templates against `repo_config/planning_artifact_schema.yaml` and recent validator behavior so prompt instructions stop implying deprecated or incomplete metadata patterns. Capture exact prompt files whose text still points users toward legacy identity fields, manual linkage habits, or underspecified lineage expectations.

### Canonical prompt text updates

Revise affected prompt templates so they consistently instruct users to use canonical schema fields (`name`, `artifact_type`, `layer`, `status`) while still acknowledging legacy IDs only where the underlying artifact family still uses them. Ensure prompts distinguish product-thread lineage from true `operating_system` exceptions and direct users to generated planning lineage instead of manual thread linkage.

### Verification-ready prompt pack state

Leave prompt surfaces in validator-clean state with updated wording reflected in prompt-ladder and lifecycle checks. If prompt changes affect derived planning lineage visibility or lifecycle examples, refresh generated planning lineage and verify no prompt metadata or required-section regressions remain.

## Task/Wave Breakdown

### task 1: audit prompt templates against current schema and validator rules

Inspect planning prompt templates that author or review roadmap, workstream, thread, spec, execution-map, and plan artifacts. Compare their current wording to `repo_config/planning_artifact_schema.yaml`, `docs/operating_system/planning/planning-dispatch.md`, and recent closure/evidence rules to identify exact mismatches such as deprecated references to manual links, missing canonical identity guidance, or stale `parent_workstream` direction.

### task 2: update high-impact prompt instructions first

Edit prompt templates that directly create or revise specs and plans (`spec-prompt.md`, `plan-prompt.md`) plus prompts that review workstream routing or consume planning lineage (`workstream-alignment-review-prompt.md`, `thread-set-to-spec-set-prompt.md`). Make lineage instructions explicit: change-layer plans should prefer `parent_thread` plus `parent_spec`, bounded thread docs should not regain manual linked-spec/linked-plan sections, and operating-system work should justify `parent_workstream: none` or `parent_thread: none` only when truly outside product workstream lineage.

### task 3: propagate schema wording across upstream planning-build prompts

Update roadmap/workstream/thread/execution-map construction prompts where needed so they mention canonical identity expectations (`name` as preferred field, legacy field awareness only where artifact family still accepts one), correct allowed statuses, and generated-lineage lookup expectations. Keep wording compact and source-of-truth oriented rather than duplicating full schema tables inside prompts.

### task 4: run prompt and lifecycle verification

Run prompt-focused validators plus lifecycle checks from the worktree. If prompt changes alter derived lineage, regenerate `docs/generated/planning_lineage.yaml` before final verification. Confirm prompt metadata, prompt ladder, template required sections, checkpoint/lifecycle validation, and fast repo validation all pass.

## Verification

- `& ".venv\Scripts\python.exe" scripts\validate_template_required_sections.py`
- `& ".venv\Scripts\python.exe" scripts\validate_prompt_metadata_schema.py`
- `& ".venv\Scripts\python.exe" scripts\validate_prompt_ladder.py`
- `& ".venv\Scripts\python.exe" scripts\validate_planning_lifecycle.py --strict`
- `& ".venv\Scripts\python.exe" scripts\generate_planning_lineage.py`
- `& ".venv\Scripts\python.exe" scripts\hooks\run_validator.py --fast`

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
