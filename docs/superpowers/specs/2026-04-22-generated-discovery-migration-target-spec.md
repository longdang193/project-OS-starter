---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/mode-b-example-migration.md
  - scripts/validate_adoption_shape.py
related_features: []
related_stages: []
---

# Generated Discovery Migration Target Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Define a concrete migration target for `docs/generated/` so downstream repos can move older generated-discovery shapes onto the current starter-style contract.
Reasoning: `JOB-PROJECT/docs/generated/` still uses an older feature/stage summary set, while `customer-churn-prediction-azureml/docs/generated/` uses the newer starter-style discovery outputs. The starter docs say generated discovery must be refreshed from source, but they do not yet state the old-to-new migration target clearly enough.
Invariants:

- The canonical migration target is the generated-discovery shape used by `customer-churn-prediction-azureml/docs/generated/`.
- Generated discovery stays generated-only and must not be hand-edited.
- Canonical truth still flows from source-owned layers into generated discovery.
- Mode B migration should not preserve older generated-discovery files just because they exist.
- Downstream repos should converge on one discovery contract instead of carrying parallel old and new index families.

Dependencies:

- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- current starter generator and validators

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- cross_cutting_docs:
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/mode-b-example-migration.md`
- generated:
  - `docs/generated/*`

Generated refresh required: yes
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter already says that generated discovery must be refreshed from source
and not hand-edited, but it does not yet make the migration target explicit
enough when a downstream repo has an older generated-discovery family.

Current example of drift:

- desired target:
  - `customer-churn-prediction-azureml/docs/generated/`
- older shape:
  - `JOB-PROJECT/docs/generated/`

Newer target files:

- `architecture_dag.yaml`
- `capability_lineage.yaml`

Older file family:

- `feature_capabilities_index.yaml`
- `feature_dependency_graph.yaml`
- `feature_overview.md`
- `features_by_status.yaml`
- `features_index.yaml`
- `stage_overview.md`
- `stages_index.yaml`

Without an explicit migration target, agents can:

- keep stale older generated files beside newer ones
- assume both file families should coexist
- preserve repo-local generated discovery shapes during Mode B migration
- treat `docs/generated/` as a menu of optional outputs instead of a contract

## Goal

Make the generated-discovery migration target explicit.

For downstream repos adopting the current starter-style managed architecture
metadata model, the canonical `docs/generated/` target should match the churn
repo shape:

- `docs/generated/architecture_dag.yaml`
- `docs/generated/capability_lineage.yaml`

The migration guidance should also state that older generated-discovery files
from pre-target shapes are migration debt and should be retired rather than
carried forward indefinitely.

## Non-Goals

This spec does not redesign the content schema of `architecture_dag.yaml` or
`capability_lineage.yaml`.

This spec does not require every repo to adopt managed metadata immediately.

This spec does not force starter-method-only or legacy-compatibility repos to
invent managed generated discovery before they adopt the generator workflow.

This spec does not require additional generated-discovery files beyond the
canonical starter outputs.

## Canonical Migration Target

For repos that have adopted the current managed architecture metadata contract,
the canonical generated-discovery target is:

```text
docs/generated/
  architecture_dag.yaml
  capability_lineage.yaml
```

Interpretation:

- `architecture_dag.yaml` is the aggregate graph/discovery view
- `capability_lineage.yaml` is the aggregate capability-lineage discovery view
- detailed capability evidence belongs in feature-local
  `docs/features/<feature_id>/lineage.generated.yaml`
- do not keep older feature/stage summary indexes as parallel generated
  discovery once the newer target is adopted

## Migration Rules

When moving an older repo onto the current starter target:

1. migrate source-owned metadata first
2. run the canonical generator
3. adopt the current `docs/generated/` target files
4. retire older generated-discovery files that represent the superseded shape

Generated-discovery migration should be treated like feature-folder migration:

- do not hand-edit generated files
- do not copy old generated facts into new source files
- do not preserve obsolete generated outputs just because they still render
- do not keep both the older summary-index family and the newer discovery pair
  as if they were equal canonical outputs

## Documentation Changes

Update the starter guidance so it explicitly says:

- the canonical current managed target is `architecture_dag.yaml` plus
  `capability_lineage.yaml`
- older generated-discovery families are examples of migration debt, not
  parallel valid steady states
- downstream repos should use the churn repo shape as the concrete example of
  the current target

The most important docs to clarify are:

- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/mode-b-example-migration.md`

## Validator Direction

The validator should eventually help prevent mixed generated-discovery shapes in
managed mode.

At minimum, the guidance should prepare for validator behavior such as:

- rejecting stale older generated-discovery files once the current target is
  adopted
- rejecting managed repos that claim current adoption while keeping only the old
  generated-discovery family

This spec does not require implementing that validator tightening immediately,
but it should leave the docs and migration guidance ready for it.

## Acceptance Criteria

This spec is complete when:

- the starter docs name the churn repo `docs/generated/` shape as the canonical
  migration target
- the docs list the current target files explicitly
- the docs make it clear that older generated-discovery files are superseded
  outputs, not coequal steady-state artifacts
- downstream migration work can point to one concrete `docs/generated/` target
  instead of inferring it from scattered mentions
