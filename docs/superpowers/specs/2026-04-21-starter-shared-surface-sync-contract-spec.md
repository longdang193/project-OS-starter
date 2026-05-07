---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - repo_config/adoption-mode.yaml
  - repo_config/
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/adoption_guide.md
  - scripts/validate_adoption_shape.py
related_features: []
related_stages: []
---

# Starter Shared-Surface Sync Contract Spec

## Triage

Layer: operating_system
Feature type: CHANGE
Summary: Define a stronger Mode B contract for reviewing and recording sync of starter-owned shared repo-control surfaces.
Reasoning: Mode B guidance now tells projects to diff shared repo-control files forward from newer starter versions, but that rule is still only guidance. Without a recorded review contract and validator support, projects can silently let critical shared surfaces drift while thinking only product metadata matters.
Invariants:

- The private repo remains the development source of truth.
- Mode B projects may customize shared repo-control files, but drift from newer starter versions must be intentional and reviewable.
- Shared repo-control sync should be stronger than advice, but weaker than a byte-for-byte mirror requirement.
- Critical control files deserve stricter enforcement than project-facing docs.
- Canonical truth for starter-owned repo method should flow from the starter into downstream projects, with downstream divergence recorded rather than re-entered ad hoc.

Dependencies:

- `docs/operating_system/adoption/project-adoption-migration-guide.md`
- `docs/adoption_guide.md`
- `repo_config/adoption-mode.yaml`
- `scripts/validate_adoption_shape.py`

Affected stages:

- none

Affected features:

- none

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
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/adoption_guide.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

Mode B migration now tells projects to diff shared repo-control surfaces when
they bring forward newer starter changes. That is a healthy direction, but it
is not yet enforceable or even machine-discoverable.

Today a project can:

- adopt Mode B
- migrate product feature metadata
- keep old repo-control surfaces
- skip reviewing newer validation, adapter, governance, or instruction files
- still look "done" unless a human notices the drift

That leaves a real class of failure:

- weaker validators than the current starter expects
- stale skills, rules, or governance docs
- outdated adapter mappings or sync surfaces
- silent divergence with no record of whether it was intentional

## Goal

Create a shared-surface sync contract for Mode B projects that is stronger than
guidance but does not require exact mirroring.

The contract should:

- require a recorded shared-surface sync review when starter updates are adopted
- classify shared surfaces by enforcement level
- allow intentional project-local divergence
- give validators something concrete to check

## Non-Goals

This spec does not require downstream projects to match starter files byte for
byte.

This spec does not require automatic pulling from a remote starter repo.

This spec does not define a full three-way merge tool in the first step.

This spec does not force Mode A or Mode C projects into the same strictness.

## Proposed Contract

For Mode B projects, starter-owned shared repo-control surfaces should have a
reviewable sync record whenever the project adopts newer starter updates.

The contract has four parts:

1. record the reviewed starter baseline
2. record that shared surfaces were reviewed
3. classify divergences by file class
4. validate the presence and shape of that record

## Proposed Repo Config Addition

Add a structured section under `repo_config/adoption-mode.yaml` or a dedicated
adjacent file in `repo_config/` to record starter shared-surface sync review.

Example shape:

```yaml
starter_sync:
  starter_baseline_ref: <commit-or-tag>
  last_shared_surface_review_at: <ISO-8601 date or timestamp>
  review_required: true
  reviewed_surface_classes:
    - repo_config
    - operating_system_docs
    - skills
    - adapters
    - generated_instruction_surfaces
    - validation_and_sync_scripts
  divergences:
    - path: docs/operating_system/procedures/publication-workflow.md
      class: operating_system_docs
      status: customized
      rationale: Project-specific publication workflow details retained.
```

The exact field names can change during implementation, but the record must
support:

- which starter baseline was reviewed
- when the review happened
- which surface classes were reviewed
- which divergences are intentional

## File-Class Enforcement Levels

Not every shared surface should be treated the same.

### Tier 1: Must Review And Usually Stay Aligned

These are control surfaces whose drift can weaken governance or validation:

- `repo_config/*`
- adapter mappings
- validation scripts
- sync scripts
- starter-controlled generator entrypoints

Expected behavior:

- review required
- divergence allowed only with explicit rationale

### Tier 2: Must Review, Local Customization Expected

These are shared method surfaces that often need local adaptation:

- `docs/operating_system/*`
- `.agents/skills/*`
- adapter templates

Expected behavior:

- review required
- customization normal
- divergence should still be declared when meaningful

### Tier 3: Generated Downstream Surfaces

These should be re-synced from source rather than hand-maintained:

- `AGENTS.md`
- `.codex/rules/*`

Expected behavior:

- review upstream source changes
- regenerate downstream surfaces after source updates
- validator checks that generated outputs exist when their source layer is adopted

## Validation Scope

Extend `scripts/validate_adoption_shape.py` or a sibling validator so that for
Mode B projects it can check at least:

- a shared-surface sync record exists
- the record includes a starter baseline reference
- the record includes a last review timestamp
- required surface classes are listed
- divergence entries, when present, have required fields

The first validator phase should check record presence and shape, not content
equality.

That is enough to stop silent neglect without forcing brittle exact matching.

## Guidance Updates

Update adoption docs so the contract is explicit:

- `docs/operating_system/adoption/project-adoption-migration-guide.md`
- `docs/adoption_guide.md`

The docs should move from:

- "diff shared files forward"

to:

- "record the baseline reviewed, the surface classes reviewed, and any
  intentional divergences"

## Future Follow-Up

Leave room for a later diff-driven helper that compares a project against a
starter baseline and emits:

- missing upstream changes
- declared divergence
- undeclared divergence
- regenerated downstream outputs needed

That helper is not required in the first implementation, but the contract
should make it possible.

## Acceptance Criteria

The implementation is complete when:

- Mode B has a machine-readable shared-surface sync record
- the record includes baseline, review timing, and reviewed surface classes
- intentional divergences can be declared
- validator checks record presence and shape for Mode B
- adoption docs explain the stronger contract clearly

## Open Questions

- Should the sync record live inside `repo_config/adoption-mode.yaml` or in a
  separate `repo_config/starter-sync.yaml` file?
- Should divergence recording be required for every customized file, or only
  for Tier 1 control surfaces at first?
- Should the validator warn or fail when a Mode B project has no recorded
  starter baseline reference?
