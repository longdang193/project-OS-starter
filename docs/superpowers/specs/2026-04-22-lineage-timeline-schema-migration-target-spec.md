---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/feature-lifecycle.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - tools/docs/generate_architecture_metadata.py
  - scripts/validate_adoption_shape.py
  - tests/test_architecture_metadata_generation.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Lineage Timeline Schema Migration Target Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Make the richer `lineage.generated.yaml > timeline` entry schema explicit and validator-enforced as the migration target for managed repos.
Reasoning: Some downstream repos still emit older `timeline` entries as simple `{kind, path}` pairs, while newer repos such as `customer-churn-prediction-azureml` emit richer completed-change records derived from plan metadata. The starter currently says timeline is fed from completed-plan metadata, but it does not yet make the richer entry schema explicit enough or validator-enforced.
Invariants:

- `lineage.generated.yaml` remains a generated artifact, never a hand-edited source.
- `timeline` remains a generated change-history view derived from completed-plan metadata.
- The canonical migration target is the richer timeline entry shape used by `customer-churn-prediction-azureml/docs/features/model-training-pipeline/lineage.generated.yaml`.
- Managed repos should not keep the older `{kind, path}` timeline entry shape once they adopt the current starter lineage contract.
- Validator and generator guidance should converge on one timeline schema instead of treating multiple shapes as equivalent.

Dependencies:

- `tools/docs/generate_architecture_metadata.py`
- `scripts/validate_adoption_shape.py`
- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`

Affected stages:

- none

Affected features:

- all managed feature folders with generated `lineage.generated.yaml` timelines

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: all managed `docs/features/*/lineage.generated.yaml`
- feature_history: none
- cross_cutting_docs:
  - `docs/operating_system/feature-lifecycle.md`
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
- generated:
  - feature-local `lineage.generated.yaml` files

Generated refresh required: yes
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

Two different `timeline` shapes are currently circulating under the same
artifact name.

Older shape:

```yaml
timeline:
  - kind: spec
    path: docs/superpowers/specs/...
  - kind: plan
    path: docs/superpowers/plans/...
```

Newer target shape:

```yaml
timeline:
  - completed_at: "2026-04-18T12:31:22+02:00"
    source_plan: docs/superpowers/plans/...
    change_id: 2026-04-18-example-change
    summary: Short change summary.
    capabilities:
      - feature-id.capability-slug
    verification:
      - pytest tests/test_example.py -q
    outcome: Short outcome summary.
```

The older shape is not just a compact variant. It loses key completed-change
meaning:

- when the change completed
- which plan it came from
- the stable change ID
- which capabilities the change touched
- what verification was run
- what outcome the change produced

That means downstream repos can technically have a `timeline` field while still
missing the actual richer history contract the starter model intends.

## Goal

Define one canonical timeline entry schema and make it the migration target for
managed repos.

The current target should match the richer timeline entries already used by
`customer-churn-prediction-azureml/docs/features/model-training-pipeline/lineage.generated.yaml`.

The validator should eventually reject the older `{kind, path}` entry shape in
managed mode.

## Non-Goals

This spec does not redesign feature-local `history.md`.

This spec does not replace top-level `timeline` with a second generated file.

This spec does not require every historical timeline entry to be retroactively
perfect if source plan metadata is missing; migration guidance may allow staged
refresh where needed.

This spec does not redefine capability lineage evidence outside the `timeline`
section.

## Canonical Timeline Entry Shape

The canonical `timeline` remains a list, but each entry should represent a
completed feature-relevant change record with this richer shape:

- `completed_at`
  - ISO-8601 timestamp
- `source_plan`
  - path to the completed implementation plan that generated the entry
- `change_id`
  - stable change identifier
- `summary`
  - short human-readable change summary
- `capabilities`
  - list of affected capability IDs, or an empty list when the change is
    feature-level but not capability-specific
- `verification`
  - list of verification commands or checks associated with the change
- `outcome`
  - short result summary

Example target:

```yaml
timeline:
  - completed_at: "2026-04-18T12:31:22+02:00"
    source_plan: docs/superpowers/plans/2026-04-18-12-31-example-plan.md
    change_id: 2026-04-18-example-change
    summary: Add architecture metadata generation pilot for feature capability lineage.
    capabilities:
      - feature-id.example-capability
    verification:
      - pytest tests/test_architecture_metadata_generation.py
      - python tools/docs/generate_architecture_metadata.py --check
    outcome: Generated contract, lineage, and discovery now refresh from completed-plan metadata.
```

## Explicitly Rejected Legacy Timeline Shape

The older entry shape should be treated as migration debt in managed repos:

```yaml
timeline:
  - kind: spec
    path: docs/superpowers/specs/...
  - kind: plan
    path: docs/superpowers/plans/...
```

That shape is allowed only as evidence of an older repo-local generator, not as
the current starter-aligned target.

## Documentation Changes

Update starter guidance so it says plainly:

- `timeline` is not just a list of referenced spec/plan paths
- the canonical target is a completed-change record list
- the churn repo timeline format is the concrete migration target
- older `{kind, path}` entries are superseded migration debt

The key docs to align are:

- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`

## Validator Direction

The validator should eventually enforce the richer entry schema in managed mode.

At minimum, planned enforcement should cover:

- `timeline` must remain a list
- each entry must be a mapping
- each entry must contain:
  - `completed_at`
  - `source_plan`
  - `change_id`
  - `summary`
  - `capabilities`
  - `verification`
  - `outcome`
- `completed_at` should be ISO-8601-like
- `capabilities` should be a list
- `verification` should be a list
- old `{kind, path}`-only entries should be rejected once the migration target
  is adopted

## Generator Direction

The generator should derive timeline entries from completed-plan metadata so the
feature-local lineage file exposes real change records rather than only a flat
ref list.

If source plan metadata is incomplete, the generator should make that gap
visible rather than silently collapsing back to the older shape.

## Acceptance Criteria

This spec is complete when:

- starter docs describe the richer timeline entry schema as the canonical target
- the churn repo timeline format is named as the concrete migration target
- the docs explicitly reject the older `{kind, path}` entry shape as the
  steady-state managed target
- follow-up implementation work can update the generator and validator against
  one clear timeline contract
