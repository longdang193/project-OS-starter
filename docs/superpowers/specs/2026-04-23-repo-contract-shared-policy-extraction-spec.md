---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - scripts/validate_repo_contracts.py
  - scripts/validate_adoption_shape.py
  - scripts/validator_policy.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Repo Contract Shared Policy Extraction Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Extract the small shared policy contract that already exists across `validate_repo_contracts.py` and `validate_adoption_shape.py` so boundary markers and metadata-marker rules stop drifting.
Reasoning: `validate_repo_contracts.py` is mostly orchestration flow, not policy sprawl. The problem is narrower: a few repo-contract rules are duplicated across validators and deserve one source of truth.
Invariants:

- `validate_repo_contracts.py` remains the canonical repo-contract orchestrator.
- Shared rule extraction must not pull subprocess orchestration into a policy layer.
- `history.md` mixed-ownership boundaries must stay validator-enforced.
- Required metadata markers must keep their current meaning unless explicitly changed.
- The refactor should reduce drift risk without making validator structure harder to read.

Dependencies:

- `scripts/validate_repo_contracts.py`
- `scripts/validate_adoption_shape.py`
- `scripts/validator_policy.py`
- `tests/test_validate_repo_contracts.py`
- `tests/test_validate_adoption_shape.py`
- `docs/superpowers/specs/2026-04-23-validator-policy-extraction-spec.md`

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

The repo already has a shared validator policy module for adoption-shape rules,
but `validate_repo_contracts.py` still carries a small set of duplicated
contract policy locally:

- the `history.md` mixed-ownership boundary markers
- the required `## Human Notes` boundary after the generated history block
- the meaning of top-of-file metadata markers like `# @architecture` and
  `@meta`

Those rules are not just local implementation details. They define repo
contract behavior, and at least part of that behavior is already validated from
another validator as well.

This creates avoidable drift risk:

- one validator can tighten the history boundary contract while another keeps
  the old shape
- marker-policy changes can be made in one place without the other inheriting
  them
- future rule expansion encourages copy-paste rather than reuse

At the same time, `validate_repo_contracts.py` is not suffering from the same
full-file policy sprawl that justified the earlier `validate_adoption_shape.py`
extraction. Most of the file is still validation flow and subprocess
orchestration.

So the right move is a narrow shared-policy extraction, not a broad rewrite.

## Goal

Move genuinely shared repo-contract policy into the shared validator policy
layer, while keeping `validate_repo_contracts.py` responsible for repo-wide
execution flow.

## Non-Goals

This spec does not move subprocess step definitions into shared policy.

This spec does not make `validate_repo_contracts.py` repo-configurable.

This spec does not redesign the reporting format, issue model, or `--fast`
behavior.

This spec does not require moving every small helper out of
`validate_repo_contracts.py`.

This spec does not change the meaning of history boundaries or required marker
policy unless an implementation finds a clearly broken inconsistency that must
be normalized.

## Recommended Design

Extend `scripts/validator_policy.py` with a small repo-contract section instead
of creating another policy file.

Recommended additions:

- history boundary constants:
  - generated start marker
  - generated end marker
  - required human-owned heading
- metadata marker policy:
  - required architecture marker line
  - required setup metadata marker line

Optionally, add one or two tiny helper predicates in shared policy only if they
truly improve reuse and stay obviously policy-oriented. The main parsing and
validation flow should remain in the validator scripts.

## Shared Policy Boundary

### Move Into Shared Policy

- exact marker strings for `history.md` boundaries
- exact heading string for the human-maintained section
- canonical top-of-file metadata marker strings used by repo-contract
  validation

### Keep Local To `validate_repo_contracts.py`

- `build_subprocess_steps()`
- `run_step()`
- `--fast` branching behavior
- issue aggregation and console reporting
- file walking and step execution control flow

### Keep Local To `validate_adoption_shape.py`

- broader adoption-mode schema and template validation flow
- managed root-doc and generated-surface validation flow

This keeps the shared layer truly about policy, not about execution.

## Why This Split Is Better

This narrower split matches how the code is actually shaped today.

`validate_repo_contracts.py` is a coordinator:

- run local policy checks
- run other validators and sync checks
- fail fast if anything breaks the repo contract

That file benefits from a small shared policy import, but not from being turned
into another policy-heavy script skeleton.

## Migration Strategy

### Phase 1

Add the shared repo-contract marker constants to `scripts/validator_policy.py`.

### Phase 2

Update `validate_repo_contracts.py` to import and use those shared constants.

### Phase 3

Update `validate_adoption_shape.py` to use the same shared history-boundary
constants if it still carries its own local copy of that contract.

### Phase 4

Add or update focused tests so the shared policy contract is locked down in both
validator paths.

## Validation And Test Strategy

The first implementation should be behavior-preserving.

Required proof:

- `tests/test_validate_repo_contracts.py` still passes
- `tests/test_validate_adoption_shape.py` still passes
- the repo-contract validator still rejects malformed `history.md` boundaries
- the repo-contract validator still rejects missing top-of-file `# @architecture`
  or `@meta` markers where required

If any tests currently cover only one side of the shared contract, add a small
regression case rather than duplicating large fixtures.

## Documentation Updates

Update operating-system docs lightly to reflect the new ownership split:

- `scripts/validator_policy.py` now owns shared validator contract strings for
  repo-contract and adoption-shape validation
- `validate_repo_contracts.py` remains the canonical orchestration entrypoint

Keep the docs concise. This is an internal maintenance improvement, not a new
repo workflow for users.

## Recommendation

Take the smallest useful extraction path:

1. add shared history-boundary and marker constants to `scripts/validator_policy.py`
2. import them into `validate_repo_contracts.py`
3. align `validate_adoption_shape.py` with the same history-boundary constants
   where applicable
4. stop there unless another duplicated contract rule becomes obvious

That gets us the benefit we want: one source of truth for the shared repo
contract policy, without over-centralizing a script whose main job is still
flow orchestration.

## Acceptance Criteria

- shared history-boundary and marker strings are no longer duplicated across
  validator files
- `validate_repo_contracts.py` stays primarily flow/orchestration code
- `validate_adoption_shape.py` and `validate_repo_contracts.py` rely on the
  same boundary contract for `history.md`
- validator behavior remains stable for existing passing and failing cases
- operating-system docs describe the split accurately and briefly
