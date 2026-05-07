---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - tools/docs/generate_architecture_metadata.py
  - scripts/validate_adoption_shape.py
  - tests/test_architecture_metadata_generation.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Lineage Generated Schema Contract Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Make the `docs/features/<feature_id>/lineage.generated.yaml` schema explicit, canonical, and validator-enforced.
Reasoning: Different repos are currently producing different `lineage.generated.yaml` shapes. Some files use the current evidence-oriented lineage schema, while others still use older summary-style generated shapes. The guidance is not explicit enough about the canonical schema or the owning generator, so agents and downstream repos can produce plausible-looking but incorrect lineage files.
Invariants:

- `lineage.generated.yaml` is a generated artifact, never a human-owned source.
- There is one canonical schema for `lineage.generated.yaml`.
- The canonical lineage file is evidence-oriented, not a generic feature summary or index.
- Downstream repos must not substitute older repo-local lineage shapes once managed architecture metadata is adopted.
- Validator and generator guidance should reject legacy lineage schemas instead of tolerating them silently.

Dependencies:

- `tools/docs/generate_architecture_metadata.py`
- `scripts/validate_adoption_shape.py`
- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: all managed `docs/features/*/lineage.generated.yaml`
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs:
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
- readme: none
- generated: aggregate architecture outputs may be indirectly affected through generator consistency

Generated refresh required: yes
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

Two different generated file shapes are currently being treated as if they were
the same artifact:

1. the current starter-style lineage evidence schema
2. an older summary-style shape that includes contract-adjacent fields such as:
   - `generated_contract`
   - `naming_policy`
   - `capability_shape`
   - `capability_ids`
   - `refs`
   - `refs_by_type`

That older shape is not just a formatting variant. It represents a different
artifact contract.

The result is drift:

- agents can generate the wrong file shape and still think they satisfied the
  `lineage.generated.yaml` requirement
- downstream repos can carry repo-local legacy generators without being stopped
- the meaning of `lineage.generated.yaml` becomes ambiguous

## Goal

Define one explicit canonical schema for `lineage.generated.yaml` and enforce
it in validation.

The contract should make it clear that `lineage.generated.yaml` is:

- generated
- feature-local
- evidence-oriented
- capability-centric
- timeline-aware

It should also explicitly reject legacy summary/index-like top-level shapes.

## Non-Goals

This spec does not redesign the whole architecture metadata system.

This spec does not replace the generated feature contract
`docs/features/<feature_id>/<feature_id>.yaml`.

This spec does not attempt to preserve backward compatibility for older lineage
schemas once the canonical contract is adopted.

This spec does not define a second lineage artifact for summary-style views.

## Canonical Top-Level Shape

The canonical `lineage.generated.yaml` file must contain:

- generated header comment
- `feature_id`
- `source`
- `invariants`
- `capabilities`
- `timeline`

Top-level meaning:

- `feature_id`
  the owning feature ID
- `source`
  the human-owned feature source path
- `invariants`
  generated invariant lineage keyed by invariant ID
- `capabilities`
  generated capability lineage keyed by capability ID
- `timeline`
  completed-plan change history relevant to the feature

## Canonical Capability Lineage Shape

Within `capabilities`, each capability entry should remain keyed by capability
ID and should use the evidence-oriented shape produced by the current starter
generator, including fields such as:

- `state`
- `statement`
- `satisfies`
- `code`
- `tests`
- `docs`
- `docs_evidence`
- `configs`
- `config_evidence`
- `components`
- `component_evidence`
- `specs`
- `plans`
- `evidence_gaps`
- `allowed_evidence_gaps`
- `lineage_exception_reason`
- `unresolved_evidence_gaps`
- `completeness_status`

The exact field list may expand carefully over time, but the artifact must stay
evidence-oriented and keyed by capability ID.

## Explicitly Rejected Legacy Shape

Validator guidance should explicitly reject `lineage.generated.yaml` files that
look like the older summary-style schema, including top-level keys such as:

- `generated_contract`
- `naming_policy`
- `capability_shape`
- `capability_ids`
- `refs`
- `refs_by_type`

Those fields indicate that the file is serving as a summary/index or contract
adjunct rather than feature-local lineage evidence.

## Ownership Boundary

Clarify the ownership split:

- `feature.source.yaml`
  human-owned semantic source
- `<feature_id>.yaml`
  generated assembled current-state feature contract
- `lineage.generated.yaml`
  generated feature-local lineage evidence

The lineage file must not drift into feature-contract summary territory.

## Generator Contract

Update generator docs and code comments so they explicitly say:

- `tools/docs/generate_architecture_metadata.py` owns the canonical lineage
  schema
- repo-local legacy generators that emit older lineage shapes must be migrated
  or retired when managed architecture metadata is adopted

The migration guide should stop treating any generated `lineage.generated.yaml`
as acceptable.

It should instead say:

- the file must match the canonical evidence schema
- older summary-style lineage outputs are invalid in managed mode

## Validation Changes

Add validation that checks at least:

1. managed feature folders have `lineage.generated.yaml`
2. the file parses as a mapping
3. required top-level keys exist
4. legacy top-level keys are absent
5. `capabilities` is a mapping keyed by capability ID, not a list of summaries
6. the file carries the generated header

The first validator pass can be shape-based. It does not need to fully
reconstruct every nested evidence entry before it becomes useful.

## Documentation Changes

Update:

- `docs/operating_system/skill-doc-system-lifecycle.md`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`

to explicitly describe `lineage.generated.yaml` as:

- canonical generated feature-local lineage evidence
- not a summary contract
- not a generic refs inventory

The migration guide should also warn that if a downstream repo has an older
repo-local sync script producing the rejected shape, that script must be
updated before the repo can truthfully claim managed architecture metadata
alignment.

## Test Changes

Add tests that fail when:

- `lineage.generated.yaml` uses the old summary-style top-level keys
- `capabilities` is a list instead of a mapping
- the generated header is missing
- required top-level keys are missing

Also ensure the current generator still produces the canonical shape.

## Acceptance Criteria

The implementation is complete when:

- the canonical `lineage.generated.yaml` schema is described explicitly in docs
- validator rules reject legacy summary-style lineage files
- tests cover the rejected legacy shape and the required canonical shape
- migration guidance tells downstream repos to update legacy repo-local
  generators instead of accepting alternate lineage formats

## Open Questions

- Should the validator live in `scripts/validate_adoption_shape.py`, the
  architecture metadata validator, or both?
- Should we add a lightweight `schema_version` field, or is the canonical shape
  better identified by required/forbidden keys alone?
- Should we later add a migration helper that rewrites older lineage summary
  files into the new evidence-oriented structure when enough source evidence
  exists?
