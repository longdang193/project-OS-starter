# Project Adoption Migration Guide

Use this guide when an existing project adopts `project-OS-starter`.

This guide is different from the feature routing guide:

- `feature-routing-guide.md` decides whether a candidate is a product feature, product stage, operating-system concern, spec, plan, generated output, or obsolete artifact.
- this guide decides how an existing project moves from legacy docs into the starter-compatible structure.

## Core Rule

Do not partially migrate architecture metadata.

Before changing feature, stage, generated discovery, or source metadata surfaces, choose one adoption mode and record it in `repo_config/adoption-mode.yaml`. The adoption spec or plan should reference that file instead of inventing a second mode source.

## Adoption Mode Source

`repo_config/adoption-mode.yaml` is the machine-checkable source of truth for adoption mode.

Validate it with:

```powershell
python scripts/validate_adoption_shape.py
```

## Adoption Modes

### Mode A: Starter Method Only

Use this mode when the project wants repo governance, intent docs, agent rules, adapter sync, publication workflow, and operating-system docs, but does not yet want feature/stage lineage.

Rules:

- do not create or migrate `docs/features/`
- do not create generated architecture indexes
- do not add feature/capability metadata to code, config, or tests
- keep product architecture docs as ordinary prose
- use operating-system specs/plans for repo-method adoption work
- `scripts/validate_adoption_shape.py` should pass with starter scaffold files only

### Mode B: Managed Architecture Metadata

Use this mode when the project wants feature/stage contracts, generated lineage, generated discovery, and code/config/test traceability.

Rules:

- migrate product features into folders
- create `feature.source.yaml` for each product feature
- generate or normalize `<feature_id>.yaml`
- generate `lineage.generated.yaml` when lineage generation is adopted
- update code/config/test/doc metadata to canonical feature and capability IDs
- refresh generated discovery
- verify no flat authoritative feature contracts remain
- remove or relocate method-layer pseudo-features
- `scripts/validate_adoption_shape.py` should pass after generated discovery is refreshed

### Mode C: Legacy Compatibility

Use this mode when a project already has flat feature YAML and is not ready for managed architecture metadata.

Rules:

- keep flat `docs/features/*.yaml` temporarily
- do not create generated feature-folder contracts beside them
- do not claim the project has adopted managed architecture metadata
- record the legacy choice in the adoption spec, plan, or project notes
- create a follow-up migration plan before adding deeper traceability
- `scripts/validate_adoption_shape.py` should warn about missing follow-up migration when none is recorded

## Mode A Step-By-Step: Starter Method Only

Use this runbook when the project wants the starter's repo operating-system method without adopting product feature, stage, capability, generated architecture, or lineage metadata.

1. Set `repo_config/adoption-mode.yaml` to `starter_method_only`.
2. Fill or update the intent layer for the project:
   - `docs/intent/project-charter.md`
   - `docs/intent/constraints-and-non-goals.md`
   - `docs/intent/stakeholders.md`
   - `docs/intent/success-outcomes.md`
3. Adopt the operating-system layer needed by the project:
   - repo governance docs under `docs/operating_system/`
   - agent instruction templates and generated instruction surfaces
   - generated rule surfaces
   - adapter sync and verification workflow
   - publication guidance
   - agent-memory guidance
4. Keep product architecture metadata absent:
   - do not create product feature folders
   - do not create stage contracts
   - do not create generated architecture indexes
   - do not add feature or capability metadata to code, config, or tests
5. Represent starter adoption, adapter work, rule updates, publication setup, and other method-layer changes as operating-system specs or plans with explicit `targets`.
6. If adapter sources, agent instructions, or generated rule surfaces changed, run:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

7. Validate the selected mode:

```powershell
python scripts/validate_adoption_shape.py
```

8. Commit only after the repo has no accidental product architecture metadata.

Stop and create a Mode B migration plan instead of adding one-off feature files if the project needs product feature lineage, stage ownership, or generated feature contracts.

## Mode B Step-By-Step: Managed Architecture Metadata

Use this runbook when the project wants managed metadata for product features, stages, capabilities, generated contracts, generated discovery, and source traceability.

Do not switch to Mode B just because one feature folder exists. Mode B means the project has adopted the managed metadata contract across docs, generated outputs, and source metadata.

For a concrete one-feature migration, see [Mode B Example Migration](mode-b-example-migration.md).

1. Set `repo_config/adoption-mode.yaml` to `managed_architecture_metadata`.
2. Inventory existing product and architecture surfaces:
   - product docs
   - flat `docs/features/*.yaml` files
   - `docs/features/*/` folders
   - stage docs and contracts
   - generated files under `docs/generated/`
   - code metadata
   - config metadata
   - test metadata
   - pipeline, component, workflow, and asset metadata
3. Classify each candidate as one of:
   - product feature
   - product stage
   - product capability
   - cross-cutting product doc
   - operating-system method material
4. Remove or re-home method-layer pseudo-features. Starter adoption, repo governance, adapter work, generated rule work, publication setup, and agent-memory guidance belong in `docs/operating_system/` or operating-system specs/plans, not `docs/features/`.
5. Create one folder per real product feature:

```text
docs/features/<feature_id>/
```

6. Move human-owned feature meaning into:

```text
docs/features/<feature_id>/feature.source.yaml
```

7. Ensure generated feature outputs use:

```text
docs/features/<feature_id>/<feature_id>.yaml
docs/features/<feature_id>/lineage.generated.yaml
```

8. Normalize capability IDs to stable identifiers, such as lowercase kebab-case IDs. Do not use prose sentences as capability IDs.
9. Update stage source files so `primary_features` and `supporting_features` describe stage ownership.
10. Update source metadata that feeds lineage so it references canonical feature and capability IDs:
    - code
    - config
    - tests
    - AML components
    - scripts
    - docs
    - pipeline and workflow manifests
11. Refresh generated architecture surfaces from source using the project generator when one exists. If no generator exists, do not hand-invent generated files; add the generator first or stay in legacy compatibility.
12. Verify no authoritative flat `docs/features/*.yaml` files remain outside feature folders.
13. Validate the selected mode:

```powershell
python scripts/validate_adoption_shape.py
```

14. Run the relevant test suite for the surfaces changed.
15. Run whitespace validation:

```powershell
git diff --check
```

16. Commit only after managed metadata, generated files, source metadata, validation, and tests agree.

## Mode C Step-By-Step: Legacy Compatibility

Use this runbook when an existing project already has legacy flat feature contracts and needs a temporary holding pattern before moving to Mode A or Mode B.

Legacy compatibility is temporary. It should make the follow-up migration discoverable instead of letting legacy metadata become an accidental permanent contract.

1. Set `repo_config/adoption-mode.yaml` to `legacy_compatibility`.
2. Record `migration_follow_up.required: true` and point it at the plan or issue that will migrate the project to Mode A or Mode B.
3. Inventory existing flat feature contracts.
4. Classify which flat contracts are real product features and which are method-layer material.
5. Keep legacy flat feature contracts as the temporary current truth.
6. Do not create managed feature folders, generated feature contracts, or generated lineage files until a Mode B migration plan is executed.
7. Re-home obvious method-layer pseudo-features into operating-system docs/specs/plans when safe.
8. Validate the selected mode:

```powershell
python scripts/validate_adoption_shape.py
```

9. Treat validator warnings as migration debt unless the guide documents why they are intentionally allowed in Mode C.
10. Commit only after the legacy state is explicit and the migration follow-up is discoverable.

Stop extending Mode C and move to a Mode B migration plan if the work requires generated lineage or capability-level code tracing.

## Canonical Managed Feature Shape

In managed architecture metadata mode, each product feature should use this shape:

```text
docs/features/<feature_id>/
  feature.source.yaml
  <feature_id>.yaml
  lineage.generated.yaml
  history.md
```

Ownership:

- `feature.source.yaml` is the human-owned semantic source.
- `<feature_id>.yaml` is the generated or normalized assembled current-state contract.
- `lineage.generated.yaml` is generated evidence and must not be edited manually.
- `history.md` contains feature-local context and human notes, plus generated blocks if the project adopts partial-generated history.

Flat files such as `docs/features/data-pipeline.yaml` are legacy compatibility only once managed architecture metadata is adopted.

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

Move human-authored semantic content into `feature.source.yaml`.

Generate or normalize the assembled contract into `<feature_id>.yaml`.

### 5. Normalize capability IDs

Capability IDs must be stable identifiers, not prose capability descriptions.

Bad legacy shape:

```yaml
capabilities:
  - "Staging: flatten nested GA4 event_params, geo, device, traffic_source, ecommerce fields"
```

Preferred managed shape:

```yaml
capabilities:
  - id: staging-ga4-events
    name: Staging GA4 Events
    summary: Flatten nested GA4 event fields into staging tables.
```

If a project schema initially supports only capability strings, label those strings as a legacy bridge and do not treat them as stable IDs.

### 6. Update code, config, test, and doc metadata

Feature migration is incomplete until source references are aligned.

Inspect project-relevant files such as:

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

Metadata should reference canonical feature IDs and capability IDs, not old prose labels or flat YAML paths.

### 7. Refresh generated discovery

After source migration, run the project's canonical architecture sync/check workflow.

If the project has no generator yet, do not hand-invent generated files. Either add the generator first or keep the project in legacy compatibility mode.

### 8. Validate the result

Managed mode validation should confirm:

- no authoritative `docs/features/*.yaml` files remain outside feature folders
- no `repo-operating-system` or method-layer pseudo-feature exists
- every feature folder has required files
- feature IDs are kebab-case
- capability IDs are stable IDs
- generated indexes exclude operating-system artifacts
- code/config/test metadata references existing feature/capability IDs
- generated files were refreshed, not edited manually

## Half-Migration Anti-Pattern

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
- code/config/test metadata may still be absent or stale

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

## Pre-Commit Checklist

Before committing a managed architecture metadata migration, confirm:

- the adoption mode is recorded
- feature routing was reviewed before creating feature or stage metadata
- no method-layer pseudo-feature remains under `docs/features/`
- every managed feature has the required folder shape
- flat feature YAML is removed or explicitly documented as legacy compatibility
- source metadata points to canonical feature/capability IDs
- generated discovery was refreshed from source
- generated files were not edited manually
