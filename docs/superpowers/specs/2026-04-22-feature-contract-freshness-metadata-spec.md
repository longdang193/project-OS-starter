---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/feature-lifecycle.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - tools/docs/generate_architecture_metadata.py
  - scripts/validate_adoption_shape.py
  - tests/test_architecture_metadata_generation.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Feature Contract Freshness Metadata Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Make generated feature-contract freshness metadata explicit and validator-directed as the migration target for managed repos.
Reasoning: Some managed repos still emit generated feature contracts without `revision`, `latest_change_id`, or `last_updated_at`, while newer repos such as `customer-churn-prediction-azureml` already include them. The starter docs currently describe those fields too softly as optional, which allows older generator shapes to keep looking aligned.
Invariants:

- `docs/features/<feature_id>/<feature_id>.yaml` remains a generated current-state contract, not a human-owned source.
- Freshness metadata remains generated from completed-plan metadata, never stored manually in `feature.source.yaml`.
- The canonical migration target is the richer generated contract shape used by `customer-churn-prediction-azureml/docs/features/notebook-hpo/notebook-hpo.yaml`.
- Managed repos using the current starter contract should not omit freshness metadata.
- Validator and generator guidance should converge on one feature-contract freshness contract instead of treating multiple shapes as equivalent.

Dependencies:

- `tools/docs/generate_architecture_metadata.py`
- `scripts/validate_adoption_shape.py`
- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`

Affected stages:

- none

Affected features:

- all managed feature contracts generated at `docs/features/<feature_id>/<feature_id>.yaml`

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: all managed `docs/features/*/<feature_id>.yaml`
- feature_lineage: none
- feature_history: none
- cross_cutting_docs:
  - `docs/operating_system/feature-lifecycle.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
- generated:
  - all generated feature contracts

Generated refresh required: yes
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

Two generated feature-contract shapes are currently being treated as if they are
equally acceptable:

1. the newer richer generated contract shape that includes freshness metadata
2. an older generated contract shape that omits freshness fields entirely

Current richer target example:

- `customer-churn-prediction-azureml/docs/features/notebook-hpo/notebook-hpo.yaml`

Freshness fields present in the target shape:

- `revision`
- `latest_change_id`
- `last_updated_at`

Current drift example:

- `JOB-PROJECT/docs/features/admin_control_plane_core/admin_control_plane_core.yaml`

That older shape still looks like a valid generated contract, but it loses
important current-state metadata about:

- which completed change most recently updated the contract
- what revision of the generated feature state the repo is on
- when the contract was last updated from completed-plan metadata

Because starter guidance currently says these fields "may" exist, agents and
repo-local generators can omit them without clearly violating the documented
target.

## Goal

Define freshness metadata as part of the canonical generated feature-contract
target for managed repos.

The current migration target should match the richer generated contract shape
already used in `customer-churn-prediction-azureml`.

## Non-Goals

This spec does not redesign the semantic body of `feature.source.yaml`.

This spec does not move freshness metadata into `feature.source.yaml`.

This spec does not move semantic authorship of freshness values to humans.
Downstream repos should update or rerun their generator rather than hand-editing
generated contracts.

This spec does not redefine feature-local lineage or history surfaces.

## Canonical Freshness Metadata

The generated contract at `docs/features/<feature_id>/<feature_id>.yaml` should
include:

- `revision`
  - generated revision indicator derived from completed plan history
- `latest_change_id`
  - stable identifier for the latest completed change reflected in the contract
- `last_updated_at`
  - generated timestamp for the latest completed change reflected in the
    contract

These fields are generated current-state metadata, not human-authored semantic
source.

## Ownership Boundary

Clarify the ownership split:

- `feature.source.yaml`
  - human-owned semantic source
- `<feature_id>.yaml`
  - generated assembled current-state contract, including freshness metadata
- `lineage.generated.yaml`
  - generated feature-local evidence and timeline surface

Do not store `revision`, `latest_change_id`, or `last_updated_at` manually in
`feature.source.yaml`.

## Explicit Migration Target

The canonical target should be stated plainly:

- repos migrating to the current starter-style managed contract should converge
  on the richer generated contract shape used by
  `customer-churn-prediction-azureml/docs/features/notebook-hpo/notebook-hpo.yaml`
- older generated contracts that omit freshness metadata are migration debt,
  not coequal steady-state outputs

## Documentation Changes

Update starter guidance so it says plainly:

- generated feature contracts should expose `revision`, `latest_change_id`, and
  `last_updated_at`
- those fields are the current migration target, not a nice-to-have
- those fields belong to the generated contract, not `feature.source.yaml`
- older generated contract shapes without those fields are migration debt
- `timeline: []` does not exempt a managed generated feature contract from the
  freshness schema

The key docs to align are:

- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`

## Validator Direction

The validator should eventually enforce this contract in managed mode.

At minimum, planned enforcement should cover:

- every managed generated feature contract should include:
  - `revision`
  - `latest_change_id`
  - `last_updated_at`
- those fields should not appear in `feature.source.yaml`
- managed repos should not claim current starter alignment while keeping older
  generated contract shapes that omit freshness metadata

This spec does not require immediate validator rollout, but it should make the
target explicit enough that follow-up enforcement is straightforward.

## Generator Direction

The generator should derive freshness metadata consistently across managed
repos. If completed-plan metadata is sparse or absent, the generator should
still emit the freshness fields from its best available generated-state inputs
rather than omitting the field family.

## Acceptance Criteria

This spec is complete when:

- starter docs describe `revision`, `latest_change_id`, and `last_updated_at`
  as the canonical generated-contract freshness fields
- the churn repo generated contract is named as the concrete migration target
- the docs explicitly say those fields belong in generated contracts rather than
  `feature.source.yaml`
- follow-up implementation work can update the generator and validator against
  one clear freshness-metadata contract
