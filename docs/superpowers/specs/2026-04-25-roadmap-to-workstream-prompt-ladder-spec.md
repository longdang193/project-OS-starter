---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/
related_features: []
related_stages: []
---

# Roadmap-To-Workstream Prompt Ladder Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Extend the prompt-template pack so users can guide agents from the master workstream roadmap into specific workstreams before moving into specs, plans, and execution.
Reasoning: The repo now has a stronger upstream planning structure, including a master roadmap and a real workstream registry, but the prompt pack still starts too far downstream. Users can ask for a spec or plan, yet still miss the earlier step of turning roadmap intent into the right workstream thread. A dedicated upstream prompt ladder would make the process easier to follow and reduce drift from the master roadmap.
Invariants:

- Prompt templates should reinforce the existing planning lifecycle rather than invent a second workflow.
- `docs/intent/master-workstream-roadmap.md` remains the overview source, not a prompt surface.
- `docs/intent/workstreams/` remains the canonical registry for named workstreams.
- Prompt templates should help users choose between `workstream` and `operating_system`, not force everything into product workstreams.
- Prompt templates should stay short, copyable, and human-usable.

Dependencies:

- `docs/operating_system/prompt_templates/`
- `docs/operating_system/skill-planning-dispatch.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/intent/master-workstream-roadmap.md`
- `docs/intent/workstreams/`

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

The prompt pack is now useful, but it still begins in the middle of the
planning ladder.

Today, users have prompts for:

- intent capture
- spec drafting
- implementation planning
- execution
- validation / drift
- mode migration

What is still underspecified is the upstream bridge:

- how to go from the master roadmap into a specific workstream
- how to decide whether work belongs to a registered workstream or to
  `operating_system`
- how to ask for the “next spec under this workstream” rather than a free-
  floating spec

That leaves a usability gap:

1. users may skip the roadmap and jump straight to spec
2. users may choose the wrong workstream or invent an unregistered one
3. users may force operating-system work into a product workstream
4. downstream specs and plans may still drift from the master roadmap even if
   the repo now has stronger registry validation

## Goal

Extend the prompt-template pack so users can naturally move through:

`master workstream roadmap -> specific workstream -> spec -> plan -> execution`

while preserving the parallel `operating_system` branch when that is the right
classification.

## Non-Goals

This spec does not add validator enforcement for prompt usage.

This spec does not replace the existing prompt pack.

This spec does not make the master roadmap itself more detailed.

This spec does not require every request to start from the roadmap when a later
artifact already exists.

## Recommended Design

Add a small upstream extension to the existing prompt pack.

### New Prompt Templates

#### 1. `roadmap-to-workstream-prompt.md`

Use when a user has project intent or a roadmap thread and wants help turning it
into the right workstream.

Expected outcome:

- confirm whether the work belongs to a product workstream or
  `operating_system`
- identify the best matching existing workstream if one exists
- recommend whether to refine an existing workstream or add a new one

#### 2. `workstream-to-spec-prompt.md`

Use when a user already knows the relevant workstream and wants the next spec
that should advance it.

Expected outcome:

- anchor the work to a registered workstream id
- identify the bounded problem to solve next
- draft the next spec in the right layer and scope

#### 3. `workstream-alignment-review-prompt.md`

Use when a user wants to check whether a proposed change actually belongs to the
named workstream.

Expected outcome:

- confirm fit with the workstream
- suggest a different workstream if needed
- recommend `parent_workstream: none` if the work is truly
  `operating_system`

#### 4. `roadmap-gap-prompt.md`

Use when a user thinks the master roadmap may be missing a durable thread.

Expected outcome:

- identify whether the gap is a real new workstream, a refinement of an
  existing one, or an operating-system concern
- recommend the next doc artifact to add

### Existing Prompt Updates

Update the prompt-pack README and the downstream prompt templates so they point
to the upstream ladder plainly:

- start from roadmap/workstream prompts when the user is still choosing the
  thread
- use spec/plan prompts only once the thread is known

## Proposed Lifecycle Wording

The prompt-pack README should describe the ladder explicitly:

1. use `intent-prompt.md` when purpose is still unclear
2. use `roadmap-to-workstream-prompt.md` when translating intent into a durable
   thread
3. use `workstream-to-spec-prompt.md` when choosing the next design slice
4. use `plan-prompt.md` once a spec is approved
5. use `execute-prompt.md` when a plan already exists
6. use `validate-or-drift-prompt.md` and `mode-migration-prompt.md` for upkeep

## Acceptance Criteria

- The prompt pack includes upstream prompts for roadmap/workstream decisions.
- The prompt-pack README explains when to use the upstream prompts versus the
  downstream prompts.
- Planning/governance docs point users to the roadmap-aware prompt ladder.
- The prompt wording preserves the `workstream` vs `operating_system`
  distinction instead of flattening everything into product workstreams.

## Risks

If the prompt pack becomes too large, users may ignore it instead of using it.

If the new prompts are too abstract, they will not actually help users choose
the right next step.

If the prompts do not clearly preserve `operating_system`, they could encourage
bad classification.

## Recommendation

Add the upstream prompt ladder now, while the workstream registry is still new.
That keeps the user-facing guidance in sync with the stronger roadmap and
`parent_workstream` structure we just added.
