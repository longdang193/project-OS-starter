---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: template-standardization-across-planning-ladder
parent_workstream: none
targets:
  - docs/operating_system/templates/master-workstream-roadmap-template.md
  - docs/operating_system/templates/registered-workstream-list-template.md
  - docs/operating_system/templates/bounded-change-thread-template.md
  - docs/operating_system/templates/complete-specification-set-template.md
  - docs/operating_system/templates/spec-authoring-map-template.md
  - docs/operating_system/templates/detailed-specification-template.md
  - docs/operating_system/templates/implementation-execution-map-template.md
  - docs/operating_system/templates/implementation-plan-template.md
  - docs/operating_system/templates/task-start-routing-guide.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-doc-system-lifecycle/SKILL.md
related_features: []
related_stages: []
---

# Template Standardization Across Planning Ladder Plan

## Goal

Standardize the planning-ladder template family so every artifact from master roadmap through implementation plan uses the same high-signal structure for `## Goal`, `## Key Deliverables`, and `## Task/Wave Breakdown`, while preserving each artifact's type-specific metadata, downstream role, and completion semantics.

## Key Deliverables

### Shared section contract defined

Define one canonical section pattern that every targeted template must follow:

- `## Goal`
- `## Key Deliverables`
  - `### <deliverable>` blocks with body text, not flat bullets
- `## Task/Wave Breakdown`
  - `### <wave/task>` blocks with body text, not flat lists

Clarify allowed naming conventions:

- use `Task Breakdown` when artifact is execution-task oriented
- use `Wave Breakdown` when artifact is orchestration or sequencing oriented
- if both semantics matter, standardize on `Task/Wave Breakdown` as shared validator-facing wording or define allowed aliases explicitly

### Target template inventory normalized

Review and update these templates:

- `master-workstream-roadmap-template.md`
- `registered-workstream-list-template.md`
- `bounded-change-thread-template.md`
- `complete-specification-set-template.md`
- `spec-authoring-map-template.md`
- `detailed-specification-template.md`
- `implementation-execution-map-template.md`
- `implementation-plan-template.md`

For each template:

- replace flat deliverable bullet lists with `###` deliverable subsections
- replace artifact-specific middle section names when required to align with shared section contract
- preserve artifact-specific downstream sections only when still necessary after normalization
- keep completion criteria and frontmatter contract intact unless deliberate schema/validator change is required

### Skill-to-template responsibility matrix documented

Identify which skills should read, route to, or author which template surfaces.

Expected minimum mapping:

- `skill-brainstorming` -> complete spec set, spec-authoring map, detailed specification templates
- `skill-writing-plans` -> implementation plan template
- `skill-executing-plans` -> execution against plan output, not template authoring, but should recognize normalized plan structure
- `skill-doc-system-lifecycle` -> source-of-truth placement and template-family governance

Also determine whether any skill should explicitly mention:

- `master-workstream-roadmap-template.md`
- `registered-workstream-list-template.md`
- `bounded-change-thread-template.md`
- `implementation-execution-map-template.md`

### Validation and drift follow-up scoped

Determine whether validator or template metadata surfaces must change so the new shared section contract is enforceable or at least discoverable.

Check impact on:

- template frontmatter `required_sections`
- any validators that inspect section names or template IDs
- routing and authoring guidance that currently uses legacy section names like `Phase Structure`, `Spec Inventory`, `Authoring Waves`, `Execution Waves`, or `Task Breakdown`

## Task/Wave Breakdown

### Wave 1: Baseline inventory and mismatch analysis

Read every targeted template and record:

- current section names
- current section shapes
- whether deliverables are bullets or subsections
- whether middle orchestration sections are task-oriented or wave-oriented
- whether template frontmatter already declares section names compatible with desired standard

Produce concise mismatch table covering:

- current state
- desired state
- compatibility risk
- whether alias support is needed

### Wave 2: Shared section contract design

Define exact normalization rules for the whole ladder.

Decide:

- whether top-level section should literally become `## Task/Wave Breakdown` everywhere, or whether validators should allow artifact-specific aliases while preserving common subsection shape
- whether roadmap phases remain nested under `## Task/Wave Breakdown` or move from `## Phase Structure`
- whether spec inventory / coverage / traceability sections remain additional sections after standard sections, or become content nested under task/wave breakdown deliverables

Keep design minimal and source-first:

- standardize structure without erasing useful artifact semantics
- avoid unnecessary schema churn if template metadata can express compatible aliases

### Wave 3: Template patch plan by artifact class

Break the templates into implementation groups:

- planning sources:
  - master roadmap
  - registered workstream list
  - bounded change thread
- specification and orchestration sources:
  - complete spec set
  - spec-authoring map
  - detailed specification
  - implementation execution map
- execution source:
  - implementation plan

For each group, define exact edits:

- required section renames
- sample placeholder rewrite
- frontmatter `required_sections` updates
- non-standard sections to preserve, move, or deprecate

### Wave 4: Skill review and template linkage mapping

Review skills that route or author these documents and classify each by responsibility:

- routing only
- design authoring
- plan authoring
- execution consumption
- lifecycle governance

Document which template references each skill should gain or keep.

Likely review set:

- `.agents/skills/skill-brainstorming/SKILL.md`
- `.agents/skills/skill-writing-plans/SKILL.md`
- `.agents/skills/skill-executing-plans/SKILL.md`
- `.agents/skills/skill-doc-system-lifecycle/SKILL.md`
- optionally `skill-finishing-a-development-branch` if closeout should recognize normalized plan structure

### Wave 5: Validation and governance impact review

Inspect whether any of these surfaces must change after template standardization:

- `repo_config/planning_artifact_schema.yaml`
- `scripts/validate_planning_lifecycle.py`
- `docs/operating_system/templates/task-start-routing-guide.md`
- any docs that explain the planning ladder or template usage

Decide whether enforcement is:

- immediate validator change
- staged documentation-first adoption
- compatibility window with follow-up enforcement patch

### Wave 6: Execution packaging and follow-up slicing

Prepare implementation-ready follow-up slices from this plan:

- template-only normalization patch
- skill linkage patch
- validator/governance alignment patch if needed

Define safe execution order so shared templates update before skill references depend on new wording.

## Skill Review: Which Skills Need Which Templates


Should use or explicitly understand:

- `docs/operating_system/templates/task-start-routing-guide.md`
- `docs/operating_system/templates/master-workstream-roadmap-template.md`
- `docs/operating_system/templates/registered-workstream-list-template.md`
- `docs/operating_system/templates/bounded-change-thread-template.md`
- awareness of downstream spec/map/plan templates for routing decisions

Reason:

- it decides correct ladder entry point
- it should route users to roadmap vs workstream vs thread vs spec vs plan correctly

### `skill-brainstorming`

Should use:

- `docs/operating_system/templates/complete-specification-set-template.md`
- `docs/operating_system/templates/spec-authoring-map-template.md`
- `docs/operating_system/templates/detailed-specification-template.md`
- likely awareness of `implementation-execution-map-template.md` for downstream handoff boundaries

Reason:

- it authors design artifacts
- it should know complete spec set vs authoring map vs detailed spec roles

### `skill-writing-plans`

Should use:

- `docs/operating_system/templates/implementation-plan-template.md`
- awareness of `docs/operating_system/templates/implementation-execution-map-template.md` when plan context comes from execution-map orchestration

Reason:

- it authors plan artifacts directly
- it should stay consistent with execution-map to plan handoff model

### `skill-executing-plans`

Should read or respect:

- `docs/operating_system/templates/implementation-plan-template.md` indirectly through plan structure expectations
- awareness of `docs/operating_system/templates/implementation-execution-map-template.md` when execution traces back to an execution map

Reason:

- not template authoring skill
- but execution depends on predictable plan structure and upstream orchestration semantics

### `skill-doc-system-lifecycle`

Should use or govern:

- whole template family as operating-system documentation source
- especially roadmap, workstream, thread, spec, map, and plan template placement rules

Reason:

- owns source-of-truth placement, template governance, and generated-vs-source boundaries

## Verification

- review all targeted templates for section-shape drift
- review targeted skills for template-reference drift
- run any template/contract validator checks required after edits
- verify resulting docs still align with `repo_config/planning_artifact_schema.yaml` and `scripts/validate_planning_lifecycle.py`

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
