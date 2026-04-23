---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/architecture_templates/feature.source.yaml
  - docs/architecture_templates/stage.source.yaml
  - docs/architecture_templates/markdown-frontmatter.md
related_features: []
related_stages: []
---

# Canonical Ordering Rules Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Add a second validator phase that enforces stable canonical ordering for non-semantic metadata lists and mappings across required managed surfaces.
Reasoning: Phase 1 closed the biggest normalization gaps, but repos can still drift through unordered lists that contain the right values in inconsistent orders. That makes diffs noisy, templates less reliable, and generated-doc migration harder to compare. We want stable ordering where order is not meaning.
Invariants:

- Canonical truth still flows downward from owning layers into downstream views.
- Ordering enforcement applies only to fields whose order is non-semantic.
- Ordered workflow and chronology surfaces must stay exempt.
- The validator should reject non-canonical ordering; it should not silently rewrite files.
- Canonical ordering rules should be narrow, explicit, and field-class based.

Dependencies:

- `docs/superpowers/specs/2026-04-23-canonical-style-validation-spec.md`
- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`
- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/project-adoption-migration-guide.md`

Affected stages:

- all managed stages indirectly through ordering rules on stage source, stage contracts, and linked root-doc metadata

Affected features:

- all managed features indirectly through ordering rules on feature source, generated contracts, lineage references, and linked root-doc metadata

Primary lens: cross-cutting

Affected docs:

- feature_source:
  - `docs/features/*/feature.source.yaml`
- feature_yaml:
  - `docs/features/*/<feature_id>.yaml`
- feature_lineage:
  - `docs/features/*/lineage.generated.yaml`
- feature_history: none
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
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/architecture_templates/feature.source.yaml`
  - `docs/architecture_templates/stage.source.yaml`
  - `docs/architecture_templates/markdown-frontmatter.md`
- readme: none
- generated:
  - `docs/generated/capability_lineage.yaml`

Generated refresh required: no for starter changes; yes for downstream repos whose managed metadata uses valid-but-non-canonical unordered ordering
Capability IDs: none new
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

Phase 1 canonical-style validation now catches trimming, duplicate-item, empty-item,
and path-format drift. That still leaves a quieter class of drift:

- the same unordered metadata values appear in different orders across files
- template examples and downstream migrations do not converge on one stable order
- diffs become noisy even when semantics do not change
- agents may preserve local incidental order instead of writing the canonical one

Examples:

- `domains` listed in different lexical orders between similar features
- `depends_on` or `explains.features` reordered by human edits
- `feature_refs`, `config_refs`, or `component_refs` emitted in unstable order
- template examples that are semantically fine but do not model the target order

These are not semantic errors, but they are contract and maintenance problems.

## Goal

Define a second canonical-validation phase that enforces stable ordering for
unordered metadata fields and any mapping families where key order is part of
the repo's canonical presentation contract.

## Non-Goals

This spec does not sort chronology or workflow sequences.

This spec does not auto-rewrite files.

This spec does not impose one global ordering rule on every list in the repo.

This spec does not treat source-order as semantic when the schema already says
the field is set-like.

This spec does not require downstream repos to fix everything at once; rollout
should remain field-scoped and objective.

## Ordering Taxonomy

### 1. Unordered Identifier Lists

These are membership lists where order does not carry meaning.

Examples:

- `domains`
- `depends_on`
- `lineage_exceptions`
- `stage_participation[*].capability_ids`
- `primary_features`
- `supporting_features`
- root-doc `explains.features`
- root-doc `explains.capabilities`
- root-doc `explains.stages`
- root-doc `explains.configs`
- root-doc `explains.components`
- generated ref families such as `feature_refs`, `capability_refs`, `doc_refs`,
  `config_refs`, and `component_refs`

Rule:

- enforce stable lexical ascending order after Phase 1 normalization

### 2. Unordered Path Lists

These are repo-relative path membership lists where order does not carry
meaning.

Examples:

- `refs.code`
- `refs.tests`
- `refs.docs`
- `refs.specs`
- `refs.plans`
- `refs.configs`
- `refs.components`
- lineage `verification` when represented as a list of path-like references

Rule:

- enforce canonical repo-relative path formatting first
- then enforce lexical ascending order on the normalized path string

### 3. Mapping Families With Canonical Presentation Order

Some mappings are semantically keyed, but the repo still benefits from a stable
key order for diff hygiene and template consistency.

Examples:

- `explains` child groups in Markdown frontmatter
- `refs` child groups in generated feature contracts
- top-level sections in `lineage.generated.yaml` where the schema already has a
  fixed presentation contract

Rule:

- enforce an explicit schema-owned key order, not ad hoc lexical order

### 4. Explicitly Ordered Sequences

These must remain exempt.

Examples:

- `timeline`
- completed change records
- process or workflow step lists
- any future field whose order is documented as semantic

Rule:

- do not sort
- validator may still enforce item shape, but not lexical order

## Canonical Ordering Policy

Use lexical ordering only for true unordered value lists.

Use explicit schema-owned order for mappings and for mixed ref families where
human readability depends on a known presentation sequence.

Recommended default group order where the schema already exposes these families:

1. feature identifiers
2. capability identifiers
3. code refs
4. test refs
5. doc refs
6. config refs
7. component refs
8. specs and plans where they appear in generated evidence views

Do not infer canonical order from current incidental file order alone. The
ordering rule must be documented per field class.

## Proposed Phase 2 Scope

Start with fields that are both high-value and low-ambiguity:

1. `feature.source.yaml`
   - `domains`
   - `depends_on`
   - `lineage_exceptions`
   - `stage_participation[*].capability_ids`
2. `docs/stages/*.source.yaml`
   - `primary_features`
   - `supporting_features`
   - `inputs`
   - `outputs`
3. managed root-doc frontmatter
   - all `explains.*` lists
4. generated stage contracts
   - `feature_refs`
   - `capability_refs`
   - `doc_refs`
   - `config_refs`
   - `component_refs`
5. generated feature contracts
   - `domains`
   - `depends_on`
   - `refs.*`

Defer harder questions until later:

- ordering inside `capabilities` mappings
- ordering of nested evidence arrays where generator output may still vary
- ordering rules that would require downstream generator rewrites first

## Validator Design

Extend the Phase 1 helper layer with reusable ordering helpers.

Suggested helpers:

- `validate_sorted_string_list(...)`
- `validate_sorted_path_list(...)`
- `validate_mapping_key_order(...)`
- `canonical_sort_key_for_repo_path(...)`

Behavior:

- run Phase 1 normalization checks first
- only run ordering checks when the values are already valid members of the
  field class
- emit exact field-path findings that say both the current and expected order
  in a concise way

Example finding:

- `feature.source.yaml depends_on must use canonical lexical order.`
- `fix: reorder items as [a, b, c].`

## Template And Guidance Updates

Update starter templates and operating-system docs so they say plainly:

- canonical style includes ordering for unordered fields
- ordered workflow or chronology lists remain exempt
- generated surfaces should emit stable canonical order, not just valid values
- downstream migrations should normalize ordering before calling the metadata
  settled

## Rollout Strategy

### Phase 2A

Land ordering rules only for human-authored unordered lists and root-doc
frontmatter lists.

### Phase 2B

Expand to generated feature and stage contract ref families once the starter
fixtures and generator outputs are confirmed stable.

### Phase 2C

Consider explicit mapping-key order checks for a small number of schema-owned
presentation mappings if the benefit remains high and the noise stays low.

## Test Coverage

Add focused tests that prove the validator rejects:

- unsorted `domains` and `depends_on` in feature source
- unsorted `capability_ids` in `stage_participation`
- unsorted `primary_features` and `supporting_features` in stage source
- unsorted `explains.*` lists in managed root docs
- unsorted generated `refs.*` lists and stage ref families where Phase 2B is enabled

Also prove canonical fixtures still pass with the documented sort policy.

## Acceptance Criteria

- a follow-up implementation plan exists
- field classes that are unordered versus ordered are documented explicitly
- starter docs explain that ordering is part of canonical style only for
  non-semantic fields
- validator helpers are designed to check ordering without touching semantic
  sequences
- the starter repo can adopt the new ordering rules without false positives on
  its own fixtures and templates
