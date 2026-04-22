---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Managed Root Doc Metadata Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Require managed repos to give the required root docs explicit frontmatter metadata so cross-cutting docs participate in the same architecture linkage surface as the rest of managed mode.
Reasoning: The starter already requires the root docs to exist, but it still treats their metadata as optional. Downstream repos can therefore keep `docs/pipeline.md` and related files as unlinked prose even when the managed migration target clearly expects `doc_id`, `doc_type`, and `explains.*` metadata.
Invariants:

- Required root docs remain cross-cutting explanation docs, not semantic source files.
- Canonical truth still flows downward from feature source, stage source, config, and component layers into linked documentation.
- Managed mode should have one migration target for root-doc metadata, not "metadata optional" guidance in some places and richer metadata in others.
- Starter-only repos should not be forced into the managed metadata contract unless they explicitly adopt managed mode.
- The validator should enforce structure and linkage presence, not try to prove every explain reference is semantically perfect.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/architecture_templates/markdown-frontmatter.md`

Affected stages:

- all managed stages indirectly through `docs/pipeline.md`, `docs/usage.md`, and `docs/architecture.md` linkage

Affected features:

- all managed features indirectly through required root-doc `explains.*` linkage

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/architecture_templates/markdown-frontmatter.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

Managed repos now carry validator-enforced generated feature contracts, stage
contracts, history structure, and generated discovery schemas. But the
cross-cutting root docs still sit in a softer state:

- the canonical reference repos already use frontmatter on `docs/setup.md`,
  `docs/configuration.md`, `docs/usage.md`, `docs/pipeline.md`, and
  `docs/architecture.md`
- the starter validator only checks those files for presence and substance
- the operating-system docs still say frontmatter is optional for required root
  docs

That mismatch means a repo can look managed on generated surfaces while still
keeping the main operator docs as unlinked prose. The result is weaker
discovery, weaker migration guidance, and validator blind spots like the one
observed in `JOB-PROJECT/docs/pipeline.md`.

## Goal

Make required root-doc metadata an explicit managed-mode contract.

For managed repos, the validator should require each required root doc to have:

- a frontmatter block
- a canonical `doc_id`
- a non-empty `doc_type`
- an `explains` mapping with non-empty reference lists appropriate to that doc

## Non-Goals

This spec does not require root-doc frontmatter in `starter_method_only`
repos.

This spec does not make root docs the semantic source of truth for features,
stages, configs, or components.

This spec does not force every Markdown file in `docs/` to carry frontmatter.

This spec does not require the validator to resolve every reference target for
existence in this pass.

## Managed Root-Doc Contract

The required root docs remain:

- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`

In managed mode, each must include YAML frontmatter.

### Required keys

- `doc_id`
- `doc_type`
- `explains`

### Canonical `doc_id` values

- `docs/setup.md` -> `setup`
- `docs/configuration.md` -> `configuration`
- `docs/usage.md` -> `usage`
- `docs/pipeline.md` -> `pipeline`
- `docs/architecture.md` -> `architecture`

### `doc_type`

The validator should require a non-empty string. Guidance should recommend the
current target values:

- `setup-guide`
- `operator-guide`
- `architecture-guide`

### `explains` expectations

The validator should require an `explains` mapping whose values are lists of
non-empty strings.

It should also require at least one non-empty reference family that matches the
doc's role:

- `docs/setup.md`: `explains.features` or `explains.stages`
- `docs/configuration.md`: `explains.features` or `explains.configs`
- `docs/usage.md`: `explains.features` or `explains.stages`
- `docs/pipeline.md`: `explains.stages`
- `docs/architecture.md`: `explains.features`, `explains.stages`, or `explains.components`

This keeps the rule explicit without overfitting to one project's exact list.

## Migration Target Example

`customer-churn-prediction-azureml/docs/pipeline.md` is the model for the
`docs/pipeline.md` target shape:

```yaml
---
doc_id: pipeline
doc_type: operator-guide
explains:
  features:
    - churn-data-preparation
  stages:
    - data_validate
    - data_prep
---
```

The important point is not the exact feature/stage inventory. The point is that
managed root docs should be architecture-linked docs, not heading-only prose
files with no metadata surface.

## Validation Changes

`validate_adoption_shape.py` should:

1. keep the existing required-root-doc presence and substance checks
2. strip frontmatter before evaluating heading/body coverage so metadata alone
   does not satisfy the content rule
3. add a managed-mode validator for required root-doc metadata
4. reject missing frontmatter, wrong `doc_id`, missing `doc_type`, missing
   `explains`, malformed `explains` lists, and missing required explain groups

## Test Coverage

Add focused tests that prove:

- managed mode rejects `docs/pipeline.md` with no frontmatter
- managed mode rejects `docs/pipeline.md` with no `explains.stages`
- managed-mode fixtures with canonical root-doc frontmatter still pass

## Documentation Updates

Update the operating-system guidance so it says plainly:

- required root docs are always required
- in managed mode, those root docs are also validator-enforced metadata-linked
  docs
- frontmatter is still not required for every Markdown file in the repo
