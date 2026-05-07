---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - docs/intent/master-workstream-roadmap.md
  - docs/operating_system/skill-planning-dispatch.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/prompt_templates/
  - docs/superpowers/specs/
  - docs/superpowers/plans/
related_features: []
related_stages: []
---

# Master Roadmap Alignment Guidance Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Strengthen the repo guidance so downstream specs, plans, prompts, and planning docs explicitly align work to the master roadmap or clearly state why they do not.
Reasoning: The repo now has a master workstream roadmap and upstream intent structure, but the “follow the master roadmap” rule is still implied more than expressed. Stronger alignment guidance would reduce drift, make downstream artifacts easier to audit, and help users and agents explain why a change exists.
Invariants:

- `docs/intent/master-workstream-roadmap.md` remains the top-down bridge from intent into durable product workstreams.
- `operating_system` remains a parallel branch, not a fake product workstream.
- Downstream artifacts should derive from upstream intent and roadmap truth rather than re-entering purpose locally.
- Guidance should become clearer before validator enforcement is considered.
- It must remain possible to say `parent_workstream: none` for true operating-system work.

Dependencies:

- `docs/intent/master-workstream-roadmap.md`
- `docs/operating_system/skill-planning-dispatch.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/prompt_templates/`

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
  - `docs/operating_system/skill-planning-dispatch.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/prompt_templates/`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo already says:

- start from the owning source
- when starting from intent, check the master roadmap
- route into workstream or operating-system branches

But the current contract is still soft:

1. users can ask for specs or plans without naming the roadmap thread
2. prompts do not consistently ask for roadmap alignment
3. specs and plans have `parent_workstream`, but the docs do not strongly say
   when and how that should reflect the master roadmap
4. downstream changes can still drift from the original intent because the link
   back upward is implicit rather than explicit

## Goal

Make roadmap alignment an explicit part of repo guidance:

- prompts should ask for it
- planning docs should require people to think about it
- specs and plans should explain it

without turning it into validator-enforced bureaucracy yet.

## Non-Goals

This spec does not add validator enforcement.

This spec does not require every operating-system change to map to a product
workstream.

This spec does not redesign the master roadmap itself.

This spec does not require changing historical artifacts retroactively.

## Recommended Design

Strengthen guidance in three places:

### 1. Planning docs

Update planning guidance so it says explicitly:

- when work is product-direction work, name the relevant roadmap thread
- when work is operating-system work, say why `parent_workstream: none` is
  appropriate
- downstream artifacts should explain how they follow the roadmap or why they
  deliberately do not

### 2. Prompt templates

Update prompt templates so they ask the user/agent to name:

- the roadmap thread this work serves
- or why this is operating-system work outside a product workstream

This should apply especially to:

- `spec-prompt.md`
- `plan-prompt.md`
- `execute-prompt.md`
- `mode-migration-prompt.md`

### 3. Spec/plan expectations

Clarify in the operating-system docs that:

- `parent_workstream` is not just metadata filler
- it should reflect the roadmap thread when one exists
- `none` should be explicit and meaningful, not a default shrug

## Proposed Guidance Language

Good guidance:

- “Name the roadmap thread this work follows, or explain why it belongs to the operating-system branch.”
- “Downstream specs and plans should make roadmap alignment explicit rather than assuming it.”

Bad guidance:

- “Use parent_workstream if helpful.”
- “Check the roadmap” with no expectation that the downstream artifact records the result

## Acceptance Criteria

1. Planning docs explicitly instruct users and agents to align work to the master roadmap.
2. Prompt templates ask for roadmap-thread alignment or an operating-system justification.
3. The repo explains that `parent_workstream: none` is valid but should be intentional.
4. The guidance is stronger and clearer without adding validator enforcement yet.

## Recommendation

Implement this as a guidance-first pass.

That gives the repo a stronger “follow the master roadmap” discipline now,
while leaving room to add validator-backed enforcement later if the roadmap
taxonomy proves stable enough.
