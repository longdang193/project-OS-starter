---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - scripts/validate_repo_contracts.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Validator Policy Extraction Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Extract validator-owned policy constants and field-class definitions from `validate_adoption_shape.py` into a shared internal policy layer.
Reasoning: The validator now carries enough schema, metadata, template, style, and ordering policy that the current single-file constant block is becoming a maintenance risk. The repo needs one clearer source for validator policy without prematurely making those rules downstream-editable.
Invariants:

- Validator contract policy remains starter-owned, not ad hoc per-repo runtime config.
- Refactoring must not weaken existing validation behavior.
- Shared policy should be typed and testable.
- Validation flow logic should remain separate from policy data.
- This change should simplify future validator work, not create a second complexity layer.

Dependencies:

- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`
- `docs/superpowers/specs/2026-04-23-canonical-style-validation-spec.md`
- `docs/superpowers/specs/2026-04-23-canonical-ordering-rules-spec.md`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/skill-doc-system-lifecycle.md`

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
- cross_cutting_docs: none
- operating_system_docs:
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

`validate_adoption_shape.py` now owns several different classes of policy:

- required file and folder surfaces
- allowed adoption modes and starter sync surface classes
- managed root-doc rules
- generated feature/stage/lineage schema keys
- template paths and template-specific constraints
- field classes for canonical style and canonical ordering

That policy is all currently embedded as one long top-of-file constant block.

This causes several problems:

- policy edits are harder to review because schema and validation flow change in the same file
- new validator features keep expanding one script instead of a clearer policy surface
- related rule families are harder to discover and reuse
- future refactors risk duplicating policy across multiple validators

The repo is at the point where validator policy deserves its own internal home.

## Goal

Create a shared internal validator policy layer that centralizes stable rule data
while keeping validation logic in the validator scripts.

## Non-Goals

This spec does not make validator policy user-editable through repo YAML.

This spec does not introduce downstream override behavior.

This spec does not redesign the validator flow itself.

This spec does not require moving every helper or every tiny constant out of the
validator script.

This spec does not force `validate_repo_contracts.py` to adopt the new policy
layer in the same first implementation unless there is an obvious low-risk win.

## Recommended Design

Start with a typed Python policy module, not external YAML.

Recommended shape:

```text
scripts/
  validator_policy/
    __init__.py
    adoption.py
    docs.py
    schemas.py
    templates.py
    canonical.py
```

This can also start as a single file such as `scripts/validator_policy.py` if
the first extraction should stay smaller. The important part is separating
policy from validation flow, not maximizing file count.

## Why Python First

Python is the better first extraction layer because:

- validator rules are code-owned contract policy
- many rule sets are structured and interdependent
- we want typed names and importable constants
- bootstrapping a YAML config layer would add another parser and schema to
  validate before the validator can even run
- tests remain simpler when policy is imported directly

Later, if there is a real need for controlled repo-level extension points, a
small subset can be made configurable deliberately. That should be a separate
design, not folded into this refactor by default.

## Policy Categories To Extract

### 1. Adoption And Folder Surface Policy

Examples:

- allowed adoption modes
- required project folders
- required starter sync surface classes
- method-layer pseudo-feature IDs and prefixes

### 2. Required Root-Doc Policy

Examples:

- required root doc paths
- optional managed root doc paths
- expected `doc_id` values
- required `explains.*` groups
- semantic keyword coverage guidance

### 3. Schema-Key Policy

Examples:

- feature contract required keys
- stage contract required keys
- generated discovery required keys
- lineage required keys and allowed completeness statuses

### 4. Template Policy

Examples:

- template paths
- required Mode A template files
- markers forbidden in Mode A templates
- template-specific feature-qualified capability rules

### 5. Canonical Field-Class Policy

Examples:

- concise-string field registries
- unordered-list field registries
- ordered-sequence exemptions
- path-like field registries
- ordering-enabled field sets

This category is especially important because recent work has made canonical
style and ordering policy a first-class validator concern.

## Separation Boundary

Keep these things in policy:

- stable constants
- field registries
- schema-required key sets
- expected paths and expected IDs
- explicit ordering/classification declarations

Keep these things in validator logic:

- file walking
- YAML/frontmatter parsing
- helper execution flow
- finding creation
- control flow for mode-specific validation

That split keeps the validator executable and understandable while giving policy
rules a real home.

## Migration Strategy

### Phase 1

Extract only `validate_adoption_shape.py` policy into a shared module.

### Phase 2

Clean up naming and collapse obviously redundant constant families after the
extraction is stable.

### Phase 3

Evaluate whether `validate_repo_contracts.py` should import selected shared
policy instead of carrying parallel copies or assumptions.

## Validation And Test Strategy

The refactor should be behavior-preserving.

Required proof:

- existing `test_validate_adoption_shape.py` still passes unchanged or with only
  import-neutral fixture updates
- `scripts/validate_adoption_shape.py` output remains stable for representative
  failure cases
- no rule is lost during extraction

Add focused tests only if needed to lock down the policy module structure or to
guard against accidental omission of key rule families.

## Documentation Updates

Update operating-system docs only lightly:

- note that validator contract policy now lives in a shared internal policy
  module
- keep docs clear that this is starter-owned validator policy, not general
  runtime config

Do not over-document internal module layout unless it becomes part of normal
repo-maintenance workflow.

## Recommendation

Use the simplest extraction path first:

1. create `scripts/validator_policy.py`
2. move the top-level policy constants into grouped sections there
3. import them back into `validate_adoption_shape.py`
4. only split into a package if the single policy module becomes unwieldy again

That path delivers most of the maintenance benefit with minimal churn.

## Acceptance Criteria

- validator-owned policy no longer lives as one giant constant block inside
  `validate_adoption_shape.py`
- extracted policy is grouped by responsibility
- `validate_adoption_shape.py` remains easier to read after the refactor
- all existing validator tests still pass
- docs clearly frame the extracted layer as internal validator policy, not
  downstream runtime configuration
