---
layer: operating_system
artifact_type: spec
status: completed
parent_workstream: none
targets:
  - scripts/audit_architecture_linkage.py
  - tools/docs/generate_architecture_metadata.py
  - scripts/validator_policy.py
  - tests/test_architecture_linkage_audit.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Manual Refs Shared Contract Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Centralize the `manual_refs` prohibition contract so the audit and generator enforce the same rule from one shared policy surface.
Reasoning: `manual_refs` is a real repo contract enforced in more than one place today. The audit and generator should not drift on the forbidden key name, rule wording, or remediation direction.
Invariants:

- `feature.source.yaml` remains human-owned semantic source, not a manual refs bridge.
- Metadata-derived refs remain the only supported ref path in managed architecture mode.
- The audit stays a focused awareness/strict check.
- The generator stays the canonical producer of generated contracts and evidence.
- This pass stays narrow and does not turn the generator into a validator-policy dumping ground.

Dependencies:

- `scripts/audit_architecture_linkage.py`
- `tools/docs/generate_architecture_metadata.py`
- `scripts/validator_policy.py`
- `tests/test_architecture_linkage_audit.py`
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

The repo treats `manual_refs` in `docs/features/*/feature.source.yaml` as a
forbidden legacy bridge. That contract is already enforced in two places:

- `scripts/audit_architecture_linkage.py`
- `tools/docs/generate_architecture_metadata.py`

Today both locations carry the rule separately:

- they both know the forbidden field name
- they both know the rule meaning
- they both tell the user to move back to metadata-derived refs

That duplication creates drift risk:

- one path could rename or expand the forbidden key rule without the other
- one path could change the remediation text while the other stays stale
- future follow-up checks could copy the rule again instead of reusing it

This is a better fit for a tiny shared contract than for duplicated local
string checks.

## Goal

Create one shared `manual_refs` contract that both the architecture-linkage
audit and the architecture generator can use.

## Non-Goals

This spec does not redesign how refs are derived.

This spec does not move broad generator validation logic into
`scripts/validator_policy.py`.

This spec does not fold all generator constants into shared policy.

This spec does not add new forbidden keys unless a separate design calls for
that later.

This spec does not change the generator output model or feature-source schema
beyond keeping `manual_refs` forbidden.

## Recommended Design

Extend `scripts/validator_policy.py` with a tiny shared contract for this rule.

Recommended shared items:

- forbidden key name:
  - `manual_refs`
- canonical rule statement:
  - metadata-derived refs are required
- canonical remediation text:
  - move ownership metadata to code, tests, docs, specs, plans, configs, or
    components instead of re-entering refs in feature source

Use that policy from both:

- `scripts/audit_architecture_linkage.py`
- `tools/docs/generate_architecture_metadata.py`

If a tiny helper improves clarity, it should stay minimal, for example:

- `feature_source_has_forbidden_manual_refs(payload)`

That helper should remain obviously contract-focused and avoid pulling parsing
or flow logic into the policy layer.

## Shared Policy Boundary

### Move Into Shared Policy

- forbidden field name for manual ref bridges
- canonical rule/remediation wording
- optional tiny predicate for checking whether a parsed feature source contains
  the forbidden field

### Keep Local To `audit_architecture_linkage.py`

- file walking
- audit CLI flags
- awareness vs strict mode behavior
- reporting format

### Keep Local To `generate_architecture_metadata.py`

- feature-source parsing
- contract assembly
- generator-specific validation flow
- generated file writing

This keeps the shared layer small and policy-oriented.

## Why This Split Is Better

This rule is stronger than a style preference. It is a repo contract:

- upstream feature semantics belong in `feature.source.yaml`
- downstream refs must derive from metadata
- `manual_refs` is explicitly not part of the allowed source model

Because both the audit and generator already enforce that same rule, one shared
contract gives us consistency without over-centralizing unrelated logic.

## Migration Strategy

### Phase 1

Add the shared `manual_refs` contract constants to `scripts/validator_policy.py`.

### Phase 2

Update `scripts/audit_architecture_linkage.py` to use the shared contract.

### Phase 3

Update `tools/docs/generate_architecture_metadata.py` to use the same shared
contract.

### Phase 4

Adjust or add focused tests so the audit still fails clearly when `manual_refs`
reappears and the generator still rejects the same drift.

## Validation And Test Strategy

Required proof:

- `tests/test_architecture_linkage_audit.py` still passes
- generator checks still fail clearly when `manual_refs` is present
- the shared rule does not change successful generation behavior when
  `manual_refs` is absent

Keep test additions narrow. One concise regression per execution path is enough
unless current coverage is missing.

## Documentation Updates

Update operating-system docs lightly so they describe the contract accurately:

- refs are metadata-derived, not manually re-entered in feature source
- the `manual_refs` prohibition is part of shared internal policy, not a loose
  convention

Keep the docs about the rule, not the implementation details.

## Recommendation

Take the same narrow approach that worked for shared repo-contract markers:

1. centralize the `manual_refs` contract
2. consume it from the audit and generator
3. stop there unless another real duplicated contract emerges

That closes a real drift seam without turning shared policy into a generic
bucket for everything.

## Acceptance Criteria

- `manual_refs` is defined as a forbidden contract in one shared policy place
- the audit and generator both use that shared contract
- user-facing remediation stays aligned across both paths
- tests still prove `manual_refs` rejection clearly
- operating-system docs continue to describe metadata-derived refs as the only
  supported model
