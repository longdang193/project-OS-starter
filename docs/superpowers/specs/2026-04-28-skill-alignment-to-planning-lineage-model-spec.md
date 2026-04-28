---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - .agents/skills/brainstorming/SKILL.md
  - .agents/skills/planning-dispatch/SKILL.md
  - .agents/skills/writing-plans/SKILL.md
  - .agents/skills/doc-system-lifecycle/SKILL.md
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/generated/planning_lineage.yaml
related_features: []
related_stages: []
---

# Skill Alignment To Planning Lineage Model Spec

## Triage

Layer: operating_system  
Feature type: MODIFY  
Summary: Align the planning-related skills to the repo’s current planning-lineage model so skills stop teaching older routing and metadata assumptions.  
Reasoning: The repo’s planning system has advanced materially: explicit thread files, `parent_thread`, `parent_spec`, generated `planning_lineage.yaml`, a strict derived-linkage boundary, and the new `execution_maps/` artifact class. The docs and prompt pack now reflect that model, but the skills that guide agent behavior may still describe older flows such as workstream-to-spec shortcuts or `parent_workstream` as the main downstream linkage.  
Invariants:

- skills should teach the same planning ladder as the current docs
- skills should not contradict prompt-template routing
- downstream planning lineage should use nearest-parent metadata
- execution maps should be treated as orchestration artifacts, not plans
- only the directly affected skills should change in the first pass

Dependencies:

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/planning-dispatch/SKILL.md`
- `.agents/skills/writing-plans/SKILL.md`
- `.agents/skills/doc-system-lifecycle/SKILL.md`
- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/intent/workstream-coverage-and-progress-guide.md`
- `docs/generated/planning_lineage.yaml`

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs:
  - `docs/operating_system/planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/intent/workstream-coverage-and-progress-guide.md`
- readme: none
- generated:
  - `docs/generated/planning_lineage.yaml`

Generated refresh required: no  
Capability IDs: none  
Invariant IDs: none  
Spec needed: yes  
Plan needed: yes

## Problem

The repo’s operating docs now teach a richer planning system:

`intent -> master roadmap -> registered workstream set -> bounded change thread files -> spec set -> execution map -> implementation plans -> execution`

It also now enforces:

- `parent_thread` for change-layer specs/plans
- `parent_spec` for change-layer plans
- derived thread/spec/plan linkage via `docs/generated/planning_lineage.yaml`
- strict thread-file boundaries against `linked_spec` / `linked_plan`

But the skills most likely to guide agent behavior were written before some or
all of those shifts. That creates a real risk:

1. skills route from workstream straight to spec without the thread layer
2. skills treat `parent_workstream` as the main downstream linkage field
3. skills do not mention execution maps as a distinct orchestration artifact
4. agents following skills can drift from the prompt pack and operating docs

## Goal

Bring the planning-related skills into explicit alignment with the current
planning-lineage model and artifact ladder.

## Non-Goals

This spec does not review every skill in the repo.

This spec does not rewrite unrelated coding, debugging, or verification skills.

This spec does not introduce a new skill surface if the existing planning
skills can be updated cleanly.

## Highest-Priority Skills

### 1. `brainstorming`

Why review it:

- it frames the design-first planning flow
- it currently shapes how agents move from intent into downstream artifacts

What should align:

- explicit thread layer
- thread set -> spec set transition
- execution map as orchestration layer before bounded plans when multiple specs
  are involved
- `parent_thread` / `parent_spec` expectations in downstream artifact thinking

### 2. `planning-dispatch`

Why review it:

- it owns triage and routing
- it is the main place where the planning ladder gets operationalized

What should align:

- current ladder including thread files, spec sets, execution maps, and plans
- distinction between one-spec work and multi-spec orchestration work
- current metadata expectations for change-layer artifacts

### 3. `writing-plans`

Why review it:

- it governs implementation-plan creation
- plans now sometimes sit downstream of an execution map instead of directly
  after a lone spec

What should align:

- `parent_thread`
- `parent_spec`
- when a plan can be written directly from one approved spec
- when execution-map context should be consulted before plan breakdown

### 4. `doc-system-lifecycle`

Why review it:

- it governs doc-system placement and source-of-truth boundaries
- it should reflect that `execution_maps/` is now its own artifact class

What should align:

- source vs derived boundary
- `docs/generated/planning_lineage.yaml` as derived inspection
- `docs/superpowers/execution_maps/` as orchestration artifacts

## Recommended Alignment Principles

Use these principles across the reviewed skills:

1. **Thread-first bounded execution**
   - do not skip from workstream intent straight to spec when a bounded thread
     should be chosen first

2. **Nearest-parent lineage**
   - specs use `parent_thread`
   - plans use `parent_thread` and `parent_spec`
   - do not teach redundant downstream `parent_workstream` restatement

3. **Derived linkage inspection**
   - use `docs/generated/planning_lineage.yaml` for assembled thread/spec/plan
     linkage
   - do not teach thread files as places to manually store derived links

4. **Execution maps are distinct**
   - execution maps orchestrate a spec set
   - plans implement one approved bounded slice or lane
   - execution maps must not be described as giant plans

## Suggested Skill-Level Changes

### `brainstorming`

Update:

- checklist and process-flow wording
- planning ladder examples
- downstream artifact handoff language

### `planning-dispatch`

Update:

- triage/routing ladder
- prompt references
- artifact routing rules
- examples that currently stop too early or flatten orchestration

### `writing-plans`

Update:

- plan header guidance if needed
- examples of plan provenance from spec or execution map context
- explicit mention of `parent_thread` / `parent_spec` for change-layer plans

### `doc-system-lifecycle`

Update:

- placement tables or source-of-truth examples
- mention of `docs/superpowers/execution_maps/`
- guidance on generated planning-lineage as derived inspection rather than
  source

## Acceptance Criteria

- the four targeted skills no longer contradict the current planning ladder
- skills mention thread files where appropriate
- skills recognize execution maps as a distinct artifact class
- skills no longer teach redundant downstream lineage entry where the repo now
  derives it
- the updated skill guidance matches the repo’s current docs and prompt pack

## Recommendation

Do a targeted skill alignment pass now, limited to the four planning-related
skills.

That is the highest-leverage move because it brings:

- skill behavior
- prompt behavior
- operating docs
- validator behavior

back into the same planning model.
