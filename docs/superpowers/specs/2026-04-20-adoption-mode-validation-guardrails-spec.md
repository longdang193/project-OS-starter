---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - repo_config/adoption-mode.yaml
  - scripts/validate_adoption_shape.py
  - docs/adoption_guide.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/feature-routing-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/features/README.md
related_features: []
related_stages: []
---

# Adoption Mode And Validation Guardrails Spec

## Problem

The starter now explains how to route feature candidates and how to avoid half-migrated project adoption states. However, the guidance is still mostly prose.

Future projects can still drift if an agent forgets to read the guides or interprets the repo shape incorrectly.

Failure modes include:

- creating product feature metadata while the project only wanted starter-method adoption
- keeping flat `docs/features/*.yaml` contracts while also creating managed feature folders
- creating `docs/features/repo-operating-system.yaml` or another method-layer pseudo-feature
- using prose sentences as capability IDs
- using feature `depends_on` to connect operating-system work to product features
- hand-editing generated discovery instead of refreshing it from source
- claiming managed architecture metadata is adopted before code/config/test metadata points to canonical feature IDs and feature-qualified capability IDs

The repo needs a small machine-checkable adoption-mode contract and a validator that fails or warns on obvious shape drift.

## Goal

Add explicit adoption-mode configuration and validation guardrails so projects starting from scratch or halfway through adoption have a clear, enforceable state.

The goal is not to force every project into managed architecture metadata. The goal is to make the chosen mode explicit and make invalid mixed states visible.

## Non-Goals

This spec does not implement full architecture metadata generation.

This spec does not migrate any downstream project.

This spec does not require every project to define product features.

This spec does not replace the routing or migration guides. It gives those guides a small enforceable contract.

This spec does not need to enforce deep semantic correctness of every capability or dependency. It should catch the high-signal shape mistakes that caused adoption drift.

## Proposed Source File

Add:

```text
repo_config/adoption-mode.yaml
```

This file is the source of truth for how far the project has adopted the starter architecture-documentation model.

### Starter Method Only Example

```yaml
adoption_mode: starter_method_only
managed_architecture_metadata: false
legacy_feature_contracts: false
architecture_generator: none
notes: >
  Repo operating-system, intent, adapter, and publication guidance are adopted.
  Product feature/stage metadata is intentionally not adopted yet.
```

### Managed Architecture Metadata Example

```yaml
adoption_mode: managed_architecture_metadata
managed_architecture_metadata: true
legacy_feature_contracts: false
architecture_generator: scripts/sync_architecture_docs.py
notes: >
  Product feature folders, generated discovery, and source metadata are managed
  by the architecture sync workflow.
```

### Legacy Compatibility Example

```yaml
adoption_mode: legacy_compatibility
managed_architecture_metadata: false
legacy_feature_contracts: true
architecture_generator: none
migration_follow_up:
  required: true
  target: docs/superpowers/plans/<migration-plan>.md
notes: >
  Existing flat feature contracts remain temporarily. Managed architecture
  metadata is not adopted yet.
```

## Allowed Adoption Modes

### `starter_method_only`

Use when a project wants intent docs, operating-system docs, agent instructions, adapter sync, publication workflow, and repo governance without feature/stage metadata.

Rules:

- `docs/features/` may contain only `README.md` unless explicitly project-owned prose already exists
- `docs/stages/` may contain only `README.md` or starter placeholders
- no generated architecture indexes should be created
- no feature/capability metadata should be added to code/config/tests
- operating-system adoption work must use `docs/operating_system/` and specs/plans with `layer: operating_system`

### `managed_architecture_metadata`

Use when a project wants feature/stage contracts, generated lineage, generated discovery, and code/config/test traceability.

Rules:

- no authoritative flat `docs/features/*.yaml` files outside feature folders
- each product feature lives under `docs/features/<feature_id>/`
- each managed feature folder has `feature.source.yaml`
- generated or normalized feature contract lives at `docs/features/<feature_id>/<feature_id>.yaml`
- feature-local generated evidence lives at `docs/features/<feature_id>/lineage.generated.yaml` when lineage generation is adopted
- generated discovery must be refreshed from source
- source metadata should reference canonical feature IDs and feature-qualified capability IDs
- method-layer pseudo-features are forbidden

### `legacy_compatibility`

Use when a project already has legacy flat feature contracts and is not ready to migrate.

Rules:

- flat `docs/features/*.yaml` files may remain temporarily
- managed feature-folder contracts must not be created beside flat authoritative contracts
- `feature.source.yaml` should not be introduced until the project moves to managed mode
- generated managed discovery should not be claimed as current unless the legacy generator explicitly supports the flat shape
- every plan touching feature metadata must state that legacy compatibility is intentional
- `migration_follow_up.required` should be true unless there is a documented reason to keep legacy mode indefinitely

## Validator Design

Add:

```text
scripts/validate_adoption_shape.py
```

The script should be safe, local, and read-only.

It should:

- load `repo_config/adoption-mode.yaml`
- inspect docs feature/stage/generated shapes
- inspect specs/plans metadata enough to catch method-layer misuse
- report actionable errors and warnings
- exit non-zero on errors

The validator should not modify files.

## Required Checks

### Common Checks

Run in all modes:

- `repo_config/adoption-mode.yaml` exists
- `adoption_mode` is one of the allowed values
- boolean fields match the selected mode
- no feature ID equals `repo-operating-system`
- no feature ID starts with obvious method-layer terms such as `repo-`, `agent-`, `docs-governance`, `publication-`, or `adapter-` unless explicitly allowlisted
- feature `depends_on` values reference existing product feature IDs only
- operating-system specs/plans use `targets` for method-layer work
- capability IDs are ID-like when the schema exposes explicit capability IDs
- generated files with generated headers are not treated as human source files

### Starter Method Only Checks

Errors:

- product feature source files exist
- managed feature contracts exist
- generated architecture indexes exist
- feature/capability metadata markers exist in code/config/tests

Warnings:

- `docs/features/` contains non-README files
- `docs/stages/` contains non-README files

### Managed Architecture Metadata Checks

Errors:

- authoritative flat `docs/features/*.yaml` files exist outside feature folders
- a feature folder is missing `feature.source.yaml`
- method-layer pseudo-feature exists
- generated discovery exists but expected source folders are missing
- `architecture_generator` is `none`

Warnings:

- `lineage.generated.yaml` is missing when lineage generation is configured
- source metadata appears absent for project code/config/test files
- capability entries are prose strings instead of structured IDs where the project schema supports structured capabilities

### Legacy Compatibility Checks

Errors:

- `feature.source.yaml` exists while `managed_architecture_metadata` is false
- managed generated feature contracts are created beside flat authoritative contracts
- `legacy_feature_contracts` is false

Warnings:

- no `migration_follow_up` is recorded
- generated discovery exists without a documented legacy generator
- flat feature contracts contain prose capability strings that should become IDs during migration

## Candidate Classification Metadata

Specs/plans that create or change feature/stage/generated/source metadata should include a routing block.

Recommended fields:

```yaml
candidate_type: product_feature | product_stage | operating_system | spec_only | plan_only | generated | obsolete
adoption_mode: starter_method_only | managed_architecture_metadata | legacy_compatibility
creates_feature_metadata: true | false
creates_stage_metadata: true | false
updates_code_metadata: true | false
updates_generated_discovery: true | false
```

Rules:

- if `candidate_type: operating_system`, then `related_features` should usually be empty and `targets` should name affected operating-system paths
- if `creates_feature_metadata: true`, the selected adoption mode must allow feature metadata changes
- if `updates_generated_discovery: true`, the plan must name the generator/check command

## Documentation Updates

### `docs/adoption_guide.md`

Add a validation step after choosing adoption mode:

```powershell
python scripts/validate_adoption_shape.py
```

If the validator script is optional in a starter-only state, the guide should say to run it once the script exists and before committing adoption changes.

### `docs/operating_system/project-adoption-migration-guide.md`

Add `repo_config/adoption-mode.yaml` as the required place to record the chosen mode.

Add mode-specific validator expectations.

### `docs/operating_system/feature-routing-guide.md`

Add the candidate classification metadata block and explain how it prevents operating-system work from becoming product feature dependencies.

### `docs/operating_system/skill-doc-system-lifecycle.md`

Add `repo_config/adoption-mode.yaml` to the source-of-truth model.

Clarify that adoption mode controls whether feature YAML is absent, legacy flat, or managed folder-based.

### `docs/features/README.md`

Add a short note that the folder shape is interpreted according to `repo_config/adoption-mode.yaml`.

## Validation Command

Preferred local command:

```powershell
python scripts/validate_adoption_shape.py
```

If a project uses a virtual environment, the guide may show the project-specific Python command instead.

## Acceptance Criteria

The implementation is complete when:

- `repo_config/adoption-mode.yaml` exists with a starter default mode.
- `scripts/validate_adoption_shape.py` exists and performs read-only validation.
- The validator supports `starter_method_only`, `managed_architecture_metadata`, and `legacy_compatibility`.
- The validator fails on method-layer pseudo-features such as `repo-operating-system`.
- The validator fails on mixed flat feature YAML plus managed feature-folder contracts in managed mode.
- The validator catches invalid mode/boolean combinations.
- The validator reports clear messages with paths and suggested fixes.
- Adoption/migration/routing/lifecycle docs reference the adoption mode file and validator.
- Existing starter state validates in `starter_method_only` mode.

## Open Questions

- Should the validator treat non-README files under `docs/features/` as errors or warnings in `starter_method_only` mode?
- Should method-layer feature ID detection use a hard-coded denylist first, with an allowlist for rare exceptions?
- Should CI run the validator by default in the starter, or should downstream projects opt in after choosing an adoption mode?
- Should candidate classification metadata be required immediately or introduced as recommended metadata first?
