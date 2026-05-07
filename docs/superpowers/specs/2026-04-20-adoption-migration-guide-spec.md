---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/adoption_guide.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/feature-routing-guide.md
  - docs/features/README.md
related_features: []
related_stages: []
---

# Adoption Migration Guide Spec

## Problem

Existing projects that adopt `project-OS-starter` can land in a half-migrated architecture-doc state.

A concrete failure mode appears when a project has:

- feature folders for histories, such as `docs/features/data-pipeline/history.md`
- flat authoritative feature contracts, such as `docs/features/data-pipeline.yaml`
- no `docs/features/<feature_id>/feature.source.yaml`
- generated discovery built from old flat contracts
- code, config, workflow, SQL, or test files that do not reference canonical feature IDs and feature-qualified capability IDs
- operating-system adoption work mixed into product architecture updates

This is confusing because the repo looks partially aligned with the starter, but future agents do not know whether the project is in legacy compatibility mode or managed architecture metadata mode.

## Goal

Add adoption/migration guidance that tells agents how to update an existing project properly after downloading or copying `project-OS-starter`.

The guidance must prevent partial migrations by requiring an explicit adoption mode before feature/stage metadata, generated discovery, or code/config traceability is changed.

## Non-Goals

This spec does not implement the actual migration for any downstream project.

This spec does not require every project to adopt managed architecture metadata.

This spec does not require adding a validator immediately, although it should define validation expectations for future hardening.

This spec does not replace the feature routing guide. The feature routing guide decides where a candidate belongs. This migration guide decides how an existing project moves from legacy docs to the starter-compatible structure.

## Design Principles

### 1. Adoption mode must be explicit

Before modifying feature, stage, generated discovery, or code/config metadata, an agent must choose one adoption mode:

- starter method only
- managed architecture metadata
- legacy compatibility

The chosen mode must be recorded in the adoption plan/spec or project notes.

### 2. Do not partially migrate architecture metadata

A project should not mix new managed architecture conventions with old flat feature contracts unless it is explicitly in legacy compatibility mode.

If managed architecture metadata is adopted, the feature folder shape, generated outputs, and code/config/test metadata must be migrated together.

### 3. Feature folders own feature truth in managed mode

In managed mode, every product feature should use this shape:

```text
docs/features/<feature_id>/
  feature.source.yaml
  <feature_id>.yaml
  lineage.generated.yaml
  history.md
```

The human-owned semantic source is `feature.source.yaml`.

The assembled current-state contract is `<feature_id>.yaml` and should be generated or normalized by the project architecture sync workflow.

The lineage/evidence file is generated and should not be edited manually.

### 4. Flat feature YAML is legacy-only

Flat files such as `docs/features/data-pipeline.yaml` may remain only when the project explicitly chooses legacy compatibility mode.

Legacy compatibility mode must not be silently mixed with generated feature-folder contracts.

### 5. Code/config/test metadata is part of migration

Managed architecture metadata is not only a docs-folder change.

The agent must inspect and update relevant source surfaces so metadata points to canonical feature IDs and feature-qualified capability IDs.

Relevant surfaces may include:

- Python files
- SQL files
- YAML config files
- workflow files
- pipeline manifests
- semantic-model files
- test files
- docs frontmatter

### 6. Generated discovery must be refreshed from source

Generated files under `docs/generated/` or feature-local lineage files must not be hand-edited.

If a generator does not exist for the project yet, the project should remain in legacy compatibility mode or add the generator before claiming managed architecture metadata adoption.

## Adoption Modes

### Mode A: Starter Method Only

Use this mode when the project wants repo governance, intent docs, agent rules, adapter sync, publication workflow, and operating-system docs, but not feature/stage lineage yet.

Rules:

- do not create or migrate `docs/features/`
- do not create generated architecture indexes
- do not add feature/capability metadata to code/config/test files
- keep product architecture docs as ordinary prose
- use operating-system specs/plans for repo-method adoption work

### Mode B: Managed Architecture Metadata

Use this mode when the project wants feature/stage contracts, generated lineage, generated discovery, and code/config/test traceability.

Rules:

- migrate product features into folders
- create `feature.source.yaml` for each product feature
- generate or normalize `<feature_id>.yaml`
- generate `lineage.generated.yaml` when lineage generation is adopted
- update code/config/test/doc metadata to canonical feature IDs and feature-qualified capability IDs
- refresh generated discovery
- verify no flat authoritative feature contracts remain
- remove or relocate method-layer pseudo-features

### Mode C: Legacy Compatibility

Use this mode when a project already has flat feature YAML and is not ready for managed architecture metadata.

Rules:

- keep flat `docs/features/*.yaml` temporarily
- do not create generated feature-folder contracts beside them
- do not claim the project has adopted managed architecture metadata
- record the legacy choice in the adoption plan/spec
- create a follow-up migration plan before adding deeper traceability

## Required Migration Sequence For Managed Mode

### 1. Inventory existing surfaces

Before editing, inventory:

```text
docs/features/*.yaml
docs/features/*/
docs/stages/*
docs/generated/*
docs/superpowers/specs/*
docs/superpowers/plans/*
code/config/test metadata markers
workflow/config manifests
cross-cutting docs
```

### 2. Classify every candidate

Classify each candidate as one of:

- product feature
- product stage
- operating-system method
- one-time spec/plan
- generated output
- obsolete artifact

Use `docs/operating_system/feature-routing-guide.md` for this classification.

### 3. Remove method-layer pseudo-features

Operating-system work must not remain under `docs/features/`.

Example cleanup:

```text
docs/features/repo-operating-system.yaml -> remove
docs/features/repo-operating-system/* -> move useful prose into docs/operating_system/
```

Durable method guidance belongs in `docs/operating_system/`.

Bounded design or implementation history belongs in specs/plans with `layer: operating_system`.

### 4. Pack product features into folders

Example migration:

```text
docs/features/data-pipeline.yaml
docs/features/data-pipeline/history.md
```

becomes:

```text
docs/features/data-pipeline/feature.source.yaml
docs/features/data-pipeline/data-pipeline.yaml
docs/features/data-pipeline/lineage.generated.yaml
docs/features/data-pipeline/history.md
```

The human-authored semantic content moves into `feature.source.yaml`.

The generated or normalized assembled contract is `<feature_id>.yaml`.

### 5. Normalize capability IDs

Capability IDs must be feature-qualified stable identifiers, not prose capability
descriptions or unscoped slugs.

Bad legacy shape:

```yaml
capabilities:
  - "Staging: flatten nested GA4 event_params, geo, device, traffic_source, ecommerce fields"
```

Preferred managed shape:

```yaml
capabilities:
  - capability_id: data-pipeline.staging-ga4-events
    name: Staging GA4 Events
    summary: Flatten nested GA4 event fields into staging tables.
```

If a project schema initially supports only capability strings, the migration guide should label those strings as a legacy bridge and avoid treating them as stable IDs.

### 6. Update code/config/test/doc metadata

Feature migration is incomplete until source references are aligned.

Agents should inspect project-relevant files such as:

```text
*.py
*.sql
*.yml
*.yaml
.github/workflows/*.yml
pipeline.yml
agent_config.yaml
semantic model files
pipeline asset manifests
tests/*
docs/*.md frontmatter
```

Metadata should reference canonical feature IDs and feature-qualified capability
IDs, not old prose labels, unscoped capability slugs, or flat YAML paths.

### 7. Refresh generated discovery

After source migration, run the project canonical architecture sync/check workflow.

If the project has no generator yet, do not hand-invent generated files. Either add the generator first or keep the project in legacy compatibility mode.

### 8. Validate the result

Managed mode validation should confirm:

- no authoritative `docs/features/*.yaml` files remain outside feature folders
- no `repo-operating-system` or method-layer pseudo-feature exists
- every feature folder has required files
- feature IDs are kebab-case
- capability IDs are feature-qualified stable IDs
- generated indexes exclude operating-system artifacts
- code/config/test metadata references existing feature IDs and feature-qualified capability IDs
- generated files were refreshed, not edited manually

## Proposed Documentation Changes

### Update `docs/adoption_guide.md`

Add an early adoption-mode checkpoint before feature/stage creation.

The adoption guide should say:

- choose starter method only, managed architecture metadata, or legacy compatibility
- do not partially migrate architecture metadata
- managed mode requires feature folders, generated outputs, and code/config/test metadata together
- legacy flat feature YAML is temporary and must be explicitly recorded

### Add `docs/operating_system/project-adoption-migration-guide.md`

Create a detailed migration guide with:

- adoption mode decision
- managed feature folder shape
- flat YAML legacy warning
- migration sequence
- code/config/test metadata update expectations
- generated discovery refresh rules
- validation checklist
- DE-PROJECT-style anti-pattern example

### Update `docs/operating_system/skill-doc-system-lifecycle.md`

Add a concise reference to the adoption migration guide.

Clarify that `docs/features/*.yaml` outside feature folders is legacy compatibility only when managed architecture metadata has not been adopted.

### Update `docs/features/README.md`

Add a short note:

- managed mode requires feature folders
- flat feature YAML files are legacy-only
- do not mix flat authoritative contracts with generated folder contracts

### Update `docs/operating_system/feature-routing-guide.md`

Add a short cross-reference:

- use the routing guide to classify candidates
- use the adoption migration guide to migrate existing project surfaces

## Anti-Pattern Example

Bad partial migration:

```text
docs/features/data-pipeline.yaml
docs/features/data-pipeline/history.md
docs/generated/features_index.yaml
```

Problems:

- feature truth is split between a flat contract and a folder
- `feature.source.yaml` is missing
- generated discovery may be based on legacy shape
- code/config metadata may still be absent or stale

Correct managed shape:

```text
docs/features/data-pipeline/feature.source.yaml
docs/features/data-pipeline/data-pipeline.yaml
docs/features/data-pipeline/lineage.generated.yaml
docs/features/data-pipeline/history.md
```

Correct legacy compatibility shape:

```text
docs/features/data-pipeline.yaml
```

with a recorded decision that managed architecture metadata is not adopted yet.

## Acceptance Criteria

The implementation is complete when:

- `docs/adoption_guide.md` requires choosing an adoption mode before feature/stage migration.
- `docs/operating_system/project-adoption-migration-guide.md` exists and explains the full migration sequence.
- `docs/operating_system/skill-doc-system-lifecycle.md` distinguishes managed feature-folder mode from legacy flat YAML mode.
- `docs/features/README.md` warns against mixing flat authoritative contracts with managed feature folders.
- `docs/operating_system/feature-routing-guide.md` links classification to migration guidance.
- The guide explicitly says code/config/test metadata must be updated in managed mode.
- The guide explicitly says generated discovery must be refreshed from source and not hand-edited.
- The DE-PROJECT-style half-migration anti-pattern is documented.

## Open Questions

- Should the starter include an advisory `scripts/validate_adoption_shape.py` later?
- Should legacy compatibility mode require a metadata marker in a repo config file?
- Should managed architecture metadata be optional per project or only enabled when a generator exists?
