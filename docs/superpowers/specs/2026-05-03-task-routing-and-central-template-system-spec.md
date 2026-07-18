---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/templates/
  - docs/operating_system/prompt_templates/
  - .agents/skills/
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
related_features: []
related_stages: []
---

# Task Routing And Central Template System Spec

## Goal

Define a reliable agent workflow for choosing the correct task starting point
and using standardized document templates with centralized ownership and
skill-level discoverability.

## Key Deliverables

- a Task Start Routing Guide integrated into agent workflow rules
- a centralized template system covering roadmap/workstream/thread/spec/plan
- a skill-reference pattern so each skill can locate and apply templates
- clear governance for template updates and compatibility

## Problem

Agents can jump into implementation too early when roadmap/workstream/thread
planning is required first. Template ownership is also split, which risks
inconsistent outputs and harder maintenance.

## Scope

This spec covers:

- task start routing rules
- template storage and naming conventions
- how skills reference and apply templates
- update/compatibility rules

This spec does not cover:

- validator implementation details
- UI changes

## Design Decision

Use a **hybrid model with central ownership**:

- canonical templates live in one central folder
- skills reference canonical templates via stable paths
- skill-local template copies are not authoritative

This gives consistency and reuse while keeping skill usage simple.

## Folder Structure

Canonical template root:

- `docs/operating_system/templates/`

Recommended sub-structure:

- `docs/operating_system/templates/routing/`
  - task-start-routing-guide.md
- `docs/operating_system/templates/planning/`
  - master-workstream-roadmap-template.md
  - registered-workstream-list-template.md
  - bounded-change-thread-template.md
  - complete-specification-set-template.md
  - spec-authoring-map-template.md
  - detailed-specification-template.md
  - implementation-execution-map-template.md
  - implementation-plan-template.md
- `docs/operating_system/templates/README.md`

Skill-side references:

- `.agents/skills/<skill>/SKILL.md` links to canonical template paths

## Naming Convention

Use:

- `<document-type>-template.md`

Examples:

- `master-workstream-roadmap-template.md`
- `bounded-change-thread-template.md`
- `implementation-plan-template.md`

Rules:

- lowercase kebab-case
- include `-template` suffix
- avoid version numbers in filenames unless a breaking schema split is required

## Task Start Routing Guide (Workflow Contract)

### Routing order

Default decision order:

`detailed spec -> bounded change thread -> registered workstream -> master roadmap`

Start at the lowest valid layer; move upward when required evidence is missing.

### Safe to start directly from detailed spec only when

- spec exists and is in scope
- lineage is valid (thread/workstream or intentional `parent_workstream: none`)
- dependencies are clear and bounded
- task is implementation-level, not reprioritization

### Must inspect/update roadmap first when

- priorities/phases/major outcomes are changing
- no workstream clearly owns the initiative
- cross-workstream sequencing is unclear

### Create/continue workstream when

- work is durable and spans multiple threads/specs/plans
- roadmap intent exists but ownership container is missing/weak

### Create/continue bounded change thread when

- workstream is known but next executable slice is not clear
- safe parallelization boundary is needed before spec/plan execution

### Required evidence checks before choosing start point

1. roadmap context exists
2. workstream fit exists
3. bounded thread exists or should be created
4. actionable spec exists (if implementation-level start)
5. dependencies/blockers/shared-surface risks known
6. status/evidence coherence (checkpoint/result-pack coverage where required)

### Ambiguity handling

If routing remains ambiguous:

1. pause implementation
2. choose safer higher-level planning start (usually thread/workstream)
3. record assumptions and proceed
4. ask for confirmation only for non-obvious tradeoffs

## Template Application Rules

For every authored planning artifact:

- apply the matching canonical template
- include required sections:
  - `Goal`
  - `Key Deliverables`
- conform to current metadata/lineage rules from governance + validators

If skill guidance conflicts with canonical template:

- canonical template + governance rules take precedence
- skill may add optional sections only

## How Skills Reference Templates

In each relevant `SKILL.md`, add a short template contract block:

- “Use canonical template at `<path>`”
- “Do not copy/maintain local duplicate template”
- “If template updates, follow canonical path automatically”

Example (spec-writing skill):

- template: `docs/operating_system/templates/planning/detailed-specification-template.md`
- required sections: `Goal`, `Key Deliverables`
- then apply skill-specific refinement steps

Example (plan-writing skill):

- template: `docs/operating_system/templates/planning/implementation-plan-template.md`
- required sections: `Goal`, `Key Deliverables`
- then add executable task breakdown per skill rules

## Agent Discovery Flow

When starting a task:

1. run routing guide decision
2. determine artifact type to create/continue
3. resolve canonical template path from `docs/operating_system/templates/`
4. apply template
5. run relevant validator checks before claiming completion

## Template Update Governance

Update rules:

- central templates are source-of-truth
- changes require:
  - update note in template README changelog section
  - compatibility check against impacted skills
  - validator-awareness review if metadata/required fields change

Breaking-change rule:

- if a change alters required structure/metadata semantics, include migration
  instructions and update affected skills in the same change set

## Rollout Plan

1. formalize central template folder structure
2. map each skill to canonical templates
3. add routing-guide section to planning/routing skills
4. run sample authoring passes for roadmap/workstream/thread/spec/plan
5. tighten enforcement once compatibility is validated

## Acceptance Criteria

- agents can deterministically choose start point for common task classes
- all key planning document types resolve to canonical templates
- skill docs reference canonical templates instead of local duplicates
- authored documents consistently include `Goal` and `Key Deliverables`
- no ambiguous template authority between central docs and skills
