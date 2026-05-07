---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/operating_system/prompt_templates/
  - docs/intent/workstream-coverage-and-progress-guide.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/governance/repo-governance.md
related_features: []
related_stages: []
---

# Parallel Bounded Change Planning Prompt Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a dedicated prompt template that helps users decide how to split bounded change threads for safe parallel execution.
Reasoning: The repo now states that bounded change threads are the safe unit of parallel execution, but it does not yet have a practical user-facing prompt for deciding what can run in parallel, what should stay sequential, and how to avoid shared-surface collisions.
Invariants:

- The prompt should reason about bounded change threads, not vague broad workstreams.
- It should distinguish independent slices from dependency-coupled slices.
- It should make shared surface and ownership risk explicit.
- It should preserve the `operating_system` branch where relevant.
- It should remain short and copyable.

Dependencies:

- `docs/operating_system/prompt_templates/`
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

The repo now has clearer planning layers:

- master roadmap
- registered workstreams
- bounded change threads
- specs and plans

And it now states that bounded change threads are the safe unit of parallel
execution.

But users still lack a practical prompt for the actual decision:

`Given this workstream or set of bounded changes, what can run in parallel safely, what should stay sequential, and how should ownership be split?`

Without a dedicated prompt, parallel execution is easy to get wrong:

- multiple slices may touch the same source-of-truth surfaces
- broad workstream intent may be mistaken for a parallelizable task list
- dependency-coupled work may be split too early
- work that belongs in `operating_system` may be bundled with product work

## Goal

Add a dedicated prompt for:

`bounded change set -> dependency/shared-surface review -> safe parallel lanes -> next execution artifacts`

## Non-Goals

This spec does not add automatic dependency analysis.

This spec does not replace specs or implementation plans.

This spec does not guarantee that all suggested lanes must be run in parallel.

This spec does not encourage parallelism for its own sake.

## Recommended Design

Add a new prompt template:

`docs/operating_system/prompt_templates/parallel-bounded-change-planning-prompt.md`

### Suggested Prompt Shape

The prompt should collect:

- workstream or branch in scope
- bounded change threads in scope
- known shared docs/code surfaces
- known dependencies
- whether the goal is:
  - parallel execution recommendation
  - ownership split
  - sequencing decision

### Suggested Prompt Responsibilities

The prompt should ask the agent to:

1. identify which bounded change threads are truly independent
2. identify shared surfaces and dependency risks
3. recommend what can run in parallel and what should stay sequential
4. recommend ownership boundaries
5. recommend the next artifacts, such as separate specs/plans or one shared
   plan with parallel lanes

## Suggested Expected Output

The prompt should aim for:

- recommended parallel lanes
- sequencing warnings
- shared-surface risks
- ownership boundaries
- next artifact recommendations

## Proposed README / Guidance Updates

The prompt-pack README should describe this as the right prompt when the user
already has bounded change candidates and wants help parallelizing safely.

The workstream coverage/progress guide and planning docs should point to it as
the practical prompt for the "bounded changes are the safe parallel unit" rule.

## Acceptance Criteria

- A dedicated parallel bounded-change planning prompt exists.
- The prompt clearly distinguishes safe parallel lanes from dependency-coupled work.
- The prompt makes shared surface risks explicit.
- The prompt-pack README and nearby planning/governance docs point users to it.

## Risks

If the prompt is too generic, it will blur back into ordinary planning.

If it is too optimistic about parallelism, it will encourage collisions.

If it does not check shared surfaces explicitly, it will miss the main failure
mode.

## Recommendation

Add the prompt. The repo now has the right vocabulary for safe parallelism, and
this prompt would turn that governance rule into a practical execution aid.
