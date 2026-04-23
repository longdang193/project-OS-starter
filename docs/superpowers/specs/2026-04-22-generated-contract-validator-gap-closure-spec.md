---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/feature-lifecycle.md
  - docs/operating_system/stage-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - scripts/validate_adoption_shape.py
  - tools/docs/generate_architecture_metadata.py
  - tests/test_validate_adoption_shape.py
  - tests/test_architecture_metadata_generation.py
  - tests/test_validate_repo_contracts.py
related_features: []
related_stages: []
---

# Generated Contract Validator Gap Closure Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Close the remaining gaps where starter-generated architecture artifacts have a clear canonical schema in generator/tests/docs, but `validate_adoption_shape.py` still does not enforce that schema.
Reasoning: The starter validator now meaningfully enforces managed feature-folder presence and rich `lineage.generated.yaml` shape, but several adjacent generated artifacts still rely on generator behavior or repo-contract validation rather than adoption-shape enforcement. This lets downstream repos keep older generated shapes while still appearing partially starter-aligned.
Invariants:

- Canonical truth still flows from human-owned source layers into generated contracts and generated discovery.
- Generated artifacts remain generated-only and must not become human-edited semantic sources.
- Starter guidance, generator output, and validator enforcement should converge on one schema per generated artifact.
- Managed repos should not treat older generated artifact shapes as coequal steady-state contracts once the current starter target is adopted.
- Repo-contract validation may still own cross-cutting wrapper/orchestration checks, but adoption-shape validation should enforce the core managed architecture artifact schemas.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `tools/docs/generate_architecture_metadata.py`
- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/stage-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`
- `tests/test_validate_adoption_shape.py`
- `tests/test_architecture_metadata_generation.py`

Affected stages:

- all managed `docs/stages/<stage_id>.yaml` contracts

Affected features:

- all managed `docs/features/<feature_id>/<feature_id>.yaml` contracts
- all managed `docs/features/<feature_id>/history.md` files

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: all managed generated feature contracts
- feature_lineage: none beyond already-enforced lineage schema
- feature_history: all managed feature `history.md`
- cross_cutting_docs:
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/operating_system/feature-lifecycle.md`
  - `docs/operating_system/stage-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
- generated:
  - `docs/stages/*.yaml`
  - `docs/generated/capability_lineage.yaml`
  - `docs/generated/architecture_dag.yaml`

Generated refresh required: yes
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter now has a split contract surface:

- generator/tests/docs define several generated artifact schemas clearly
- adoption-shape validation only enforces some of them

Current gaps:

1. generated stage contracts
2. generated feature contracts
3. feature `history.md` structure inside adoption-shape validation
4. generated discovery schemas under `docs/generated/*`

This creates a recurring drift pattern:

- a downstream repo keeps an older generated file shape
- the generator in a newer repo proves a richer target exists
- docs imply the newer shape is canonical
- but `validate_adoption_shape.py` does not reject the older file

Concrete example already observed:

- accepted target:
  - `customer-churn-prediction-azureml/docs/stages/data_prep.yaml`
- undetected drift:
  - `JOB-PROJECT/docs/stages/enrich.yaml`

The same class of gap also exists for generated feature contracts and generated
discovery, where the current starter generator emits a canonical shape but the
adoption validator mostly checks presence rather than structure.

## Goal

Make `validate_adoption_shape.py` enforce the remaining core generated-contract
schemas that define current managed adoption.

That means managed-mode validation should reject older generated artifact
shapes for:

- `docs/stages/*.yaml`
- `docs/features/<feature_id>/<feature_id>.yaml`
- malformed managed `history.md` boundary structure
- `docs/generated/capability_lineage.yaml`
- `docs/generated/architecture_dag.yaml`

## Non-Goals

This spec does not redesign the generator outputs themselves.

This spec does not move every repo-contract rule into adoption-shape
validation.

This spec does not require adoption-shape validation to reproduce every single
generator semantic cross-check.

This spec does not change `lineage.generated.yaml` again; that schema gap is
already addressed separately.

This spec does not require backfilling perfect historical generated artifacts
when the source metadata is genuinely absent; it only makes the current managed
target explicit and validator-enforced when those artifacts exist.

## Gap 1: Generated Stage Contract Schema

### Current canonical target

The generator and tests already define generated stage contracts as a flat
mapping like:

```yaml
stage_id: data_prep
name: Data preparation
status: active
purpose: ...
workflow_position: pre_training
depends_on: []
hands_off_to: []
inputs: []
outputs: []
feature_refs: []
capability_refs: []
code_refs: []
test_refs: []
doc_refs: []
config_refs: []
component_refs: []
human_notes: []
```

### Drift to reject

Older nested contracts like:

```yaml
enrich:
  name: Enrich
  summary: ...
  refs:
    docs: []
    spec: []
    plan: []
```

should be treated as migration debt, not current managed output.

### Validator direction

`validate_adoption_shape.py` should:

- validate generated header on `docs/stages/*.yaml`
- require a top-level mapping
- require `stage_id` and the flat generated keys
- reject nested `<stage_id>:` wrapper shapes
- require ref fields like `feature_refs`, `capability_refs`, `code_refs`,
  `test_refs`, `doc_refs`, `config_refs`, `component_refs` to be string lists
- optionally allow `human_notes`

## Gap 2: Generated Feature Contract Schema

### Current canonical target

Generated feature contracts already have a clearer canonical shape in generator
tests, including:

- `feature_id`
- `name`
- `status`
- `type`
- `summary`
- `invariants`
- `capabilities`
- `revision`
- `latest_change_id`
- `last_updated_at`
- `refs`

### Current gap

Managed-mode validation currently checks that `<feature_id>.yaml` exists, but
not that it is actually the canonical generated feature contract shape.

### Validator direction

`validate_adoption_shape.py` should:

- validate generated header on managed generated feature contracts
- require a top-level mapping
- require the core generated contract keys
- require `refs` to be a mapping of string-list ref families
- require freshness metadata fields to be present:
  - `revision`
  - `latest_change_id`
  - `last_updated_at`
- require freshness metadata fields to use the expected types

This spec does not require adoption-shape validation to infer the semantic
correctness of the revision number, latest change ID, or timestamp.

## Gap 3: Managed Feature History Structure

### Current canonical target

Managed feature `history.md` uses a partial-generated pattern:

- generated block between:
  - `<!-- GENERATED HISTORY START -->`
  - `<!-- GENERATED HISTORY END -->`
- human-owned section:
  - `## Human Notes`

### Current gap

Adoption-shape validation currently checks only that `history.md` exists. The
more detailed boundary validation lives under repo-contract validation.

### Validator direction

`validate_adoption_shape.py` should enforce the minimal managed history
structure for managed feature folders:

- file exists
- contains generated start marker
- contains generated end marker
- contains `## Human Notes`

This keeps adoption-shape validation aligned with the actual managed history
contract instead of treating any markdown file named `history.md` as valid.

## Gap 4: Generated Discovery Schema

### Current canonical target

The current managed generated discovery target is:

- `docs/generated/capability_lineage.yaml`
- `docs/generated/architecture_dag.yaml`

### Current gap

Adoption-shape validation currently only reasons loosely about generated
discovery presence. It does not validate either file's schema.

### Validator direction

`validate_adoption_shape.py` should validate:

#### `docs/generated/capability_lineage.yaml`

- generated header
- top-level mapping
- expected top-level sections needed by the current generator contract
- per-feature entries shaped like the current aggregate lineage view

#### `docs/generated/architecture_dag.yaml`

- generated header
- top-level mapping
- expected node/edge container keys
- node and edge entries use the current structured shape

This does not require exhaustive graph-semantic validation, only schema-level
enforcement of the current generated discovery contract.

## Documentation Changes

Starter docs should say more plainly that these generated artifacts are not
just "some generated files" but specific validator-enforced contracts.

The most important docs to align are:

- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/stage-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`

The docs should explicitly distinguish:

- human-owned source files
- generated contracts
- generated discovery

and name which generated surfaces now have schema enforcement.

## Suggested Implementation Order

Implement in this order:

1. generated stage contract schema
2. generated feature contract schema
3. managed feature history boundary structure
4. generated discovery schema

Reasoning:

- stage drift is already visible in downstream repos
- generated feature contract freshness drift is also active
- history structure is smaller and straightforward
- generated discovery schema is useful, but a little less urgent than the two
  per-feature/per-stage contract surfaces

## Acceptance Criteria

This spec is complete when:

- adoption-shape validation rejects old nested generated stage contracts
- adoption-shape validation validates the canonical flat stage contract shape
- adoption-shape validation validates generated feature contract structure
- adoption-shape validation validates minimal managed history boundary markers
- adoption-shape validation validates the schemas of
  `docs/generated/capability_lineage.yaml` and `docs/generated/architecture_dag.yaml`
- starter docs say these generated schemas are validator-enforced managed
  contracts
- downstream drift like `JOB-PROJECT/docs/stages/enrich.yaml` is caught by the
  starter validator for the right reason
