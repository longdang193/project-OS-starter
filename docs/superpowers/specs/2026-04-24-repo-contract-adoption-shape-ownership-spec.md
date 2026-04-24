---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - scripts/validate_repo_contracts.py
  - scripts/validate_repo_config.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_repo_config.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Repo Contract And Adoption-Shape Ownership Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Restore `validate_adoption_shape.py` as the sole owner of required root-doc and managed root-doc metadata validation, and make the canonical repo-contract gate call that validator directly.
Reasoning: Required root docs and their managed metadata are adoption-shape contract surfaces, not repo-config ownership surfaces. Duplicating those rules in `validate_repo_config.py` creates drift and weakens the canonical gate.
Invariants:

- Required root-doc presence and managed metadata remain validator-enforced.
- `validate_adoption_shape.py` stays the single owner of adoption-shape root-doc rules.
- `validate_repo_config.py` remains focused on repo/system config and runtime config validation.
- `scripts/validate_repo_contracts.py` remains the canonical repo-wide contract command.
- The canonical gate must not pass while skipping adoption-shape root-doc drift.

Dependencies:

- `scripts/validate_repo_contracts.py`
- `scripts/validate_adoption_shape.py`
- `scripts/validate_repo_config.py`
- `tests/test_validate_repo_contracts.py`
- `tests/test_validate_repo_config.py`
- `docs/operating_system/repo-governance.md`
- `docs/operating_system/doc-system-lifecycle.md`

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
  - `docs/operating_system/doc-system-lifecycle.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The current uncommitted validator/config changes move required root-doc checks
into `scripts/validate_repo_config.py`.

That creates two owners for the same contract:

- `scripts/validate_adoption_shape.py` already validates required root-doc
  presence, heading/content quality, semantic coverage, and managed root-doc
  frontmatter contracts
- `scripts/validate_repo_config.py` now validates a second, weaker version of
  that same surface

This introduces two concrete problems:

1. duplicated contract logic can drift
2. the canonical repo-contract gate can miss adoption-shape drift if it relies
   on the weaker duplicate instead of invoking the real owner

That is the opposite of the repo’s own doc-system rule that canonical truth
should flow downward from the owning layer instead of being re-entered by a
downstream layer.

## Goal

Keep one owner for adoption-shape root-doc rules and make the canonical
repo-contract command invoke that owner directly.

## Non-Goals

This spec does not redesign root-doc requirements.

This spec does not weaken required root-doc validation.

This spec does not merge `validate_repo_config.py` into
`validate_adoption_shape.py`.

This spec does not redesign the broader repo-contract orchestration model.

## Recommended Design

### Ownership

Treat required root docs and their managed metadata as adoption-shape policy.

That means:

- `scripts/validate_adoption_shape.py` owns those rules
- `scripts/validate_repo_config.py` does not duplicate them

### Canonical gate

`scripts/validate_repo_contracts.py` should call:

1. `scripts/sync_architecture_docs.py --check`
2. `scripts/validate_adoption_shape.py`
3. `scripts/validate_repo_config.py`

This keeps the canonical gate broad while preserving single ownership for each
contract family.

### Tests

- remove repo-config tests that assert required root-doc behavior
- add or update repo-contract tests so the orchestration path explicitly
  includes adoption-shape validation

### Docs

State plainly in the operating-system docs that:

- required root-doc validation is enforced through the adoption-shape validator
- the canonical repo-contract gate includes that validator as part of its
  normal flow

## Acceptance Criteria

- `validate_repo_config.py` no longer validates required root docs or managed
  root-doc metadata
- `validate_repo_contracts.py` invokes `validate_adoption_shape.py` directly
- repo-config tests cover only repo-config ownership surfaces
- repo-contract tests cover the canonical orchestration path
- operating-system docs describe the ownership boundary accurately
