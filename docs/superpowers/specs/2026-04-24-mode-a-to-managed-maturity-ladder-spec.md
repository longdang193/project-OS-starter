---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - scripts/validator_policy.py
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/README.md
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Mode A To Managed Maturity Ladder Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Make the `starter_method_only -> managed_architecture_metadata` maturity path explicit in validator warnings and Mode A guidance.
Reasoning: The current Mode A warning layer correctly detects missing lightweight anchors, but it undersells the intended destination. A growing repo can read the current guidance as "add `docs/features/README.md` and stop," even though the intended mature target is migration to managed architecture metadata.
Invariants:

- `starter_method_only` remains a valid lightweight starting mode.
- `docs/features/README.md` remains a useful early discoverability anchor.
- The mature destination for repos with durable product feature surface is `managed_architecture_metadata`.
- The validator should guide migration without silently auto-promoting the repo.
- Warning text should describe a maturity ladder, not a dead-end minimum.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `scripts/validator_policy.py`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`
- `docs/project_templates/mode-a/README.md`

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
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current Mode A warning layer fixes one real gap:

- it warns when a repo has meaningful runtime/product surface but lacks
  `docs/features/README.md`

But it creates a new ambiguity:

- it sounds like `docs/features/README.md` may be the full answer

That is not the intended lifecycle.

The intended lifecycle is:

1. start in `starter_method_only`
2. add lightweight discoverability anchors as the repo grows
3. migrate to `managed_architecture_metadata` once the repo has durable product
   feature/stage surface

Without that explicit ladder:

- users may stop at the lightweight anchor
- Mode A docs can read as a stable long-term destination for mature product repos
- validator guidance can feel underpowered relative to the actual governance intent

## Goal

Make the maturity ladder explicit in both validator messaging and Mode A docs:

`starter_method_only -> lightweight anchors -> managed_architecture_metadata`

## Non-Goals

This spec does not make the migration automatic.

This spec does not convert the current Mode A warnings into hard errors.

This spec does not require feature-name inference or immediate creation of
managed feature folders.

This spec does not collapse the distinction between Mode A and managed mode.

## Recommended Design

Keep the current lightweight-anchor warnings, but reframe them as stage-1
guidance rather than the final recommendation.

### Validator message shape

When Mode A detects missing `docs/features/README.md`, the warning should say
both things:

- what to do now:
  - add `docs/features/README.md`
- what this means longer term:
  - treat this as a migration signal toward `managed_architecture_metadata`
    once the repo has durable feature surface

Likewise for `docs/api.md`:

- add the doc now
- but do not imply that Mode A is the permanent mature end-state for an API-rich
  product repo

### Documentation shape

Mode A docs should say plainly:

- `starter_method_only` is a valid starting state
- lightweight anchors are the first discoverability step
- once the project has durable product features, stages, or interfaces, the
  target state is migration to `managed_architecture_metadata`

### Optional future threshold

This spec only clarifies the ladder.

A future pass may add a stronger maturity warning such as:

- "This repo appears to have outgrown lightweight anchors and should schedule a
  move to `managed_architecture_metadata`."

That stronger heuristic is intentionally separate from this wording pass.

## Proposed Text Direction

Good wording:

- "Add `docs/features/README.md` now as the lightweight feature index."
- "Treat this as an early migration signal toward `managed_architecture_metadata`
  once the repo has durable feature surface."

Bad wording:

- "Add `docs/features/README.md`" with no lifecycle context
- "switch modes later" with no statement that managed mode is the intended
  mature destination

## Acceptance Criteria

1. The Mode A feature-index warning explicitly names `managed_architecture_metadata`
   as the intended mature destination.
2. The Mode A API-doc warning no longer reads like a permanent steady-state
   answer for mature repos.
3. Mode A docs explicitly describe lightweight anchors as a waypoint, not the
   final maturity target.
4. The docs state the ladder plainly:
   `starter_method_only -> lightweight anchors -> managed_architecture_metadata`.
5. No new hard errors are added in this pass.

## Recommendation

Implement this as a small wording and guidance pass first.

That gives the repo a clearer maturity story immediately, without overreaching
into a second heuristic-enforcement phase before the language is settled.
