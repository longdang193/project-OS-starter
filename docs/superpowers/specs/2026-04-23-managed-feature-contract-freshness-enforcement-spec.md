---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/lifecycle/feature-lifecycle.md
  - docs/superpowers/specs/2026-04-22-feature-contract-freshness-metadata-spec.md
  - docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md
related_features: []
related_stages: []
---

# Managed Feature Contract Freshness Enforcement Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Tighten managed-mode validation so generated feature contracts always require `revision`, `latest_change_id`, and `last_updated_at`.
Reasoning: The current validator only requires generated feature-contract freshness metadata when `lineage.generated.yaml` has a non-empty timeline. This lets managed repos pass validation even when generated contracts omit the freshness triplet and carry older generator output shapes.
Invariants:

- `docs/features/<feature_id>/<feature_id>.yaml` remains a generated current-state contract, not a human-owned source.
- Freshness metadata belongs in the generated feature contract, not `feature.source.yaml`.
- Managed-mode validation should enforce the current generated contract shape rather than treating older generated output as coequal.
- Empty `timeline: []` must not be a loophole that allows stale generated feature contracts to pass.
- The validator should check schema presence and field types; it does not need to prove the semantic correctness of the chosen change ID or timestamp.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/lifecycle/feature-lifecycle.md`

Affected stages:

- none directly

Affected features:

- all managed generated feature contracts at `docs/features/<feature_id>/<feature_id>.yaml`

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: all managed generated feature contracts
- feature_lineage: none
- feature_history: none
- cross_cutting_docs:
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/lifecycle/feature-lifecycle.md`
  - `docs/superpowers/specs/2026-04-22-feature-contract-freshness-metadata-spec.md`
  - `docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md`
- generated: none in the starter repo

Generated refresh required: no for starter changes; yes for downstream managed repos that currently omit freshness metadata.
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter validator already knows the generated feature-contract freshness
fields:

- `revision`
- `latest_change_id`
- `last_updated_at`

However, the current enforcement has a loophole. It validates the field types
only when freshness fields are present, and it requires the full freshness set
only when the sibling `lineage.generated.yaml` contains a non-empty `timeline`.

That means this managed-mode shape passes validation:

```yaml
# GENERATED FILE - do not edit directly.
feature_id: admin_control_plane_core
name: Admin Control Plane Core
status: active
type: add
summary: Internal admin UI and REST API to manage FitCV pipeline runs without terminal access.
invariants: []
domains: []
depends_on: []
capabilities: []
refs:
  code: []
  tests: []
  specs: []
  plans: []
  docs: []
  configs: []
  components: []
```

when its sibling lineage file contains:

```yaml
timeline: []
```

Observed drift:

- `JOB-PROJECT/docs/features/admin_control_plane_core/admin_control_plane_core.yaml`
  omits the freshness triplet.
- Most JOB-PROJECT generated feature contracts omit the freshness triplet.
- The validator reports `Adoption shape validation passed`.

Accepted target example:

- `customer-churn-prediction-azureml/docs/features/workspace-bootstrap/workspace-bootstrap.yaml`
  includes `revision`, `latest_change_id`, and `last_updated_at`.

## Goal

Make freshness metadata a required part of every managed generated feature
contract validated by `scripts/validate_adoption_shape.py`.

In managed mode, every `docs/features/<feature_id>/<feature_id>.yaml` should
include:

```yaml
revision: <integer>
latest_change_id: <non-empty string>
last_updated_at: <non-empty string>
```

This should be true even when `lineage.generated.yaml` has `timeline: []`.

## Non-Goals

This spec does not require manually editing generated feature contracts.
Downstream repos should regenerate contracts from the owning generator.

This spec does not require the validator to infer the correct revision number,
change ID, or timestamp.

This spec does not move freshness metadata into `feature.source.yaml`.

This spec does not change the rich timeline schema for
`lineage.generated.yaml`.

This spec does not make `customer-churn-prediction-azureml` itself the
validator baseline; it only uses that repo as the desired generated-contract
shape example.

## Validator Rule

Update `validate_generated_feature_contract_schema()` so missing freshness
fields are always an error for managed generated feature contracts.

Current behavior to remove:

- freshness fields are only type-checked if any freshness key is present
- missing freshness fields are only rejected when lineage timeline is non-empty

Target behavior:

- compute `missing_freshness = FEATURE_CONTRACT_FRESHNESS_KEYS.difference(payload)`
- emit an error if `missing_freshness` is non-empty
- require `revision` to be an integer
- require `latest_change_id` and `last_updated_at` to be non-empty strings

Suggested error:

```text
Generated feature contract is missing required freshness metadata.
```

Suggested fix:

```text
Regenerate the contract so revision, latest_change_id, and last_updated_at are emitted.
```

## Regression Tests

Add tests for:

- a managed generated feature contract with `timeline: []` and no freshness
  fields fails validation
- a managed generated feature contract with all three freshness fields passes
  the freshness check
- partial freshness metadata fails, for example `revision` present but
  `latest_change_id` missing
- incorrect freshness types fail:
  - `revision` is not an integer
  - `latest_change_id` is empty
  - `last_updated_at` is empty

The first test should mirror the JOB-PROJECT drift class directly:

```yaml
timeline: []
```

must not suppress the generated-contract freshness requirement.

## Documentation Updates

Update starter guidance to remove the soft conditional wording that makes the
freshness triplet sound optional for current managed generated contracts.

Docs should say:

- managed generated feature contracts require `revision`,
  `latest_change_id`, and `last_updated_at`
- those fields are generated current-state metadata
- those fields do not belong in `feature.source.yaml`
- repos that omit them have older generated contract output and should
  regenerate or update their generator
- `timeline: []` does not exempt a managed generated contract from the
  freshness schema

Docs to align:

- `docs/operating_system/adoption/project-adoption-migration-guide.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/lifecycle/feature-lifecycle.md`
- `docs/superpowers/specs/2026-04-22-feature-contract-freshness-metadata-spec.md`
- `docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md`

## Downstream Migration Note

After this validator change, downstream managed repos like JOB-PROJECT should
fail validation until their architecture generator emits freshness metadata for
all generated feature contracts.

That failure is desirable. It identifies older generated output that should be
regenerated or brought forward to the current managed contract.

## Acceptance Criteria

This spec is complete when:

- a new implementation plan exists for the validator and docs changes
- validator tests cover the `timeline: []` loophole
- `scripts/validate_adoption_shape.py` rejects managed generated feature
  contracts missing any freshness key
- starter guidance consistently describes the freshness triplet as required for
  managed generated feature contracts
- the starter validator still passes its focused test suite after the rule is
  tightened
