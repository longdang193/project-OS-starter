---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - scripts/validator_policy.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/README.md
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Mode A Outgrown-Threshold Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Add a second warning tier that detects when a `starter_method_only` repo has likely outgrown lightweight anchors and should plan migration to `managed_architecture_metadata`.
Reasoning: The current Mode A warnings now say the maturity ladder out loud, but they still only catch missing lightweight anchors. The starter should also help detect the next state: when a repo already has enough durable product surface that staying in Mode A is becoming process debt rather than a healthy lightweight choice.
Invariants:

- `starter_method_only` remains a valid early-stage mode.
- Existing missing-anchor warnings remain warning-only.
- The outgrown-threshold signal is still warning-only in this phase.
- Migration to `managed_architecture_metadata` remains deliberate, never automatic.
- The validator should use objective heuristics rather than subjective “feels mature” guesses.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `scripts/validator_policy.py`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/project_templates/mode-a/README.md`
- `tests/test_validate_adoption_shape.py`

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
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter now expresses this ladder:

`starter_method_only -> lightweight anchors -> managed_architecture_metadata`

That fixed an important guidance gap, but there is still a robustness gap:

- the validator can say “you need `docs/features/README.md`”
- it cannot yet say “this repo has likely outgrown lightweight anchors”

So a repo can remain in a long-lived middle state:

1. it has real runtime surface
2. it added the minimum anchor docs
3. it still avoids managed feature/stage structure indefinitely
4. the starter has no stronger signal that migration should be planned

That weakens the starter as a lifecycle guide.

## Goal

Teach `project-OS-starter` to emit a second-stage warning when a Mode A repo
looks mature enough that migration planning toward
`managed_architecture_metadata` should begin.

## Non-Goals

This spec does not auto-switch adoption modes.

This spec does not make outgrown-threshold findings hard errors.

This spec does not require full feature inference or auto-generated feature IDs.

This spec does not require managed metadata in every moderately sized repo.

This spec does not redesign the managed architecture system itself.

## Recommended Design

Add a new warning-only pass after the existing lightweight-anchor checks in
`validate_starter_method_only()`.

This pass should answer:

- “This repo may have outgrown Mode A as a steady-state operating mode.”

It should not answer:

- “You are already invalid.”

## Maturity Model

### Tier 1: Missing lightweight anchors

Current behavior:

- warn when the repo has meaningful runtime/API surface but lacks lightweight
  doc anchors

This remains the first threshold.

### Tier 2: Outgrown lightweight anchors

New behavior:

- warn when the repo already has lightweight anchors or equivalent prose homes,
  but the runtime/product surface looks durable enough that planning migration
  to `managed_architecture_metadata` is now the healthier path

This second-tier warning should explicitly say:

- Mode A is no longer obviously wrong
- but it now appears underspecified for the repo’s size and complexity

## Phase 1 Heuristics

Start with objective file-tree signals only.

Possible signals:

- many runtime code files under `src/` or `app/`
- multiple top-level runtime modules or subdomains
- multiple workflow/orchestration scripts
- multiple interface surfaces
- tests spread across multiple runtime areas
- existing lightweight anchors already present, which means the repo has crossed
  the first threshold and still kept growing

The heuristic should be additive, not single-signal.

Example model:

- require non-trivial runtime surface
- require a higher file-count threshold than the current lightweight-anchor rule
- require at least one “breadth” signal such as multiple subdirectories or both
  runtime and API/workflow evidence

## Warning Shape

Good warning:

- “Mode A repo appears to have outgrown lightweight anchors.”
- “Plan migration to `managed_architecture_metadata` so durable product features
  and stages can move into managed source and generated contract surfaces.”

Bad warning:

- “Switch now.”
- “You are invalid.”
- “Create feature.source.yaml immediately.”

## Documentation Shape

Mode A docs should say:

- lightweight anchors are a waypoint
- some repos can remain in Mode A for a while
- once complexity crosses the outgrown threshold, the intended next move is to
  plan migration to `managed_architecture_metadata`

## Policy Placement

Keep thresholds and file-signal rules in `scripts/validator_policy.py`.

Keep orchestration and finding emission in `scripts/validate_adoption_shape.py`.

## Acceptance Criteria

1. Small starter-only repos remain clean.
2. Repos with only the first-threshold signal still get only lightweight-anchor warnings.
3. Repos with stronger mature-surface signals get an additional warning that they appear to have outgrown lightweight anchors.
4. The new warning explicitly names `managed_architecture_metadata` as the intended next planning target.
5. No hard errors are introduced in this pass.

## Recommendation

Implement this as a warning-only Phase 1 maturity gate.

That would make `project-OS-starter` more robust in the way you want: not only
checking structure, but helping repos recognize when their current adoption mode
is starting to lag behind the reality of the project.
