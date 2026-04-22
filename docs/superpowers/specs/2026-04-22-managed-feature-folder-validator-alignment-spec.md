---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/feature-lifecycle.md
  - docs/operating_system/doc-system-lifecycle.md
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Managed Feature Folder Validator Alignment Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Close the gap between managed-feature folder guidance and validator enforcement by requiring `history.md` and the concrete generated feature contract in managed mode.
Reasoning: The current starter guidance says an opted-in managed feature folder should include `feature.source.yaml`, `<feature_id>.yaml`, `lineage.generated.yaml`, and `history.md`, but the validator currently enforces only part of that contract. This leaves room for downstream repos and agents to produce incomplete managed feature folders while still passing validation.
Invariants:

- Managed feature folders remain source-plus-generated bundles, not loose collections of optional files.
- `feature.source.yaml` remains the human-owned semantic source.
- `docs/features/<feature_id>/<feature_id>.yaml` remains the concrete generated current-state contract.
- `lineage.generated.yaml` remains the generated evidence-oriented lineage artifact.
- `history.md` remains the required human-readable chronology surface for opted-in managed features.
- Validation should fail on missing required managed-folder artifacts instead of relying on prose guidance alone.

Dependencies:

- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/doc-system-lifecycle.md`
- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`

Affected stages:

- none

Affected features:

- all downstream managed feature folders in `managed_architecture_metadata` mode

Primary lens: cross-cutting

Affected docs:

- feature_source: managed `docs/features/*/feature.source.yaml`
- feature_yaml: managed `docs/features/*/<feature_id>.yaml`
- feature_lineage: managed `docs/features/*/lineage.generated.yaml`
- feature_history: managed `docs/features/*/history.md`
- cross_cutting_docs:
  - `docs/operating_system/feature-lifecycle.md`
  - `docs/operating_system/doc-system-lifecycle.md`

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter currently has a contract mismatch:

- guidance describes a concrete managed feature folder shape
- validator enforcement only checks a subset of that shape

Today, in managed mode, `scripts/validate_adoption_shape.py` requires:

- `feature.source.yaml`

and only warns or omits enforcement for:

- missing `lineage.generated.yaml`
- missing `<feature_id>.yaml`
- missing `history.md`

That produces two forms of drift:

1. starter guidance overpromises what the validator guarantees
2. downstream repos can pass validation with partially migrated managed feature folders

## Goal

Make managed-mode validation match the documented managed feature folder contract.

For every managed feature folder under `docs/features/<feature_id>/`, the validator should require:

- `feature.source.yaml`
- `<feature_id>.yaml`
- `lineage.generated.yaml`
- `history.md`

Missing any of those files in `managed_architecture_metadata` mode should be a validation error.

## Non-Goals

This spec does not redesign feature source schema fields.

This spec does not change the lineage schema beyond its required presence.

This spec does not require feature-folder `README.md`; that file remains optional.

This spec does not change legacy-compatibility mode behavior except where messaging needs to remain clear.

## Desired Contract

The required managed feature folder shape is:

```text
docs/features/<feature_id>/
  feature.source.yaml
  <feature_id>.yaml
  lineage.generated.yaml
  history.md
```

Interpretation:

- `feature.source.yaml` is the human-owned source and must exist
- `<feature_id>.yaml` is the generated contract and must exist
- `lineage.generated.yaml` is the generated evidence surface and must exist
- `history.md` is the required history/notes surface and must exist
- `README.md` may exist when prose explanation adds value, but it is not part of the validator-required minimum

## Validation Changes

Update `scripts/validate_adoption_shape.py` so that managed mode:

- errors when a managed feature folder is missing `feature.source.yaml`
- errors when a managed feature folder is missing `<feature_id>.yaml`
- errors when a managed feature folder is missing `lineage.generated.yaml`
- errors when a managed feature folder is missing `history.md`

Validator messages should be explicit about the missing artifact and should tell the user whether to:

- create the missing source file, or
- regenerate the missing generated artifact, or
- add the required history file using the managed history pattern

`lineage.generated.yaml` presence should move from warning-level drift to required-contract enforcement.

## Documentation Changes

Update the operating-system docs so they stop sounding softer than the intended contract:

- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/doc-system-lifecycle.md`

The docs should describe the same required-vs-optional split the validator enforces:

- required: `feature.source.yaml`, `<feature_id>.yaml`, `lineage.generated.yaml`, `history.md`
- optional: `README.md`

The docs should also make clear that validation enforces the required set in managed mode.

## Test Changes

Add or update validator tests so managed mode fails when any required artifact is missing:

- missing `feature.source.yaml`
- missing `<feature_id>.yaml`
- missing `lineage.generated.yaml`
- missing `history.md`

Keep at least one passing managed-mode fixture that includes the full required folder shape.

## Rollout Notes

This is a tightening change, so downstream repos that adopted managed mode with incomplete feature folders may start failing validation.

That is acceptable and intended because the spec is closing a starter contract gap rather than inventing a new folder shape.

The fix path for downstream repos should be straightforward:

- add the missing `history.md`, or
- regenerate the missing contract/lineage files, or
- finish the managed-folder migration before claiming managed mode

## Acceptance Criteria

This spec is complete when:

- starter guidance explicitly states the validator-required managed feature folder shape
- `scripts/validate_adoption_shape.py` rejects missing `feature.source.yaml`, `<feature_id>.yaml`, `lineage.generated.yaml`, and `history.md` in managed mode
- `tests/test_validate_adoption_shape.py` covers each missing-artifact case
- the starter repo still passes its own validator after the change
