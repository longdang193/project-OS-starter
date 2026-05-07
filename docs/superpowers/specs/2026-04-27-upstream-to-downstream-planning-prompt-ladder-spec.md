---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
related_features: []
related_stages: []
---

# Upstream-To-Downstream Planning Prompt Ladder Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a prompt ladder that helps users build the planning structure from the top down: master roadmap, complete registered workstream set, bounded change threads, then specs, plans, and execution.
Reasoning: The repo now has many strong prompts for routing, drift review, migration, divergence review, and parallel bounded-change planning. What is still missing is the construction ladder for creating the planning structure itself from upstream intent all the way down to executable slices.
Invariants:

- The prompt ladder should follow the repo’s planning model from upstream to downstream.
- The prompts should distinguish construction of planning structure from review of existing structure.
- The master roadmap remains strategic.
- Registered workstreams should collectively cover the roadmap.
- Bounded change threads remain the execution-capable unit beneath a workstream or `operating_system`.
- The prompts should stay short, copyable, and sequence-aware.

Dependencies:

- `docs/operating_system/prompt_templates/`
- `docs/intent/master-workstream-roadmap.md`
- `docs/intent/workstreams/`
- `docs/intent/workstream-coverage-and-progress-guide.md`
- `docs/operating_system/skill-planning-dispatch.md`
- `docs/operating_system/governance/repo-governance.md`

Affected stages:

- none directly

Affected features:

- none directly

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs: none
- operating_system_docs:
  - `docs/operating_system/prompt_templates/`
  - `docs/operating_system/skill-planning-dispatch.md`
  - `docs/operating_system/governance/repo-governance.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo now has useful prompts for:

- routing intent into a workstream
- routing a workstream into a spec
- reviewing roadmap gaps
- reviewing workstream fit
- reviewing roadmap vs execution divergence
- planning safe parallel bounded changes

But it still lacks the explicit top-down build path for the planning structure
itself.

Today, a user can still ask:

- how do I build the master workstream roadmap?
- how do I turn that roadmap into the complete set of registered workstreams?
- how do I break a workstream into bounded change threads?

Those are not quite the same as:

- routing an already-known thread
- reviewing an existing gap
- drafting a spec for an already-bounded slice

So the prompt pack is strong in the middle, but not yet complete at the top.

## Goal

Add a construction-oriented prompt ladder that helps users move from:

`intent -> master workstream roadmap -> complete registered workstream set -> bounded change threads -> specs -> implementation plans -> execution`

The new prompts should build the planning structure itself, not just inspect or
route it.

## Non-Goals

This spec does not replace the existing routing or review prompts.

This spec does not add validator enforcement by itself.

This spec does not turn the master roadmap into a progress board.

This spec does not require every project to create all downstream artifacts at
once.

## Recommended Design

Add three core build prompts first.

### 1. `master-workstream-roadmap-build-prompt.md`

Use when intent exists but the roadmap of major delivery threads has not been
built clearly enough.

Expected outcome:

- identify the major delivery threads needed to reach the end goal
- distinguish product workstreams from `operating_system`
- draft or refine the master workstream roadmap

### 2. `registered-workstream-set-build-prompt.md`

Use when the master roadmap exists and the user wants to derive the concrete,
complete set of registered workstreams.

Expected outcome:

- convert roadmap threads into named workstream docs
- identify missing, duplicate, or too-vague workstreams
- assess whether the set covers the roadmap adequately

### 3. `bounded-change-thread-build-prompt.md`

Use when a workstream exists and the user wants to break it into discrete,
execution-capable slices.

Expected outcome:

- identify bounded change threads under the workstream
- separate independent slices from coupled ones
- recommend which threads need specs first

## How This Fits With Existing Prompts

The ladder would then become:

1. intent prompt
2. master-workstream-roadmap build prompt
3. registered-workstream-set build prompt
4. bounded-change-thread build prompt
5. workstream-to-spec prompt
6. spec prompt
7. plan prompt
8. execute prompt

Existing review prompts remain useful:

- roadmap gap review
- workstream alignment review
- roadmap vs execution divergence review
- parallel bounded-change planning

## Suggested README / Guidance Updates

The prompt-pack README should distinguish:

- **construction prompts**
  - used to build the planning structure from upstream to downstream
- **routing prompts**
  - used to choose the right next thread or artifact
- **review prompts**
  - used to inspect completeness, fit, drift, or divergence

Planning/governance docs should mention that the repo now supports building the
full planning structure top-down, not just routing inside an existing one.

## Acceptance Criteria

- The prompt pack includes upstream construction prompts for:
  - master roadmap
  - registered workstream set
  - bounded change threads
- The README and planning docs explain how those prompts fit into the existing
  ladder.
- The prompts preserve the distinction between product workstreams and
  `operating_system`.

## Risks

If the prompts are too abstract, users will still skip directly to specs/plans.

If they overlap too much with existing routing prompts, the pack will feel
redundant.

If the ladder is too rigid, it may feel heavy for small projects.

## Recommendation

Add the upstream construction prompts now. The repo already has the governance
model and many downstream prompts; the missing piece is the practical top-down
build path that takes users from intent to a complete planning structure and
then onward to execution.
