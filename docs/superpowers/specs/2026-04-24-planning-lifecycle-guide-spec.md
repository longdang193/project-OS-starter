---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - .agents/skills/brainstorming/SKILL.md
  - .agents/skills/planning-dispatch/SKILL.md
  - .agents/skills/writing-plans/SKILL.md
related_features: []
related_stages: []
---

# Planning Lifecycle Guide Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Add one canonical planning-lifecycle guide that states the repo's flow from intent through layer classification, triage, spec, and implementation plan.
Reasoning: The workflow exists today, but it is distributed across skills and partially reflected in operating-system docs. The repo needs one plain-language human guide for the lifecycle instead of relying on readers to reconstruct it from multiple skill files.
Invariants:

- `docs/intent/` remains the source for project what-and-why.
- Layer classification remains `intent | operating_system | workstream | change`.
- Triage still happens before spec or plan work.
- Specs remain design artifacts under `docs/superpowers/specs/`.
- Plans remain implementation artifacts under `docs/superpowers/plans/`.

Dependencies:

- `docs/operating_system/planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/planning-dispatch/SKILL.md`
- `.agents/skills/writing-plans/SKILL.md`

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
  - `docs/operating_system/planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo already has the pieces of the planning workflow:

- `docs/intent/` for project purpose and outcome sources
- `planning-dispatch` for layer classification and triage
- `brainstorming` for design and spec writing
- `writing-plans` for implementation plans

That is good structure, but the guidance is still spread across several files:

- the skills contain the clearest end-to-end flow
- `docs/operating_system/planning-dispatch.md` focuses on the triage gate
- `docs/operating_system/repo-governance.md` names the folders but does not
  act as the single lifecycle explainer

This means a human reader can still miss the intended sequence:

`intent -> layer classification -> triage -> spec -> implementation plan -> execution`

The workflow is real, but it is more implicit than it should be.

## Goal

Create one canonical operating-system guide that states the planning lifecycle
plainly and links the existing skills and docs that implement it.

## Non-Goals

This spec does not redesign the layer model.

This spec does not replace the skills as the executable workflow surface.

This spec does not add a new planning layer.

This spec does not require rewriting the existing skill logic unless a small
cross-link or wording alignment improves clarity.

This spec does not turn planning docs into a heavyweight process manual.

## Recommended Design

Add or reshape one concise operating-system document as the front door for the
planning lifecycle.

Recommended outcome:

- keep `docs/operating_system/planning-dispatch.md` as the canonical guide, but
  expand or restructure it so the lifecycle is explicit from the start

Alternative acceptable outcome:

- add a new `docs/operating_system/planning-lifecycle.md` and let
  `planning-dispatch.md` remain the narrower triage-focused companion

Recommendation:

- prefer evolving `planning-dispatch.md` unless the content becomes awkward
  enough that a separate front-door guide is cleaner

The key requirement is not the filename. It is having one plainly readable
operating-system doc that answers:

1. where work starts
2. how the layer is classified
3. when triage is required
4. when a spec is needed
5. when a plan is needed
6. which skills/docs carry the next step

## Canonical Lifecycle To State Plainly

The guide should make this flow explicit:

1. Start with the owning source layer:
   - `docs/intent/` for project what-and-why
   - `docs/operating_system/` for repo method/governance
   - feature or stage source only when the work is feature- or stage-owned
2. Classify the work as:
   - `intent`
   - `operating_system`
   - `workstream`
   - `change`
3. Produce triage
4. Decide whether design is settled enough:
   - unsettled -> spec first
   - settled and non-trivial -> implementation plan
5. Write the spec under `docs/superpowers/specs/` when needed
6. Write the implementation plan under `docs/superpowers/plans/`
7. Execute only after the plan is approved or explicitly requested for direct
   execution

This does not need to be verbose. It just needs to be unmistakable.

## Relationship To Existing Skills

The guide should cross-link the current skill roles rather than duplicate all
their detail:

- `brainstorming`
  - design exploration
  - spec writing
- `planning-dispatch`
  - layer classification
  - triage block
  - routing decision
- `writing-plans`
  - implementation plan creation
- `executing-plans`
  - plan execution

The operating-system doc should explain the flow.
The skills should continue to encode the detailed working instructions.

## Documentation Shape

The guide should stay short and structured.

Recommended sections:

- Purpose
- Lifecycle Summary
- Owning Source First
- Four Layers
- Triage Gate
- When To Write A Spec
- When To Write A Plan
- Skill Handoff Map
- Anti-Patterns

## Why This Is Worth Doing

This is a documentation clarity improvement, not a workflow invention.

Benefits:

- easier onboarding for humans
- less ambiguity when deciding whether to start from intent, operating-system,
  feature, or stage
- less reliance on skill files as the only readable explanation of the process
- clearer repo-level source for future validator, guide, or training work

## Documentation Updates

At minimum:

- update `docs/operating_system/planning-dispatch.md` or add a new lifecycle
  guide there
- lightly cross-link from `docs/operating_system/repo-governance.md`

Optional light updates:

- add a one-line alignment note in the relevant skill docs if the wording needs
  to match the new canonical operating-system explanation more closely

## Recommendation

Use the smallest good move:

1. make one operating-system doc the canonical planning-lifecycle explainer
2. keep it concise and front-door oriented
3. cross-link the existing skills instead of rewriting them into prose

That gives the repo one clear answer to the user’s question without creating a
second competing process system.

## Acceptance Criteria

- one operating-system doc plainly states the lifecycle from owning source
  through triage, spec, and implementation plan
- the doc makes the `intent | operating_system | workstream | change` layer
  model explicit
- the doc explains when a spec is needed versus when a plan can follow triage
  directly
- `repo-governance.md` points to that lifecycle guide
- the skill layer and operating-system docs no longer feel like separate
  stories about planning
