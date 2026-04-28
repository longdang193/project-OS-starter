---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/README.md
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/superpowers/execution_maps/README.md
  - .agents/skills/brainstorming/SKILL.md
  - .agents/skills/planning-dispatch/SKILL.md
  - .agents/skills/writing-plans/SKILL.md
  - .agents/skills/doc-system-lifecycle/SKILL.md
related_features: []
related_stages: []
---

# Spec-Authoring Map And Implementation Execution Map Spec

## Triage

Layer: operating_system  
Feature type: MODIFY  
Summary: Split the current single "execution map" concept into two distinct orchestration layers: a spec-authoring map before detailed specs and an implementation execution map after approved detailed specs.  
Reasoning: The current ladder is clearer than the old workstream-to-plan shortcut, but it still overloads one "execution map" term across two different orchestration questions. We now need the repo to teach the more precise flow from complete spec coverage into detailed-spec authoring, and then from approved detailed specs into implementation sequencing.  
Invariants:

- canonical planning truth still flows downward from intent and workstreams
- the repo keeps separate artifact roles for spec coverage, orchestration, and bounded plans
- the spec-authoring map must not collapse into a design spec
- the implementation execution map must not collapse into a giant plan
- downstream layers should derive lineage rather than restating upstream semantic truth manually

Dependencies:

- `docs/operating_system/prompt_templates/README.md`
- `docs/operating_system/prompt_templates/thread-set-to-spec-set-prompt.md`
- `docs/operating_system/prompt_templates/spec-set-execution-map-prompt.md`
- `docs/operating_system/prompt_templates/spec-prompt.md`
- `docs/operating_system/prompt_templates/plan-prompt.md`
- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/superpowers/execution_maps/README.md`
- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/planning-dispatch/SKILL.md`
- `.agents/skills/writing-plans/SKILL.md`
- `.agents/skills/doc-system-lifecycle/SKILL.md`

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
    - `docs/operating_system/prompt_templates/README.md`
    - `docs/operating_system/prompt_templates/thread-set-to-spec-set-prompt.md`
    - `docs/operating_system/prompt_templates/spec-set-execution-map-prompt.md`
    - `docs/operating_system/prompt_templates/spec-prompt.md`
    - `docs/operating_system/prompt_templates/plan-prompt.md`
    - `docs/operating_system/planning-dispatch.md`
    - `docs/operating_system/repo-governance.md`
    - `docs/superpowers/execution_maps/README.md`
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

## Problem

The current repo language still compresses two different orchestration steps
into one term:

`thread set -> spec set -> execution map -> plans`

That is good enough for showing that orchestration exists, but it is no longer
precise enough for the way we want the planning system to work.

There are now two different orchestration questions:

1. after the complete spec set is known, how should the detailed-spec work be
   sequenced or parallelized?
2. after the detailed specs are approved, how should implementation be
   sequenced or parallelized?

Using the same generic "execution map" term for both introduces ambiguity in:

- prompt routing
- skill guidance
- repo-control docs
- artifact definitions

## Goal

Teach and document the more precise planning ladder:

`master roadmap -> registered workstreams -> bounded change threads -> complete spec set -> spec-authoring map -> detailed specs -> implementation execution map -> implementation plans -> execution`

## Non-Goals

This spec does not add new validator-backed artifact rules yet.

This spec does not redesign spec metadata or plan metadata again.

This spec does not create a second folder class unless the terminology pass
shows the current execution-map folder is no longer sufficient.

## Recommended Model

### 1. Complete Spec Set

Owns:

- the inventory of needed specs
- thread-to-spec coverage
- whether threads are covered, split, or merged

Does not own:

- detailed design reasoning
- sequencing of detailed-spec authoring
- sequencing of implementation

### 2. Spec-Authoring Map

Owns:

- ordering for writing detailed specs
- dependencies among detailed-spec authoring tasks
- parallel authoring lanes where safe
- shared-surface design risks during spec creation

Does not own:

- the final detailed spec content
- implementation plan details

### 3. Detailed Specs

Own:

- the actual design reasoning for each bounded slice
- scope
- invariants
- dependencies
- targets and doc impacts

### 4. Implementation Execution Map

Owns:

- orchestration after detailed specs are approved
- implementation waves
- implementation parallel lanes
- shared-surface implementation risks
- plan breakdown guidance

Does not own:

- detailed design reasoning
- step-by-step implementation commands

### 5. Implementation Plans

Own:

- exact bounded execution steps
- tests
- verification commands
- doc updates
- commit-ready implementation slices

## Recommended Terminology Changes

Use these terms consistently:

- `complete spec set`
- `spec-authoring map`
- `detailed specs`
- `implementation execution map`
- `implementation plans`

Prefer not to use the ambiguous phrase `execution map` by itself when the
phase is unclear.

## Prompt-Surface Changes

The prompt pack is part of the owning surface for this adjustment, not just a
downstream reference. The implementation should treat prompt changes as a
first-class deliverable.

The prompt pack should distinguish:

1. `thread-set-to-spec-set-prompt.md`
   - output: complete spec set
   - should stop short of writing detailed specs
   - should name uncovered threads, split/merge choices, and recommended next
     spec-authoring step
2. new or renamed prompt for spec-authoring orchestration
   - output: spec-authoring map
   - should decide which detailed specs get written first
   - should identify spec-authoring dependencies and safe parallel authoring
     lanes
3. `spec-prompt.md`
   - output: detailed spec
   - should now clearly assume a chosen detailed-spec target rather than acting
     like the complete spec inventory step
4. current `spec-set-execution-map-prompt.md` should be narrowed or renamed
   - output: implementation execution map
   - should clearly assume approved detailed specs already exist
   - should focus on implementation waves, lanes, and plan breakdown
5. `plan-prompt.md`
   - output: implementation plan
   - should now point back to the implementation execution map when the plan is
     part of a multi-spec implementation wave

Recommended prompt actions:

- keep `thread-set-to-spec-set-prompt.md` but tighten its expected output
- add or rename a prompt so the spec-authoring-map step is explicit
- rename or rewrite `spec-set-execution-map-prompt.md` if needed so it no
  longer sounds like it owns pre-spec orchestration
- update `spec-prompt.md` and `plan-prompt.md` so they fit the refined ladder
- update `docs/operating_system/prompt_templates/README.md` so the lifecycle
  order reflects both orchestration phases

## Related Repo-Control Doc Changes

Update repo-control docs so they teach the refined ladder rather than the
compressed one:

- `docs/operating_system/prompt_templates/README.md`
- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/superpowers/execution_maps/README.md`

These docs should:

- explicitly distinguish spec-authoring orchestration from implementation
  orchestration
- keep the complete spec set separate from detailed specs
- keep orchestration artifacts separate from plans

## Related Skill Changes

Update the planning-related skills so they stop flattening the two
orchestration phases:

- `brainstorming`
  - should teach the handoff from complete spec set into spec-authoring map,
    then into detailed specs
- `planning-dispatch`
  - should route to the correct orchestration phase instead of one generic
    execution-map step
- `writing-plans`
  - should assume detailed specs and the implementation execution map already
    exist when plan-level sequencing matters
- `doc-system-lifecycle`
  - should describe the orchestration artifact roles precisely

## Open Design Choice

The first implementation pass should decide one of these:

1. keep one folder `docs/superpowers/execution_maps/` and distinguish the two
   map types by naming and metadata
2. split into two artifact surfaces later if the single folder becomes noisy

Recommendation:

- keep one folder first
- distinguish the map types by title, prompt, and metadata wording
- revisit folder split only if usage becomes confusing

## Acceptance Criteria

- repo-control docs teach:
  - `complete spec set -> spec-authoring map -> detailed specs -> implementation execution map -> implementation plans`
- prompt guidance distinguishes the two orchestration phases
- the owning prompt files explicitly distinguish:
  - complete spec set
  - spec-authoring map
  - detailed specs
  - implementation execution map
  - implementation plans
- skills no longer speak as if one generic execution map covers both phases
- `docs/superpowers/execution_maps/README.md` explains the refined artifact
  roles clearly
- the terminology no longer collapses detailed-spec authoring and
  implementation sequencing into one ambiguous step

## Recommendation

Adopt option B:

`complete spec set -> spec-authoring map -> detailed specs -> implementation execution map -> implementation plans`

Then adjust prompts, skills, and repo-control docs in one narrow terminology
and routing pass before adding any validator-backed enforcement.
