---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tools/docs/generate_architecture_metadata.py
  - tests/test_validate_adoption_shape.py
  - tests/test_architecture_metadata_generation.py
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Optional Root Doc Metadata Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Keep optional root docs optional when absent, but enforce managed metadata shape when they are present.
Reasoning: Optional docs such as `docs/dataset.md` and `docs/api.md` should not be required for every project. But once a managed repo creates them, they become cross-cutting explanation docs and should participate in the same architecture linkage metadata as required root docs.
Invariants:

- Optional docs remain optional when absent.
- Present optional docs in managed mode must not become unlinked prose islands.
- Root docs explain upstream truth; they do not become the source of truth for features, stages, configs, components, APIs, datasets, or tests.
- Metadata-looking frontmatter must be parsed or rejected clearly, not silently ignored.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `tools/docs/generate_architecture_metadata.py`
- `tests/test_validate_adoption_shape.py`
- `tests/test_architecture_metadata_generation.py`

Affected stages:

- none directly

Affected features:

- none directly

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
  - `docs/dataset.md`
  - `docs/api.md`
  - `docs/observability.md`
  - `docs/testing.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/architecture_templates/markdown-frontmatter.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The starter documents four optional root docs:

- `docs/dataset.md`
- `docs/api.md`
- `docs/observability.md`
- `docs/testing.md`

The absence of those docs should not fail validation. That remains correct.

The gap is what happens after a managed repo creates one of them. Today, a repo
can add `docs/api.md` or `docs/dataset.md` with missing or malformed metadata,
and adoption-shape validation does not reject it. That creates the same drift
class recently fixed for required root docs.

There is also a parser edge case: Markdown that starts with whitespace before a
frontmatter block can be silently treated as having no metadata. That makes
metadata drift harder to see.

## Goal

In managed mode, validate optional root docs when they exist.

The validator should require:

- canonical `doc_id`
- non-empty `doc_type`
- an `explains` mapping
- list-shaped `explains.*` values
- at least one doc-appropriate explain family

## Non-Goals

This spec does not make optional docs required.

This spec does not require every Markdown file under `docs/` to carry
frontmatter.

This spec does not resolve every metadata reference target in adoption-shape
validation.

## Managed Optional Root-Doc Contract

Expected optional root-doc targets:

- `docs/dataset.md` -> `doc_id: dataset`
- `docs/api.md` -> `doc_id: api`
- `docs/observability.md` -> `doc_id: observability`
- `docs/testing.md` -> `doc_id: testing`

Required explain families:

- `docs/dataset.md`: `explains.features`, `explains.stages`, or `explains.configs`
- `docs/api.md`: `explains.features`, `explains.capabilities`, or `explains.components`
- `docs/observability.md`: `explains.features`, `explains.stages`, `explains.configs`, or `explains.components`
- `docs/testing.md`: `explains.features`, `explains.capabilities`, or `explains.stages`

## Parser Rule

Frontmatter must start at the first byte of the Markdown file, except for a
UTF-8 BOM. Metadata-looking blocks that appear after whitespace should fail
with a clear message so agents do not accidentally create invisible metadata.

## Validation

Add tests for:

- malformed optional-root-doc frontmatter in `docs/dataset.md`
- present optional docs without doc-appropriate links in `docs/api.md`
- misplaced optional-root-doc frontmatter
- metadata generator rejection of misplaced Markdown frontmatter
