---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/architecture_templates/feature.source.yaml
  - docs/architecture_templates/stage.source.yaml
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Canonical Style Validation Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Add repo-wide canonical style validation for required docs and managed metadata so valid-but-messy files stop slipping past the validator.
Reasoning: The starter already enforces many presence and schema rules, but it still accepts too many non-canonical values such as folded summary strings with trailing blank lines, unstable list ordering, or inconsistent concise-field formatting. Those values parse, yet they create drift, awkward generated output, and avoidable migration confusion.
Invariants:

- Canonical truth still flows downward from owning source layers into derived and generated surfaces.
- Required docs and managed metadata should be machine-checkable for both schema and canonical style.
- Canonical style validation should harden existing contracts, not create a second semantic source of truth.
- The validator should reject non-canonical input; it should not silently rewrite files in place.
- Long-form prose fields may remain multiline where the contract explicitly allows it.
- Concise metadata fields should stay concise and normalized.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`
- `docs/superpowers/specs/2026-04-21-required-doc-validation-spec.md`
- `docs/superpowers/specs/2026-04-23-managed-root-doc-metadata-spec.md`
- `docs/superpowers/specs/2026-04-22-lineage-generated-schema-contract-spec.md`
- `docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`

Affected stages:

- all managed stages indirectly through stricter stage-doc and root-doc style checks

Affected features:

- all managed features indirectly through stricter feature source, contract, lineage, and linked-doc style checks

Primary lens: cross-cutting

Affected docs:

- feature_source:
  - `docs/features/*/feature.source.yaml`
- feature_yaml:
  - `docs/features/*/<feature_id>.yaml`
- feature_lineage:
  - `docs/features/*/lineage.generated.yaml`
- feature_history:
  - `docs/features/*/history.md`
- stage_source:
  - `docs/stages/*.source.yaml`
- stage_contract:
  - `docs/stages/*.yaml`
- feature_docs: none directly
- cross_cutting_docs:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/architecture_templates/feature.source.yaml`
  - `docs/architecture_templates/stage.source.yaml`
  - `docs/architecture_templates/markdown-frontmatter.md`
- readme: none
- generated: none

Generated refresh required: no for starter changes; yes for downstream repos whose current files are syntactically valid but non-canonical
Capability IDs: none new
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current validator family mostly enforces:

- required file presence
- top-level schema shape
- selected required keys
- a few targeted canonical rules such as feature-qualified capability IDs

That is not enough to keep required docs and managed metadata stable over time.

Observed and likely drift patterns include:

- concise fields stored as folded multiline YAML scalars
- leading or trailing whitespace in strings
- trailing blank lines inside metadata values
- duplicate list items that still parse
- set-like lists with unstable ordering
- mixed path styles or non-canonical repo-relative paths
- docs that satisfy schema but still carry placeholder or low-signal metadata

Example: a `feature.source.yaml` `summary` may parse as a non-empty string even
when it is represented as a folded block with an extra blank line at the end.
That value is technically valid YAML, but it is not a canonical concise summary.

## Goal

Introduce a canonical style validation layer for required docs and managed
metadata.

The validator should enforce not only that a field exists and has the right
type, but also that it uses the canonical style for its field class.

## Non-Goals

This spec does not require the validator to rewrite files automatically.

This spec does not attempt to grade prose quality or domain correctness.

This spec does not require every Markdown file in the repo to adopt the same
metadata scheme.

This spec does not ban multiline strings everywhere. It only bans them for
fields that are contractually concise.

This spec does not replace field-specific schema specs for lineage, generated
contracts, root-doc metadata, or stage docs. It adds a cross-cutting style
layer above them.

## Canonical Style Model

Add a field taxonomy so each required field belongs to one style class.

### 1. Concise String Fields

These fields should be normalized as single logical lines with no extra
surrounding whitespace.

Examples:

- `summary`
- `name`
- `statement`
- `role`
- `status`
- `type`
- `doc_id`
- `doc_type`
- `change_id`
- `latest_change_id`
- `last_updated_at`
- `revision`

Rules:

- must parse to a non-empty string
- must equal `value.strip()`
- must not contain leading or trailing blank lines
- must not contain double newline sequences
- should be rejected when represented as multiline prose for fields that are
  contractually concise

### 2. Long Prose Fields

These fields may be multiline when the contract explicitly allows it.

Examples:

- `notes`
- longer Markdown body content
- future explicitly-long description fields

Rules:

- may be multiline
- still must reject placeholder-only content when the field is required
- still must reject leading or trailing all-whitespace padding

### 3. Set-Like Lists

These lists represent membership, not order.

Examples:

- `depends_on`
- `domains`
- `explains.features`
- `explains.stages`
- `explains.configs`
- `primary_features`
- `supporting_features`
- `capability_ids` where stage participation treats them as a set

Rules:

- items must be non-empty strings
- no duplicates
- canonical ordering should be stable, such as lexical order, unless a field
  explicitly documents semantic order

### 4. Ordered Lists

These lists preserve sequence meaning.

Examples:

- lineage timeline entries
- execution steps
- history blocks with explicit chronology

Rules:

- no duplicate sequence items where duplicates are nonsensical
- order remains semantic and should not be auto-sorted by validation logic

### 5. Path And Reference Fields

Examples:

- repo-relative file paths
- generated source references
- plan/spec links in lineage entries

Rules:

- use repo-relative forward-slash style
- no empty strings
- no backslash-separated repo paths in managed metadata
- no surrounding whitespace

## Initial Enforcement Scope

The first implementation pass should cover the highest-value required and
managed surfaces:

1. `docs/features/*/feature.source.yaml`
2. generated feature contracts
3. `docs/stages/*.source.yaml`
4. generated stage contracts
5. managed required root docs frontmatter
6. managed template examples under `docs/architecture_templates/`

Mode A prose templates may remain lighter-weight initially, but any metadata or
repo-config fields they carry should still stay canonical.

## First Canonical Rules To Add

### Feature Source

For `feature.source.yaml`, require canonical style for:

- `feature_id`
- `name`
- `status`
- `type`
- `summary`
- `depends_on`
- `domains`
- `capabilities[*].capability_id`
- `capabilities[*].name`
- `capabilities[*].summary`
- `capabilities[*].state`
- `stage_participation[*].stage_id`
- `stage_participation[*].role`
- `stage_participation[*].capability_ids`

Important early rule:

- `summary` must be a normalized concise string, not a folded multiline scalar
  with trailing blank space or blank lines

### Stage Source And Contracts

Apply the same concise-string and set-like-list rules to required stage fields
such as:

- `stage_id`
- `name`
- `summary`
- `primary_features`
- `supporting_features`

### Managed Root Docs

For required managed root-doc frontmatter:

- `doc_id` and `doc_type` must be normalized concise strings
- each `explains.*` list must contain unique, non-empty canonical IDs
- list ordering should be stable where order is non-semantic

### Templates

Starter-managed templates should demonstrate canonical formatting rather than
merely acceptable formatting. That keeps downstream migrations from copying
drift into new repos.

## Validator Design

Extend `validate_adoption_shape.py` with reusable canonical-style helpers
instead of embedding one-off string checks everywhere.

Suggested helper classes:

- `validate_concise_string(...)`
- `validate_string_list(...)`
- `validate_repo_relative_path(...)`
- `validate_no_duplicate_strings(...)`
- `validate_sorted_list_when_unordered(...)`

The validator should report:

- the file path
- the exact field path
- the canonical expectation that was violated
- the simplest corrective direction

Example error shape:

- `docs/features/cv_system/feature.source.yaml`
- `summary must be a canonical concise string with no leading/trailing whitespace or blank-line padding`

## Rollout Strategy

Implement this in phases.

### Phase 1

Fail on the most objective style problems:

- leading/trailing whitespace
- blank-line padding
- empty-string list items
- duplicate items in set-like lists
- non-canonical path separators

### Phase 2

Fail on concise-field multiline representations where the contract says the
field should stay concise.

### Phase 3

Expand canonical ordering rules to more unordered lists once current repos and
templates are aligned.

## Test Coverage

Add focused tests that prove the validator rejects:

- `summary` with trailing whitespace
- `summary` with trailing blank lines
- `summary` expressed as multiline padded content for concise fields
- duplicate items in unordered metadata lists
- empty-string items in metadata lists
- backslash repo paths in path/reference fields

Also prove canonical fixtures still pass for:

- managed feature sources
- stage docs
- generated contracts
- managed root docs
- starter templates

## Documentation Updates

Update the operating-system guidance so it says plainly:

- passing validation means schema and canonical style are both satisfied
- concise metadata fields should remain concise
- unordered metadata lists should stay deduplicated and stable
- templates are migration targets and must demonstrate canonical style

## Acceptance Criteria

- a follow-up implementation plan exists
- validator helpers exist for reusable canonical-style checks
- focused tests cover concise strings, unordered lists, and path normalization
- starter templates and guidance describe canonical style, not just required
  fields
- `scripts/validate_adoption_shape.py` still passes in the starter repo after
  the stricter rules land
